# 0x06 — RAG: naive → advanced

Tasks **0–4** build the naive pipeline (chunk → embed → cosine → top-k). Tasks
**5–8** turn it into what production systems actually run: **hybrid retrieval** plus
**two-stage reranking**. If you've built naive RAG before, sprint through 0–4 (you
still need the code — everything after it builds on that `VectorStore`) and spend
your time on 5–8.


## Concepts

**The problem.** Your model knows what was in its training data. It does **not** know
your notes, your company's docs, yesterday's meeting minutes, or the PDF you saved this
morning. And you can't just paste everything into the prompt — the context window is
finite, and on a local 8B model it's *small*.

**The answer: retrieve first, then generate.** RAG = *Retrieval-Augmented Generation*:

```
   ahead of time:   documents ──chunk──► pieces ──embed──► vectors ──► store
   at question time: question ──embed──► vector ──compare──► top 3 closest pieces
                                                                    │
                                          "answer using ONLY this:" ┘ ──► model
```

You never send the whole library. You send the question plus the 3 paragraphs that
actually matter.

**What is an embedding?** A model that turns text into a list of numbers (e.g. 768 of
them) such that **texts with similar meaning land close together** in that space.
"How do I cancel my subscription?" and "unsubscribe instructions" share almost no
words, but their vectors are neighbours. That's why RAG beats keyword search: it
matches *meaning*, not spelling.

Ollama serves embedding models through the **same client you already built**:

```python
resp = client.embeddings.create(model="nomic-embed-text",
                                input=["first chunk", "second chunk"])
resp.data[0].embedding    # -> [0.013, -0.44, 0.87, ...]
```

Note `input` takes a **list**: always batch. One request for 500 chunks beats 500
requests. (Same client object, different endpoint — `.embeddings` instead of
`.chat.completions`.)

**Closeness = cosine similarity.** Two vectors are "similar" when they point the same
*direction*, regardless of length:

```
cos(a, b) = (a · b) / (|a| × |b|)      1.0 = identical direction
                                       0.0 = unrelated (perpendicular)
                                      -1.0 = opposite
```

Why direction and not distance? Because a long document and a short question about it
have very different magnitudes but should still match. Dividing by both lengths
cancels magnitude out. It's ~4 lines of Python and — like `find_free_slots` — it's
**pure math, no LLM**: another place where plain code beats a model.

**Chunking is a real design decision.** Chunks too big → you waste context and drag in
noise. Too small → a chunk loses the context that made it meaningful. And a naive
split can cut a sentence in half, so chunks **overlap** by a few words: the tail of
one chunk is the head of the next, so no idea gets guillotined at a boundary.

