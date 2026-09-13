---
duration: 30s
format: 1920x1080
fps: 30
music: none
captions: false
style_preset: blockframe
flow: companion
storyboard: false
---

# Storyboard — hellochusquis-launch (30s horizontal, whole-product)

## Frame 1 — Hook: your terminal, upgraded (0.0-3.5s)
- duration: 3.5s
- blueprint: intro-reveal
- asset_candidates: [capture/screenshots/full-page.png]
- transition_in: cut
- vo: "Your terminal — upgraded."
- visual:
  - Scene A (0.0-1.5s): amber wordmark "HelloChusquis" on near-black (#0a0a0c). Subtle grain.
  - Scene B (1.5-3.5s): shell prompt types `pip install hellochusquis` with caret, monospace. One-line tag: "local-first AI agent for terminal, browser, and the tools around your work."

## Frame 2 — Three surfaces, one agent (3.5-9.0s)
- duration: 5.5s
- blueprint: triple-card-spread
- asset_candidates: [capture/screenshots/full-page.png]
- transition_in: slide-left
- vo: "One agent — three surfaces. Terminal TUI, visual web chat, and an authenticated REST API with streaming."
- visual:
  - Scene A (0.0-2.0s): three pill cards slide in: "Terminal · TUI", "Web UI · localhost:7272", "REST API · /chat/stream" (SSE).
  - Scene B (2.0-5.5s): mini code strips under each: `hellochusquis`, `open http://localhost:7272`, `curl /chat/stream`. Amber dividers.

## Frame 3 — 74 providers, 150+ tools (9.0-15.0s)
- duration: 6.0s
- blueprint: stat-triptych
- asset_candidates: [capture/screenshots/contact-sheet.jpg]
- transition_in: cut
- vo: "Seventy-four providers — from OpenAI and Groq to Ollama local — with automatic failover. Plus one hundred fifty tools: shell, files, browser, and every integration you already use."
- visual:
  - Scene A (0.0-3.0s): big numbers "74" / "150+" on elevated cards, labels "PROVIDERS" / "TOOLS & INTEGRATIONS". Count-up animation.
  - Scene B (3.0-6.0s): provider ribbon scrolls: Groq · OpenRouter · Ollama · DeepSeek · Together · Anthropic · Mistral · Cohere · etc.

## Frame 4 — Tools in action: browser, web search, files, code (15.0-20.5s)
- duration: 5.5s
- blueprint: mosaic-reveal
- asset_candidates: [capture/screenshots/full-page.png]
- transition_in: slide-up
- vo: "Search the web. Drive a real browser. Read, write, and edit files. Run code — safely, with approvals for the risky bits."
- visual:
  - Scene A (0.0-2.5s): 2x2 grid: Browser automation, Web search, Files, Code execution — each with one-line proof.
  - Scene B (2.5-5.5s): browser trace highlight + approval gate badge "High-impact → Approve / Reject" pulses amber.

## Frame 5 — Memory + Knowledge that makes small models big (20.5-26.0s)
- duration: 5.5s
- blueprint: stat-reveal
- asset_candidates: [capture/screenshots/full-page.png]
- transition_in: cut
- vo: "Persistent memory and twelve hundred knowledge files — recalled into context every turn. On a small local model, measured accuracy went eighty-six to one hundred percent."
- visual:
  - Scene A (0.0-2.8s): dual counters: "1249 files / 9926 facts" and accuracy bar "86% → 100%" (3B local, 35-question probe).
  - Scene B (2.8-5.5s): tiny note: "~/.hellochusquis/knowledge/ overrides repo — your facts win."

## Frame 6 — CTA: pip (26.0-30.0s)
- duration: 4.0s
- blueprint: closing-cta
- asset_candidates: [capture/screenshots/full-page.png#cta]
- transition_in: cut
- vo: "HelloChusquis — pip install and start."
- visual:
  - Scene A (0.0-4.0s): one command centered: `pip install hellochusquis` then `hellochusquis` with blinking caret. Subline: "Terminal · Web · API · Memory". GitHub wordmark bottom-right.
