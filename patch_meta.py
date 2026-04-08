"""Copy sitemap.xml and robots.txt into Streamlit's static folder for serving."""
import streamlit as st
import pathlib
import shutil

st_dir = pathlib.Path(st.__file__).parent
static_dir = st_dir / "static"

print(f"[patch_meta] Streamlit static dir: {static_dir}")
print(f"[patch_meta] Exists: {static_dir.exists()}")

if static_dir.exists():
    # Copy sitemap.xml and robots.txt to Streamlit's static folder
    for filename in ["sitemap.xml", "robots.txt"]:
        src = pathlib.Path(filename)
        dst = static_dir / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"✅ Copied {filename} → {dst}")
        else:
            print(f"⚠️  {filename} not found in project root")
else:
    print(f"⚠️  Static dir not found: {static_dir}")
