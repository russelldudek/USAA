# USAA Candidate Campaign Audit

## Campaign state

- Campaign state: building - public `main` and live GitHub Pages verification pending
- Campaign repository: https://github.com/russelldudek/USAA
- Audited branch: `main` after publication
- Job posting: supplied USAA Jobs URL in `campaign-metadata.json`
- Candidate thesis: **Scale the workflow and its assurance together.**
- Operating artifact: **Automation Assurance Twin**

## Factual and evidence integrity

- Career claims trace to the verified candidate evidence record.
- No direct USAA RPA-platform, financial-services automation-COE, or private USAA process ownership is claimed.
- Six Sigma is presented only as `Six Sigma Certification`; Green Belt level and three named completed Lean/Six Sigma projects are explicitly not claimed.
- Tampa/St. Petersburg is presented as a planned relocation, not a completed move or a request for employer-funded relocation.
- Company-specific internal conditions are labeled as hypotheses for discovery.

## Brand fidelity

- Visible company identity: passed in source and rendered local review.
- Official logo/wordmark: official USAA Newsroom asset used locally and unmodified.
- Color token provenance: passed; navy, blue, red, gold, white, and light-blue values are official-source sampled or documented candidate-original signals.
- Typography decision: passed; licensed/system substitutes reproduce the public condensed editorial hierarchy without copying proprietary font binaries.
- Committed brand assets: pending verification from public `main`.
- Document brand continuity: passed in HTML and rendered PDFs.
- Independent-candidate distinction: passed.
- Official-reference comparison: local campaign rendering was reviewed against the current official 2025 Annual Report cover and CEO spread; USAA identity remains recognizable while the Automation Assurance Twin remains an original candidate argument.

## Visual, interaction, and UX

- Signature hero composition: passed.
- Role-derived motion: passed; the work and assurance signals move in synchronization and visibly diverge under weaker assurance states.
- Meaningful participation: passed; four keyboard-operable scenarios change the operating disposition and evidence readout.
- Smart starting state: passed; the default stable-rules scenario opens with a useful `Automate + standardize` decision.
- Reset/baseline: passed through the default scenario control.
- Value before ask: passed.
- Cost-of-inaction integrity: passed; no fabricated urgency or unsupported score.
- Contextual comparison integrity: passed.
- Dark-pattern review: passed.
- Reduced motion: passed; computed continuous animation is `none` under reduced-motion preference while all content and controls remain available.

## Responsive and browser QA

Local file navigation was restricted by the managed browser policy, so the QA harness materialized the exact committed HTML, CSS, JavaScript, and official logo into Playwright Chromium using `page.set_content`. This verifies layout, interaction, assets, and scripts, but does not substitute for the separate live deployment check.

- Routes checked: 7
- Viewports checked per route: 1440x900, 1280x800, 768x1024, 390x844
- Route/viewport checks: 28
- Horizontal-overflow findings: 0
- Broken-image findings: 0
- Console-error findings: 0
- Scenario state change: passed
- Reduced-motion behavior: passed

## Documents and PDFs

- Resume: passed at exactly 2 US Letter pages.
- Cover letter: passed at exactly 1 US Letter page.
- Interview thesis brief: passed at 4 US Letter pages.
- 120-day entry plan: passed at 3 US Letter pages.
- Hard-objection analysis: passed at 1 US Letter page.
- Automation Assurance Review: passed at 1 US Letter page.
- PDF openability/preflight: passed for all six PDFs.
- PDF text selectability: passed.
- PDF links: passed; 50 total link annotations retained across the six PDFs.
- PDF metadata: passed; candidate author, candidate-work subject, title, and neutral keywords present.
- Resume page-one balance: passed by full-page raster review.
- Cover letter one-page composition: passed by full-page raster review.
- Other PDF page breaks and footer visibility: passed by raster and extracted-text review.
- Reciprocal resume/cover-letter navigation: passed in source; live verification pending.

## Candidate-facing confidentiality

- Public source/filename scan: passed.
- PDF text and metadata scan: passed.
- Forbidden internal-name matches: 0.

## Publication gates

- Complete public manifest on `main`: pending.
- Audited final `main` head SHA: pending.
- Live GitHub Pages routes and downloads: pending.
- Live reciprocal document navigation: pending.
- Live source/PDF byte correspondence: pending.
- Canonical source alignment refresh after final publication: pending.

The campaign must remain `building` until the public `main` manifest and the live repository-named Pages deployment are verified against one captured final head.
