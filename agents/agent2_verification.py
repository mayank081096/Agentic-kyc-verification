"""
Agent 2 — Verification Agent
Cross-validates extracted KYC fields for completeness, consistency, and document validity.
"""

import anthropic
import json

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a KYC verification specialist.
Given extracted document data, perform three checks:

1. COMPLETENESS CHECK (score 0-100):
   - Are all required KYC fields present?
   - Required: company_name, registration_number, incorporation_date, registered_address, directors

2. CONSISTENCY CHECK:
   - Are dates logical (incorporation before expiry)?
   - Do director/shareholder details look valid?
   - Are there any contradictions across fields?

3. DOCUMENT VALIDITY:
   - Is the document expired?
   - Are there suspicious signals (missing issuer, vague authority)?
   - Does the document type match expected KYC docs?

Respond ONLY in valid JSON with this structure:
{
  "completeness_score": <0-100>,
  "missing_fields": [...],
  "consistency_check": "PASSED" | "FAILED" | "WARNING",
  "consistency_notes": "...",
  "document_validity": "VALID" | "EXPIRED" | "SUSPICIOUS" | "UNKNOWN",
  "validity_notes": "...",
  "verification_status": "PASS" | "FAIL" | "REQUIRES_REVIEW",
  "verification_summary": "..."
}"""


def run_verification(state: dict) -> dict:
    """
    LangGraph node: verifies extracted KYC data.

    Reads from state:
        - extracted_data (dict): output from Agent 1
        - company_name (str)

    Adds to state:
        - verification_result (dict)
        - verification_status (str): PASS | FAIL | REQUIRES_REVIEW
        - agent2_status (str): success | error
    """
    extracted = state.get("extracted_data", {})
    if not extracted:
        state["agent2_status"] = "error"
        state["verification_status"] = "FAIL"
        state["agent2_error"] = "No extracted data from Agent 1"
        return state

    prompt = f"""
Company: {state.get('company_name', 'Unknown')}

Extracted KYC Data:
{json.dumps(extracted, indent=2)}

Please perform all three verification checks and return JSON only.
"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"raw_response": raw, "verification_status": "REQUIRES_REVIEW"}

    state["verification_result"] = result
    state["verification_status"] = result.get("verification_status", "REQUIRES_REVIEW")

    status = state["verification_status"]
    icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"[Agent 2] {icon} Verification status: {status} | Completeness: {result.get('completeness_score', '?')}/100")

    state["agent2_status"] = "success"
    return state


# ── Gateway logic (used by pipeline) ─────────────────────────────
def verification_gateway(state: dict) -> str:
    """
    LangGraph conditional edge: routes to risk_scoring or reject.
    Returns the name of the next node.
    """
    status = state.get("verification_status", "FAIL")
    if status in ("PASS", "REQUIRES_REVIEW"):
        return "risk_scoring"
    return "reject"


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
            "document_type": "Certificate of Incorporation",
            "document_expiry": None,
            "issuing_authority": "Ministry of Corporate Affairs",
            "confidence_score": "high",
        },
    }
    result = run_verification(test_state)
    print(json.dumps(result.get("verification_result"), indent=2))
