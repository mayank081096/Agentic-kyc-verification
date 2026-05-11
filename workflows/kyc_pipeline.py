"""
KYC Pipeline — LangGraph Orchestrator
Wires Agent 1 → Agent 2 → Gateway → Agent 3 (or Reject)
"""

import json
from langgraph.graph import StateGraph, END
from agents.agent1_document_extractor import run_document_extractor
from agents.agent2_verification import run_verification, verification_gateway
from agents.agent3_risk_scoring import run_risk_scoring, reject_case


def build_kyc_graph() -> StateGraph:
    graph = StateGraph(dict)

    # ── Register nodes ────────────────────────────────────────────
    graph.add_node("document_extractor", run_document_extractor)
    graph.add_node("verification",       run_verification)
    graph.add_node("risk_scoring",       run_risk_scoring)
    graph.add_node("reject",             reject_case)

    # ── Entry point ───────────────────────────────────────────────
    graph.set_entry_point("document_extractor")

    # ── Sequential edges ──────────────────────────────────────────
    graph.add_edge("document_extractor", "verification")

    # ── Conditional gateway after verification ────────────────────
    graph.add_conditional_edges(
        "verification",
        verification_gateway,           # returns "risk_scoring" or "reject"
        {
            "risk_scoring": "risk_scoring",
            "reject":       "reject",
        }
    )

    # ── Terminal edges ────────────────────────────────────────────
    graph.add_edge("risk_scoring", END)
    graph.add_edge("reject",       END)

    return graph.compile()


def run_kyc_pipeline(company_name: str, document_paths: list[str]) -> dict:
    """
    Run the full KYC pipeline for a company.

    Args:
        company_name:    Legal name of the company
        document_paths:  List of file paths to KYC documents

    Returns:
        Final state dict with all agent outputs and decision
    """
    print(f"\n{'='*60}")
    print(f"  KYC PIPELINE STARTED: {company_name}")
    print(f"{'='*60}\n")

    initial_state = {
        "company_name":    company_name,
        "document_paths":  document_paths,
    }

    pipeline = build_kyc_graph()
    final_state = pipeline.invoke(initial_state)

    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"  Decision : {final_state.get('final_decision', 'N/A')}")
    print(f"  Risk Tier: {final_state.get('risk_tier', 'N/A')}")
    print(f"{'='*60}\n")

    return final_state


# ── Entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_kyc_pipeline(
        company_name="Acme Technologies Ltd",
        document_paths=[],     # e.g. ["./docs/cert.jpg", "./docs/id.pdf"]
    )
    # Pretty-print the full output
    summary = {
        "company":      result.get("company_name"),
        "decision":     result.get("final_decision"),
        "risk_tier":    result.get("risk_tier"),
        "risk_score":   result.get("risk_result", {}).get("overall_risk_score"),
        "verification": result.get("verification_status"),
        "agent1_ok":    result.get("agent1_status") == "success",
        "agent2_ok":    result.get("agent2_status") == "success",
        "agent3_ok":    result.get("agent3_status") == "success",
    }
    print(json.dumps(summary, indent=2))
