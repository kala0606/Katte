#!/usr/bin/env python3
"""Gubbi — answer questions from the ingested admin index (RAG).

Stdlib only. Embeds the question, finds the closest chunks in index.json,
and asks the local LLM to answer strictly from them, with the source cited.

Usage:  python3 serve.py            (port 8787)
Expose: cloudflared tunnel --url http://localhost:8787
Ask:    POST /ask  {"q": "when does the NAAC team visit?"}
        → {"answer": "...", "sources": ["naac-circular.md"]}
"""
import json, math, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

OLLAMA = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.2"
PORT = 8787
TOP_K = 6
MIN_SCORE = 0.45          # below this, the corpus doesn't cover the question
INDEX = Path(__file__).parent / "index.json"

SYSTEM = (
    "You are Gubbi (ಗುಬ್ಬಿ — sparrow in Kannada), the little sparrow who nests in "
    "the tree above the katte at Srishti Manipal Institute and reads every circular "
    "the office pins up. Your voice: warm, quick, lightly bird-like. Most replies "
    "should be plain and helpful; only occasionally add one small flourish — a "
    "sparrow's-eye remark, or an everyday Kannada word (sari, swalpa, aiyo) where it "
    "fits naturally. Never start two replies the same way. Facts always come first. "
    "Answer ONLY from the document extracts provided, in 2 to 4 short sentences. "
    "If the extracts don't contain the answer, say so plainly and point them to the "
    "admin office — a sparrow doesn't guess. Never invent dates, names or numbers."
)

index = json.loads(INDEX.read_text()) if INDEX.exists() else []
print(f"loaded {len(index)} chunks from {INDEX.name}" if index
      else "WARNING: no index.json — run ingest.py first")


def ollama(path, payload):
    req = urllib.request.Request(f"{OLLAMA}{path}", json.dumps(payload).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def answer(q):
    if not index:
        return {"answer": "I have no documents yet — the office needs to run the ingest step.", "sources": []}
    qv = ollama("/api/embed", {"model": EMBED_MODEL, "input": [f"search_query: {q}"]})["embeddings"][0]
    scored = sorted(((cosine(qv, e["vec"]), e) for e in index), key=lambda s: -s[0])[:TOP_K]
    hits = [e for s, e in scored if s >= MIN_SCORE]
    if not hits:
        return {"answer": "Hmm — that one isn't in any circular I've read. Best to ask the admin office directly.",
                "sources": []}
    extracts = "\n\n".join(f"[from {e.get('title', e['file'])} ({e['file']})]\n{e['text']}" for e in hits)
    resp = ollama("/api/chat", {
        "model": CHAT_MODEL, "stream": False,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": f"Document extracts:\n\n{extracts}\n\nQuestion: {q}"}],
        "options": {"temperature": 0.2},
    })
    return {"answer": resp["message"]["content"].strip(),
            "sources": list(dict.fromkeys(e["file"] for e in hits))}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self): self._send(204, {})

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True, "chunks": len(index), "model": CHAT_MODEL})
        else:
            self._send(404, {"error": "POST /ask or GET /health"})

    def do_POST(self):
        if self.path != "/ask":
            return self._send(404, {"error": "POST /ask"})
        try:
            q = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)))).get("q", "").strip()
            if not q or len(q) > 500:
                return self._send(400, {"error": "send {'q': 'your question'} (max 500 chars)"})
            self._send(200, answer(q))
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}")


if __name__ == "__main__":
    print(f"Gubbi serving on http://localhost:{PORT}  (POST /ask)")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
