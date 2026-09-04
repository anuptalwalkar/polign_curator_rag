from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Evidence:
    id: str
    collection: str
    text: str
    source_url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def citation(self) -> str:
        prefixes = {
            "nga_candidates": "CAND",
            "art_context": "CTX",
            "visual_cache": "IMG",
            "curator_memory": "MEM",
        }
        return f"{prefixes.get(self.collection, 'EVID')}:{self.id}"


@dataclass(frozen=True)
class VisualPlan:
    needed: bool
    artwork_ids: List[str]
    reason: str


@dataclass(frozen=True)
class Review:
    passed: bool
    score: int
    issues: List[str]
    required_changes: List[str]


@dataclass(frozen=True)
class PipelineResult:
    answer: str
    draft: str
    review: Review
    evidence: List[Evidence]
    visual_plan: VisualPlan
    trace: List[str]

