from __future__ import annotations

from pathlib import Path
import json
import re

import fitz
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "artifact-manifest.json").read_text(encoding="utf-8"))
missing = [path for path in manifest["expected"] if not (ROOT / path).exists()]
if missing:
    raise SystemExit(f"Missing manifest entries: {missing}")

forbidden = [
    re.compile(r"role[\s_-]*forge", re.I),
    re.compile(r"github\.com/russelldudek/USAA", re.I),
    re.compile(r"public campaign repository", re.I),
    re.compile(r"campaign repository", re.I),
    re.compile(r"strongest objections", re.I),
    re.compile(r"no claim of direct equivalence", re.I),
    re.compile(r"what is not verified", re.I),
]
public_paths = [ROOT / path for path in manifest["expected"]]
for path in public_paths:
    if path.suffix.lower() == ".pdf":
        doc = fitz.open(path)
        value = "\n".join(page.get_text() for page in doc)
        value += "\n" + " ".join(str(v) for v in doc.metadata.values() if v)
        doc.close()
    elif path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        value = path.name
    else:
        value = path.read_text(encoding="utf-8", errors="ignore")
    for pattern in forbidden:
        if pattern.search(value + "\n" + path.name):
            raise SystemExit(f"Forbidden candidate-facing pattern in {path}: {pattern.pattern}")

for path in ROOT.glob("*.html"):
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    ids = [element.get("id") for element in soup.find_all(attrs={"id": True})]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise SystemExit(f"Duplicate IDs in {path.name}: {duplicates}")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
            continue
        target = ROOT / href.split("#")[0]
        if href.split("#")[0] and not target.exists():
            raise SystemExit(f"Broken local link in {path.name}: {href}")

resume = (ROOT / "resume.html").read_text(encoding="utf-8")
cover = (ROOT / "cover-letter.html").read_text(encoding="utf-8")
index = (ROOT / "index.html").read_text(encoding="utf-8")
brief = (ROOT / "interview-brief.html").read_text(encoding="utf-8")
if "cover-letter.html" not in resume or "resume.html" not in cover:
    raise SystemExit("Reciprocal resume / cover-letter navigation missing")
if "candidate vision" not in cover.lower() or "Automation Assurance Twin" not in cover:
    raise SystemExit("Cover letter does not explain the candidate-vision link")
if "Leadership advantage" not in index or "Leadership Advantage Brief" not in index:
    raise SystemExit("Positive transfer positioning is missing from the candidate vision")
if "Leadership advantage" not in brief:
    raise SystemExit("Interview brief does not carry the transfer-advantage argument")
if (ROOT / "hard-objection.html").exists() or (ROOT / "docs/Russell-Dudek-USAA-Hard-Objection.pdf").exists():
    raise SystemExit("Legacy hard-objection artifact remains")
qa = json.loads((ROOT / "campaign-qa.json").read_text(encoding="utf-8"))
if qa.get("status") != "passed" or qa.get("findings"):
    raise SystemExit("campaign-qa.json does not report a clean pass")

print("Manifest, repository privacy, positioning, links, IDs, documents, PDFs, and QA contracts passed.")
