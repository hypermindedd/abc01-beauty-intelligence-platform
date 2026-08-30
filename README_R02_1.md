# ABC.01 — R02.1 Clean Core Bootstrap

R02.1 is the first clean Productization implementation stage. It does **not** promote the Men's Demo into product authority.

## Purpose

- establish a clean `src/abc_core` package;
- consume the frozen Productization baseline fail-closed;
- enforce exact Product document versions, 16 runtime knowledge records, canonical test range 001–132, AG-01..10 and OUT-01..17;
- preserve Groom ID restrictions;
- expose an executable health/build-info surface without claiming production capabilities;
- create a compatibility baseline for subsequent R02 stages.

## Explicit non-claims

R02.1 does not claim production auth, durable production persistence, deployed visual provider/compositor, live cross-domain validation, pilot readiness or production readiness.

## Local verification

```bash
python -m pip install -e '.[dev]'
pytest -q
uvicorn abc_core.app:app --app-dir src --host 127.0.0.1 --port 8770
```
