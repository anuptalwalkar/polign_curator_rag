from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Protocol, Sequence

from .models import Evidence, Review, VisualPlan


class Reasoner(Protocol):
    def plan_visuals(self, question: str, candidates: Sequence[Evidence], memories: Sequence[Evidence]) -> VisualPlan: ...
    def inspect_image(self, question: str, candidate: Evidence) -> str: ...
    def draft(self, question: str, memories: Sequence[Evidence], candidates: Sequence[Evidence], contexts: Sequence[Evidence], visuals: Sequence[Evidence]) -> str: ...
    def review(self, question: str, draft: str, evidence: Sequence[Evidence], allowed_candidate_ids: Sequence[str]) -> Review: ...
    def revise(self, question: str, draft: str, review: Review, evidence: Sequence[Evidence]) -> str: ...
    def summarize(self, question: str, draft: str, review: Review) -> str: ...


class OpenAIReasoner:
    def __init__(self, model: str, reviewer_model: str = ""):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = model
        self.reviewer_model = reviewer_model or model

    def plan_visuals(self, question, candidates, memories) -> VisualPlan:
        prompt = f"""You plan evidence gathering for a museum curator. Decide whether the actual images must be inspected to answer the question. Image inspection is needed for visual comparisons such as color, composition, mood, visible people, brushwork, or spatial arrangement. It is not needed for dates, artists, medium, or provenance already in catalog records.

Question: {question}
Memories:\n{_evidence_block(memories)}
Candidates:\n{_evidence_block(candidates)}

Return JSON only: {{"needed": boolean, "artwork_ids": [IDs from candidates, at most 3], "reason": "short reason"}}"""
        obj = self._json(prompt)
        allowed = {item.id for item in candidates}
        ids = [item for item in obj.get("artwork_ids", []) if item in allowed][:3]
        needed = bool(obj.get("needed")) and bool(ids)
        return VisualPlan(needed, ids if needed else [], str(obj.get("reason", "")))

    def inspect_image(self, question: str, candidate: Evidence) -> str:
        image_url = str(candidate.metadata.get("image_url") or "")
        response = self.client.responses.create(
            model=self.model,
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": (
                        "Inspect this artwork only for visible evidence relevant to the question. "
                        "Separate observation from interpretation, do not identify unseen details, "
                        f"and answer in at most 120 words.\nQuestion: {question}\n"
                        f"Catalog identity: {candidate.text}"
                    )},
                    {"type": "input_image", "image_url": image_url, "detail": "high"},
                ],
            }],
        )
        return response.output_text.strip()

    def draft(self, question, memories, candidates, contexts, visuals) -> str:
        prompt = f"""Write an evidence-grounded curatorial recommendation. Select only from the candidate records. Use the research context to support interpretation and memories only as user preferences. Every factual or visual claim must end with one or more exact evidence tags shown below, such as [CAND:nga-74796] [CTX:ctx-impressionism]. Do not cite memory as scholarship. Explicitly distinguish catalog fact, visible observation, and interpretation. End with a Sources list containing only the source URLs actually used. If evidence is insufficient, say so.

Question: {question}

MEMORY\n{_evidence_block(memories)}
CANDIDATES\n{_evidence_block(candidates)}
RESEARCH\n{_evidence_block(contexts)}
IMAGE OBSERVATIONS\n{_evidence_block(visuals)}
"""
        return self._text(prompt)

    def review(self, question, draft, evidence, allowed_candidate_ids) -> Review:
        prompt = f"""You are an independent evidence reviewer. Review the draft against the ledger. Fail it for any unsupported claim, invented citation, selected artwork outside ALLOWED CANDIDATES, image-derived claim without IMG evidence, or conclusion that overstates the sources. Do not rewrite the draft.

QUESTION: {question}
ALLOWED CANDIDATES: {', '.join(allowed_candidate_ids)}
LEDGER:\n{_evidence_block(evidence)}
DRAFT:\n{draft}

Return JSON only: {{"passed": boolean, "score": integer 0-100, "issues": [strings], "required_changes": [strings]}}"""
        obj = self._json(prompt, model=self.reviewer_model)
        return Review(
            bool(obj.get("passed")),
            max(0, min(100, int(obj.get("score", 0)))),
            [str(item) for item in obj.get("issues", [])],
            [str(item) for item in obj.get("required_changes", [])],
        )

    def revise(self, question, draft, review, evidence) -> str:
        prompt = f"""Revise the draft to resolve every required change. Preserve exact evidence tags and remove claims that the ledger cannot support. Return only the revised draft.

QUESTION: {question}
LEDGER:\n{_evidence_block(evidence)}
DRAFT:\n{draft}
REVIEW: {json.dumps(review.__dict__)}"""
        return self._text(prompt)

    def summarize(self, question, draft, review) -> str:
        prompt = f"""Produce the final curator-facing answer from the reviewed draft. Start with the recommendation, retain its evidence tags and source URLs, and end with a two-bullet summary labeled 'In short'. Do not add facts. Mention the review score in one short line.

QUESTION: {question}
REVIEW: {json.dumps(review.__dict__)}
REVIEWED DRAFT:\n{draft}"""
        return self._text(prompt)

    def _text(self, prompt: str, model: str = "") -> str:
        response = self.client.responses.create(model=model or self.model, input=prompt)
        return response.output_text.strip()

    def _json(self, prompt: str, model: str = "") -> Dict[str, Any]:
        return _parse_json(self._text(prompt, model=model))


def _evidence_block(items: Sequence[Evidence]) -> str:
    if not items:
        return "(none)"
    lines: List[str] = []
    for item in items:
        source = f" source={item.source_url}" if item.source_url else ""
        lines.append(f"[{item.citation}] {item.text}{source}")
    return "\n".join(lines)


def _parse_json(text: str) -> Dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError(f"model did not return a JSON object: {text[:160]}")
    value = json.loads(cleaned[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("model JSON response must be an object")
    return value
