from dataclasses import dataclass, asdict, field

@dataclass
class Chunk:
    chunk_id: str
    text: str
    start_offset: int
    end_offset: int   # exclusive: full_text[start_offset:end_offset] == text

@dataclass
class PageSpan:
    page_number: int
    start_offset: int
    end_offset: int   # exclusive: full_text[start_offset:end_offset] belongs to page_number

@dataclass
class ExtractedDocument:
    full_text: str
    page_spans: list[PageSpan]

@dataclass
class DocStore:
    doc_id: str
    full_text: str    # canonical source of truth; never mutated after creation
    chunks: list[Chunk]
    page_spans: list[PageSpan] = field(default_factory=list)
    document_name: str | None = None
    fixture_id: str | None = None
    detected_doc_type: str | None = None

@dataclass
class RawFinding:
    finding: str
    severity: str     # "high" | "medium" | "low"
    source_chunk_id: str
    quote: str

@dataclass
class VerifiedFinding:
    finding: str
    severity: str
    source_chunk_id: str
    quote: str
    verified: bool
    abs_start: int | None   # None when verified=False
    abs_end: int | None     # None when verified=False
    source_page: int | None = None

@dataclass
class AnalysisProfile:
    profile_id: str
    display_name: str
    system_prompt: str
    tool_description: str
    output_schema: dict

@dataclass
class LegalAuthority:
    authority_id: str
    title: str
    source_type: str  # "case" | "statute" | "secondary" | "similar_case"
    summary: str
    relevance: int
    quote: str
    url: str
    source_text: str

@dataclass
class AuthorityRecord:
    authority_id: str
    title: str
    source_type: str  # "case" | "statute" | "secondary"
    summary_seed: str
    quote_seed: str
    url: str
    source_text: str
    metadata: dict

@dataclass
class ExtractedParty:
    id: str
    name: str
    role: str
    type: str
    selected_by_default: bool = False

@dataclass
class WorkflowTask:
    id: str
    title: str
    description: str
    category: str
    enabled: bool
    fixture_supported: bool

@dataclass
class ComplaintWorkflowResponse:
    doc_id: str
    document_name: str
    full_text: str
    workflow_id: str
    detected_doc_type: str
    detected_summary: str
    fixture_available: bool
    tasks: list[WorkflowTask]
    parties: list[ExtractedParty]

@dataclass
class ReportCitation:
    id: str
    label: str
    source_doc_name: str
    page: int
    quote: str
    abs_start: int | None
    abs_end: int | None

@dataclass
class ReportBlock:
    type: str
    text: str | None = None
    items: list[str] = field(default_factory=list)
    citation_ids: list[str] = field(default_factory=list)
    table_id: str | None = None

@dataclass
class ReportSection:
    id: str
    heading: str
    blocks: list[ReportBlock]

@dataclass
class ReportTable:
    id: str
    title: str
    columns: list[str]
    rows: list[dict]

@dataclass
class AnalysisReport:
    id: str
    title: str
    subtitle: str
    sections: list[ReportSection]
    tables: list[ReportTable]
    citations: list[ReportCitation]
    primary_task_ids: list[str]
    represented_party_ids: list[str]

@dataclass
class ChatMessage:
    id: str
    role: str
    content: str
    report: AnalysisReport | None
    citations: list[ReportCitation]
    created_at: str

@dataclass
class ChatThread:
    thread_id: str
    doc_id: str
    selected_task_ids: list[str]
    represented_party_ids: list[str]
    messages: list[ChatMessage]

FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "finding":         {"type": "string"},
                    "severity":        {"type": "string", "enum": ["high", "medium", "low"]},
                    "source_chunk_id": {"type": "string"},
                    "quote": {
                        "type": "string",
                        "description": (
                            "Verbatim copy from source. "
                            "Do NOT normalize quotes, em-dashes, section symbols (§), "
                            "or whitespace. Return the exact bytes."
                        ),
                    },
                },
                "required": ["finding", "severity", "source_chunk_id", "quote"],
            },
        }
    },
    "required": ["findings"],
}
