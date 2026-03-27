"""LangGraph StateGraph builder — assembles the hunt pipeline with loop."""

from typing import Callable

from langgraph.graph import END, StateGraph

from graph.state import HuntState


def _noop_node(state: HuntState) -> dict:
    """Placeholder node used when real agent is not yet wired."""
    return {}


def build_graph(
    *,
    parse_description_node: Callable | None = None,
    insight_node: Callable | None = None,
    keyword_gen_node: Callable | None = None,
    search_node: Callable | None = None,
    lead_extract_node: Callable | None = None,
    evaluate_node: Callable | None = None,
    should_continue_fn: Callable | None = None,
    email_craft_node: Callable | None = None,
    checkpointer=None,
) -> StateGraph:
    """Build and compile the AI Hunter StateGraph.

    All node callables default to no-op placeholders so the graph structure
    can be tested independently of agent implementations.

    Args:
        insight_node: InsightAgent node function.
        keyword_gen_node: KeywordGenAgent node function.
        search_node: SearchAgent node function.
        lead_extract_node: LeadExtractAgent node function.
        evaluate_node: evaluate_progress function.
        should_continue_fn: Conditional edge function returning "continue" | "finish".
        email_craft_node: EmailCraftAgent node function.
        checkpointer: LangGraph checkpointer for persistence.

    Returns:
        Compiled StateGraph ready to invoke.
    """
    builder = StateGraph(HuntState)

    # ── Register nodes ──────────────────────────────────────────────────
    builder.add_node("parse_description", parse_description_node or _noop_node)
    builder.add_node("insight", insight_node or _noop_node)
    builder.add_node("keyword_gen", keyword_gen_node or _noop_node)
    builder.add_node("search", search_node or _noop_node)
    builder.add_node("lead_extract", lead_extract_node or _noop_node)
    builder.add_node("evaluate", evaluate_node or _noop_node)
    builder.add_node("email_craft", email_craft_node or _noop_node)

    # ── Edges ───────────────────────────────────────────────────────────
    # parse_description always runs first (no-op when description is empty)
    builder.set_entry_point("parse_description")
    builder.add_edge("parse_description", "insight")
    builder.add_edge("insight", "keyword_gen")

    # Hunting loop: KeywordGen → Search → LeadExtract → Evaluate
    builder.add_edge("keyword_gen", "search")
    builder.add_edge("search", "lead_extract")
    builder.add_edge("lead_extract", "evaluate")

    # Conditional edge: evaluate decides continue, email_craft, or done
    _base_should_continue = should_continue_fn or (lambda _: "finish")

    def _route_after_evaluate(state: HuntState) -> str:
        decision = _base_should_continue(state)
        if decision == "finish":
            if state.get("enable_email_craft", False):
                return "email_craft"
            return "done"
        return "continue"

    builder.add_conditional_edges(
        "evaluate",
        _route_after_evaluate,
        {"continue": "keyword_gen", "email_craft": "email_craft", "done": END},
    )

    builder.add_edge("email_craft", END)

    # ── Compile ─────────────────────────────────────────────────────────
    return builder.compile(checkpointer=checkpointer)
