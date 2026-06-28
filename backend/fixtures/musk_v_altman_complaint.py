from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from backend.models import (
    AnalysisReport,
    ChatMessage,
    ComplaintWorkflowResponse,
    DocStore,
    ExtractedParty,
    ReportBlock,
    ReportCitation,
    ReportSection,
    ReportTable,
    WorkflowTask,
)


FIXTURE_ID = "musk-v-altman-openai-complaint-sf"
DOCUMENT_NAME = "musk-v-altman-openai-complaint-sf.pdf"

SUMMARY = (
    "Complaint by Elon Musk against Samuel Altman, Gregory Brockman, OpenAI entities, "
    "and related defendants concerning OpenAI's nonprofit founding purpose, later "
    "for-profit restructuring, Microsoft relationship, and asserted contract, "
    "promissory estoppel, fiduciary duty, unfair competition, and accounting claims."
)

PARTIES = [
    ExtractedParty("elon-musk", "Elon Musk", "plaintiff", "person", True),
    ExtractedParty("samuel-altman", "Samuel Altman", "defendant", "person"),
    ExtractedParty("gregory-brockman", "Gregory Brockman", "defendant", "person"),
    ExtractedParty("openai-inc", "OpenAI, Inc.", "defendant", "company"),
    ExtractedParty("openai-llc", "OpenAI, L.L.C.", "defendant", "company"),
    ExtractedParty("openai-lp", "OpenAI, L.P.", "defendant", "company"),
    ExtractedParty("openai-gp-llc", "OpenAI GP, L.L.C.", "defendant", "company"),
    ExtractedParty("openai-global-llc", "OpenAI Global, LLC", "defendant", "company"),
    ExtractedParty("openai-holdings-llc", "OpenAI Holdings, LLC", "defendant", "company"),
    ExtractedParty("openai-opco-llc", "OpenAI OpCo, LLC", "defendant", "company"),
    ExtractedParty("oai-corporation-llc", "OAI Corporation, LLC", "defendant", "company"),
    ExtractedParty("microsoft", "Microsoft", "third-party", "company"),
    ExtractedParty("does-1-100", "DOES 1 through 100", "defendant", "unknown"),
]

TASKS = [
    WorkflowTask("claims", "Claims", "Identify pleaded causes of action and claim elements.", "analysis", True, True),
    WorkflowTask("defenses", "Defenses", "Surface likely responsive defenses.", "analysis", False, False),
    WorkflowTask("timeline", "Timeline", "Extract a chronology of key events.", "facts", False, False),
    WorkflowTask("client_questions", "Client Questions", "Draft questions for client follow-up.", "work_product", False, False),
    WorkflowTask("dramatis_personae", "Dramatis Personae", "Summarize actors and relationships.", "facts", False, False),
    WorkflowTask("matters_like_this", "Matters Like This", "Find analogous authorities and matters.", "ground_truth", True, True),
    WorkflowTask("parties", "Parties", "Extract parties, roles, and entity types.", "facts", True, True),
    WorkflowTask("relief", "Relief", "Summarize requested relief.", "analysis", False, False),
    WorkflowTask("key_allegations", "Key Allegations", "Summarize central factual allegations.", "facts", True, True),
    WorkflowTask("contract_formation", "Contract Formation", "Analyze alleged agreement formation.", "analysis", True, True),
    WorkflowTask("fiduciary_duties", "Fiduciary Duties", "Analyze alleged fiduciary duty theory.", "analysis", True, True),
]

