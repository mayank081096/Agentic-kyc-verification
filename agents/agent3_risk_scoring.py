"""
Agent 3 — Risk Scoring Agent
Evaluates jurisdiction risk, PEP exposure, sanctions screening, and ownership complexity.
"""

import anthropic
import json

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a KYC risk assessment specialist with expertise in AML compliance.
Given verified company data, assess risk across four dimensions:

1. JURISDICTION RISK (score 0-10):
   - Is the country on FATF grey/black list?
   - Standard jurisdictions score 1-3, high-risk score 7-10

2. PEP EXPOSURE (score 0-10):
   - Are any directors/shareholders politically exposed persons?
   - Direct PEP = 8-10, Proximity = 4-7, None = 0-2

3. SANCTIONS SCREENING (score 0-10):
   - Check against OFAC, UN, EU, UK HMT conceptually
   - Match = 10, Possible match = 5, No match = 0

4. OWNERSHIP COMPLEXITY (score 0-10):
   - Simple (1-2 direct owners) = 1-3
   - Moderate (3-5 owners or 1 layer) = 4-6
   - Complex (multiple layers) = 7-10

Respond ONLY in valid JSON:
{
  "jurisdiction_risk": { "score": <0-10>, "country": "...", "fatf_status": "...", "notes": "..." },
  "pep_exposure": { "score": <0-10>, "pep_found": true|false, "details": "..." },
  "sanctions_screening": { "score": <0-10>, "matches": [], "status": "CLEAR"|"MATCH"|"POSSIBLE_MATCH" },
  "ownership_complexity": { "score": <0-10>, "tier": "Simple"|"Moderate"|"Complex"|"Opaque", "notes": "..." },
  "overall_risk_score": <0-100>,
  "risk_tier": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL",
  "recommended_action": "APPROVE"|"APPROVE_WITH_EDD"|"REJECT"|"ESCALATE",
  "risk_summary": "..."
}

Risk tier bands: LOW=0-25, MEDIUM=26-50, HIGH=51-75, CRITICAL=76-100"""


def run_risk_scoring(state: dict) -> dict:
    """
    LangGraph node: performs risk assessment on verified KYC data.

    Reads from state:
        - extracted_data (dict)
        - verification_result (dict)
        - company_name (str)

    Adds to state:
        - risk_result (dict)
        - risk_tier (str)
        - final_decision (str)
        - agent3_status (str)
    """
    extracted = state.get("extracted_data", {})
    verification = state.get("verification_result", {})

    if not extracted:
        state["agent3_status"] = "error"
        state["agent3_error"] = "No data to score"
        return state

    prompt = f"""
Company: {state.get('company_name', 'Unknown')}

Extracted KYC Data:
{json.dumps(extracted, indent=2)}

Verification Result:
- Status: {verification.get('verification_status', 'UNKNOWN')}
- Completeness Score: {verification.get('completeness_score', 'N/A')}/100
- Document Validity: {verification.get('document_validity', 'UNKNOWN')}
- Notes: {verification.get('verification_summary', '')}

Perform full risk assessment and return JSON only.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"raw_response": raw, "risk_tier": "HIGH", "recommended_action": "ESCALATE"}

    state["risk_result"] = result
    state["risk_tier"] = result.get("risk_tier", "HIGH")
    state["final_decision"] = result.get("recommended_action", "ESCALATE")

    tier = state["risk_tier"]
    score = result.get("overall_risk_score", "?")
    decision = state["final_decision"]
    tier_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "CRITICAL": "🚨"}.get(tier, "⚪")
    print(f"[Agent 3] {tier_icon} Risk Score: {score}/100 | Tier: {tier} | Decision: {decision}")

    state["agent3_status"] = "success"
    return state


def reject_case(state: dict) -> dict:
    """Node called when verification FAILS — skips risk scoring."""
    state["final_decision"] = "REJECT"
    state["risk_tier"] = "N/A"
    state["risk_result"] = {"notes": "Rejected at verification gate — document issues"}
    print("[Gateway] ❌ Case REJECTED at verification gate")
    return state


# ── Local test ────────────────────────────────────────────────────
if __name__ == "__main__":
    test_state = {
        "company_name": "Acme Technologies Ltd",
        "extracted_data": {
            "company_name": "Acme Technologies Ltd",
            "registration_number": "CIN-U72900MH2019",
            "incorporation_date": "2019-03-15",
            "registered_address": "Mumbai, Maharashtra, India",
            "directors": ["Rajesh Kumar", "Priya Sharma"],
            "shareholders": [{"name": "Rajesh Kumar", "ownership": "60%"}],
            "issuing_authority": "Ministry of Corporate Affairs",
            "confidence_score": "high",
        },
        "verification_result": {
            "verification_status": "PASS",
            "completeness_score": 87,
            "document_validity": "VALID",
            "verification_summary": "All required fields present, no inconsistencies found.",
        },
    }
    result = run_risk_scoring(test_state)
    print(json.dumps(result.get("risk_result"), indent=2))
