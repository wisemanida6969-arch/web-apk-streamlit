"""
Forcibly patch Streamlit's index.html for SEO.
Prints every step so we can see in Railway logs what's happening.
"""
import subprocess, pathlib, re, shutil, sys

# ── Step 1: Find index.html via pip show ──
print("[PATCH] Step 1: Finding Streamlit location...")
result = subprocess.run([sys.executable, "-m", "pip", "show", "streamlit"],
                        capture_output=True, text=True)
print(result.stdout)

location = None
for line in result.stdout.splitlines():
    if line.startswith("Location:"):
        location = line.split(":", 1)[1].strip()
        break

if not location:
    print("[PATCH] ERROR: Could not find Streamlit location via pip show!")
    sys.exit(1)

index_path = pathlib.Path(location) / "streamlit" / "static" / "index.html"
print(f"[PATCH] Step 2: index.html path = {index_path}")
print(f"[PATCH] Step 2: exists = {index_path.exists()}")

if not index_path.exists():
    print("[PATCH] ERROR: index.html does not exist!")
    sys.exit(1)

# ── Step 3: Read current content ──
html = index_path.read_text(encoding="utf-8")
print(f"[PATCH] Step 3: Read {len(html)} chars")
print(f"[PATCH] Step 3: Current title = {re.search(r'<title>(.*?)</title>', html).group(1) if re.search(r'<title>(.*?)</title>', html) else 'NOT FOUND'}")

original = html

# ── Step 4: Replace <title> ──
NEW_TITLE = "Trytimeback - AI YouTube Summarizer &amp; PDF Export"
html = re.sub(r"<title>[^<]*</title>", f"<title>{NEW_TITLE}</title>", html)
print(f"[PATCH] Step 4: Title replaced")

# ── Step 5: Replace lang ──
html = re.sub(r'<html\s+lang="[^"]*"', '<html lang="en"', html)
print(f"[PATCH] Step 5: lang set to en")

# ── Step 6: Replace <noscript> ──
NOSCRIPT = (
    '<noscript>'
    '<h1>Trytimeback - AI YouTube Summarizer</h1>'
    '<p>Paste any YouTube lecture URL and get 5 key-point short clips '
    'plus a detailed PDF summary in seconds. Save 10+ hours a week.</p>'
    '<p>Basic $12.99/mo | Pro $29.99/mo</p>'
    '<p>Visit <a href="https://trytimeback.com">trytimeback.com</a></p>'
    '</noscript>'
)
html = re.sub(r"<noscript>.*?</noscript>", NOSCRIPT, html, flags=re.DOTALL)
print(f"[PATCH] Step 6: noscript replaced")

# ── Step 7: Inject meta tags (only once) ──
MARKER = "<!-- SEO-INJECTED -->"
if MARKER not in html:
    meta_block = MARKER + """
<meta name="description" content="Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week with Trytimeback.">
<meta name="keywords" content="YouTube summary, AI summarizer, PDF export, lecture notes, Trytimeback">
<meta name="author" content="Trytimeback">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://trytimeback.com">
<meta property="og:type" content="website">
<meta property="og:url" content="https://trytimeback.com">
<meta property="og:title" content="Trytimeback - AI YouTube Summarizer & PDF Export">
<meta property="og:description" content="Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week with Trytimeback.">
<meta property="og:site_name" content="Trytimeback">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Trytimeback - AI YouTube Summarizer & PDF Export">
<meta name="twitter:description" content="Summarize YouTube videos in seconds and export to PDF. Save 10+ hours a week.">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "Trytimeback",
  "url": "https://trytimeback.com",
  "description": "Summarize YouTube videos in seconds and export to PDF.",
  "applicationCategory": "EducationalApplication",
  "offers": {"@type": "AggregateOffer","lowPrice": "9.99","highPrice": "29.99","priceCurrency": "USD"}
}
</script>
"""
    html = html.replace("</head>", meta_block + "\n</head>")
    print(f"[PATCH] Step 7: Meta tags injected")
else:
    print(f"[PATCH] Step 7: Already has meta tags")

# ── Step 8: Copy sitemap.xml and robots.txt ──
static_dir = index_path.parent
for fname in ["sitemap.xml", "robots.txt"]:
    src = pathlib.Path(fname)
    if src.exists():
        shutil.copy2(src, static_dir / fname)
        print(f"[PATCH] Step 8: Copied {fname}")

# ── Step 9: Write back ──
if html != original:
    index_path.write_text(html, encoding="utf-8")
    print(f"[PATCH] ✅ DONE! Wrote {len(html)} chars to {index_path}")
    # Verify
    verify = index_path.read_text(encoding="utf-8")
    title_check = re.search(r"<title>(.*?)</title>", verify)
    print(f"[PATCH] VERIFY title = {title_check.group(1) if title_check else 'FAILED'}")
else:
    print(f"[PATCH] No changes needed (already patched)")
