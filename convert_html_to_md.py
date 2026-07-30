"""Convert all HTML docs to .md copies for GitHub."""
import os
import glob
import html2text

base = os.path.dirname(os.path.abspath(__file__))

converter = html2text.HTML2Text()
converter.ignore_links = False
converter.ignore_images = True
converter.body_width = 0        # no line wrapping
converter.protect_links = False
converter.unicode_snob = True

html_files = glob.glob(os.path.join(base, "*.html")) + \
             glob.glob(os.path.join(base, "interview_prep", "*.html"))

for html_path in sorted(html_files):
    md_path = html_path.replace(".html", ".md")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    md = converter.handle(html)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  {os.path.relpath(md_path, base)}")

print(f"\nDone — {len(html_files)} files converted.")
