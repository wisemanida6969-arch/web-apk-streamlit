import streamlit as st, pathlib, re, shutil, traceback

try:
    p = pathlib.Path(st.__file__).parent / "static" / "index.html"
    print(f"[SEO] path={p} exists={p.exists()}")

    h = p.read_text(encoding="utf-8")
    print(f"[SEO] read {len(h)} chars")

    # Title
    h = re.sub(r"<title>[^<]*</title>",
               "<title>PostGenie - AI Blog Automation Platform</title>", h)

    # Lang
    h = re.sub(r'lang="[^"]*"', 'lang="en"', h, count=1)

    # Noscript (for crawlers that don't run JS)
    h = re.sub(r"<noscript>.*?</noscript>",
               "<noscript><h1>PostGenie - AI-Powered Blog Automation</h1>"
               "<p>PostGenie writes and publishes SEO blog posts to your Blogger or WordPress blog automatically using Claude AI. "
               "Connect your blog, pick topics, and let AI generate content daily. Free plan available, no credit card required. "
               "Visit postgenie.trytimeback.com to get started.</p>"
               "<p>Features: AI-written content, trending topics from Google News, multi-language support (English, Korean, Japanese, Spanish), "
               "auto-publishing to Blogger and WordPress, flexible scheduling (daily, twice daily, weekly), SEO optimization.</p>"
               "<p>Plans: Free ($0, 1 post/week), Basic ($9/mo, 1 post/day), Pro ($29/mo, 3 posts/day), Agency ($99/mo, 30 posts/day).</p>"
               "</noscript>",
               h, flags=re.DOTALL)

    # Meta tags
    if "<!-- SEO PostGenie -->" not in h:
        h = h.replace("</head>",
            '<!-- SEO PostGenie -->'
            '<meta name="description" content="AI writes and publishes blog posts to your blog automatically. Connect Blogger or WordPress, pick topics, and let Claude AI generate SEO content daily. Free plan available.">'
            '<meta name="keywords" content="AI blog, blog automation, AI content writer, Claude AI, Blogger automation, WordPress automation, SEO blog, automatic blog posting, AI SEO, content generation">'
            '<meta name="robots" content="index, follow, max-image-preview:large">'
            '<meta name="googlebot" content="index, follow">'
            '<meta name="author" content="PostGenie">'
            '<link rel="canonical" href="https://postgenie.trytimeback.com/">'
            '<meta property="og:type" content="website">'
            '<meta property="og:url" content="https://postgenie.trytimeback.com/">'
            '<meta property="og:title" content="PostGenie - AI Blog Automation Platform">'
            '<meta property="og:description" content="AI writes and publishes blog posts to your blog every day, automatically. Claude AI + trending topics + auto-publishing.">'
            '<meta property="og:site_name" content="PostGenie">'
            '<meta property="og:image" content="https://postgenie.trytimeback.com/static/postgenie_logo.jpg">'
            '<meta name="twitter:card" content="summary_large_image">'
            '<meta name="twitter:title" content="PostGenie - AI Blog Automation">'
            '<meta name="twitter:description" content="AI writes and publishes blog posts to your blog every day, automatically.">'
            '<meta name="twitter:image" content="https://postgenie.trytimeback.com/static/postgenie_logo.jpg">'
            '<script type="application/ld+json">'
            '{'
            '"@context":"https://schema.org",'
            '"@type":"SoftwareApplication",'
            '"name":"PostGenie",'
            '"applicationCategory":"BusinessApplication",'
            '"operatingSystem":"Web",'
            '"description":"AI-powered blog automation platform. Connect your blog and let Claude AI write and publish SEO posts automatically.",'
            '"url":"https://postgenie.trytimeback.com/",'
            '"offers":{"@type":"Offer","price":"0","priceCurrency":"USD","description":"Free plan available"}'
            '}'
            '</script>'
            '\n</head>')

    p.write_text(h, encoding="utf-8")

    # Verify
    v = re.search(r"<title>(.*?)</title>", p.read_text(encoding="utf-8"))
    print(f"[SEO] DONE title={v.group(1) if v else 'FAIL'}")

    # Copy sitemap + robots + logo to Streamlit's static directory
    for f in ["sitemap.xml", "robots.txt", "postgenie_logo.jpg", "postgenie_logo_square.jpg"]:
        s = pathlib.Path(f)
        if s.exists():
            shutil.copy2(s, p.parent / f)
            print(f"[SEO] copied {f}")

except Exception:
    traceback.print_exc()
    print("[SEO] ERROR - patch failed but continuing to start app")
