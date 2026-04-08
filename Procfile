web: python -c "
import streamlit as st, pathlib, re, shutil
p = pathlib.Path(st.__file__).parent / 'static' / 'index.html'
print(f'[SEO] path={p} exists={p.exists()}')
h = p.read_text()
print(f'[SEO] BEFORE title: {re.search(r\"<title>(.*?)</title>\", h).group(1)}')
h = re.sub(r'<title>[^<]*</title>', '<title>Trytimeback - AI YouTube Summarizer &amp; PDF Export</title>', h)
h = re.sub(r'lang=\"[^\"]*\"', 'lang=\"en\"', h, count=1)
h = re.sub(r'<noscript>.*?</noscript>', '<noscript><h1>Trytimeback - AI YouTube Summarizer</h1><p>Paste any YouTube URL and get 5 key-point clips plus a detailed PDF summary in seconds.</p><p>Basic \$12.99/mo | Pro \$29.99/mo</p></noscript>', h, flags=re.DOTALL)
if '<!-- SEO -->' not in h:
    h = h.replace('</head>', '<!-- SEO --><meta name=\"description\" content=\"Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week with Trytimeback.\"><meta name=\"keywords\" content=\"YouTube summary, AI summarizer, PDF export, lecture notes, Trytimeback\"><meta name=\"robots\" content=\"index, follow\"><link rel=\"canonical\" href=\"https://trytimeback.com\"><meta property=\"og:type\" content=\"website\"><meta property=\"og:url\" content=\"https://trytimeback.com\"><meta property=\"og:title\" content=\"Trytimeback - AI YouTube Summarizer and PDF Export\"><meta property=\"og:description\" content=\"Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week.\"><meta property=\"og:site_name\" content=\"Trytimeback\"><meta name=\"twitter:card\" content=\"summary_large_image\"><meta name=\"twitter:title\" content=\"Trytimeback - AI YouTube Summarizer\"><meta name=\"twitter:description\" content=\"Summarize YouTube videos in seconds and export to PDF.\">\n</head>')
p.write_text(h)
v = p.read_text()
print(f'[SEO] AFTER title: {re.search(r\"<title>(.*?)</title>\", v).group(1)}')
print(f'[SEO] has description: {\"meta name=\" in v}')
print('[SEO] DONE')
for f in ['sitemap.xml','robots.txt']:
    s=pathlib.Path(f)
    if s.exists(): shutil.copy2(s, p.parent/f); print(f'[SEO] copied {f}')
" && streamlit run app.py --server.port $PORT --server.headless true --server.address 0.0.0.0
