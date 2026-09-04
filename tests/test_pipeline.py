import json
import unittest
from pathlib import Path

from polign_curator.embeddings import HashingEmbedder
from polign_curator.pipeline import CuratorPipeline, _static_review
from polign_curator.store import PolignRAGStore, VISUAL

from fakes import FakeClient, FakeReasoner


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()
        self.store = PolignRAGStore(self.client, HashingEmbedder(64))
        self.store.seed(
            json.loads((ROOT / "data/candidates.json").read_text()),
            json.loads((ROOT / "data/context.json").read_text()),
        )
        self.store.remember("curator", "preferred_mood", "contemplative")

    def test_full_pipeline_inspects_then_reuses_visual_cache(self):
        reasoner = FakeReasoner()
        pipeline = CuratorPipeline(self.store, reasoner)
        question = "Choose a work whose visible color and composition feel contemplative."

        first = pipeline.run("curator", "river-and-landscape-2026", question)
        second = pipeline.run("curator", "river-and-landscape-2026", question)

        self.assertTrue(first.review.passed)
        self.assertEqual(1, reasoner.inspect_calls)
        self.assertEqual(1, len(self.client.collections[VISUAL]))
        self.assertTrue(any("reused visual_cache" in step for step in second.trace))
        self.assertIn("In short", second.answer)

    def test_failed_review_gets_one_revision_and_second_review(self):
        reasoner = FakeReasoner(fail_first_review=True)
        result = CuratorPipeline(self.store, reasoner).run(
            "curator", "river-and-landscape-2026", "Compare visible composition."
        )
        self.assertEqual(2, reasoner.review_calls)
        self.assertTrue(result.review.passed)
        self.assertTrue(any("revised draft once" in step for step in result.trace))

    def test_static_review_rejects_unknown_evidence(self):
        issues = _static_review("A claim [CAND:not-allowed].", [], ["nga-74796"])
        self.assertTrue(any("invented" in issue for issue in issues))
        self.assertTrue(any("outside" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()

