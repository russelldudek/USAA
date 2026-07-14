from __future__ import annotations

from pathlib import Path
import base64
import re
import sys

import fitz
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

ROUTES = {
    "resume.html": "Russell-Dudek-USAA-Resume.pdf",
    "cover-letter.html": "Russell-Dudek-USAA-Cover-Letter.pdf",
    "interview-brief.html": "Russell-Dudek-USAA-Interview-Thesis-Brief.pdf",
    "120-day-plan.html": "Russell-Dudek-USAA-120-Day-Plan.pdf",
    "hard-objection.html": "Russell-Dudek-USAA-Hard-Objection.pdf",
    "automation-assurance-review.html": "Russell-Dudek-USAA-Automation-Assurance-Review.pdf",
}
EXPECTED_PAGES = {
    "Russell-Dudek-USAA-Resume.pdf": 2,
    "Russell-Dudek-USAA-Cover-Letter.pdf": 1,
    "Russell-Dudek-USAA-Interview-Thesis-Brief.pdf": 4,
    "Russell-Dudek-USAA-120-Day-Plan.pdf": 3,
    "Russell-Dudek-USAA-Hard-Objection.pdf": 1,
    "Russell-Dudek-USAA-Automation-Assurance-Review.pdf": 1,
}

CSS = (ROOT / "brand-tokens.css").read_text(encoding="utf-8") + "\n" + (
    ROOT / "styles.css"
).read_text(encoding="utf-8").replace('@import url("brand-tokens.css");', "")
LOGO_BYTES = (ROOT / "assets/brand/usaa-logo-official.png").read_bytes()
LOGO_URI = "data:image/png;base64," + base64.b64encode(LOGO_BYTES).decode("ascii")


def materialize(route: str) -> str:
    html = (ROOT / route).read_text(encoding="utf-8")
    html = re.sub(
        r'<link[^>]+href=["\']styles\.css["\'][^>]*>',
        "<style>" + CSS + "</style>",
        html,
        flags=re.I,
    )
    html = html.replace(
        'src="assets/brand/usaa-logo-official.png"', f'src="{LOGO_URI}"'
    )
    return html


def set_metadata(path: Path) -> None:
    doc = fitz.open(path)
    metadata = doc.metadata.copy()
    metadata.update(
        {
            "author": "Russell Dudek",
            "subject": "Independent candidate work product for USAA Director, Process Excellence - Process Automation",
            "keywords": "USAA, process excellence, process automation, business process management, Russell Dudek",
            "creator": "Russell Dudek candidate campaign",
        }
    )
    temp = path.with_suffix(".tmp.pdf")
    doc.set_metadata(metadata)
    doc.save(temp, garbage=4, deflate=True, clean=True)
    doc.close()
    temp.replace(path)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for route, filename in ROUTES.items():
        page = browser.new_page()
        page.set_content(materialize(route), wait_until="load")
        page.pdf(
            path=str(DOCS / filename),
            format="Letter",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            prefer_css_page_size=True,
        )
        page.close()
    browser.close()

for filename, expected in EXPECTED_PAGES.items():
    path = DOCS / filename
    set_metadata(path)
    doc = fitz.open(path)
    if doc.page_count != expected:
        raise SystemExit(f"{filename}: expected {expected} pages, found {doc.page_count}")
    if not any(page.get_text().strip() for page in doc):
        raise SystemExit(f"{filename}: no selectable text")
    doc.close()

print("Generated and verified six candidate PDFs.")
