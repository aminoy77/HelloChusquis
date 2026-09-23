"""Fake-home smoke: isolated user (temp HOME, Ollama-only config) vs local models.

Hunts launch-day bugs on the from-zero path without touching the real
~/.hellochusquis. Pool-level chat only — no tools, no shell, nothing executes.
Discovers installed Ollama models <= MAX_B Params (default 4) and runs:
  1. KB ingest into the fake home + recall hit check.
  2. Instruction-following probe ("Reply with exactly: ok").
  3. KB-grounded factual probe (Cairo / Rwanda).

Usage:
    python3 tools/fakehome_smoke.py [--max-b 4] [--models llama3.2:1b]
"""
import json
import os
import shutil
import sys
import tempfile

# tools/http.py shadows stdlib `http` when this script's dir is sys.path[0];
# drop it so stdlib (urllib) imports resolve before anything else.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]
sys.path.insert(0, os.path.join(_here, ".."))
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

CHECKS = [
    ("follow", "Reply with exactly: ok", ["ok"]),
    ("factual", "What is the capital of Egypt? Reply in one short sentence.", ["cairo"]),
    ("kb-grounded", "About how many people live in Rwanda? Reply in one short sentence.", ["14 million"]),
]


def _api(path, timeout=30):
    with urllib.request.urlopen(OLLAMA_URL + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def discover_models(max_b):
    models = []
    for m in _api("/api/tags").get("models", []):
        name = m.get("name", "")
        size = (m.get("details") or {}).get("parameter_size", "")
        try:
            b = float("".join(ch for ch in size if ch.isdigit() or ch == "."))
            if "b" not in size.lower():
                continue
        except ValueError:
            continue
        if b <= max_b:
            models.append(name)
    return sorted(models)


def main():
    max_b = 4.0
    only = None
    args = sys.argv[1:]
    if "--max-b" in args:
        max_b = float(args[args.index("--max-b") + 1])
    if "--models" in args:
        only = args[args.index("--models") + 1].split(",")
    models = only or discover_models(max_b)
    print(f"models under test (<= {max_b}B): {models}")
    if not models:
        print("no local models found; start ollama and pull one first")
        return 2

    fakehome = tempfile.mkdtemp(prefix="fakehome-")
    os.environ["HOME"] = fakehome
    sys.path.insert(0, "/Users/Arni/Library/Python/3.12/lib/python/site-packages")
    import yaml
    import core.db_memory as db_memory
    from core.provider import ProviderPool

    cfg_dir = os.path.join(fakehome, ".hellochusquis")
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, "config.yaml"), "w") as fh:
        yaml.safe_dump({"agent": {}, "providers": [
            {"name": "Ollama", "base_url": "http://localhost:11434/v1",
             "model": models[0], "priority": 1}], "settings": {}}, fh)

    print("db:", db_memory.MEMORY_DB_PATH)
    n = db_memory.load_knowledge()
    print("kb ingested:", n)
    assert n > 1000, "KB ingest broken on fresh home"

    cfg = yaml.safe_load(open(os.path.join(cfg_dir, "config.yaml")))
    pool = ProviderPool(config=cfg)
    failures = []
    for model in models:
        print(f"--- {model} ---")
        for kind, question, golds in CHECKS:
            ctx = db_memory.recall_context(question) if kind != "follow" else ""
            system = "Answer concisely. Context:\n" + ctx if ctx else "Answer concisely."
            try:
                resp = pool.chat_with_retry(
                    [{"role": "system", "content": system},
                     {"role": "user", "content": question}],
                    provider_name="Ollama", model=model)
                text = str(resp["choices"][0]["message"].get("content") or "")
            except Exception as exc:  # noqa: BLE001 - harness must report, not crash
                print(f"  {kind}: ERROR {type(exc).__name__}: {exc}")
                failures.append((model, kind, "error"))
                continue
            ok = any(g.lower() in text.lower() for g in golds)
            print(f"  {kind}: {'PASS' if ok else 'MISS'} {text[:100]!r}")
            if not ok:
                failures.append((model, kind, text[:100]))
    shutil.rmtree(fakehome, ignore_errors=True)
    print(f"\n{len(failures)} misses/errors across {len(models)} models x {len(CHECKS)} checks")
    for f in failures:
        print(" -", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
