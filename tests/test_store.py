import json
import unittest
from pathlib import Path

from polign_curator.embeddings import HashingEmbedder
from polign_curator.store import CANDIDATES, MEMORY, PolignRAGStore

from fakes import FakeClient


ROOT = Path(__file__).resolve().parents[1]


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()
        self.store = PolignRAGStore(self.client, HashingEmbedder(64))
        candidates = json.loads((ROOT / "data/candidates.json").read_text())
        contexts = json.loads((ROOT / "data/context.json").read_text())
        self.store.seed(candidates, contexts)

    def test_candidate_search_cannot_leak_control_set(self):
        rows = self.store.candidate_set("river-and-landscape-2026", "Monet figures", limit=20)
        self.assertEqual(6, len(rows))
        self.assertNotIn("nga-93067-control", {row.id for row in rows})
        self.assertTrue(all(row.metadata["candidate_set"] == "river-and-landscape-2026" for row in rows))

    def test_memory_supersession_preserves_history(self):
        first = self.store.remember("u1", "preferred_mood", "energetic")
        second = self.store.remember("u1", "preferred_mood", "contemplative")

        active = self.store.list_memories("u1")
        history = self.store.list_memories("u1", include_history=True)
        self.assertEqual([second.id], [item.id for item in active])
        self.assertEqual(2, len(history))
        old = self.client.collections[MEMORY][first.id]
        self.assertEqual("superseded", old.metadata["status"])
        self.assertEqual(second.id, old.metadata["superseded_by"])

    def test_seed_is_idempotent(self):
        before = len(self.client.collections[CANDIDATES])
        candidates = json.loads((ROOT / "data/candidates.json").read_text())
        contexts = json.loads((ROOT / "data/context.json").read_text())
        self.store.seed(candidates, contexts)
        self.assertEqual(before, len(self.client.collections[CANDIDATES]))


if __name__ == "__main__":
    unittest.main()

