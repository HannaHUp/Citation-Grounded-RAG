import argparse

from backend.services.authority_ingest import AuthorityIngestor


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest legal authorities for local RAG")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    ingestor = AuthorityIngestor()
    seeded = ingestor.write_seed_records()
    result = ingestor.ingest_courtlistener(limit=args.limit, resume=args.resume)
    print(
        f"seeded={seeded} courtlistener_written={result.records_written} "
        f"next_url={result.next_url or ''}"
    )


if __name__ == "__main__":
    main()