CITATION_QUOTES = {
    "caption-claims": "COMPLAINT FOR (1) BREACH OF 18 BROCKMAN, an individual, OPENAI, INC., a CONTRACT, (2) PROMISSORY",
    "openai-nonprofit": "OpenAI, Inc. is a registered non-profit organization incorporated under the laws of 10 Delaware on December 8, 2015.",
    "founding-agreement": "Founding Agreement Of OpenAI, Inc. 26  23.Mr. Altman purported to share Mr. Musk’s concerns over the threat posed by AGI.",
    "microsoft-license": "Microsoft, exclusively licensing to Microsoft its Generative Pre-10 Trained Transformer (GPT)-3 language model.",
    "breach-contract": "Breach of Contract  4 Against All Defendants 5  123.Plaintiff realleges and incorporates by reference only paragraphs of this Complaint",
    "promissory-estoppel": "Promissory Estoppel  2 Against All Defendants 3  128.Plaintiff realleges and incorporates by reference only paragraphs of this Complaint",
    "fiduciary-duty": "Breach of Fiduciary Duty  2 Against All Defendants 3  133.Plaintiff realleges and incorporates by reference only paragraphs of this Complaint",
}


def workflow_response(doc: DocStore) -> ComplaintWorkflowResponse:
    return ComplaintWorkflowResponse(
        doc_id=doc.doc_id,
        document_name=doc.document_name or DOCUMENT_NAME,
        full_text=doc.full_text,
        workflow_id="complaint",
        detected_doc_type="complaint",
        detected_summary=SUMMARY,
        fixture_available=doc.fixture_id == FIXTURE_ID,
        tasks=TASKS,
        parties=PARTIES,
    )


def limited_workflow_response(doc: DocStore) -> ComplaintWorkflowResponse:
    return ComplaintWorkflowResponse(
        doc_id=doc.doc_id,
        document_name=doc.document_name or "uploaded document",
        full_text=doc.full_text,
        workflow_id="complaint",
        detected_doc_type="complaint",
        detected_summary=(
            "Document was extracted and stored. Rich Vincent-style complaint analysis for "
            "arbitrary uploads requires LLM mode."
        ),
        fixture_available=False,
        tasks=[
            WorkflowTask(task.id, task.title, task.description, task.category, False, False)
            for task in TASKS
        ],
        parties=[],
    )


