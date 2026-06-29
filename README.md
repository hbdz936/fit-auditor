# FitAuditor

A resume audit that can't bluff. Every verdict cites a specific resume line — then a separate verification layer checks that the citation actually holds up, using both keyword overlap and semantic embeddings, so a confident-sounding LLM claim with no real backing gets caught, not trusted.

**Live demo:** https://fit-auditor-production.up.railway.app/

![Python](https://img.shields.io/badge/Python-3.11-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-async-009688) ![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-orange) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-async-336791)

## How it works
Resume (paste or PDF/DOCX) → line-indexed parser → async Groq call (cites line IDs as evidence)→ verifier (keyword overlap + embedding similarity) → SSE stream → PostgreSQL
The model is never trusted at its word — a citation only stands if it's backed by either signal:

```python
has_keyword_overlap = bool(_keywords(requirement) & _keywords(cited_text))
is_semantically_close = _semantic_similarity(requirement, cited_text) >= THRESHOLD

if not has_keyword_overlap and not is_semantically_close:
    verdict["status"] = "UNVERIFIED"
```

Embeddings run locally (`all-MiniLM-L6-v2`) — no network call, and a genuinely independent check rather than asking the same model to grade its own homework.

## Stack

FastAPI (async) · Groq Llama 3.3 70B · PostgreSQL + async SQLAlchemy · `sentence-transformers` · `tenacity` retries · bearer-token auth · `pytest` · Docker

## Quick start

```bash
pip install -r requirements.txt
# set GROQ_API_KEY, DATABASE_URL, API_TOKEN in .env
pytest tests/ -v
python main.py
```

Or: `docker compose up`