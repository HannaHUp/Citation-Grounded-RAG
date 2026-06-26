import json
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from backend.models import AuthorityRecord

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "authorities"
CORPUS_PATH = DATA_DIR / "corpus.jsonl"
STATE_PATH = DATA_DIR / "ingest_state.json"
COURTLISTENER_SEARCH_URL = (
    "https://www.courtlistener.com/api/rest/v4/search/?q=antitrust%20competition"
)


@dataclass
class IngestResult:
    records_written: int
    next_url: str | None


def seeded_authority_records() -> list[AuthorityRecord]:
    return [
        AuthorityRecord(
            authority_id="15-usc-18",
            title="Clayton Act Section 7",
            source_type="statute",
            summary_seed="Bars acquisitions whose effect may substantially lessen competition.",
            quote_seed="the effect of such acquisition may be substantially to lessen competition, or to tend to create a monopoly",
            url="https://www.law.cornell.edu/uscode/text/15/18",
            source_text=(
                "No person engaged in commerce or in any activity affecting commerce "
                "shall acquire, directly or indirectly, the whole or any part of the "
                "stock or other share capital and no person subject to the jurisdiction "
                "of the Federal Trade Commission shall acquire the whole or any part "
                "of the assets of another person engaged also in commerce or in any "
                "activity affecting commerce, where in any line of commerce or in any "
                "activity affecting commerce in any section of the country, the effect "
                "of such acquisition may be substantially to lessen competition, or to "
                "tend to create a monopoly."
            ),
            metadata={"source": "cornell_law"},
        ),
        AuthorityRecord(
            authority_id="brown-shoe",
            title="Brown Shoe Co. v. United States",
            source_type="case",
            summary_seed=(
                "Merger analysis concerns probabilities and practical competitive effects."
            ),
            quote_seed=(
                "Congress used the words 'may be substantially to lessen competition' "
                "to indicate that its concern was with probabilities, not certainties"
            ),
            url="https://supreme.justia.com/cases/federal/us/370/294/",
            source_text=(
                "Congress used the words 'may be substantially to lessen competition' "
                "to indicate that its concern was with probabilities, not certainties. "
                "Statutes existed to arrest anticompetitive tendencies in their incipiency."
            ),
            metadata={"source": "justia"},
        ),
        AuthorityRecord(
            authority_id="ftc-doj-merger-guidelines",
            title="FTC and DOJ Merger Guidelines",
            source_type="secondary",
            summary_seed=(
                "Frames merger review around whether a transaction may substantially lessen competition."
            ),
            quote_seed="mergers should not substantially lessen competition or tend to create a monopoly",
            url="https://www.justice.gov/atr/merger-guidelines",
            source_text=(
                "The agencies identify mergers that may violate the antitrust laws. "
                "The guidelines explain that mergers should not substantially lessen "
                "competition or tend to create a monopoly, and that agencies examine "
                "market structure, competitive effects, entry, and rebuttal evidence."
            ),
            metadata={"source": "doj"},
        ),
    ]


def load_corpus(path: Path = CORPUS_PATH) -> list[AuthorityRecord]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(AuthorityRecord(**json.loads(line)))
    return records


def write_corpus(records: list[AuthorityRecord], path: Path = CORPUS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(asdict(record), ensure_ascii=False) for record in records)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


class AuthorityIngestor:
    def __init__(
        self,
        data_dir: Path = DATA_DIR,
        fetch_json: Callable[[str], dict] | None = None,
    ) -> None:
        self.data_dir = data_dir
        self.corpus_path = data_dir / "corpus.jsonl"
        self.state_path = data_dir / "ingest_state.json"
        self.fetch_json = fetch_json or _fetch_json

    def load_state(self) -> dict:
        if not self.state_path.exists():
            return {"courtlistener": {"next_url": COURTLISTENER_SEARCH_URL, "records_written": 0}}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def write_seed_records(self) -> int:
        existing = {record.authority_id: record for record in load_corpus(self.corpus_path)}
        before = len(existing)
        for record in seeded_authority_records():
            existing.setdefault(record.authority_id, record)
        write_corpus(list(existing.values()), self.corpus_path)
        return len(existing) - before

    def ingest_courtlistener(self, limit: int = 25, resume: bool = False) -> IngestResult:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        state = self.load_state()
        next_url = state.get("courtlistener", {}).get("next_url") if resume else COURTLISTENER_SEARCH_URL
        corpus = {record.authority_id: record for record in load_corpus(self.corpus_path)}
        written = 0

        while next_url and written < limit:
            payload = self.fetch_json(next_url)
            for result in payload.get("results", []):
                record = _record_from_courtlistener(result)
                if record.authority_id in corpus:
                    continue
                corpus[record.authority_id] = record
                written += 1
                if written >= limit:
                    break
            next_url = payload.get("next")
            break

        write_corpus(list(corpus.values()), self.corpus_path)
        total_written = state.get("courtlistener", {}).get("records_written", 0) + written
        self.state_path.write_text(
            json.dumps(
                {
                    "courtlistener": {
                        "next_url": next_url,
                        "completed": next_url is None,
                        "records_written": total_written,
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return IngestResult(records_written=written, next_url=next_url)


def _record_from_courtlistener(result: dict) -> AuthorityRecord:
    cluster_id = result.get("cluster_id") or result.get("id")
    title = result.get("caseName") or result.get("caseNameFull") or f"CourtListener authority {cluster_id}"
    source_text = _strip_tags(result.get("snippet") or result.get("plain_text") or title)
    quote = source_text[:240].strip()
    url = result.get("absolute_url") or result.get("download_url") or ""
    if url.startswith("/"):
        url = f"https://www.courtlistener.com{url}"
    return AuthorityRecord(
        authority_id=f"courtlistener-{cluster_id}",
        title=title,
        source_type="case",
        summary_seed=f"CourtListener case discussing {title}.",
        quote_seed=quote,
        url=url or "https://www.courtlistener.com/",
        source_text=source_text,
        metadata={
            "source": "courtlistener",
            "court": result.get("court"),
            "date_filed": result.get("dateFiled"),
        },
    )


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "citation-grounded-rag-demo"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _strip_tags(text: str) -> str:
    return " ".join(text.replace("<mark>", "").replace("</mark>", "").split())
