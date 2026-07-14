from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json
import os
import re
import threading

from bs4 import BeautifulSoup
import fitz
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
REPORT = ROOT / "campaign-qa.json"
ROUTES = [
    "index.html",
    "resume.html",
    "cover-letter.html",
    "interview-brief.html",
    "120-day-plan.html",
    "leadership-advantage.html",
    "automation-assurance-review.html",
]
VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "laptop": {"width": 1280, "height": 800},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
}
PDFS = {
    "Russell-Dudek-USAA-Resume.pdf": 2,
    "Russell-Dudek-USAA-Cover-Letter.pdf": 1,
    "Russell-Dudek-USAA-Interview-Thesis-Brief.pdf": 4,
    "Russell-Dudek-USAA-120-Day-Plan.pdf": 3,
    "Russell-Dudek-USAA-Leadership-Advantage.pdf": 1,
    "Russell-Dudek-USAA-Automation-Assurance-Review.pdf": 1,
}
FORBIDDEN = [
    re.compile(r"role[\s_-]*forge", re.I),
    re.compile(r"github\.com/russelldudek/USAA", re.I),
    re.compile(r"public campaign repository", re.I),
    re.compile(r"campaign repository", re.I),
    re.compile(r"strongest objections", re.I),
    re.compile(r"no claim of direct equivalence", re.I),
    re.compile(r"what is not verified", re.I),
]

report: dict = {
    "status": "passed",
    "routes": {},
    "interaction": {},
    "reduced_motion": {},
    "pdf": {},
    "findings": [],
}


def fail(scope: str, message: str) -> None:
    report["findings"].append({"scope": scope, "message": message})


def source_audit() -> None:
    for route in ROUTES:
        path = ROOT / route
        if not path.exists():
            fail("source", f"Missing route: {route}")
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN:
            if pattern.search(text):
                fail("source", f"Forbidden recruiter-facing pattern in {route}: {pattern.pattern}")
        soup = BeautifulSoup(text, "html.parser")
        ids = [node.get("id") for node in soup.find_all(attrs={"id": True})]
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        if duplicates:
            fail("source", f"Duplicate IDs in {route}: {duplicates}")
        if not soup.find("h1"):
            fail("source", f"Missing H1 in {route}")
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            parsed = urlparse(href)
            if parsed.scheme or href.startswith(("#", "mailto:", "tel:")):
                continue
            local = href.split("#", 1)[0]
            if local and not (ROOT / local).exists():
                fail("source", f"Broken local link in {route}: {href}")


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


source_audit()
os.chdir(ROOT)
server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{server.server_port}"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for label, viewport in VIEWPORTS.items():
        context = browser.new_context(viewport=viewport, reduced_motion="no-preference")
        for route in ROUTES:
            page = context.new_page()
            console_errors: list[str] = []
            page.on("console", lambda msg, store=console_errors: store.append(msg.text) if msg.type == "error" else None)
            response = page.goto(f"{base}/{route}", wait_until="networkidle")
            route_key = f"{label}:{route}"
            details = {
                "http_status": response.status if response else None,
                "console_errors": console_errors,
            }
            if response is None or response.status != 200:
                fail(route_key, f"Route did not return 200: {details['http_status']}")
            if len(page.locator("body").inner_text().strip()) < 120:
                fail(route_key, "Page rendered without meaningful content")
            geometry = page.evaluate(
                """() => ({
                    scrollWidth: document.documentElement.scrollWidth,
                    clientWidth: document.documentElement.clientWidth,
                    images: [...document.images].map(i => ({src:i.getAttribute('src'), complete:i.complete, naturalWidth:i.naturalWidth})),
                    papers: [...document.querySelectorAll('.paper')].map(p => {
                      const footer = p.querySelector('.doc-footer');
                      const children = [...p.children].filter(el => el !== footer);
                      const bottoms = children.map(el => el.getBoundingClientRect().bottom);
                      return {
                        scrollHeight: p.scrollHeight,
                        clientHeight: p.clientHeight,
                        contentBottom: bottoms.length ? Math.max(...bottoms) : null,
                        footerTop: footer ? footer.getBoundingClientRect().top : null,
                        overflow: getComputedStyle(p).overflow
                      };
                    })
                })"""
            )
            details.update(geometry)
            if geometry["scrollWidth"] > geometry["clientWidth"] + 1:
                fail(route_key, f"Horizontal overflow: {geometry['scrollWidth']} > {geometry['clientWidth']}")
            broken_images = [img for img in geometry["images"] if not img["complete"] or img["naturalWidth"] <= 0]
            if broken_images:
                fail(route_key, f"Broken images: {broken_images}")
            if console_errors:
                fail(route_key, f"Console errors: {console_errors}")
            for index, paper in enumerate(geometry["papers"]):
                if paper["footerTop"] is not None and paper["contentBottom"] is not None and paper["contentBottom"] > paper["footerTop"] + 1:
                    fail(route_key, f"Document content/footer collision on paper {index + 1}")
                if paper["overflow"] == "hidden" and paper["scrollHeight"] > paper["clientHeight"] + 1:
                    fail(route_key, f"Hidden document overflow on paper {index + 1}")
            report["routes"][route_key] = details

            if label == "mobile" and route == "index.html":
                menu = page.locator(".menu-btn")
                menu.click()
                expanded = menu.get_attribute("aria-expanded")
                visible = page.locator("#nav-links").is_visible()
                if expanded != "true" or not visible:
                    fail(route_key, "Mobile navigation did not open correctly")
            page.close()
        context.close()

    context = browser.new_context(viewport=VIEWPORTS["desktop"])
    page = context.new_page()
    page.goto(f"{base}/index.html", wait_until="networkidle")
    expected = {
        "stable": "Synchronized for scale",
        "exception": "Work plane outruns process truth",
        "human": "Human judgment remains a control",
        "evidence": "Assurance is not ready",
    }
    interaction_results = {}
    for scenario, state in expected.items():
        button = page.locator(f'[data-scenario="{scenario}"]')
        button.click()
        observed = page.locator("#model-state").inner_text().strip()
        selected = button.get_attribute("aria-selected")
        interaction_results[scenario] = {"expected": state, "observed": observed, "selected": selected}
        if observed != state or selected != "true":
            fail("interaction", f"Scenario {scenario} did not produce the expected state")
    paint_boundary = page.evaluate(
        """() => {
          const track = document.querySelector('.plane-track');
          const signal = document.querySelector('.track-signal');
          const ts = getComputedStyle(track);
          const ss = getComputedStyle(signal);
          return {overflow: ts.overflow, contain: ts.contain, isolation: ts.isolation, signalLeft: ss.left, animationName: ss.animationName};
        }"""
    )
    if paint_boundary["overflow"] != "hidden" or "paint" not in paint_boundary["contain"]:
        fail("interaction", f"Motion paint boundary is not clipped: {paint_boundary}")
    report["interaction"] = {"scenarios": interaction_results, "paint_boundary": paint_boundary}
    page.close()
    context.close()

    context = browser.new_context(viewport=VIEWPORTS["desktop"], reduced_motion="reduce")
    page = context.new_page()
    page.goto(f"{base}/index.html", wait_until="networkidle")
    animation_names = page.evaluate(
        """() => [...document.querySelectorAll('.track-signal,.twin-links i,.sync-meter i')].map(el => getComputedStyle(el).animationName)"""
    )
    if any(name != "none" for name in animation_names):
        fail("reduced_motion", f"Animations remain active: {animation_names}")
    report["reduced_motion"] = {"animation_names": animation_names}
    page.close()
    context.close()
    browser.close()

