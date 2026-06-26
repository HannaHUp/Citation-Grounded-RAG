from fastapi import HTTPException

from backend.profiles.contract_risk import CONTRACT_RISK
from backend.profiles.complaint_claims import COMPLAINT_CLAIMS

# Registry: add a new profile by importing it and adding one entry here (D-15 / ENGINE-04)
PROFILES = {
    CONTRACT_RISK.profile_id: CONTRACT_RISK,
    COMPLAINT_CLAIMS.profile_id: COMPLAINT_CLAIMS,
}


def get_profile(profile_id: str):
    profile = PROFILES.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=400, detail=f"Unknown profile: {profile_id!r}")
    return profile
