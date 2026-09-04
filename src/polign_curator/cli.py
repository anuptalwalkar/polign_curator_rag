from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional, Sequence

from .embeddings import HashingEmbedder, OpenAIEmbedder
from .llm import OpenAIReasoner
from .pipeline import CuratorPipeline
from .store import PolignRAGStore, load_seed_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reviewed multimodal RAG with polign_db")
    parser.add_argument("--polign-url", default=os.getenv("POLIGN_URL", "http://127.0.0.1:23000"))
    parser.add_argument("--embedding-provider", choices=("hashing", "openai"), default="hashing")
    parser.add_argument("--user", default="demo-curator")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("seed", help="idempotently seed candidate and context collections")

    remember = sub.add_parser("remember", help="store a durable curator memory")
    remember.add_argument("key")
    remember.add_argument("value")
    remember.add_argument("--kind", choices=("preference", "decision", "constraint"), default="preference")

    memories = sub.add_parser("memories", help="list durable memories")
    memories.add_argument("--history", action="store_true")

    ask = sub.add_parser("ask", help="run the full reviewed RAG pipeline")
    ask.add_argument("question")
    ask.add_argument("--set", dest="candidate_set", default="river-and-landscape-2026")
    ask.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5.4"))
    ask.add_argument("--reviewer-model", default=os.getenv("OPENAI_REVIEWER_MODEL", ""))
    ask.add_argument("--json", action="store_true")

    sub.add_parser("collections", help="show collection record counts")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    from polign import Client

    embedder = OpenAIEmbedder() if args.embedding_provider == "openai" else HashingEmbedder()
    store = PolignRAGStore(Client(args.polign_url), embedder)

    if args.command == "seed":
        data_dir = Path(__file__).resolve().parents[2] / "data"
        if not data_dir.exists():
            data_dir = Path.cwd() / "data"
        candidates, contexts = load_seed_data(str(data_dir))
        print(json.dumps(store.seed(candidates, contexts), indent=2))
        return 0

    if args.command == "remember":
        print(json.dumps(store.remember(args.user, args.key, args.value, args.kind).metadata, indent=2))
        return 0

    if args.command == "memories":
        print(json.dumps([item.metadata for item in store.list_memories(args.user, args.history)], indent=2))
        return 0

    if args.command == "collections":
        print(json.dumps(store.collection_counts(), indent=2))
        return 0

    pipeline = CuratorPipeline(store, OpenAIReasoner(args.model, args.reviewer_model))
    result = pipeline.run(args.user, args.candidate_set, args.question)
    if args.json:
        print(json.dumps({
            "answer": result.answer,
            "review": result.review.__dict__,
            "visual_plan": result.visual_plan.__dict__,
            "trace": result.trace,
            "evidence": [item.__dict__ for item in result.evidence],
        }, indent=2))
    else:
        for line in result.trace:
            print(f"  -> {line}")
        print("\n" + result.answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
