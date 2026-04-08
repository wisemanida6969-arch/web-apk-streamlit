"""Patch Streamlit's index.html for SEO — robust regex-based replacement."""
import streamlit as st
import pathlib
import re

st_dir = pathlib.Path(st.__file__).parent
index_path = st_dir / "static" / "index.html"

if not index_path.exists():
    print(f"⚠️  Not found: {index_path}")
    exit()

html = index_path.read_text(encoding="utf-8")
original = html  # keep copy to detect changes

# ══════════════════════════════════════════════
# 1) Force <title> — replace ANY existing <title>
# ══════════════════════════════════════════════
NEW_TITLE = "세월은간다 - AI 유튜브 요약 · 핵심 숏츠 5개 + PDF 추출 | trytimeback.com"
html = re.sub(
    r"<title>[^<]*</title>",
    f"<title>{NEW_TITLE}</title>",
    html,
    count=1,
)

# ══════════════════════════════════════════════
# 2) Force <html lang="ko">
# ══════════════════════════════════════════════
if 'lang="ko"' not in html:
    html = re.sub(r"<html([^>]*)>", r'<html lang="ko"\1>', html, count=1)

# ══════════════════════════════════════════════
# 3) Force <noscript> content — replace entire noscript body
# ══════════════════════════════════════════════
NOSCRIPT_HTML = (
    '<div style="font-family:sans-serif;max-width:800px;margin:40px auto;padding:20px;line-height:1.8;">'
    '<h1>세월은간다 (Trytimeback) - AI 유튜브 요약 서비스</h1>'
    '<p>유튜브 강의 URL만 붙여넣으면 AI가 <strong>핵심 포인트 숏츠 5개</strong>와 '
    '<strong>상세 PDF 요약</strong>을 자동으로 생성합니다.</p>'
    '<ul>'
    '<li>AI가 선별한 핵심 포인트 숏츠 5개 자동 추출</li>'
    '<li>강의 전체 내용을 정리한 상세 PDF 요약 다운로드</li>'
    '<li>한국어, 영어 등 다국어 자막 자동 감지</li>'
    '<li>PC / 모바일 반응형 디자인</li>'
    '</ul>'
    '<p>Basic $12.99/월 (300분) | Pro $29.99/월 (1,200분) — 연간 결제 시 최대 23% 할인</p>'
    '<p><a href="https://trytimeback.com">trytimeback.com</a>에서 지금 시작하세요!</p>'
    '</div>'
)
html = re.sub(
    r"<noscript>.*?</noscript>",
    f"<noscript>{NOSCRIPT_HTML}</noscript>",
    html,
    flags=re.DOTALL,
)

# ══════════════════════════════════════════════
# 4) SEO meta block — inject once
# ══════════════════════════════════════════════
MARKER = "<!-- SEO-V4 -->"
if MARKER not in html:
    # Remove any old SEO patches
    html = re.sub(r"<!-- SEO-V\d+ -->.*?(?=\n*</head>)", "", html, flags=re.DOTALL)
    html = re.sub(r"<!-- PATCHED-V\d+ -->.*?(?=\n*</head>)", "", html, flags=re.DOTALL)
    # Remove stale individual meta tags
    html = re.sub(r'<meta\s+name="description"[^>]*>\s*', "", html)
    html = re.sub(r'<meta\s+property="og:[^"]*"[^>]*>\s*', "", html)
    html = re.sub(r'<meta\s+name="twitter:[^"]*"[^>]*>\s*', "", html)
    html = re.sub(r'<meta\s+name="keywords"[^>]*>\s*', "", html)
    html = re.sub(r'<link\s+rel="canonical"[^>]*>\s*', "", html)

    seo_block = MARKER + """
<meta name="description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다. 학습 시간을 80% 절약하세요!">
<meta name="keywords" content="유튜브 요약, AI 요약, 유튜브 강의 요약, PDF 요약, 핵심 숏츠, YouTube summary, AI lecture summary, trytimeback, 세월은간다">
<meta name="author" content="Trytimeback">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://trytimeback.com">

<meta property="og:type" content="website">
<meta property="og:url" content="https://trytimeback.com">
<meta property="og:title" content="세월은간다 - AI 유튜브 요약 · 핵심 숏츠 + PDF 추출">
<meta property="og:description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다. 학습 시간을 80% 절약하세요!">
<meta property="og:site_name" content="세월은간다 (Trytimeback)">
<meta property="og:locale" content="ko_KR">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="세월은간다 - AI 유튜브 요약 · 핵심 숏츠 + PDF 추출">
<meta name="twitter:description" content="유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성.">

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "세월은간다 (Trytimeback)",
  "url": "https://trytimeback.com",
  "description": "유튜브 강의 URL만 붙여넣으면 AI가 핵심 포인트 숏츠 5개와 상세 PDF 요약을 자동 생성합니다.",
  "applicationCategory": "EducationalApplication",
  "operatingSystem": "Web",
  "offers": {
    "@type": "AggregateOffer",
    "lowPrice": "9.99",
    "highPrice": "29.99",
    "priceCurrency": "USD",
    "offerCount": "4"
  },
  "featureList": [
    "AI 핵심 포인트 숏츠 5개 자동 추출",
    "상세 PDF 요약 다운로드",
    "다국어 자막 지원",
    "모바일 반응형 디자인"
  ]
}
</script>
"""
    html = html.replace("</head>", seo_block + "\n</head>")

# ══════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════
if html != original:
    index_path.write_text(html, encoding="utf-8")
    print(f"✅ SEO v4 patched: {index_path}")
    # Debug: print what Google will see
    title_match = re.search(r"<title>([^<]+)</title>", html)
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html)
    ns_match = re.search(r"<noscript>(.*?)</noscript>", html, re.DOTALL)
    print(f"   title: {title_match.group(1) if title_match else 'NOT FOUND'}")
    print(f"   description: {desc_match.group(1)[:80] if desc_match else 'NOT FOUND'}...")
    print(f"   noscript: {len(ns_match.group(1)) if ns_match else 0} chars")
else:
    print(f"ℹ️  Already patched (v4): {index_path}")
