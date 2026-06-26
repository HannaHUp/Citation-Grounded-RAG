from dataclasses import dataclass, asdict

@dataclass
class Chunk:
    chunk_id: str
    text: str
    start_offset: int
    end_offset: int   # exclusive: full_text[start_offset:end_offset] == text

@dataclass
class DocStore:
    doc_id: str
    full_text: str    # canonical source of truth; never mutated after creation
    chunks: list[Chunk]

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

@dataclass
class AnalysisProfile:
    profile_id: str
    display_name: str
    system_prompt: str
    tool_description: str
    output_schema: dict

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
