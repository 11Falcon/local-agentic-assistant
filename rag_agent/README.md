# RAG: naive → advanced

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
model output" reflex from structured output.

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

---

## What this module produced

- [`core/rag.py`](../core/rag.py) — `chunk_text`, `embed_texts`,
  `cosine_similarity`, `VectorStore`, then the advanced half: `bm25_scores`,
  `reciprocal_rank_fusion`, `hybrid_search`, `rerank_with_llm`
- [`agents/notes_agent.py`](../agents/notes_agent.py) — indexing and the
  `search_notes` tool

Two-stage retrieval: hybrid search for recall, LLM reranking for precision.

Verified by [`tests/test_rag_agent.py`](tests/test_rag_agent.py) — `python checker.py rag_agent`
