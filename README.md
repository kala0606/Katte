# Katte

**Presence without policing** — a warm, kolam-woven availability platform for
faculty & staff at Srishti Manipal Institute.

> *katte* (n., Kannada) — the raised platform under a tree where a
> neighbourhood gathers. The original availability system.

A single self-contained `index.html` (vanilla JS, no build step). Mark where
you are today, find a colleague, book office hours, log teaching-plus work on
your Work Pie, and gather in the **Adda** channels. Every faculty member gets a
generative kolam mark, minted daily from their identity.

## Installable PWA

Katte installs to the home screen and runs offline (the app shell and fonts are
service-worker cached). On a phone: open the site → **Add to Home Screen**.

Just open `index.html` in a browser, or serve the folder statically:

```sh
python3 -m http.server 4173
```

## Gubbi — the admin-desk bot

**Gubbi** (ಗುಬ್ಬಿ, the sparrow) answers admin questions in the *Ask the Office*
adda — dates, deadlines, contacts — strictly from the office's own documents,
and always names the source. It runs fully on one local machine via
[Ollama](https://ollama.com) + retrieval (RAG); nothing leaves the machine
except the answers. See [`bot/README.md`](bot/README.md) for setup, the
document-ingest workflow, and the demo runbook.

The bot's scraped/generated data is git-ignored — regenerate it with
`bot/scrape.py` + `bot/ingest.py`. The sample docs in `bot/docs/` are
fictional, for demonstration.

---

*Prototype. Everything stays on the device; the real version signs in with an
`@srishti.ac.in` account.*
