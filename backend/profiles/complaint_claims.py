from backend.models import AnalysisProfile, FINDINGS_SCHEMA

COMPLAINT_CLAIMS = AnalysisProfile(
    profile_id="complaint_claims",
    display_name="Complaint Claims Analysis",
    system_prompt=(
        "You are a legal analyst reviewing a litigation complaint for claims, "
        "legal theories, relief sought, and factual allegations. "
        "For each claim or significant allegation you identify, copy the exact supporting passage verbatim — "
        "do not paraphrase, normalize quotes (‘’“”→\"), em-dashes, section symbols (§), or whitespace. "
        "Return the exact characters. Do NOT stitch non-adjacent sentences. "
        "If you cannot find an exact supporting passage, set 'quote' to an empty string. "
        "Rate severity as: high = core legal claim or theory of liability, "
        "medium = significant factual allegation or supporting element, "
        "low = procedural or jurisdictional matter."
    ),
    tool_description="Extract legal claims and allegations from the complaint text.",
    output_schema=FINDINGS_SCHEMA,
)