server.shutdown()
server.server_close()


def page_gap_before_footer(page: fitz.Page, marker: str) -> float:
    blocks = page.get_text("blocks")
    footer_blocks = [block for block in blocks if marker in block[4]]
    if not footer_blocks:
        raise ValueError(f"Footer marker not found: {marker}")
    footer_top = min(block[1] for block in footer_blocks)
    substantive = [
        block for block in blocks
        if marker not in block[4] and "Independent candidate work product" not in block[4]
    ]
    content_bottom = max(block[3] for block in substantive)
    return round(footer_top - content_bottom, 2)


for filename, expected_pages in PDFS.items():
    path = DOCS / filename
    if not path.exists():
        fail("pdf", f"Missing PDF: {filename}")
        continue
    doc = fitz.open(path)
    entry = {"pages": doc.page_count, "text_chars": 0, "metadata": doc.metadata}
    if doc.page_count != expected_pages:
        fail("pdf", f"{filename}: expected {expected_pages} pages, found {doc.page_count}")
    text = "\n".join(page.get_text() for page in doc)
    entry["text_chars"] = len(text)
    if not text.strip():
        fail("pdf", f"{filename}: no selectable text")
    combined = text + "\n" + " ".join(str(value) for value in doc.metadata.values() if value)
    for pattern in FORBIDDEN:
        if pattern.search(combined):
            fail("pdf", f"Forbidden recruiter-facing pattern in {filename}: {pattern.pattern}")
    for page_number, pdf_page in enumerate(doc, start=1):
        pix = pdf_page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
        if pix.width <= 0 or pix.height <= 0:
            fail("pdf", f"{filename}: page {page_number} did not render")
    if filename == "Russell-Dudek-USAA-Resume.pdf" and doc.page_count >= 2:
        gap = page_gap_before_footer(doc[0], "Resume · 1")
        entry["page1_gap_before_footer_points"] = gap
        entry["page1_gap_before_footer_inches"] = round(gap / 72, 3)
        if gap < 6:
            fail("pdf", f"Resume page one content is too close to or collides with footer: {gap} pt")
        if gap > 54:
            fail("pdf", f"Resume page one underfilled: {gap} pt before footer exceeds 0.75 inch")
    if filename == "Russell-Dudek-USAA-Cover-Letter.pdf":
        gap = page_gap_before_footer(doc[0], "Cover Letter · 1")
        entry["gap_before_footer_points"] = gap
        if gap < 6:
            fail("pdf", f"Cover letter content is too close to or collides with footer: {gap} pt")
        if gap > 72:
            fail("pdf", f"Cover letter lower-page region is unbalanced: {gap} pt before footer")
    report["pdf"][filename] = entry
    doc.close()

if (ROOT / "hard-objection.html").exists():
    fail("legacy", "Legacy hard-objection route remains")
if (DOCS / "Russell-Dudek-USAA-Hard-Objection.pdf").exists():
    fail("legacy", "Legacy hard-objection PDF remains")

if report["findings"]:
    report["status"] = "failed"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if report["findings"]:
    raise SystemExit(1)
