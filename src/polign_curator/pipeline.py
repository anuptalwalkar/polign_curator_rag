from __future__ import annotations

import re
from typing import List

from .llm import Reasoner
from .models import Evidence, PipelineResult, Review
from .store import PolignRAGStore


class CuratorPipeline:
    """A visible retrieve -> inspect -> derive -> review -> summarize workflow."""

    def __init__(self, store: PolignRAGStore, reasoner: Reasoner):
        self.store = store
        self.reasoner = reasoner

    def run(self, user_id: str, candidate_set: str, question: str) -> PipelineResult:
        trace: List[str] = []

        memories = self.store.recall(user_id, question, limit=5)
        trace.append(f"recalled {len(memories)} active memories from curator_memory")

        candidates = self.store.candidate_set(candidate_set, question, limit=6)
        if not candidates:
            raise ValueError(f"candidate set {candidate_set!r} returned no eligible records")
        trace.append(
            f"retrieved {len(candidates)} eligible works from nga_candidates with candidate_set={candidate_set!r}"
        )

        visual_plan = self.reasoner.plan_visuals(question, candidates, memories)
        trace.append(f"visual decision: needed={visual_plan.needed}; {visual_plan.reason}")
        by_id = {item.id: item for item in candidates}
        visuals: List[Evidence] = []
        for artwork_id in visual_plan.artwork_ids:
            candidate = by_id[artwork_id]
            cached = self.store.visual_observation(artwork_id, question)
            if cached:
                visuals.append(cached)
                trace.append(f"reused visual_cache observation for {artwork_id}")
                continue
            observation = self.reasoner.inspect_image(question, candidate)
            visuals.append(self.store.save_visual_observation(
                artwork_id,
                question,
                observation,
                str(candidate.metadata.get("image_url") or ""),
                candidate.source_url,
            ))
            trace.append(f"inspected NGA image and cached observation for {artwork_id}")

        research_query = _research_query(question, candidates, memories)
        contexts = self.store.research(research_query, limit=6)
        trace.append(f"retrieved {len(contexts)} supporting passages from art_context")

        evidence = [*memories, *candidates, *contexts, *visuals]
        draft = self.reasoner.draft(question, memories, candidates, contexts, visuals)
        trace.append("created evidence-tagged draft")

        static_issues = _static_review(draft, evidence, [item.id for item in candidates])
        model_review = self.reasoner.review(question, draft, evidence, [item.id for item in candidates])
        review = _merge_review(model_review, static_issues)
        trace.append(f"independent review score={review.score}, passed={review.passed}")

        if not review.passed:
            draft = self.reasoner.revise(question, draft, review, evidence)
            trace.append("revised draft once from reviewer feedback")
            static_issues = _static_review(draft, evidence, [item.id for item in candidates])
            model_review = self.reasoner.review(question, draft, evidence, [item.id for item in candidates])
            review = _merge_review(model_review, static_issues)
            trace.append(f"final review score={review.score}, passed={review.passed}")

        if not review.passed:
            raise RuntimeError("answer failed evidence review: " + "; ".join(review.issues))

        answer = self.reasoner.summarize(question, draft, review)
        trace.append("summarized reviewed draft")
        return PipelineResult(answer, draft, review, evidence, visual_plan, trace)


def _research_query(question: str, candidates: List[Evidence], memories: List[Evidence]) -> str:
    identities = " ".join(
        f"{item.metadata.get('artist', '')} {item.metadata.get('title', '')}"
        for item in candidates[:4]
    )
    preferences = " ".join(item.text for item in memories[:3])
    return f"{question} {identities} {preferences}".strip()


def _static_review(draft: str, evidence: List[Evidence], candidate_ids: List[str]) -> List[str]:
    allowed_tags = {item.citation for item in evidence}
    cited_tags = set(re.findall(r"\[((?:CAND|CTX|IMG|MEM):[^\]]+)\]", draft))
    issues = [f"invented or unavailable evidence tag [{tag}]" for tag in sorted(cited_tags - allowed_tags)]
    selected = set(re.findall(r"\[CAND:([^\]]+)\]", draft))
    illegal = selected - set(candidate_ids)
    issues.extend(f"candidate {item} is outside the retrieved candidate set" for item in sorted(illegal))
    if not cited_tags:
        issues.append("draft contains no machine-checkable evidence tags")
    allowed_urls = {item.source_url for item in evidence if item.source_url}
    cited_urls = set(re.findall(r"https?://[^\s)\]]+", draft))
    issues.extend(
        f"source URL is not in the retrieval ledger: {url}"
        for url in sorted(cited_urls - allowed_urls)
    )
    if allowed_urls and not cited_urls:
        issues.append("draft contains no source URL from the retrieval ledger")
    return issues


def _merge_review(review: Review, static_issues: List[str]) -> Review:
    if not static_issues:
        return review
    issues = list(dict.fromkeys([*static_issues, *review.issues]))
    changes = list(dict.fromkeys(["remove or correct invalid evidence tags", *review.required_changes]))
    return Review(False, min(review.score, 50), issues, changes)
