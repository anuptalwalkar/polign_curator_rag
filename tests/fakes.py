from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List

from polign_curator.models import Review, VisualPlan


@dataclass
class Row:
    id: str
    values: List[float]
    metadata: Dict[str, Any]


@dataclass
class Page:
    vectors: List[Row]
    total: int


@dataclass
class Hit:
    id: str
    distance: float
    metadata: Dict[str, Any]


class FakeClient:
    def __init__(self):
        self.collections: Dict[str, Dict[str, Row]] = {}

    def put(self, collection, id, values, metadata=None):
        self.collections.setdefault(collection, {})[id] = Row(id, list(values), dict(metadata or {}))
        return id

    def put_many(self, collection, vectors):
        return [self.put(collection, row.id, row.values, row.metadata) for row in vectors]

    def list(self, collection, limit=0, offset=0, filter=None, typed_metadata=False):
        if collection not in self.collections:
            raise LookupError(collection)
        rows = [row for row in self.collections[collection].values() if _matches(row.metadata, filter or {})]
        rows.sort(key=lambda row: row.id)
        selected = rows[offset: offset + limit] if limit else rows[offset:]
        return Page(selected, len(rows))

    def search(self, collection, values=None, k=10, filter=None, **kwargs):
        if collection not in self.collections:
            raise LookupError(collection)
        rows = [row for row in self.collections[collection].values() if _matches(row.metadata, filter or {})]
        hits = [Hit(row.id, _distance(values, row.values), dict(row.metadata)) for row in rows]
        hits.sort(key=lambda hit: hit.distance)
        return hits[:k]

    def update_metadata(self, collection, ids, set=None, unset=None):
        changed = []
        for id in ids:
            row = self.collections.get(collection, {}).get(id)
            if not row:
                continue
            row.metadata.update(set or {})
            for key in unset or []:
                row.metadata.pop(key, None)
            changed.append(id)
        return changed


def _matches(metadata, selector):
    return all(metadata.get(key) == value for key, value in selector.items())


def _distance(left, right):
    if left is None:
        return 0.0
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))


class FakeReasoner:
    def __init__(self, fail_first_review: bool = False):
        self.fail_first_review = fail_first_review
        self.review_calls = 0
        self.inspect_calls = 0

    def plan_visuals(self, question, candidates, memories):
        return VisualPlan(True, [candidates[0].id], "the question asks for visible color and composition")

    def inspect_image(self, question, candidate):
        self.inspect_calls += 1
        return "Visible green enclosure and a bridge pressed near the upper edge."

    def draft(self, question, memories, candidates, contexts, visuals):
        return (
            f"Recommend the first work [{candidates[0].citation}] because the visible enclosure supports the theme "
            f"[{visuals[0].citation}], consistent with the research frame [{contexts[0].citation}].\n"
            f"Sources\n{candidates[0].source_url}\n{contexts[0].source_url}"
        )

    def review(self, question, draft, evidence, allowed_candidate_ids):
        self.review_calls += 1
        if self.fail_first_review and self.review_calls == 1:
            return Review(False, 60, ["make the distinction between observation and interpretation explicit"], ["qualify the interpretation"])
        return Review(True, 96, [], [])

    def revise(self, question, draft, review, evidence):
        return "Observation and interpretation are separated. " + draft

    def summarize(self, question, draft, review):
        return f"{draft}\n\nIn short\n- Selected from the allowed set.\n- Review score: {review.score}."