def report_for(doc: DocStore, task_ids: list[str], represented_party_ids: list[str]) -> AnalysisReport:
    citations = _resolve_citations(doc)
    selected = set(task_ids)
    sections: list[ReportSection] = []
    tables: list[ReportTable] = []

    if "claims" in selected:
        sections.append(
            ReportSection(
                id="all-claims",
                heading="(1) All Claims",
                blocks=[
                    ReportBlock(
                        type="ordered_list",
                        items=[
                            "Breach of contract against all defendants based on alleged commitments tied to OpenAI, Inc.'s founding purpose.",
                            "Promissory estoppel based on alleged inducements for Musk to contribute money, time, recruiting support, and strategic assistance.",
                            "Breach of fiduciary duty premised on use of contributions for the purposes for which they were allegedly made.",
                            "Unfair competition and accounting are pleaded as additional California-law remedies and accountability theories.",
                        ],
                        citation_ids=["caption-claims", "breach-contract", "promissory-estoppel", "fiduciary-duty"],
                    )
                ],
            )
        )
        tables.append(
            ReportTable(
                id="claims-table",
                title="(2) Claims Table",
                columns=["Claim", "Related citations", "Governing law", "Related facts", "Related parties / witnesses", "Source"],
                rows=[
                    {
                        "Claim": "Breach of Contract",
                        "Related citations": ["breach-contract", "founding-agreement"],
                        "Governing law": "California contract formation and breach principles.",
                        "Related facts": "OpenAI founding purpose, contributions, and alleged mission commitments.",
                        "Related parties / witnesses": "Musk, Altman, Brockman, OpenAI entities.",
                        "Source": "Complaint",
                    },
                    {
                        "Claim": "Breach of Fiduciary Duty",
                        "Related citations": ["fiduciary-duty", "openai-nonprofit"],
                        "Governing law": "California nonprofit and fiduciary-duty principles.",
                        "Related facts": "Alleged nonprofit purpose and use of contributed resources.",
                        "Related parties / witnesses": "OpenAI, Inc.; OpenAI affiliates; individual defendants.",
                        "Source": "Complaint",
                    },
                ],
            )
        )

    if "parties" in selected:
        sections.append(
            ReportSection(
                id="parties",
                heading="Parties",
                blocks=[
                    ReportBlock(
                        type="paragraph",
                        text="The complaint identifies Musk as plaintiff, Altman and Brockman as individual defendants, multiple OpenAI entities as organizational defendants, Microsoft as a central commercial actor, and DOES 1 through 100.",
                        citation_ids=["caption-claims", "openai-nonprofit", "microsoft-license"],
                    )
                ],
            )
        )

    if "key_allegations" in selected:
        sections.append(
            ReportSection(
                id="key-allegations",
                heading="Key Allegations",
                blocks=[
                    ReportBlock(
                        type="bulleted_list",
                        items=[
                            "OpenAI, Inc. was formed as a nonprofit with a public-facing mission around AGI.",
                            "The complaint attacks later commercialization and the Microsoft relationship as inconsistent with that mission.",
                        ],
                        citation_ids=["openai-nonprofit", "microsoft-license"],
                    )
                ],
            )
        )

    if "contract_formation" in selected:
        sections.append(
            ReportSection(
                id="contract-formation",
                heading="Contract Formation",
                blocks=[
                    ReportBlock(
                        type="paragraph",
                        text="The contract theory turns on whether the founding materials, communications, and course of contribution plausibly formed enforceable commitments rather than aspirational mission statements.",
                        citation_ids=["founding-agreement", "breach-contract"],
                    )
                ],
            )
        )

    if "fiduciary_duties" in selected:
        sections.append(
            ReportSection(
                id="fiduciary-duties",
                heading="Fiduciary Duties",
                blocks=[
                    ReportBlock(
                        type="paragraph",
                        text="The fiduciary-duty theory depends on tying defendants' control of contributed nonprofit resources to duties owed to Musk or to the stated charitable purpose.",
                        citation_ids=["fiduciary-duty", "openai-nonprofit"],
                    )
                ],
            )
        )

    if "matters_like_this" in selected:
        sections.append(
            ReportSection(
                id="matters-like-this",
                heading="Matters Like This",
                blocks=[
                    ReportBlock(
                        type="callout",
                        text="The closest analogs are not generic AI disputes, but nonprofit governance, charitable-purpose, fiduciary-duty, and mission-to-commercialization disputes.",
                        citation_ids=["openai-nonprofit", "microsoft-license"],
                    )
                ],
            )
        )

    if not sections:
        sections.append(
            ReportSection(
                id="limited-selection",
                heading="Selected Tasks",
                blocks=[
                    ReportBlock(
                        type="callout",
                        text="The selected tasks are not fixture-backed in demo mode. Switch to LLM mode for arbitrary task execution.",
                    )
                ],
            )
        )

    return AnalysisReport(
        id=f"report-{doc.doc_id}",
        title="Musk v. Altman / OpenAI Complaint Analysis",
        subtitle="Fixture-backed legal work product grounded to the uploaded complaint.",
        sections=sections,
        tables=tables,
        citations=list(citations.values()),
        primary_task_ids=task_ids,
        represented_party_ids=represented_party_ids,
    )


def citation_for(doc: DocStore, citation_id: str) -> ReportCitation | None:
    return _resolve_citations(doc).get(citation_id)


