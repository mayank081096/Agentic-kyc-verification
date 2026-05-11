"""
Agent 1 — Document Extractor
Reads uploaded KYC documents via Claude Vision and extracts structured fields.
"""

import anthropic
import base64
import json
from pathlib import Path

client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are a KYC document extraction specialist.
Extract the following fields from any document image provided:
- company_name
- registration_number
- incorporation_date
- registered_address
- directors (list)
- shareholders (list with ownership %)
- document_type
- document_expiry
- issuing_authority

Respond ONLY in valid JSON. If a field is not found, use null.
Add a confidence_score (high | medium | low) based on document clarity."""


def encode_file(file_path: str) -> tuple[str, str]:
    """Base64-encode a file and detect its media type."""
    path = Path(file_path)
    ext = path.suffix.lower()
    media_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".pdf": "application/pdf",
    }
    media_type = media_map.get(ext, "image/jpeg")
    with open(file_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8"), media_type


def run_document_extractor(state: dict) -> dict:
    """
    LangGraph node: extracts KYC fields from uploaded documents.

    Expected state keys:
        - document_paths (list[str]): local file paths to documents

    Adds to state:
        - extracted_data (dict): structured KYC fields
        - agent1_status (str): success | error
    """
    doc_paths = state.get("document_paths", [])
    if not doc_paths:
        state["agent1_status"] = "error"
        state["extracted_data"] = {}
        state["agent1_error"] = "No documents provided"
        return state

    content = []
    for path in doc_paths:
        try:
            data, media_type = encode_file(path)
            if media_type == "application/pdf":
                content.append({
                    "type": "document",
                    "source": {"type": "base64", "media_type": media_type, "data": data},
                })
            else:
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": data},
                })
        except Exception as e:
            print(f"[Agent 1] Warning: could not encode {path}: {e}")

    content.append({
        "type": "text",
        "text": f"Extract all KYC fields from the {len(doc_paths)} document(s) above for company: {state.get('company_name', 'Unknown')}",
    })

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        extracted = {"raw_response": raw}

    state["extracted_data"] = extracted
    state["agent1_status"] = "success"
    print(f"[Agent 1] ✅ Extracted data with confidence: {extracted.get('confidence_score', 'unknown')}")
    return state


# ── Local test ────────────────────────────────────────────────────
if __name__ == "__main__":
    test_state = {
        "company_name": "Acme Technologies Ltd",
        "document_paths": [],  # Add real paths here: ["./sample_cert.jpg"]
    }
    result = run_document_extractor(test_state)
    print(json.dumps(result.get("extracted_data"), indent=2))
