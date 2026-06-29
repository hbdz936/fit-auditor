# FitAuditor

**A resume audit that can't bluff — every verdict is cited, then independently re-checked against the source text.**

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)
![Groq](https://img.shields.io/badge/LLM-Llama%203.3%2070B%20(Groq)-orange)
![SSE](https://img.shields.io/badge/Streaming-SSE-purple)

Most "resume vs JD" tools prompt an LLM and trust whatever it says. FitAuditor doesn't — every match claim has to cite a specific resume line, and a separate verification pass checks that the cited line actually supports the claim before the verdict is allowed to stand.

## Why

- **Citations are verified, not trusted.** A confident-sounding match with no real backing gets caught and downgraded to `UNVERIFIED` — programmatically, not by asking the model to double-check itself.
- **Live audit trail, not a loading spinner.** Verdicts stream in over SSE as they're produced, each with a status, rationale, and clickable line reference.
- **Fully auditable.** Every outcome — `MATCHED` / `PARTIAL` / `GAP` / `UNVERIFIED` — traces back to an exact line in the source resume.

## Example Outcome

Candidate: Aanya Verma · Role: Backend Engineer (Python)

| Requirement | Verdict | Evidence |
|---|---|---|
| REST APIs in Python | ✅ MATCHED | L003 |
| Load balancing / distributed systems | ✅ MATCHED | L004 |
| Cloud data pipelines (Databricks) | ✅ MATCHED | L005 |
| Kubernetes | ❌ GAP | — |
| Mentoring junior engineers | ✅ MATCHED | L007 |

**Fit Score: 80%** · **Risk Flags: 0**

## How it works

```
Resume + Job Description
        ↓
Line-indexed parser  →  resume split into [L001], [L002], ...
        ↓
Single LLM call      →  extracts requirements, cites line IDs as evidence
        ↓
Verification layer   →  checks cited lines actually support the claim
        ↓
SSE stream           →  verdicts appear live, flagged citations marked
```

The verification step is the actual point of the project — the model is never trusted at its word:

```python
def verify_verdict(verdict: dict, line_map: dict[str, str]) -> dict:
    cited_text = " ".join(line_map.get(lid, "") for lid in verdict["evidence_line_ids"])
    overlap = _keywords(verdict["requirement"]) & _keywords(cited_text)

    if not overlap:
        verdict["status"] = "UNVERIFIED"
        verdict["verification_note"] = "Cited line(s) share no keywords with the requirement."
    return verdict
```

## Quick Start

```bash
git clone <your-repo-url>
cd fit-auditor
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
echo GROQ_API_KEY=your_key_here > .env
python main.py
```
Open `http://localhost:8000`, click **Load demo scenario**, then **Run audit**.

## Project Structure

```
fit-auditor/
├── main.py              # FastAPI server + SSE streaming
├── core/
│   ├── parser.py          # line-indexes the resume
│   ├── auditor.py          # single structured LLM call (Groq)
│   └── verifier.py          # the verification layer
├── models/
│   └── schemas.py            # Pydantic request/response models
├── data/                       # demo resume + JD
└── static/
    └── index.html               # frontend, no build step
```

## Known Limitations

| Limitation | Fix if extended |
|---|---|
| Verification is keyword-overlap, not semantic | Swap for embedding similarity |
| Requirement extraction itself isn't re-verified | Second pass cross-checking against raw JD text |
| One resume/JD pair per run, nothing persisted | Add a database for batch audits |
| Single LLM provider (Groq) | Abstract behind a provider-agnostic client |

## Stack

Python · FastAPI · Groq (Llama 3.3 70B) · Server-Sent Events 