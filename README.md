# polign_curator_rag

A complex RAG demo in which collection boundaries are part of the application,
not just names in a prompt. A museum-research agent remembers a curator's
preferences, retrieves only from an approved case set, conditionally inspects
public-domain artwork images, derives a recommendation from a separate research
corpus, has the result independently reviewed, and summarizes only after it
passes.

The demo uses [polign_db](https://polign.com) for every durable or retrieved
artifact. It is deliberately small, observable, and suitable for a live demo.

## The four collections

| Collection | Access | Contents | Why it is separate |
|---|---|---|---|
| `curator_memory` | read/write | active and superseded user preferences, constraints, prior decisions | Personal state must never become scholarly evidence. |
| `nga_candidates` | read-only after seed | NGA artwork records and IIIF URLs | Every query is filtered by `candidate_set` and `eligible`; the agent cannot recommend a semantically similar work from another case. |
| `art_context` | read-only after seed | short sourced research passages | Interpretations must be supported independently of catalog ranking. |
| `visual_cache` | read/write | question-specific image observations | Images are inspected only when needed; derived observations are reusable and auditable. |

One extra artwork is seeded into `nga_candidates` under a control set. Tests
prove it cannot leak into the main `river-and-landscape-2026` case.

## What happens on one question

```text
question
   |
   +--> recall active preferences -------- curator_memory
   |
   +--> retrieve approved works ---------- nga_candidates
   |          filter: candidate_set + eligible
   |
   +--> visual planner
   |       +-- no --> continue
   |       +-- yes -> search cache -------- visual_cache
   |                    +-- miss -> inspect NGA IIIF image -> cache
   |
   +--> retrieve scholarly support ------- art_context
   |
   +--> evidence-tagged draft
   +--> independent review + code checks
   |       +-- fail -> one revision -> review again
   |       +-- fail again -> no answer
   |
   +--> final summary
```

The code-level reviewer validates every `[CAND:*]`, `[CTX:*]`, `[IMG:*]`, and
`[MEM:*]` tag against the actual retrieval ledger. A separate stateless model
review checks subtler problems: unsupported claims, catalog/observation/
interpretation confusion, candidate-set violations, and overstatement. The
summary stage only runs after both checks pass.

## Run it

Prerequisites: Python 3.9+, `polign-server`, and an OpenAI API key for reasoning
and conditional image inspection. The CLI automatically loads an ignored
project-local `.env` file; exported environment variables take precedence.

```bash
python3 -m venv .venv
.venv/bin/pip install -e .

# Terminal 1: one durable Polign database, four named collections.
polign-server -data ./curator.polign

# Terminal 2: idempotently seed the two read-only corpora.
.venv/bin/polign-curator seed

# Store durable, superseding preferences.
.venv/bin/polign-curator remember preferred_mood "quiet and contemplative"
.venv/bin/polign-curator remember avoid_theme "industrial triumphalism" --kind constraint

cp .env.example .env
# Edit .env and set OPENAI_API_KEY. Never commit this file.
.venv/bin/polign-curator ask \
  "Choose two works for a room about humans reshaping nature. Compare their visible composition, respect my preferences, and explain the contrast."
```

The default 256-dimensional hashing embedder is local, deterministic, and has
no model download. It is good for a transparent fixture, not production search.
Use OpenAI embeddings for a more semantic demonstration; seed and query must use
the same provider:

```bash
.venv/bin/polign-curator --embedding-provider openai seed
.venv/bin/polign-curator --embedding-provider openai ask "..."
```

Useful inspection commands:

```bash
.venv/bin/polign-curator collections
.venv/bin/polign-curator memories --history
.venv/bin/polign-curator ask --json "Compare visible color and spatial enclosure."
```

The agent sends NGA image URLs as `input_image` content through the OpenAI
Responses API only after its visual planner opts in. That integration follows
the official [images and vision](https://developers.openai.com/api/docs/guides/images-vision)
guidance. Text reasoning also uses stateless Responses API calls so the durable
state remains Polign, not provider conversation history.

## Demo script

A good live sequence makes all boundaries visible:

1. Seed, then show `collections`: candidates and context exist; memory and
   visual cache are empty.
2. Ask a date/medium-only question. The trace should show `needed=False`, so no
   image call occurs.
3. Store `preferred_mood=quiet and contemplative` and ask a visual composition
   question. The trace shows memory recall, filtered candidates, IIIF image
   inspection, context retrieval, review, and summary.
4. Ask the same visual question again. The trace reports `reused visual_cache`.
5. Change the preference to `energetic`. `memories --history` shows the old
   record as superseded, while normal recall returns only the active value.
6. Ask for `nga-93067-control` while keeping the main candidate set. The
   pipeline cannot retrieve it, and the reviewer rejects a fabricated citation.
7. Restart `polign-server` from `curator.polign`; memories and visual
   observations remain.

## Why these sources

The National Gallery of Art is unusually suitable for a reproducible
multimodal demo: its collection data is available as CC0 open data, eligible
artwork images are offered under CC0, object records link to stable IIIF image
endpoints, and the museum pages provide enough interpretive context to build a
small, traceable research corpus. See [SOURCES.md](SOURCES.md) for record-level
provenance and licensing notes.

`data/candidates.json` contains six eligible works in the main set and one
control work. `data/context.json` contains eight short summaries whose
`source_url` travels through Polign and into the evidence ledger. The repository
does not bundle image binaries; it references source-hosted IIIF renditions.

For a larger demo, replace the fixture loader with an ingest job over the
[NGA Open Data CSVs](https://github.com/NationalGalleryOfArt/opendata). Keep the
same boundary: materialize a case-specific `candidate_set` during ingest and
require that filter on every query.

## Tests

Tests are deterministic and do not need a server, network, or API key:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

They cover collection isolation, idempotent seeding, memory supersession,
conditional image caching, the review/revision loop, citation validation, and
embedding determinism.

## Repository map

```text
data/                       auditable NGA fixture and research passages
src/polign_curator/store.py collection-specific Polign reads and writes
src/polign_curator/llm.py   visual planner, vision, writer, reviewer, summarizer
src/polign_curator/pipeline.py deterministic orchestration and hard review checks
src/polign_curator/cli.py   seed, remember, inspect, and ask commands
tests/                      dependency-free unit tests with an in-memory client
```
