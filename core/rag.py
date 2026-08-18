import os
import math
from openai import OpenAI
import json

def chunk_text(text, chunk_size=200, overlap=30):
    words = text.split()
    start = 0
    n = len(words)
    chunks = []
    while start < n:
        chunks.append(" ".join(words[start: start + chunk_size]))
        start +=  chunk_size - overlap
    return chunks

def embed_texts(texts, client=None, model= None):
    """ list of vectors (list of lists of flostas)"""
    if not client :
        from core.llm import get_embed_client
        client = get_embed_client()
    if not model :
        model = os.environ.get("EMBED_MODEL", "nomic-embed-text")
    resp = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in resp.data]

def cosine_similarity(a, b):
    a_mag = math.sqrt(sum(i **2 for i in a))
    b_mag = math.sqrt(sum(i** 2 for i in b))
    if a_mag == 0 or  b_mag == 0 :
        return 0.0
    return (sum(x * y for x , y in zip(a, b)))/(b_mag * a_mag)

class VectorStore:
    def __init__(self):
        self.items = []
    def add(self, text, vector, metadata = None):
        to_add = {"text" : text,
                  "vector" : vector,
                  "metadata" : metadata or {}}
        self.items.append(to_add)

    def search(self, query_vector, top_k= 3):
        """ scores every item against query_vector with your cosine_similarity, sorts best first, and returns the top top_k as a list of ....
        returns the top_k {"score":..., "text":..., "metadata": ....}"""
        scored = [{"score":cosine_similarity(query_vector, item["vector"]),
                   "text" : item["text"],
                   "metadata" : item["metadata"]}
                   for item in self.items]
        sorted_dic = sorted(scored, key= lambda t: t["score"], reverse=True)
        return sorted_dic[: top_k]

def bm25_scores(query, documents, k1=1.5, b=0.75):
    if not documents:
        return []
    query_tokens = str(query).lower().split()
    documentsInTokens = [str(document).lower().split() for document in documents]
    avgdl = sum(len(doc_tok) for doc_tok in documentsInTokens)/len(documents)
    tokens = set(query_tokens)
    idfs = {}
    for token in tokens:
        n_q = sum(token in doc for doc in documentsInTokens)
        N = len(documentsInTokens)
        idf = math.log((N - n_q + 0.5) / (n_q + 0.5) + 1)
        idfs[token] = idf
    output = []
    for doc in documentsInTokens:
        the_idf = 0
        for token in tokens:
            f = doc.count(token)
            d = len(doc)
            the_idf += idfs[token] * (f * (k1 + 1)) / (f + k1 * (1 - b + b * d / avgdl))
        output.append(the_idf)
    return output

def reciprocal_rank_fusion(rankings, k = 60):
    """
    @rankings: is a list of ranked lists of keys (best first) - e.g [[3, 0, 7], [0, 3, 9]]
    """
    store = {}

    for ranking in rankings:
        for rank, key in enumerate(ranking, start= 1):
            store[key] = store.get(key , 0.0) + 1/(rank + k)
    output = [{"key": key, "score" : score} for key, score in store.items()]
    output = sorted(output, key=lambda l: l["score"], reverse=True)
    return output

# hybrid search (mandatory)

def hybrid_search(store, query, client=None, model = None, top_k = 5, candidates = 20):
    """
    hybrid search : embed the query , score it agaist every stored vector with cosine_similarity
    take the candidates best indexes ( into store.items), best first
    Return : {"score", "text", "metadata"}
    """
    if not store.items:
        return []
    texts = [item["text"] for item in store.items]
    #1: embed the query:
    query_vector = embed_texts([query], client = client , model=model)[0]
    dense_score = [cosine_similarity(query_vector, item["vector"] ) for item in store.items]
    dense = sorted(range(len(dense_score)), key=lambda i: dense_score[i], reverse=True)[:candidates]

    # bm25
    sparse_scores = bm25_scores(query=query, documents=texts) # ===> the scores of the documents
    scores = sorted(range(len(sparse_scores)), key=lambda i: sparse_scores[i], reverse=True)[:candidates]
    final_rank = reciprocal_rank_fusion([dense, scores])[:top_k]
    out = []
    for rank in final_rank:
        out.append({"score": rank["score"], "text": texts[rank["key"]], "metadata":store.items[rank["key"]]["metadata"]})
    return out

def parse_json(answer):
    counter = 0
    start = answer.find("{")

    while start != -1:
        for i in range(start, len(answer)):
            if answer[i] == "{":
                counter +=1
            elif answer[i] == "}":
                counter -= 1
            if counter == 0:
                try:
                    output = json.loads(answer[start: i + 1])
                    return output
                except json.JSONDecodeError:
                    start = answer.find("{",  start+1)
                    counter = 0
                    break
    raise ValueError("No json file is found")


def rerank_with_llm(client, model, query, candidates, top_n = 5):
    candidates = list(candidates)
    if not candidates : return []

    numbered = "\n".join(f"{i} : {text}" for i, text in enumerate(candidates))
    prompt = (
        "Rank the passages below by how well they answer the question. \n\n"
        f"Question: {query} \n\n Passages: \n{numbered}\n\n"
        'REPLY ONLY WITH JSON: {"ranking": [indexes, most relevant first]}'
    )
    try:
        resp = client.chat.completions.create(
            model = model, messages = [{"role" : "user", "content" : prompt}]
        )
        order = parse_json(resp.choices[0].message.content or "")["ranking"]
    except Exception:
        return candidates[:top_n]

    out, seen = [], set()
    for index in order:
        if isinstance(index, int) and 0 <= index < len(candidates) and index not in seen:
            seen.add(index)
            out.append(candidates[index])
        if len(out) >= top_n:
            break
    return out
