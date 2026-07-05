# Gubbi — local Ollama + RAG pilot

Answers admin questions in the **Ask the Office** adda, strictly from the
documents in `docs/`, with the source cited. Runs entirely on one machine
(this Mac for the pilot; a campus box later). Nothing leaves the machine
except the answers.

## One-time setup

```sh
ollama pull nomic-embed-text        # embedding model (~270 MB)
ollama pull llama3.2                # answer model (already installed)
brew install cloudflared            # public tunnel for demos
```

Note for this 8 GB Mac: stick to llama3.2 (3B). gemma4 (9.6 GB) will not fit.

## Every time documents change ("training")

Drop pdf / docx / xlsx / txt / md files into `docs/`, then:

```sh
python3 ingest.py
```

(pdf/docx/xlsx parsing needs `pip install pypdf python-docx openpyxl`;
txt and md need nothing.)

### Guidelines for admin docs (share with the office)
- One topic per document, a clear title, and an issue date in the first lines.
- Real text, not scans — scanned PDFs have no extractable text.
- Tables are fine (Word tables and Excel sheets are read row by row).
- When a document is superseded, delete the old one and re-run ingest.

## Run the bot

```sh
python3 serve.py                    # http://localhost:8787
```

Quick test: `curl -s localhost:8787/health`
and `curl -s -X POST localhost:8787/ask -d '{"q":"when is the NAAC visit?"}'`

## Demo to phones (different wifi)

```sh
cloudflared tunnel --url http://localhost:8787
```

Copy the printed `https://<random>.trycloudflare.com` URL, then share the
prototype as:

```
https://<your-github-pages>/katte/?botapi=https://<random>.trycloudflare.com
```

The `?botapi=` parameter stores the bot's address in each phone's browser —
one link wires up the whole room. The tunnel URL changes every time
cloudflared restarts, so mint the link fresh before each demo.
Keep the Mac awake during demos: `caffeinate -dims` in a spare terminal.

## Moving to a campus machine later

Same three pieces (ollama, ingest.py, serve.py) on any always-on box with
16 GB RAM; swap `CHAT_MODEL` in serve.py to `llama3.1:8b` or `qwen2.5:7b`
for better answers, and replace the throwaway tunnel with a named
Cloudflare tunnel or a college subdomain.
