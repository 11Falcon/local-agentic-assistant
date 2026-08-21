"""Checks for rag_agent. DO NOT EDIT."""
import pytest

import course_kit as kit
from course_kit import (FakeEmbedder, FakeLLM, import_or_fail, sample_documents)

HINT = "create core/rag.py at the COURSE ROOT"
HINT_AGENT = "create agents/notes_agent.py at the COURSE ROOT"


def _rag():
    return import_or_fail("core.rag", HINT)


def _notes():
    return import_or_fail("agents.notes_agent", HINT_AGENT)


# ---------------------------------------------------------------- task 0

def test_task_0_chunk_text_windows_and_overlap():
    r = _rag()
    text = " ".join(f"w{i}" for i in range(100))
    chunks = r.chunk_text(text, chunk_size=10, overlap=2)
    assert isinstance(chunks, list) and len(chunks) > 1
    assert all(isinstance(c, str) for c in chunks)
    assert len(chunks[0].split()) == 10, "the first chunk must hold chunk_size words"
    assert chunks[0].split()[-2:] == chunks[1].split()[:2], \
        "chunks must overlap: the last `overlap` words of one chunk start the next"
    joined = " ".join(chunks)
    assert "w0" in joined and "w99" in joined, "no words may be dropped"


def test_task_0_chunk_text_edge_cases():
    r = _rag()
    assert r.chunk_text("just a few words", chunk_size=50, overlap=10) == ["just a few words"]
    assert r.chunk_text("", chunk_size=10, overlap=2) == []
    assert r.chunk_text("   \n  ", chunk_size=10, overlap=2) == []


# ---------------------------------------------------------------- task 1

def test_task_1_embed_texts_batches_one_call():
    r = _rag()
    fake = FakeEmbedder()
    vectors = r.embed_texts(["hello agent", "calendar meeting"], client=fake)
    assert isinstance(vectors, list) and len(vectors) == 2
    assert all(isinstance(v, list) for v in vectors), "return a list of vectors (lists of floats)"
    assert all(isinstance(x, float) for x in vectors[0])
    assert len(fake.calls) == 1, \
        "send ALL texts in ONE embeddings.create call - don't loop one call per text"
    assert fake.calls[0]["input"] == ["hello agent", "calendar meeting"]
    assert fake.calls[0]["model"], "pass the embedding model name to the API"


# ---------------------------------------------------------------- task 2

def test_task_2_cosine_similarity_math():
    r = _rag()
    assert r.cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)
    assert r.cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert r.cosine_similarity([1, 1], [3, 3]) == pytest.approx(1.0), \
        "same direction, different magnitude -> still 1.0 (that's the point of cosine)"
    assert r.cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)


def test_task_2_cosine_similarity_zero_vector_is_safe():
    r = _rag()
    assert r.cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0, \
        "a zero vector must return 0.0, never raise ZeroDivisionError"


# ---------------------------------------------------------------- task 3