**Where RAG meets your agent.** Two designs:
- *Always retrieve* — every question triggers a search. Simple, but wasteful ("hi" doesn't need your docs).
- *RAG as a tool* — `search_notes` is just another tool on the registry, and the **model decides** when its own knowledge is insufficient.

You'll build the second, because you already own the machinery — and because it's the
one that composes with Gmail and Calendar in the final assistant.

---

## Concepts, part 2 — the three ways naive RAG fails

**Failure 1: dense embeddings are bad at exact terms.** Ask for `RFC3339`, error code
`ERR_2043`, a SKU, or a colleague's surname. An embedding *compresses meaning*, which
means it blurs rare literal tokens into "something technical-ish". Meanwhile a 30-year-old
keyword algorithm finds them instantly. The fix isn't to pick one — it's **hybrid
search**: run both, merge the results.

**BM25** is that keyword algorithm, still in every serious search stack. Three ideas:

- *term frequency* — more mentions = more relevant, but **saturating** (10 mentions isn't 10× better than 1)
- *inverse document frequency* — a word in every document tells you nothing; a rare word is a strong signal
- *length normalisation* — one hit in a 10-word note means more than one hit in a 10-page doc

```
score(D,Q) = Σ  IDF(q) · ────────f(q,D) · (k₁+1)────────
             q∈Q          f(q,D) + k₁·(1 − b + b·|D|/avgdl)
```
Scary-looking, ~15 lines of Python, and no model involved. Another *pure logic* piece.

**Failure 2: two ranked lists, incomparable scores.** Cosine lives in [-1, 1]; BM25 is
unbounded and depends on your corpus. Normalising them onto a common scale is fiddly and
corpus-dependent. So the trick everyone actually uses is to **throw the scores away and
keep only the ranks**:

```
Reciprocal Rank Fusion:   score(d) = Σ  1 / (k + rank_i(d))        k ≈ 60
                                  rankings i
```

A document that's #2 in *both* lists beats one that's #1 in one list and #8 in the other.
That's exactly what you want: agreement between independent judges. Ten lines, no tuning,
and it outperforms most clever score-normalisation schemes.

**Failure 3: the embedding never saw your question.** This is the deep one. A chunk's
vector is computed *once, offline, before your question exists* — that's what makes
retrieval fast (precompute millions, compare in milliseconds) and also what makes it
lossy. The fix is a **second stage**:

```
query ──►[ stage 1: bi-encoder ]  compares two vectors    ──► top 30 candidates
          fast · precomputed · a bit sloppy                    (high recall)
      ──►[ stage 2: cross-encoder ] reads query + chunk    ──► top 5, well ordered
          slow · per-pair · much smarter                       (high precision)
```

A **cross-encoder** reads the question and the chunk *together* and scores the actual
relationship. Far more accurate — and impossible to precompute, so you can only afford it
on ~30 candidates, never on 100k. Hence: **cast a wide net cheaply, then sort it
carefully.** Recall first, precision second.

Ollama has no dedicated rerank endpoint, so locally your stage 2 is **the LLM itself**:
hand Qwen the query plus numbered candidates and ask which are actually relevant. You
already own every piece that needs — the client, JSON extraction, and the "never trust
model output" reflex from 0x01.

**And the rule that governs all three:** every one of these adds latency. Hybrid doubles
your search work; reranking adds a whole model call. Production RAG is a *recall vs.
precision vs. latency* negotiation, not a checklist. Build them, measure, then decide.

## Read (time-boxed — the Concepts section above is the actual lesson)

**Before the tasks (5 min, then pull the model):**
- Ollama embedding models — skim, then run `ollama pull nomic-embed-text`:
  https://ollama.com/blog/embedding-models

**Only when a task sends you there (lookup, not reading):**
- Task 1 — the `embeddings.create` request/response shape (one example is enough):
  https://platform.openai.com/docs/api-reference/embeddings

**Before tasks 5–8 (10 min, optional — the Concepts part 2 above already covers it):**
- BM25 in one page (skim the formula, ignore the derivations):
  https://en.wikipedia.org/wiki/Okapi_BM25

**After the module is green (20 min, genuinely worth it):** Anthropic's Contextual
Retrieval — it *combines* everything you just built (hybrid + rerank) and adds one more
trick on top. You'll understand every word of it once your own version runs:
https://www.anthropic.com/news/contextual-retrieval

## You're done when you can answer these without Google

- Why can't you just paste all your documents into the system prompt?
- What makes two embeddings "similar", and why cosine (direction) rather than distance?
- Why do chunks overlap?
- Why is `search_notes` a *tool* rather than something that runs on every message?
- Which parts of RAG involve no LLM at all? (There are more than you'd think.)
- Give a concrete query where dense embeddings lose to plain keyword search, and say why.
- Why does RRF fuse **ranks** instead of averaging the two systems' scores?
- What can a cross-encoder do that a bi-encoder structurally cannot — and why can't you
  just use the cross-encoder for everything?
- Your reranker returns garbage. What should your search return, and why is that the
  only acceptable answer?

## Before the tasks

```powershell
ollama pull nomic-embed-text
```
(If you prefer another embedding model, set `EMBED_MODEL` in your environment.)

## General requirements

- New file: `core/rag.py` (the reusable machinery) and `agents/notes_agent.py` (the agent-facing part).
- Same dependency-injection rule: anything that embeds takes `client=None, model=None`.
- Tasks 0, 2, 3 are **pure logic** — no network, no model, no I/O.
- Verify: `python checker.py 0x06`

---

## Tasks

### 0. Chop the documents (mandatory)
**File:** `core/rag.py`

`chunk_text(text, chunk_size=200, overlap=30)` → list of strings.
- Split `text` on whitespace into words, then slide a window of `chunk_size` words
  forward by `chunk_size - overlap` each step, joining each window back with spaces.
- Empty/whitespace-only text → `[]`.
- Text shorter than `chunk_size` → a single chunk containing all of it.
- `overlap` must be smaller than `chunk_size` (otherwise the window never advances —
  guard against it or your loop hangs forever).

```powershell
python checker.py 0x06 0
```

### 1. Text → vectors (mandatory)
**File:** `core/rag.py`

`embed_texts(texts, client=None, model=None)` → list of vectors (list of lists of floats).
- `client=None` → `core.llm.get_client()`; `model=None` → `os.environ.get("EMBED_MODEL", "nomic-embed-text")`.
- Send **all** texts in ONE `client.embeddings.create(model=..., input=texts)` call.
- Pull each vector out of the response: `[item.embedding for item in resp.data]`.

```powershell
python checker.py 0x06 1
```

### 2. How close are two vectors? (mandatory)
**File:** `core/rag.py`

`cosine_similarity(a, b)` → float.
- dot product divided by the product of both magnitudes.
- If either vector has zero magnitude, return `0.0` — **never** let it raise
  `ZeroDivisionError` (an empty chunk would take your whole search down).
- No numpy needed: `sum(x * y for x, y in zip(a, b))` and `math.sqrt`.

```powershell
python checker.py 0x06 2
python checker.py 0x06 2 --integration   # real Ollama embeddings: do two sentences
                                         # that MEAN the same thing score higher?
```

(Remember: the task number narrows the scope, `--integration` just *adds* the live
tests. `checker.py 0x06 --integration` runs the whole module — every task, done or not.)

### 3. The vector store (mandatory)
**File:** `core/rag.py`

```python
class VectorStore:
    def __init__(self): ...              # self.items = []
    def add(self, text, vector, metadata=None): ...
    def search(self, query_vector, top_k=3): ...
```

- `add` appends `{"text": ..., "vector": ..., "metadata": metadata or {}}` to `self.items`.
- `search` scores **every** item against `query_vector` with your `cosine_similarity`,
  sorts **best first**, and returns the top `top_k` as a list of
  `{"score": float, "text": str, "metadata": dict}`.
- Fewer items than `top_k` → return them all; empty store → `[]`.

(This is a toy version of what Chroma / FAISS / pgvector do. They add indexes so you
don't compare against *every* vector — but at your scale, a loop is genuinely fine,
and now you know what those libraries are hiding.)

```powershell
python checker.py 0x06 3
```

### 4. The notes agent (mandatory)
**File:** `agents/notes_agent.py`

`index_documents(store, documents, client=None, model=None, chunk_size=200, overlap=30)`
- `documents` is a list of `{"title": str, "text": str}`.
- For each document: chunk it, embed the chunks (batched!), and `add` each chunk to
  the store with metadata `{"title": <the document's title>}` so answers can cite a source.

`build_notes_registry(store, client=None, model=None)` → a `core.tools.ToolRegistry`
with one tool (the closure captures `store` — the model never sees it):

| tool name | parameters | behavior |
|---|---|---|
| `search_notes` | `query: str`, optional `top_k: int` | embed the query, search the store, return the matching chunks as a readable string (title + text per result) |

Write the description so the model knows *when* to reach for it — e.g. "Search the
user's personal notes and documents. Use this whenever the user asks about something
that isn't general knowledge."

```powershell
python checker.py 0x06 4
python checker.py 0x06
```

---

## Part 2 — advanced retrieval

### 5. BM25: keyword scoring (mandatory)
**File:** `core/rag.py`

`bm25_scores(query, documents, k1=1.5, b=0.75)` → a list of floats, **one per document,
in the same order**.

- Tokenise by `str(x).lower().split()` — both the query and each document.
- `avgdl` = average document length in words.
- For each **distinct** query term appearing in at least one document:
  `idf = math.log((N - n_q + 0.5) / (n_q + 0.5) + 1)` where `N` is the number of
  documents and `n_q` how many contain the term. (The `+ 1` keeps IDF positive even for
  a term that's in every document.)
- Add to each document's score: `idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * len(d)/avgdl))`
  where `f` is the term's count in that document. Documents with `f == 0` gain nothing.
- Empty `documents` → `[]`. Guard `avgdl == 0`.

No LLM, no network — pure logic, like `find_free_slots`.

```powershell
python checker.py 0x06 5
```

### 6. Reciprocal Rank Fusion (mandatory)
**File:** `core/rag.py`

`reciprocal_rank_fusion(rankings, k=60)` where `rankings` is a **list of ranked lists**
of keys (best first) — e.g. `[[3, 0, 7], [0, 3, 9]]`.

- Every key gets `1 / (k + rank)` from each list it appears in, with **rank starting at 1**.
- Return `[{"key": ..., "score": ...}, ...]` sorted **best first**.
- A key missing from a list simply contributes nothing from it.

Ten lines. Test yourself on `[["a","b","c"], ["b","c","a"]]` before running the checker —
`b` should win despite never being first in list 1. Understand *why* and you understand RRF.

```powershell
python checker.py 0x06 6
```

### 7. Hybrid search (mandatory)
**File:** `core/rag.py`

`hybrid_search(store, query, client=None, model=None, top_k=5, candidates=20)`

1. Embed the query; score it against **every** stored vector with `cosine_similarity`;
   take the `candidates` best **indexes** (into `store.items`), best first.
2. Run `bm25_scores(query, [item["text"] for item in store.items])`; take the
   `candidates` best indexes the same way.
3. Fuse the two index rankings with `reciprocal_rank_fusion`.
4. Return the top `top_k` as `{"score", "text", "metadata"}` — same shape as
   `VectorStore.search`, so it's a drop-in replacement. Empty store → `[]`.

```powershell
python checker.py 0x06 7
```

### 8. Stage 2: rerank with the LLM (mandatory)
**File:** `core/rag.py`

`rerank_with_llm(client, model, query, candidates, top_n=5)` where `candidates` is a
list of strings.

- Build a prompt with the query and the candidates **numbered from 0**, asking the model
  to reply with JSON: `{"ranking": [<indexes, most relevant first>]}`.
- Parse the reply and return the candidate **strings** in that order, capped at `top_n`.
- **Skip** any index that's out of range or repeated.
- If the reply can't be parsed at all → **fall back to the original order** (first
  `top_n`). A reranker that crashes is strictly worse than no reranker: stage 1 already
  gave you a decent list, so a broken stage 2 must degrade to it, never take the whole
  search down. (Same instinct as `ToolRegistry.execute` returning `"Error: ..."`.)
- Empty `candidates` → `[]`.

Reuse your brace-matching `extract_json` from 0x01 — this is a good moment to promote it
into `core/text.py` (you'll put `strip_thinking` there in 0x07 too).

```powershell
python checker.py 0x06 8
python checker.py 0x06
```

### 9. Wire it up (not checked — but do it)
**File:** `agents/notes_agent.py`

Upgrade `search_notes` to the full pipeline:

```
query ──► hybrid_search(candidates=20) ──► rerank_with_llm(top_n=4) ──► string for the model
```

Then compare answers before and after on your own notes. Ask something with a rare
literal term in it (a filename, an error message) — that's where you'll *see* hybrid earn
its keep.

### Try it for real (not checked)

Put a few `.md` or `.txt` files in a `notes/` folder, then at the course root:

```python
from core.rag import VectorStore
from core.agent import Agent
from agents.notes_agent import index_documents, build_notes_registry
from pathlib import Path

docs = [{"title": p.name, "text": p.read_text(encoding="utf-8")}
        for p in Path("notes").glob("*.md")]

store = VectorStore()
index_documents(store, docs)
agent = Agent("notes", "You answer from the user's notes. Use search_notes, and say "
                       "so when the notes don't contain the answer - never invent.",
              registry=build_notes_registry(store))
print(agent.run("What did I write about the agent loop?"))
```

Drop your own course notes in there and ask your assistant about them. That's a
private, local, personal knowledge base — built by you, in one module.
