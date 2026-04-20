"""LangGraph workflow definition for claims explanation."""

from langgraph.graph import StateGraph

from src.graph.nodes import (
    assemble_context,
    audit_log,
    fetch_claim,
    fetch_denial_code,
    fetch_member,
    llm_explain,
    parse_intent,
    retrieve_policy_context,
)
from src.graph.state import ClaimsGraphState
from src.logging_config import get_logger

logger = get_logger(__name__)


def should_fetch_denial_code(state: ClaimsGraphState) -> bool:
    claim = state.get("claim")
    return bool(claim and claim.status == "DENIED" and claim.denial_code)


def build_claims_graph() -> StateGraph:
    """Build the claims explanation LangGraph workflow.

    The workflow follows this flow:
    1. parse_intent: Extract member_id and claim_id from question
    2. fetch_claim: Retrieve claim from service
    3. fetch_member: Retrieve member from service
    4. fetch_denial_code: (conditional) Fetch denial code if claim denied
    5. retrieve_policy_context: Use RAG to get relevant policies
    6. assemble_context: Log context assembly
    7. llm_explain: Generate plain-English explanation
    8. audit_log: Record interaction for compliance
    9. END

    Returns:
        Compiled StateGraph for execution
    """
    # Create graph with state
    graph = StateGraph(ClaimsGraphState)

    # Add all nodes
    graph.add_node("parse_intent", parse_intent)
    graph.add_node("fetch_claim", fetch_claim)
    graph.add_node("fetch_member", fetch_member)
    graph.add_node("fetch_denial_code", fetch_denial_code)
    graph.add_node("retrieve_policy_context", retrieve_policy_context)
    graph.add_node("assemble_context", assemble_context)
    graph.add_node("llm_explain", llm_explain)
    graph.add_node("audit_log", audit_log)

    # Define edges - linear flow with conditional branch
    graph.add_edge("parse_intent", "fetch_claim")
    graph.add_edge("fetch_claim", "fetch_member")

    # Conditional edge: only fetch denial code if claim is denied
    graph.add_conditional_edges(
        "fetch_member",
        should_fetch_denial_code,
        {
            True: "fetch_denial_code",
            False: "retrieve_policy_context",
        },
    )
    graph.add_edge("fetch_denial_code", "retrieve_policy_context")

    # Continue linear flow
    graph.add_edge("retrieve_policy_context", "assemble_context")
    graph.add_edge("assemble_context", "llm_explain")
    graph.add_edge("llm_explain", "audit_log")

    # Set entry point
    graph.set_entry_point("parse_intent")

    # Set finish point
    graph.set_finish_point("audit_log")

    logger.info("claims_graph_built", nodes_count=8)

    return graph


def get_claims_graph() -> StateGraph:
    """Get or build the claims explanation graph.

    Returns:
        Compiled StateGraph
    """
    return build_claims_graph()