def test_task_3_store_add_and_search_ranking():
    r = _rag()
    store = r.VectorStore()
    store.add("cats purr", [1.0, 0.0], {"title": "a.md"})
    store.add("dogs bark", [0.0, 1.0], {"title": "b.md"})
    store.add("kittens purr", [0.9, 0.1], {"title": "c.md"})

    assert len(store.items) == 3, "store every added chunk in self.items"

    results = store.search([1.0, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0]["text"] == "cats purr"
    assert results[1]["text"] == "kittens purr"
    assert results[0]["score"] > results[1]["score"], "results must be sorted best-first"
    assert results[0]["metadata"] == {"title": "a.md"}


def test_task_3_store_handles_small_and_empty():
    r = _rag()
    store = r.VectorStore()
    assert store.search([1.0, 0.0], top_k=3) == [], "an empty store returns an empty list"
    store.add("only one", [1.0, 1.0])
    out = store.search([1.0, 1.0], top_k=5)
    assert len(out) == 1, "top_k larger than the store returns everything it has"
    assert out[0]["metadata"] == {}, "metadata defaults to an empty dict, not None"


# ---------------------------------------------------------------- task 4

def test_task_4_index_documents_chunks_embeds_and_tags():
    r = _rag()
    n = _notes()
    fake = FakeEmbedder()
    store = r.VectorStore()
    docs = sample_documents()

    n.index_documents(store, docs, client=fake, chunk_size=12, overlap=3)

    assert len(store.items) >= len(docs), "each document should produce at least one chunk"
    titles = {item["metadata"].get("title") for item in store.items}
    assert titles == {d["title"] for d in docs}, \
        "every chunk needs metadata carrying its source document's title"
    assert all(isinstance(item["vector"], list) and item["vector"]
               for item in store.items), "every chunk must be stored with its embedding"
    assert fake.calls, "index_documents must embed the chunks"


def test_task_4_registry_search_notes_tool():
    r = _rag()
    n = _notes()
    fake = FakeEmbedder()
    store = r.VectorStore()
    n.index_documents(store, sample_documents(), client=fake, chunk_size=12, overlap=3)

    registry = n.build_notes_registry(store, client=fake)
    names = {s["function"]["name"] for s in registry.get_schemas()}
    assert "search_notes" in names, f"registry must expose search_notes - got {names}"

    out = registry.execute("search_notes", '{"query": "how does the agent loop work"}')
    assert isinstance(out, str) and out.strip(), "the tool must return a non-empty string"
    assert "agent" in out.lower(), \
        "the closest chunk to an agent-loop question should come from the agent-loop note"


# ---------------------------------------------------------------- task 5

def test_task_5_bm25_ranks_by_term_frequency():
    r = _rag()
    docs = ["the cat sat on the mat", "the cat cat cat sat", "dogs run in the park"]
    scores = r.bm25_scores("cat", docs)
    assert isinstance(scores, list) and len(scores) == 3, \
        "return one score per document, in the same order"
    assert scores[2] == 0.0, "a document without the query term scores 0"
    assert scores[1] > scores[0] > 0, "more occurrences of the term -> higher score"
    assert r.bm25_scores("cat", []) == []


def test_task_5_bm25_rewards_rare_terms_and_short_documents():
    r = _rag()
    docs = ["cat dog", "cat fish", "cat bird"]
    common = r.bm25_scores("cat", docs)[0]     # 'cat' is in every document
    rare = r.bm25_scores("dog", docs)[0]       # 'dog' is in only one
    assert rare > common, "IDF: a rare term must count for far more than a ubiquitous one"

    lengths = ["cat", "cat " + "filler " * 30]
    scored = r.bm25_scores("cat", lengths)
    assert scored[0] > scored[1], \
        "length normalisation: same term count, the shorter document wins"


# ---------------------------------------------------------------- task 6

def test_task_6_rrf_rewards_consistency():
    r = _rag()
    fused = r.reciprocal_rank_fusion([["a", "b", "c"], ["b", "c", "a"]])
    assert isinstance(fused, list) and len(fused) == 3
    assert set(fused[0]) >= {"key", "score"}, "each row needs 'key' and 'score'"
    keys = [row["key"] for row in fused]
    assert keys == ["b", "a", "c"], (
        "b is 2nd and 1st -> it must beat a, which is 1st and 3rd. "
        "Consistently-high beats once-first: that is the whole point of RRF.")
    assert fused[0]["score"] > fused[1]["score"] > fused[2]["score"]


def test_task_6_rrf_prefers_items_found_by_both_and_honours_k():
    r = _rag()
    fused = r.reciprocal_rank_fusion([["a", "b"], ["a", "c"]])
    assert fused[0]["key"] == "a", "an item in both rankings outranks items in only one"

    single = r.reciprocal_rank_fusion([["a", "b"]], k=1)
    assert single[0]["score"] == pytest.approx(0.5), \
        "rank must start at 1, so the best item scores 1/(k+1)"
    assert r.reciprocal_rank_fusion([]) == []


# ---------------------------------------------------------------- task 7

def test_task_7_hybrid_search_shape_and_top_k():
    r = _rag()
    n = _notes()
    fake = FakeEmbedder()
    store = r.VectorStore()
    n.index_documents(store, sample_documents(), client=fake)

    out = r.hybrid_search(store, "the agent loop", client=fake, top_k=2)
    assert isinstance(out, list) and len(out) == 2, "hybrid_search must respect top_k"
    for row in out:
        assert set(row) >= {"score", "text", "metadata"}, \
            "return the same shape as VectorStore.search so it is a drop-in replacement"
    assert r.hybrid_search(r.VectorStore(), "anything", client=fake) == [], \
        "an empty store returns an empty list"


def test_task_7_hybrid_finds_a_rare_literal_term_that_embeddings_blur():
    r = _rag()
    n = _notes()
    fake = FakeEmbedder()
    store = r.VectorStore()
    n.index_documents(store, sample_documents(), client=fake)

    # 'RFC3339' means nothing to the embedding model, but BM25 matches it exactly.
    hybrid = r.hybrid_search(store, "RFC3339", client=fake, top_k=len(store.items))
    hybrid_rank = next(i for i, row in enumerate(hybrid) if "RFC3339" in row["text"])

    qvec = r.embed_texts(["RFC3339"], client=fake)[0]
    dense = store.search(qvec, top_k=len(store.items))
    dense_rank = next(i for i, row in enumerate(dense) if "RFC3339" in row["text"])

    assert hybrid_rank <= dense_rank, (
        "the keyword half must pull an exact-match chunk up, never push it down "
        f"(hybrid rank {hybrid_rank}, dense-only rank {dense_rank})")


# ---------------------------------------------------------------- task 8

CANDIDATES = ["chunk zero", "chunk one", "chunk two", "chunk three"]


def test_task_8_rerank_reorders_by_the_models_ranking():
    r = _rag()
    fake = FakeLLM(['{"ranking": [2, 0, 3, 1]}'])
    out = r.rerank_with_llm(fake, "fake-model", "my question", CANDIDATES, top_n=2)
    assert out == ["chunk two", "chunk zero"], \
        "return the candidate STRINGS in the model's order, capped at top_n"

    sent = " ".join(str(m.get("content", "")) for m in fake.calls[0]["messages"])
    assert "my question" in sent, "the prompt must contain the query"
    assert "chunk two" in sent, "the prompt must contain the candidates to rank"


def test_task_8_rerank_survives_a_bad_reply():
    r = _rag()
    fake = FakeLLM(["honestly they all look fine to me"])
    out = r.rerank_with_llm(fake, "fake-model", "q", CANDIDATES, top_n=2)
    assert out == ["chunk zero", "chunk one"], (
        "an unparseable reply must fall back to the original stage-1 order - "
        "a broken reranker degrades, it never takes the search down")


def test_task_8_rerank_ignores_invalid_indexes():
    r = _rag()
    fake = FakeLLM(['{"ranking": [99, 1, 1, -4]}'])
    out = r.rerank_with_llm(fake, "fake-model", "q", CANDIDATES, top_n=3)
    assert out == ["chunk one"], "skip out-of-range and duplicated indexes"
    assert r.rerank_with_llm(FakeLLM([]), "fake-model", "q", [], top_n=3) == [], \
        "no candidates -> no model call, just an empty list"


@pytest.mark.integration
@pytest.mark.skipif(not kit.ollama_available(), reason="Ollama is not running on localhost:11434")
def test_task_2_integration_real_embeddings_capture_meaning():
    r = _rag()
    vectors = r.embed_texts(["the cat sat on the mat", "a feline rested on a rug",
                             "quarterly revenue increased by 12 percent"])
    assert len(vectors) == 3 and len(vectors[0]) > 10, \
        "expected real embedding vectors (pull one: ollama pull nomic-embed-text)"
    close = r.cosine_similarity(vectors[0], vectors[1])
    far = r.cosine_similarity(vectors[0], vectors[2])
    assert close > far, \
        "two sentences with the same meaning must score higher than two unrelated ones"
