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
        "Trytimeback — AI-powered YouTube lecture analyzer. "
        "Paste any YouTube lecture URL and get 5 key point short clips "
        "and a full PDF summary in seconds. Save hours of study time. "
        "Visit trytimeback.com to get started."
    )
    if old_noscript in html:
        html = html.replace(old_noscript, new_noscript)
        patched = True

    # 2) Add meta description in <head> if not already there
    if 'name="description"' not in html:
        meta_tags = (
            '<meta name="description" content="Trytimeback — AI-powered YouTube lecture analyzer. '
            'Get 5 key point short clips + full PDF summary from any lecture video in seconds.">\n'
            '<meta property="og:title" content="Trytimeback | AI YouTube Lecture Summary">\n'
            '<meta property="og:description" content="Stop watching hour-long lectures. '
            'Get AI-extracted key points in 60-second shorts and a detailed PDF summary. Free to start.">\n'
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
