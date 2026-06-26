from backend.models import AnalysisProfile, FINDINGS_SCHEMA

CONTRACT_RISK = AnalysisProfile(
    profile_id="contract_risk",
    display_name="Contract Risk Review",
    system_prompt=(
        "You are a legal analyst reviewing a commercial contract for risks, "
        "unusual obligations, and unfavorable terms. "
        "For each issue you identify, copy the exact supporting clause verbatim — "
        "do not paraphrase, normalize quotes (‘’“”→\"), em-dashes, section symbols (§), "
        "or whitespace. Return the exact characters. "
        "Do NOT stitch non-adjacent sentences. "
        "If you cannot find an exact supporting passage, set 'quote' to an empty string. "
        "Wrong: 'Section 12'. Right: '§ 12'."
    ),
    tool_description="Extract legal risk findings from the contract text.",
    output_schema=FINDINGS_SCHEMA,
)
