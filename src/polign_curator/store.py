from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Protocol, Sequence

from .embeddings import Embedder
from .models import Evidence

MEMORY = "curator_memory"
CANDIDATES = "nga_candidates"
CONTEXT = "art_context"
VISUAL = "visual_cache"


class VectorClient(Protocol):
    def put(self, collection: str, id: str, values: Sequence[float], metadata=None): ...
    def put_many(self, collection: str, vectors): ...
    def search(self, collection: str, values=None, k: int = 10, **kwargs): ...
    def list(self, collection: str, limit: int = 0, offset: int = 0, **kwargs): ...


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


class PolignRAGStore:
    def __init__(self, client: VectorClient, embedder: Embedder):
        self.client = client
        self.embedder = embedder

    def seed(self, candidates: Iterable[Dict[str, Any]], contexts: Iterable[Dict[str, Any]]) -> Dict[str, int]:
        from polign import Vector

        candidate_rows = list(candidates)
        context_rows = list(contexts)
        candidate_vectors = [
            Vector(
                id=row["id"],
                values=self.embedder.embed(_candidate_document(row)),
                metadata={**row, "document": _candidate_document(row)},
            )
            for row in candidate_rows
        ]
        context_vectors = [
            Vector(
                id=row["id"],
                values=self.embedder.embed(row["text"]),
                metadata={**row, "document": row["text"]},
            )
            for row in context_rows
        ]
        if candidate_vectors:
            self.client.put_many(CANDIDATES, candidate_vectors)
        if context_vectors:
            self.client.put_many(CONTEXT, context_vectors)
        return {CANDIDATES: len(candidate_vectors), CONTEXT: len(context_vectors)}

    def remember(self, user_id: str, key: str, value: str, kind: str = "preference") -> Evidence:
        try:
            active = self.client.list(
                MEMORY,
                limit=100,
                filter={"user_id": user_id, "key": key, "status": "active"},
                typed_metadata=True,
            )
            old_rows = list(active.vectors)
        except Exception as exc:
            # Collections auto-create on first put.
            if not _is_missing_collection(exc):
                raise
            old_rows = []
        memory_id = _stable_id("mem", user_id, key, value, _now())
        # Re-upsert with the original vector instead of relying on the newer
        # vectors:update endpoint. This keeps the demo compatible with both
        # polign-server 0.4.x and 0.5.x.
        for row in old_rows:
            old_metadata = dict(row.metadata)
            old_metadata.update({"status": "superseded", "superseded_by": memory_id})
            self.client.put(MEMORY, row.id, row.values, metadata=old_metadata)
        document = f"{kind}: {key.replace('_', ' ')} = {value}"
        metadata = {
            "user_id": user_id,
            "kind": kind,
            "key": key,
            "value": value,
            "status": "active",
            "created_at": _now(),
            "document": document,
        }
        self.client.put(MEMORY, memory_id, self.embedder.embed(document), metadata=metadata)
        return Evidence(memory_id, MEMORY, document, metadata=metadata)

    def recall(self, user_id: str, query: str, limit: int = 5) -> List[Evidence]:
        try:
            hits = self.client.search(
                MEMORY,
                values=self.embedder.embed(query),
                k=limit,
                filter={"user_id": user_id, "status": "active"},
                typed_metadata=True,
            )
        except Exception as exc:
            if _is_missing_collection(exc):
                return []
            raise
        return [_hit_to_evidence(hit, MEMORY) for hit in hits]

    def list_memories(self, user_id: str, include_history: bool = False) -> List[Evidence]:
        selector: Dict[str, Any] = {"user_id": user_id}
        if not include_history:
            selector["status"] = "active"
        try:
            page = self.client.list(MEMORY, limit=500, filter=selector, typed_metadata=True)
        except Exception as exc:
            if _is_missing_collection(exc):
                return []
            raise
        return [_vector_to_evidence(row, MEMORY) for row in page.vectors]

    def candidate_set(self, set_id: str, query: str, limit: int = 6) -> List[Evidence]:
        hits = self.client.search(
            CANDIDATES,
            values=self.embedder.embed(query),
            k=limit,
            filter={"candidate_set": set_id, "eligible": True},
            typed_metadata=True,
        )
        return [_hit_to_evidence(hit, CANDIDATES) for hit in hits]

    def research(self, query: str, limit: int = 6) -> List[Evidence]:
        hits = self.client.search(
            CONTEXT,
            values=self.embedder.embed(query),
            k=limit,
            typed_metadata=True,
        )
        return [_hit_to_evidence(hit, CONTEXT) for hit in hits]

    def visual_observation(self, artwork_id: str, question: str) -> Optional[Evidence]:
        try:
            hits = self.client.search(
                VISUAL,
                values=self.embedder.embed(question),
                k=1,
                filter={"artwork_id": artwork_id},
                typed_metadata=True,
            )
        except Exception as exc:
            if _is_missing_collection(exc):
                return None
            raise
        if not hits or hits[0].distance > 0.28:
            return None
        return _hit_to_evidence(hits[0], VISUAL)

    def save_visual_observation(
        self,
        artwork_id: str,
        question: str,
        observation: str,
        image_url: str,
        source_url: str,
    ) -> Evidence:
        observation_id = _stable_id("visual", artwork_id, question)
        metadata = {
            "artwork_id": artwork_id,
            "question": question,
            "observation": observation,
            "image_url": image_url,
            "source_url": source_url,
            "created_at": _now(),
            "document": observation,
        }
        self.client.put(VISUAL, observation_id, self.embedder.embed(question), metadata=metadata)
        return Evidence(observation_id, VISUAL, observation, source_url, metadata)

    def collection_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for collection in (MEMORY, CANDIDATES, CONTEXT, VISUAL):
            try:
                counts[collection] = int(self.client.list(collection, limit=1).total)
            except Exception as exc:
                if _is_missing_collection(exc):
                    counts[collection] = 0
                    continue
                raise
        return counts


def load_seed_data(data_dir: str):
    with open(f"{data_dir}/candidates.json", encoding="utf-8") as handle:
        candidates = json.load(handle)
    with open(f"{data_dir}/context.json", encoding="utf-8") as handle:
        contexts = json.load(handle)
    return candidates, contexts


def _candidate_document(row: Dict[str, Any]) -> str:
    return (
        f"{row['title']} by {row['artist']}, {row['year']}. {row['medium']}. "
        f"{row['description']} Themes: {row.get('themes', '')}"
    )


def _hit_to_evidence(hit, collection: str) -> Evidence:
    metadata = dict(hit.metadata)
    text = str(metadata.get("document") or metadata.get("observation") or metadata.get("value") or "")
    return Evidence(hit.id, collection, text, str(metadata.get("source_url") or ""), metadata)


def _vector_to_evidence(row, collection: str) -> Evidence:
    metadata = dict(row.metadata)
    text = str(metadata.get("document") or metadata.get("value") or "")
    return Evidence(row.id, collection, text, str(metadata.get("source_url") or ""), metadata)


def _is_missing_collection(exc: Exception) -> bool:
    # Avoid importing a transport-specific error type so the store remains
    # straightforward to test with an in-process client.
    return exc.__class__.__name__ in {"NotFoundError", "LookupError"}
