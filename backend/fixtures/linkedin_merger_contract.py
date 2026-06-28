from dataclasses import asdict
from datetime import UTC, datetime
from uuid import uuid4

from backend.models import (
    AnalysisReport,
    ChatMessage,
    ComplaintWorkflowResponse,
    DocStore,
    ExtractedParty,
    PageSpan,
    ReportBlock,
    ReportCitation,
    ReportSection,
    ReportTable,
    WorkflowTask,
)


FIXTURE_ID = "linkedin-merger-agreement"
DOCUMENT_NAME = "LinkedIn Merger Agreement.docx"

DEMO_TEXT = """DEMO FIXTURE CONTENT - LinkedIn Merger Agreement.docx

AGREEMENT AND PLAN OF MERGER among Microsoft Corporation, Liberty Merger Sub Inc., and LinkedIn Corporation.

Section 1.01 The Merger. At the Effective Time, Merger Sub shall be merged with and into LinkedIn, with LinkedIn surviving as a wholly owned subsidiary of Microsoft.

Section 4.03 Board Approval. The LinkedIn board has determined that the merger is fair to and in the best interests of LinkedIn and its stockholders and has approved this Agreement.

Section 5.01 Conduct of Business. LinkedIn shall use commercially reasonable efforts to conduct its business in the ordinary course and preserve relationships with customers, employees, and suppliers.

Section 6.01 Regulatory Approvals. Microsoft and LinkedIn shall use reasonable best efforts to obtain required antitrust approvals and make filings under the HSR Act and other competition laws.

Section 6.02 No Divestiture Obligation. Microsoft shall not be required to divest assets or accept remedies that would materially impair the combined company.

Section 7.01 Conditions. Closing is conditioned on stockholder approval, regulatory clearance, and the absence of a law prohibiting consummation of the merger.

Section 8.01 Termination Fee. LinkedIn may be required to pay a termination fee if the Agreement is terminated after a superior proposal or board recommendation change.
"""

SUMMARY = (
    "Demo fixture content for a LinkedIn merger agreement. The fixture supports transactional "
    "tasks around risk mitigation, antitrust approvals, fiduciary duties, obligations, and summary."
)

PARTIES = [
    ExtractedParty("microsoft", "Microsoft Corporation", "buyer", "company", True),
    ExtractedParty("linkedin", "LinkedIn Corporation", "target", "company"),
    ExtractedParty("merger-sub", "Liberty Merger Sub Inc.", "merger subsidiary", "company"),
    ExtractedParty("linkedin-board", "LinkedIn Board of Directors", "fiduciary actor", "organization"),
]

TASKS = [
    WorkflowTask("definitions", "Definitions", "Extract defined terms and cross-reference usage.", "drafting", True, False),
    WorkflowTask("overlaps", "Overlaps", "Identify overlapping covenants, closing conditions, and remedies.", "drafting", True, False),
    WorkflowTask("language", "Language", "Review drafting clarity and negotiation language.", "drafting", True, False),
    WorkflowTask("risk_mitigation", "Risk Mitigation", "Surface deal risks and mitigation options.", "analysis", True, True),
    WorkflowTask("obligations", "Obligations", "Extract party obligations and operating covenants.", "analysis", True, True),
    WorkflowTask("strategy", "Strategy", "Develop negotiation and closing strategy.", "work_product", True, False),
    WorkflowTask("summarize", "Summarize", "Summarize the transaction and key provisions.", "analysis", True, True),
    WorkflowTask("timeline", "Timeline", "Build a closing and termination chronology.", "facts", True, False),
    WorkflowTask("compliance_checklist", "Compliance Checklist", "Create a closing and compliance checklist.", "work_product", True, False),
    WorkflowTask("antitrust_implications", "Antitrust Implications", "Analyze competition-law approval risk.", "ground_truth", True, True),
    WorkflowTask("fiduciary_duties", "Fiduciary Duties", "Analyze board duties in the transaction process.", "ground_truth", True, True),
]

CITATION_QUOTES = {
    "merger-structure": "Merger Sub shall be merged with and into LinkedIn, with LinkedIn surviving as a wholly owned subsidiary of Microsoft.",
    "board-approval": "The LinkedIn board has determined that the merger is fair to and in the best interests of LinkedIn and its stockholders",
    "ordinary-course": "LinkedIn shall use commercially reasonable efforts to conduct its business in the ordinary course",
    "antitrust-approvals": "obtain required antitrust approvals and make filings under the HSR Act and other competition laws.",
    "no-divestiture": "Microsoft shall not be required to divest assets or accept remedies that would materially impair the combined company.",
    "termination-fee": "LinkedIn may be required to pay a termination fee if the Agreement is terminated after a superior proposal",
}


