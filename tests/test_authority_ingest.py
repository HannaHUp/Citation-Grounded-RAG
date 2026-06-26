from pathlib import Path

from backend.services.authority_ingest import (
    AuthorityIngestor,
    load_corpus,
    seeded_authority_records,
)


def test_seeded_authority_records_cover_required_tabs_and_verify_quotes():
    records = seeded_authority_records()

    source_types = {record.source_type for record in records}
    assert {"case", "statute", "secondary"} <= source_types

    for record in records:
        assert record.authority_id
        assert record.title
        assert record.url.startswith("https://")
        assert record.quote_seed
        assert record.quote_seed in record.source_text


def test_ingestor_writes_checkpoint_and_skips_duplicates_on_resume(tmp_path: Path):
    calls = []

    def fake_fetch(url: str):
        calls.append(url)
        return {
            "next": "https://www.courtlistener.com/api/rest/v4/search/?page=2",
            "results": [
                {
                    "cluster_id": 123,
                    "caseName": "Example v. Demo",
                    "absolute_url": "/opinion/123/example-v-demo/",
                    "snippet": "A court discussed monopoly power and competition in detail.",
                    "court": "scotus",
                    "dateFiled": "2020-01-01",
                }
            ],
        }

    ingestor = AuthorityIngestor(tmp_path, fetch_json=fake_fetch)

    first = ingestor.ingest_courtlistener(limit=1)
    second = ingestor.ingest_courtlistener(limit=1, resume=True)

    records = load_corpus(tmp_path / "corpus.jsonl")
    assert first.records_written == 1
    assert second.records_written == 0
    assert len(records) == 1
    assert records[0].authority_id == "courtlistener-123"
    assert records[0].quote_seed in records[0].source_text

    state = ingestor.load_state()
    assert state["courtlistener"]["records_written"] == 1
    assert state["courtlistener"]["next_url"].endswith("page=2")
