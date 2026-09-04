from __future__ import annotations

import hashlib
import math
import re
from typing import List, Protocol, Sequence


class Embedder(Protocol):
    dimension: int

    def embed(self, text: str) -> List[float]: ...

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]: ...


class HashingEmbedder:
    """Small deterministic embedder for a zero-download local demo.

    It uses signed feature hashing over words and character trigrams. This is
    intentionally not a production semantic model, but it makes seed/search
    repeatable and keeps the Polign path runnable without another service.
    """

    def __init__(self, dimension: int = 256):
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        words = re.findall(r"[a-z0-9]+", text.lower())
        features = list(words)
        features.extend(
            f"#{word[i:i + 3]}" for word in words for i in range(max(0, len(word) - 2))
        )
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            slot = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[slot] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        return [self.embed(text) for text in texts]


class OpenAIEmbedder:
    def __init__(self, model: str = "text-embedding-3-small", dimension: int = 256):
        from openai import OpenAI

        self.client = OpenAI()
        self.model = model
        self.dimension = dimension

    def embed(self, text: str) -> List[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            input=list(texts),
            dimensions=self.dimension,
        )
        return [list(item.embedding) for item in response.data]