def follow_up_answer(doc: DocStore, message: str) -> ChatMessage:
    normalized = message.strip().lower()
    citations = _resolve_citations(doc)
    content: str
    citation_ids: list[str]

    if "strongest" in normalized and "claim" in normalized:
        content = (
            "The strongest fixture-backed theories are breach of contract and breach of fiduciary duty. "
            "The contract theory has a direct pleaded claim and founding-agreement narrative; the fiduciary-duty "
            "theory turns on nonprofit-purpose allegations and control over contributed resources."
        )
        citation_ids = ["founding-agreement", "breach-contract", "fiduciary-duty", "openai-nonprofit"]
    elif "defense" in normalized or "altman" in normalized:
        content = (
            "In fixture mode, likely Altman defenses include arguing that the founding statements were aspirational "
            "rather than enforceable promises, that Musk lacks a fiduciary-duty theory personal to him, and that later "
            "entity restructuring does not itself establish breach."
        )
        citation_ids = ["founding-agreement", "breach-contract", "fiduciary-duty"]
    elif "cases" in normalized or "matters" in normalized:
        content = (
            "The closest analogs are nonprofit governance and fiduciary-duty authorities, plus matter-style records "
            "involving mission, control, and commercialization disputes."
        )
        citation_ids = ["openai-nonprofit", "microsoft-license"]
    elif "fiduciary" in normalized:
        content = (
            "The complaint pleads breach of fiduciary duty as a distinct count and links the theory to OpenAI's "
            "nonprofit purpose and defendants' alleged control over resources contributed for that purpose."
        )
        citation_ids = ["fiduciary-duty", "openai-nonprofit"]
    else:
        content = (
            "Fixture mode can answer only the bundled demo follow-up questions. This question needs provider-backed "
            "LLM mode before the app can answer it from the uploaded complaint without fabricating support."
        )
        citation_ids = []

    selected_citations = [citations[citation_id] for citation_id in citation_ids if citation_id in citations]
    return ChatMessage(
        id=f"msg-{uuid4().hex}",
        role="assistant",
        content=content,
        report=None,
        citations=selected_citations,
        created_at=datetime.now(UTC).isoformat(),
    )


def authorities() -> list[dict]:
    return [
        {
            "authority_id": "cal-corp-5231",
            "title": "California Corporations Code Section 5231",
            "source_type": "statute",
            "summary": "Defines duties of directors of nonprofit public benefit corporations.",
            "relevance": 91,
            "quote": "A director shall perform the duties of a director...in good faith",
            "verified": True,
            "url": "https://law.justia.com/codes/california/code-corp/title-1/division-2/part-2/chapter-2/article-3/section-5231/",
            "metadata": {"jurisdiction": "California", "treatment": "Relevant"},
        },
        {
            "authority_id": "bancroft-whitney-v-glen",
            "title": "Bancroft-Whitney Co. v. Glen",
            "source_type": "case",
            "summary": "California authority on fiduciaries using positions of trust for private advantage.",
            "relevance": 84,
            "quote": "Corporate officers and directors are not permitted to use their position of trust and confidence to further their private interests",
            "verified": True,
            "url": "https://law.justia.com/cases/california/supreme-court/2d/64/327.html",
            "metadata": {"court": "California Supreme Court", "treatment": "Distinguished"},
        },
        {
            "authority_id": "openai-removal-litigation",
            "title": "OpenAI governance dispute records",
            "source_type": "similar_case",
            "summary": "Matter-style comparison for disputes involving OpenAI governance, nonprofit purpose, and control.",
            "relevance": 78,
            "quote": "Governance and mission-control disputes often turn on entity documents, board authority, and fiduciary framing.",
            "verified": False,
            "url": "https://www.courtlistener.com/",
            "metadata": {"jurisdiction": "California", "record_type": "similar matter"},
        },
    ]


def _resolve_citations(doc: DocStore) -> dict[str, ReportCitation]:
    resolved: dict[str, ReportCitation] = {}
    for citation_id, quote in CITATION_QUOTES.items():
        start = doc.full_text.find(quote)
        end = start + len(quote) if start >= 0 else None
        page = _page_for_offset(doc, start) if start >= 0 else 1
        resolved[citation_id] = ReportCitation(
            id=citation_id,
            label=f"p. {page}",
            source_doc_name=doc.document_name or DOCUMENT_NAME,
            page=page,
            quote=quote,
            abs_start=start if start >= 0 else None,
            abs_end=end,
        )
    return resolved


def _page_for_offset(doc: DocStore, offset: int) -> int:
    for span in doc.page_spans:
        if span.start_offset <= offset < span.end_offset:
            return span.page_number
    return 1


def to_dict(value):
    return asdict(value)
