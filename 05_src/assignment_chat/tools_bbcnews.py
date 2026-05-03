from langchain.tools import tool
from fastmcp import FastMCP
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from pydantic import BaseModel, Field

import pandas as pd
from dotenv import load_dotenv
#from utils.logger import get_logger
import os
import re
from pathlib import Path
from typing import Optional
import csv, time
from openai import OpenAI


#_logs = get_logger(__name__)

load_dotenv()
#load_dotenv(".secrets")


#We will not use docker

#vector_db_client_url="http://localhost:8000"
#chroma = chromadb.HttpClient(host=vector_db_client_url)
#collection = chroma.get_collection(name="pitchfork_reviews", 
#                                   embedding_function=OpenAIEmbeddingFunction(
#                                       api_key = os.getenv("OPENAI_API_KEY"),
#                                       model_name="text-embedding-3-small")
#                                   )

CHROMA_PATH      = "./chroma_db"
COLLECTION_NAME  = "bbc_news"
EMBED_MODEL      = "text-embedding-3-small"   # OpenAI embedding model
DATASET_CSV      = "./bbc_news.csv"
 
# Candidate column names (auto-detected from CSV headers)
TEXT_COLUMNS     = ["text", "news", "content", "body", "description", "summary", "article"]
TITLE_COLUMNS    = ["title", "headline", "head"]
CATEGORY_COLUMNS = ["category", "type", "label", "topic", "class"]
 
MAX_DOC_LENGTH   = 1_000   # truncate docs to this many characters before embedding
EMBED_BATCH_SIZE = 100     # OpenAI allows up to 2048 inputs, 100 is safe and fast

from dotenv import load_dotenv
load_dotenv("../../05_src/.secrets")

def _build_client() -> OpenAI:
    return OpenAI(
        base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
        api_key="any-value",
        default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY")},
    )

_openai_client: Optional[OpenAI] = None
 
def _get_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = _build_client()
    return _openai_client
 
 
# ── Globals (lazy-loaded) ──────────────────────────────────────────────────────
 
_client: Optional[chromadb.PersistentClient] = None
_collection = None
 
 
# Embedding via gateway
 
