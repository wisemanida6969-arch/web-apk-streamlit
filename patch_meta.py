"""Patch Streamlit's index.html to add site description for SEO and noscript."""
import streamlit as st
import pathlib

# Find Streamlit's index.html
st_dir = pathlib.Path(st.__file__).parent
index_path = st_dir / "static" / "index.html"

if index_path.exists():
    html = index_path.read_text(encoding="utf-8")
    patched = False

    # 1) Patch noscript tag
    old_noscript = "You need to enable JavaScript to run this app."
    new_noscript = (
        "세월은간다 (Trytimeback) — 유튜브를 요약하고 학습 시간을 단축하는 최고의 AI 도구. "
        "유튜브 강의 URL을 붙여넣으면 핵심 포인트 숏츠 5개와 PDF 전체 요약을 "
        "몇 초 만에 받아보세요. trytimeback.com"
    )
    if old_noscript in html:
        html = html.replace(old_noscript, new_noscript)
        patched = True

    # 2) Patch <title>
    if "<title>Streamlit</title>" in html:
        html = html.replace(
            "<title>Streamlit</title>",
            "<title>세월은간다 - AI 유튜브 요약 및 PDF 추출</title>"
        )
        patched = True

    # 3) Add meta description in <head> if not already there
    if 'name="description"' not in html:
        meta_tags = (
            '<meta name="description" content="유튜브를 요약하고 학습 시간을 단축하는 최고의 AI 도구. '
            '핵심 포인트 숏츠 5개 + PDF 전체 요약을 몇 초 만에 받아보세요.">\n'
            '<meta property="og:title" content="세월은간다 - AI 유튜브 요약 및 PDF 추출">\n'
            '<meta property="og:description" content="유튜브를 요약하고 학습 시간을 단축하는 최고의 AI 도구. '
            '강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠와 상세 PDF 요약을 자동 생성합니다.">\n'
            '<meta property="og:type" content="website">\n'
            '<meta property="og:url" content="https://trytimeback.com">\n'
        )
        html = html.replace("</head>", meta_tags + "</head>")
        patched = True

    if patched:
        index_path.write_text(html, encoding="utf-8")
        print(f"✅ Patched {index_path}")
    else:
        print(f"ℹ️  Already patched: {index_path}")
else:
    print(f"⚠️  index.html not found at {index_path}")
