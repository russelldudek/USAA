from __future__ import annotations

from pathlib import Path
import re

from bs4 import BeautifulSoup
import fitz

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HTML_ROUTES = [
    "resume.html",
    "cover-letter.html",
    "interview-brief.html",
    "120-day-plan.html",
    "leadership-advantage.html",
    "automation-assurance-review.html",
]
PDFS = {
    "Russell-Dudek-USAA-Resume.pdf": 2,
    "Russell-Dudek-USAA-Cover-Letter.pdf": 1,
    "Russell-Dudek-USAA-Interview-Thesis-Brief.pdf": 4,
    "Russell-Dudek-USAA-120-Day-Plan.pdf": 3,
    "Russell-Dudek-USAA-Leadership-Advantage.pdf": 1,
    "Russell-Dudek-USAA-Automation-Assurance-Review.pdf": 1,
}
FOOTER_PATTERN = re.compile(
    r"(Resume|Cover Letter|Interview Brief|120-Day Plan|Leadership Advantage|Assurance Review)\s*·\s*\d+"
)

findings: list[str] = []

for route in HTML_ROUTES:
    path = ROOT / route
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    papers = soup.select(".paper")
    if not papers:
        findings.append(f"{route}: no .paper elements")
        continue
    for index, paper in enumerate(papers, start=1):
        direct_footers = [
            child for child in paper.find_all(recursive=False)
            if "doc-footer" in (child.get("class") or [])
        ]
        all_footers = paper.select(".doc-footer")
        if len(all_footers) != 1:
            findings.append(f"{route} page {index}: expected one footer, found {len(all_footers)}")
        if len(direct_footers) != 1:
            findings.append(
                f"{route} page {index}: footer must be a direct .paper child; found {len(direct_footers)}"
            )

for filename, expected_pages in PDFS.items():
    path = DOCS / filename
    if not path.exists():
        findings.append(f"Missing PDF: {filename}")
        continue
    doc = fitz.open(path)
    if doc.page_count != expected_pages:
        findings.append(f"{filename}: expected {expected_pages} pages, found {doc.page_count}")
    for page_number, page in enumerate(doc, start=1):
        blocks = page.get_text("blocks")
        footer_blocks = [block for block in blocks if FOOTER_PATTERN.search(block[4])]
        if not footer_blocks:
            findings.append(f"{filename} page {page_number}: page-number footer not found")
            continue
        footer_top = min(block[1] for block in footer_blocks)
        if footer_top < 720:
            findings.append(
                f"{filename} page {page_number}: footer begins at {footer_top:.2f} pt, outside bottom page zone"
            )
    doc.close()

if findings:
    raise SystemExit("\n".join(findings))

print("Document hierarchy and bottom-zone footer placement passed for every printable page.")
