from core.rag import embed_texts, chunk_text, bm25_scores
def index_documents(store, documents, client = None, model = None, chunk_size=200, overlap=30):
    """ spliting each document in documents into chunk_size length with an overlap """
    for document in documents:
        chunks = chunk_text(document["text"], chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            continue
        embeded_chunks = embed_texts(chunks, client, model)
        for (chunk, embeding_chunk) in zip(chunks, embeded_chunks):
            store.add(chunk,embeding_chunk, metadata = {"title" : document["title"]} )
    return store


def build_notes_registry(store, client=None, model=None):
    from core.tools import ToolRegistry
    from core.rag import hybrid_search, rerank_with_llm
    registry = ToolRegistry()

    
    def search_notes(query, candidates = 20, top_n = 4):
        hybrid_search_candidates = hybrid_search(store, query, client, model, top_n, candidates) # +++> 20 candidates Return : {"score", "text", "metadata"}
        if not hybrid_search_candidates:
            return "No matching notes."
        candidates_text = [doc_text["text"] for doc_text in hybrid_search_candidates]

        reranking_llm = rerank_with_llm(client, model, query, candidates_text, top_n) #--->Returns the top_n candidatures: [texts] || input : list [texts]
        title_of = {hit["text"]: hit["metadata"].get("title", "note") for hit in hybrid_search_candidates}
        return "\n\n".join(f"[{title_of.get(text, 'note')}] \n {text}" for text in reranking_llm)

    registry.register(name="search_notes", fn = search_notes, schema={
        "type" : "function",
        "function": {
            "name":"search_notes",
            "description" :"this tool is used to retreive data from existing documents to help answer to the user question",
            "parameters":{
                "type":"objects",
                "properties":{"query":{"type": "string", "description":"the question of the user"},
                              "candidates" :{"type" : "integer", "description" : "the number of candidates to extract using the hybrid search and then to feed to the llm reranking model it should be less than 25"},
                              "top_n":{"type": "integer", "description" :"the number of queries to retrieve from the data"}},
                "required":["query"]
            }
        }
    })
    return registry
    