def _embed(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts using the OpenAI embeddings endpoint via your gateway.
    Automatically batches to stay within API limits.
    """
    client = _get_client()
    all_embeddings = []
 
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        try:
            response = client.embeddings.create(
                model=EMBED_MODEL,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            print(f"[search]   embedded {min(i + EMBED_BATCH_SIZE, len(texts)):,} / {len(texts):,}")
        except Exception as e:
            raise RuntimeError(f"Embedding API call failed on batch {i}: {e}")
 
        # batching
        if i + EMBED_BATCH_SIZE < len(texts):
            time.sleep(0.2)
 
    return all_embeddings
 
 
# CSV loader
 
def _detect_column(headers: list[str], candidates: list[str]) -> Optional[str]:
    """Return the first matching column name from candidates (case-insensitive)."""
    headers_lower = [h.lower().strip() for h in headers]
    for candidate in candidates:
        if candidate.lower() in headers_lower:
            return headers[headers_lower.index(candidate.lower())]
    return None
 
 
def _load_csv(path: str) -> list[dict]:
    """As per class lab, Load CSV and return list of dicts with keys: text, title, category."""
    if not Path(path).exists():
        raise FileNotFoundError(
            f"Dataset CSV not found at '{path}'.\n\n"
        )
 
    rows = []
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
 
        text_col     = _detect_column(headers, TEXT_COLUMNS)
        title_col    = _detect_column(headers, TITLE_COLUMNS)
        category_col = _detect_column(headers, CATEGORY_COLUMNS)
 
        if not text_col:
            raise ValueError(
                f"Could not find a text column in CSV.\n"
                f"Columns found: {headers}\n"
                f"Expected one of: {TEXT_COLUMNS}"
            )
 
        print(f"[search] CSV columns → text='{text_col}' | "
              f"title='{title_col}' | category='{category_col}'")
 
        for row in reader:
            text = row.get(text_col, "").strip()
            if not text:
                continue
            rows.append({
                "text":     text[:MAX_DOC_LENGTH],
                "title":    row.get(title_col, "").strip()    if title_col    else "",
                "category": row.get(category_col, "").strip() if category_col else "",
            })
 
    print(f"[search] Loaded {len(rows):,} documents from '{path}'.")
    return rows
 
 
# ChromaDB collection
 
def _get_collection():
    """Return the ChromaDB collection from the local CSV."""
    global _client, _collection
 
    if _collection is not None:
        return _collection
 
    Path(CHROMA_PATH).mkdir(exist_ok=True)
    _client = chromadb.PersistentClient(path=CHROMA_PATH)
 
    existing = [c.name for c in _client.list_collections()]
 
    if COLLECTION_NAME in existing:
        print(f"[search] Loading existing ChromaDB collection '{COLLECTION_NAME}'.")
        _collection = _client.get_collection(COLLECTION_NAME)
        print(f"[search] Collection ready — {_collection.count():,} documents.")
        return _collection
 
    print("building ChromaDB collection")
 
    rows       = _load_csv(DATASET_CSV)
    texts      = [r["text"]     for r in rows]
    titles     = [r["title"]    for r in rows]
    categories = [r["category"] for r in rows]
    ids        = [f"doc_{i}"    for i in range(len(rows))]
 
    print(f"[search] Sending {len(texts):,} documents to embedding API…")
    embeddings = _embed(texts)
 
    _collection = _client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
 
    # Insert in batches
    BATCH = 500
    for start in range(0, len(texts), BATCH):
        end = start + BATCH
        _collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            embeddings=embeddings[start:end],
            metadatas=[
                {"title": t, "category": c}
                for t, c in zip(titles[start:end], categories[start:end])
            ],
        )
 
    print(f"[search] Collection built and saved to '{CHROMA_PATH}'. Won't rebuild again.")
    return _collection
 
 
# Use Open API embeddings. I guess I could have used a local model too? 
@tool
def handle_semantic_search(query: str, top_k: int = 5) -> str:
    """
    Semantic search: embed the query via the OpenAI gateway, then find the
    closest documents in ChromaDB using cosine similarity.
 
    Args:
        query:  The user's natural language question.
        top_k:  Number of results to return (default 5).
 
    Returns:
        Formatted markdown string with the top matching documents.
    """
    try:
        collection = _get_collection()
    except FileNotFoundError as e:
        return f"Dataset not found.\n\n{e}"
    except Exception as e:
        return f"Search service unavailable: {e}"
 
    # Embed the query via gateway
    try:
        query_vec = _embed([query])   # returns list of 1 embedding
    except Exception as e:
        return f"Embedding API failed: {e}"
 
    # Query ChromaDB
    try:
        results = collection.query(
            query_embeddings=query_vec,
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        return f"ChromaDB query failed: {e}"
 
    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]   # cosine distance lower = more similar
 
    if not docs:
        return "No results found for your query."
 
    lines = [f"**Semantic Search Results** for: *\"{query}\"*\n"]
 
    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
        similarity = round(1 - dist, 3)
        title      = meta.get("title", "")
        category   = meta.get("category", "")
        snippet    = doc[:300] + ("…" if len(doc) > 300 else "")
 
        header_parts = [f"**{rank}.**"]
        if title:
            header_parts.append(f"**{title}**")
        if category:
            header_parts.append(f"[{category}]")
        header_parts.append(f"_(similarity: {similarity:.3f})_")
 
        lines.append(" ".join(header_parts))
        lines.append(snippet)
        lines.append("")
 
    return "\n".join(lines)

def initialize_search_service() -> str:
    """
    Warm up the collection at startup so the first user query is not slow.
    Called once from app.py in a background thread.
    """
    try:
        _get_collection()
        count = _collection.count()
        return f"Search service ready — {count:,} documents indexed."
    except FileNotFoundError:
        return "Dataset CSV missing"
    except Exception as e:
        return f"Search service init failed: {e}"