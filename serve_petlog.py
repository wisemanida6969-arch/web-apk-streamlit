"""
PetLog server wrapper.

Streamlit intercepts every URL path with its React SPA, so /sitemap.xml
and /robots.txt cannot be reached at the root. This wrapper runs a thin
aiohttp reverse proxy in front of Streamlit:

  - GET /sitemap.xml  → static petlog_sitemap.xml from disk
  - GET /robots.txt   → static petlog_robots.txt from disk
  - everything else (HTTP + WebSocket) → proxied to Streamlit on an
    internal port, so the app continues to work exactly as before.

Modeled after postgenie/serve.py — same approach, different files.
"""
import asyncio
import os
import pathlib
import signal
import subprocess
import sys

import aiohttp
from aiohttp import web, WSMsgType

HERE = pathlib.Path(__file__).resolve().parent

PORT = int(os.environ.get("PORT", "8501"))
INTERNAL_PORT = int(os.environ.get("STREAMLIT_INTERNAL_PORT", "8599"))
INTERNAL_HOST = "127.0.0.1"

STATIC_FILES = {
    "/sitemap.xml": ("petlog_sitemap.xml", "application/xml; charset=utf-8"),
    "/robots.txt": ("petlog_robots.txt", "text/plain; charset=utf-8"),
}

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
}


async def static_handler(request: web.Request) -> web.Response:
    filename, ctype = STATIC_FILES[request.path]
    path = HERE / filename
    if not path.exists():
        return web.Response(status=404, text="Not found")
    return web.Response(
        body=path.read_bytes(),
        content_type=ctype.split(";")[0].strip(),
        charset="utf-8",
        headers={"Cache-Control": "public, max-age=3600"},
    )


async def websocket_proxy(request: web.Request) -> web.WebSocketResponse:
    ws_server = web.WebSocketResponse()
    await ws_server.prepare(request)

    target = f"ws://{INTERNAL_HOST}:{INTERNAL_PORT}{request.rel_url}"
    session: aiohttp.ClientSession = request.app["session"]

    try:
        async with session.ws_connect(target, autoping=False) as ws_client:

            async def client_to_server():
                async for msg in ws_client:
                    if msg.type == WSMsgType.TEXT:
                        await ws_server.send_str(msg.data)
                    elif msg.type == WSMsgType.BINARY:
                        await ws_server.send_bytes(msg.data)
                    elif msg.type == WSMsgType.PING:
                        await ws_server.ping(msg.data)
                    elif msg.type == WSMsgType.PONG:
                        await ws_server.pong(msg.data)
                    elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
                        break

            async def server_to_client():
                async for msg in ws_server:
                    if msg.type == WSMsgType.TEXT:
                        await ws_client.send_str(msg.data)
                    elif msg.type == WSMsgType.BINARY:
                        await ws_client.send_bytes(msg.data)
                    elif msg.type == WSMsgType.PING:
                        await ws_client.ping(msg.data)
                    elif msg.type == WSMsgType.PONG:
                        await ws_client.pong(msg.data)
                    elif msg.type in (WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR):
                        break

            await asyncio.gather(client_to_server(), server_to_client())
    except Exception as e:
        print(f"[petlog-proxy] websocket error: {e}", flush=True)
    finally:
        if not ws_server.closed:
            await ws_server.close()
    return ws_server


async def http_proxy(request: web.Request) -> web.StreamResponse:
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return await websocket_proxy(request)

    target = f"http://{INTERNAL_HOST}:{INTERNAL_PORT}{request.rel_url}"

    out_headers = {}
    for k, v in request.headers.items():
        if k.lower() in HOP_BY_HOP or k.lower() == "host":
            continue
        out_headers[k] = v

    session: aiohttp.ClientSession = request.app["session"]
    body = await request.read() if request.can_read_body else None

    async with session.request(
        request.method,
        target,
        headers=out_headers,
        data=body,
        allow_redirects=False,
    ) as upstream:
        data = await upstream.read()
        resp_headers = {
            k: v for k, v in upstream.headers.items() if k.lower() not in HOP_BY_HOP
        }
        return web.Response(
            body=data,
            status=upstream.status,
            reason=upstream.reason,
            headers=resp_headers,
        )


async def wait_for_streamlit(timeout: float = 60.0) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout
    async with aiohttp.ClientSession() as s:
        while asyncio.get_event_loop().time() < deadline:
            try:
                async with s.get(
                    f"http://{INTERNAL_HOST}:{INTERNAL_PORT}/_stcore/health",
                    timeout=aiohttp.ClientTimeout(total=2),
                ) as r:
                    if r.status == 200:
                        return True
            except Exception:
                pass
            await asyncio.sleep(0.5)
    return False


def start_streamlit() -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "petlog_app.py",
        "--server.port",
        str(INTERNAL_PORT),
        "--server.address",
        INTERNAL_HOST,
        "--server.headless",
        "true",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false",
        "--browser.gatherUsageStats",
        "false",
    ]
    print(f"[petlog-proxy] starting streamlit: {' '.join(cmd)}", flush=True)
    return subprocess.Popen(cmd, cwd=str(HERE))


async def main() -> None:
    streamlit_proc = start_streamlit()

    async def shutdown(*_):
        print("[petlog-proxy] shutting down", flush=True)
        try:
            streamlit_proc.terminate()
        except Exception:
            pass

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        except NotImplementedError:
            pass

    print("[petlog-proxy] waiting for streamlit to become healthy…", flush=True)
    ready = await wait_for_streamlit()
    if not ready:
        print("[petlog-proxy] WARNING: streamlit did not report healthy in time; proxying anyway", flush=True)

    app = web.Application(client_max_size=1024 * 1024 * 50)
    app["session"] = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=0),
        auto_decompress=False,
    )

    async def close_session(app):
        await app["session"].close()

    app.on_cleanup.append(close_session)

    for path in STATIC_FILES:
        app.router.add_get(path, static_handler)
    app.router.add_route("*", "/", http_proxy)
    app.router.add_route("*", "/{tail:.*}", http_proxy)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"[petlog-proxy] listening on 0.0.0.0:{PORT} -> streamlit {INTERNAL_HOST}:{INTERNAL_PORT}", flush=True)

    while True:
        if streamlit_proc.poll() is not None:
            print(f"[petlog-proxy] streamlit exited with code {streamlit_proc.returncode}", flush=True)
            break
        await asyncio.sleep(2)

    await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