def workflow_response(doc: DocStore) -> ComplaintWorkflowResponse:
    return ComplaintWorkflowResponse(
        doc_id=doc.doc_id,
        document_name=doc.document_name or DOCUMENT_NAME,
        full_text=doc.full_text,
        workflow_id="contract",
        detected_doc_type="contract",
        detected_summary=SUMMARY,
        fixture_available=doc.fixture_id == FIXTURE_ID,
        tasks=TASKS,
        parties=PARTIES,
    )


def limited_workflow_response(doc: DocStore) -> ComplaintWorkflowResponse:
    return ComplaintWorkflowResponse(
        doc_id=doc.doc_id,
        document_name=doc.document_name or "uploaded contract",
        full_text=doc.full_text,
        workflow_id="contract",
        detected_doc_type="contract",
        detected_summary=(
            "Contract document was extracted and stored. Rich Vincent-style contract analysis for "
            "arbitrary uploads requires LLM mode."
        ),
        fixture_available=False,
        tasks=[WorkflowTask(task.id, task.title, task.description, task.category, False, False) for task in TASKS],
        parties=[],
    )


def demo_page_spans() -> list[PageSpan]:
    return [PageSpan(page_number=1, start_offset=0, end_offset=len(DEMO_TEXT))]


def report_for(doc: DocStore, task_ids: list[str], represented_party_ids: list[str]) -> AnalysisReport:
    citations = _resolve_citations(doc)
    selected = set(task_ids)
    sections: list[ReportSection] = []
    tables: list[ReportTable] = []

    if "summarize" in selected:
        sections.append(
            ReportSection(
                id="summary",
                heading="Summarize",
                blocks=[
                    ReportBlock(
                        type="paragraph",
                        text="The agreement structures Microsoft as buyer, LinkedIn as target, and Merger Sub as the acquisition vehicle, with LinkedIn surviving after the merger.",
                        citation_ids=["merger-structure"],
                    )
                ],
            )
        )

    if "risk_mitigation" in selected:
        sections.append(
            ReportSection(
                id="risk-mitigation",
                heading="Risk Mitigation",
                blocks=[
                    ReportBlock(
                        type="bulleted_list",
                        items=[
                            "Regulatory risk is concentrated in antitrust clearance and any remedy package Microsoft is unwilling to accept.",
                            "Operating covenant risk should be tracked against ordinary-course obligations while approvals are pending.",
                            "Deal certainty risk should be monitored around termination-fee triggers and recommendation-change events.",
                        ],
                        citation_ids=["antitrust-approvals", "no-divestiture", "ordinary-course", "termination-fee"],
                    )
                ],
            )
        )

    if "antitrust_implications" in selected:
        sections.append(
            ReportSection(
                id="antitrust-implications",
                heading="Antitrust Implications",
                blocks=[
                    ReportBlock(
                        type="paragraph",
                        text="The contract expressly anticipates HSR and other competition-law filings, but also preserves a no-divestiture position that could matter if agencies seek structural remedies.",
                        citation_ids=["antitrust-approvals", "no-divestiture"],
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
                        text="The board approval recital and superior-proposal termination fee provision are the core fixture-backed facts for fiduciary-duty review.",
                        citation_ids=["board-approval", "termination-fee"],
                    )
                ],
            )
        )

    if "obligations" in selected:
        sections.append(
            ReportSection(
                id="obligations",
                heading="Obligations",
                blocks=[
                    ReportBlock(
                        type="ordered_list",
                        items=[
                            "Microsoft and LinkedIn must pursue regulatory approvals.",
                            "LinkedIn must operate in the ordinary course pending closing.",
                            "Closing depends on stockholder approval, regulatory clearance, and no legal restraint.",
                        ],
                        citation_ids=["antitrust-approvals", "ordinary-course"],
                    )
                ],
            )
        )

    tables.append(
        ReportTable(
            id="contract-risk-table",
            title="Fixture-Backed Contract Issues",
            columns=["Issue", "Contract source", "Work product"],
            rows=[
                {"Issue": "Antitrust approvals", "Contract source": ["antitrust-approvals", "no-divestiture"], "Work product": "Escalate remedy-risk scenarios."},
                {"Issue": "Fiduciary process", "Contract source": ["board-approval", "termination-fee"], "Work product": "Review board record and superior-proposal mechanics."},
                {"Issue": "Interim operations", "Contract source": ["ordinary-course"], "Work product": "Track covenant compliance through closing."},
            ],
        )
    )

    if not sections:
        sections.append(
            ReportSection(
                id="limited-selection",
                heading="Selected Tasks",
                blocks=[ReportBlock(type="callout", text="The selected contract tasks are not fixture-backed in demo mode.")],
            )
        )

    return AnalysisReport(
        id=f"report-{doc.doc_id}",
        title="LinkedIn Merger Agreement Contract Analysis",
        subtitle="Structured fixture-backed contract work product grounded to the demo agreement.",
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
    if "antitrust" in normalized or "competition" in normalized:
        content = "The fixture-backed antitrust issue is the combination of required HSR/competition filings and the no-divestiture limitation on remedies."
        citation_ids = ["antitrust-approvals", "no-divestiture"]
    elif "fiduciary" in normalized or "board" in normalized:
        content = "The fixture-backed fiduciary issues are board approval, fairness to stockholders, and the superior-proposal termination-fee path."
        citation_ids = ["board-approval", "termination-fee"]
    else:
        content = "Fixture mode can answer only the bundled contract demo follow-up questions without LLM mode."
        citation_ids = []
    return ChatMessage(
        id=f"msg-{uuid4().hex}",
        role="assistant",
        content=content,
        report=None,
        citations=[citations[citation_id] for citation_id in citation_ids if citation_id in citations],
        created_at=datetime.now(UTC).isoformat(),
    )


def authorities(finding: str | None = None) -> list[dict]:
    normalized = (finding or "").lower()
    if "fiduciary" in normalized:
        return _fiduciary_authorities()
    if "antitrust" in normalized:
        return _antitrust_authorities()
    return _antitrust_authorities() + _fiduciary_authorities()


def _antitrust_authorities() -> list[dict]:
    return [
        {
            "authority_id": "15-usc-18",
            "title": "Clayton Act Section 7",
            "source_type": "statute",
            "summary": "Bars acquisitions where the effect may substantially lessen competition or tend to create a monopoly.",
            "relevance": 94,
            "quote": "the effect of such acquisition may be substantially to lessen competition",
            "verified": True,
            "url": "https://www.law.cornell.edu/uscode/text/15/18",
            "metadata": {"jurisdiction": "Federal", "treatment": "Controlling statute"},
        },
        {
            "authority_id": "standard-oil",
            "title": "Standard Oil Co. of New Jersey v. United States",
            "source_type": "case",
            "summary": "Foundational antitrust authority addressing monopoly power and restraints of trade.",
            "relevance": 81,
            "quote": "restraint of trade",
            "verified": True,
            "url": "https://supreme.justia.com/cases/federal/us/221/1/",
            "metadata": {"court": "U.S. Supreme Court", "treatment": "Background authority"},
        },
        {
            "authority_id": "ftc-doj-merger-guidelines",
            "title": "FTC and DOJ Merger Guidelines",
            "source_type": "secondary",
            "summary": "Agency framework for merger review, competitive effects, entry, and rebuttal evidence.",
            "relevance": 89,
            "quote": "mergers should not substantially lessen competition or tend to create a monopoly",
            "verified": True,
            "url": "https://www.justice.gov/atr/merger-guidelines",
            "metadata": {"source": "DOJ/FTC", "treatment": "Agency guidance"},
        },
    ]


def _fiduciary_authorities() -> list[dict]:
    return [
        {
            "authority_id": "revlon-v-macandrews",
            "title": "Revlon, Inc. v. MacAndrews & Forbes Holdings, Inc.",
            "source_type": "case",
            "summary": "Delaware authority on directors' duties when selling control of a company.",
            "relevance": 92,
            "quote": "the duty of the board had thus changed from the preservation of Revlon as a corporate entity to the maximization of the company's value",
            "verified": True,
            "url": "https://law.justia.com/cases/delaware/supreme-court/1986/506-a-2d-173-4.html",
            "metadata": {"court": "Delaware Supreme Court", "treatment": "Transactional fiduciary duty"},
        },
        {
            "authority_id": "del-gcl-141",
            "title": "Delaware General Corporation Law Section 141",
            "source_type": "statute",
            "summary": "Vests corporate business and affairs under board direction.",
            "relevance": 76,
            "quote": "The business and affairs of every corporation organized under this chapter shall be managed by or under the direction of a board of directors",
            "verified": True,
            "url": "https://delcode.delaware.gov/title8/c001/sc04/",
            "metadata": {"jurisdiction": "Delaware", "treatment": "Board authority"},
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
