"""Patch Streamlit's index.html for SEO (Korean-targeted)."""
import streamlit as st
import pathlib
import re

st_dir = pathlib.Path(st.__file__).parent
index_path = st_dir / "static" / "index.html"

if index_path.exists():
    html = index_path.read_text(encoding="utf-8")
    patched = False

    # 1) <html lang="ko">
    if '<html lang="ko">' not in html:
        html = re.sub(r"<html(?!\s+lang=)", '<html lang="ko"', html, count=1)
        patched = True

    # 2) <title>
    if "<title>Streamlit</title>" in html:
        html = html.replace(
            "<title>Streamlit</title>",
            "<title>세월은간다 - AI 유튜브 요약 · 핵심 숏츠 5개 + PDF 추출 | trytimeback.com</title>",
        )
        patched = True

    # 3) SEO meta block
    MARKER = "<!-- SEO-V3 -->"
    if MARKER not in html:
        # clean old patches
        html = re.sub(r"<!-- PATCHED-V3 -->.*?(?=</head>)", "", html, flags=re.DOTALL)
        html = re.sub(r"<!-- SEO-PATCHED-V2 -->.*?(?=</head>)", "", html, flags=re.DOTALL)
        html = re.sub(r'<meta\s+name="description"[^>]*>\n?', "", html)
        html = re.sub(r'<meta\s+property="og:[^"]*"[^>]*>\n?', "", html)

        seo = f"""{MARKER}
<meta name="description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다. 학습 시간을 80% 절약하세요!">
<meta name="keywords" content="유튜브 요약, AI 요약, 유튜브 강의 요약, PDF 요약, 핵심 숏츠, YouTube summary, AI lecture summary, trytimeback">
<meta name="author" content="Trytimeback">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://trytimeback.com">
<meta property="og:type" content="website">
<meta property="og:url" content="https://trytimeback.com">
<meta property="og:title" content="세월은간다 - AI 유튜브 요약 · 핵심 숏츠 + PDF 추출">
<meta property="og:description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다.">
<meta property="og:site_name" content="세월은간다 (Trytimeback)">
<meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="세월은간다 - AI 유튜브 요약 · 핵심 숏츠 + PDF 추출">
<meta name="twitter:description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성.">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "세월은간다 (Trytimeback)",
  "url": "https://trytimeback.com",
  "description": "유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다.",
  "applicationCategory": "EducationalApplication",
  "operatingSystem": "Web",
  "offers": {{
    "@type": "AggregateOffer",
    "lowPrice": "9.99",
    "highPrice": "29.99",
    "priceCurrency": "USD"
  }}
}}
</script>
"""
        html = html.replace("</head>", seo + "</head>")
        patched = True

    # 4) noscript
    old_ns = "You need to enable JavaScript to run this app."
    if old_ns in html:
        html = html.replace(old_ns, (
            '<div style="font-family:sans-serif;max-width:800px;margin:40px auto;padding:20px;line-height:1.8;">'
            "<h1>세월은간다 (Trytimeback) - AI 유튜브 요약 서비스</h1>"
            "<p>유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동으로 생성합니다.</p>"
            "<p>Basic $12.99/월 | Pro $29.99/월</p>"
            '<p><a href="https://trytimeback.com">trytimeback.com</a></p></div>'
        ))
        patched = True

    if patched:
        index_path.write_text(html, encoding="utf-8")
        print(f"✅ SEO patched: {index_path}")
    else:
        print(f"ℹ️  Already patched: {index_path}")
else:
    print(f"⚠️  Not found: {index_path}")
