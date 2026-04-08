import streamlit as st, pathlib, re, shutil, traceback

try:
    p = pathlib.Path(st.__file__).parent / "static" / "index.html"
    print(f"[SEO] path={p} exists={p.exists()}")

    h = p.read_text(encoding="utf-8")
    print(f"[SEO] read {len(h)} chars")

    # Title
    h = re.sub(r"<title>[^<]*</title>",
               "<title>Trytimeback - AI YouTube Summarizer &amp; PDF Export</title>", h)

    # Lang
    h = re.sub(r'lang="[^"]*"', 'lang="en"', h, count=1)

    # Noscript
    h = re.sub(r"<noscript>.*?</noscript>",
               "<noscript><h1>Trytimeback - AI YouTube Summarizer</h1>"
               "<p>Paste any YouTube URL and get 5 key-point clips plus a detailed PDF summary. "
               "Basic $12.99/mo | Pro $29.99/mo at trytimeback.com</p></noscript>",
               h, flags=re.DOTALL)

    # Meta tags
    if "<!-- SEO -->" not in h:
        h = h.replace("</head>",
            '<!-- SEO -->'
            '<meta name="description" content="Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week with Trytimeback.">'
            '<meta name="keywords" content="YouTube summary, AI summarizer, PDF export, Trytimeback">'
            '<meta name="robots" content="index, follow">'
            '<link rel="canonical" href="https://trytimeback.com">'
            '<meta property="og:type" content="website">'
            '<meta property="og:url" content="https://trytimeback.com">'
            '<meta property="og:title" content="Trytimeback - AI YouTube Summarizer and PDF Export">'
            '<meta property="og:description" content="Summarize YouTube videos in seconds and export to PDF.">'
            '<meta property="og:site_name" content="Trytimeback">'
            '<meta name="twitter:card" content="summary_large_image">'
            '<meta name="twitter:title" content="Trytimeback - AI YouTube Summarizer">'
            '<meta name="twitter:description" content="Summarize YouTube videos in seconds and export to PDF.">'
            '\n</head>')

    p.write_text(h, encoding="utf-8")

    # Verify
    v = re.search(r"<title>(.*?)</title>", p.read_text(encoding="utf-8"))
    print(f"[SEO] DONE title={v.group(1) if v else 'FAIL'}")

    # Copy sitemap + robots
    for f in ["sitemap.xml", "robots.txt"]:
        s = pathlib.Path(f)
        if s.exists():
            shutil.copy2(s, p.parent / f)
            print(f"[SEO] copied {f}")

except Exception:
    traceback.print_exc()
    print("[SEO] ERROR - patch failed but continuing to start app")
