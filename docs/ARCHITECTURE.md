# ABC.DEMO.02 Architecture

```text
Safari / Browser
       |
       v
FastAPI Local Backend (Mac)
       |
       +-- Session Store (local JSON)
       +-- Media Store (local folder)
       |
       v
Orchestrator
  1 Consultation Engine
  2 Context Engine
  3 Safety Pre-Gate
  4 Recommendation Engine
  5 Visual Preview Engine
  6 Safety & Visual QA
  7 Specialist Validation
       |
       +-- Local deterministic fallbacks
       |
       +-- OpenAI Provider Adapter (optional LIVE mode)
             |
             +-- GPT-5.6 Terra: consultation / vision context / visual QA
             +-- GPT-Image-2: live image edit
```

## Truth / authority rules

- The browser sends commands; it does not directly mutate Safety or validation truth.
- Client Selection is separate from Specialist Validation.
- Safety can block recommendation/preview.
- If a chemical/color path needs a professional check, `PROCEED` is compiled back to `CHECK_FIRST` until resolved.
- Provider output never sets Specialist Validation.
- Visual QA is support, not biometric identity verification.
