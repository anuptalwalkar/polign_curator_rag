import math
import unittest

from polign_curator.embeddings import HashingEmbedder


class EmbeddingTests(unittest.TestCase):
    def test_hash_embedding_is_deterministic_and_normalized(self):
        embedder = HashingEmbedder(64)
        first = embedder.embed("green reflected garden")
        second = embedder.embed("green reflected garden")
        self.assertEqual(first, second)
        self.assertAlmostEqual(1.0, math.sqrt(sum(value * value for value in first)))


if __name__ == "__main__":
    unittest.main()

