"""Tests for graph/builder.py — verify graph structure, nodes, edges, conditional edges."""

import pytest
from langgraph.graph import END

from graph.builder import build_graph, _noop_node
from graph.state import HuntState


class TestGraphStructure:
    """Verify the graph has the correct nodes and edges."""

    def test_graph_compiles_with_defaults(self):
        graph = build_graph()
        assert graph is not None

    def test_graph_has_all_nodes(self):
        graph = build_graph()
        node_names = set(graph.get_graph().nodes.keys())
        expected = {"__start__", "__end__", "parse_description", "insight",
                    "keyword_gen", "search", "lead_extract", "evaluate", "email_craft"}
        assert expected.issubset(node_names)

    def test_graph_entry_point_is_parse_description(self):
        graph = build_graph()
        g = graph.get_graph()
        # __start__ should have an edge to parse_description
        start_edges = [e for e in g.edges if e[0] == "__start__"]
        assert any(e[1] == "parse_description" for e in start_edges)

    def test_parse_description_connects_to_insight(self):
        graph = build_graph()
        g = graph.get_graph()
        edges = [(e[0], e[1]) for e in g.edges]
        assert ("parse_description", "insight") in edges

    def test_insight_connects_to_keyword_gen(self):
        graph = build_graph()
        g = graph.get_graph()
        edges = [(e[0], e[1]) for e in g.edges]
        assert ("insight", "keyword_gen") in edges

    def test_hunting_loop_edges(self):
        graph = build_graph()
        g = graph.get_graph()
        edges = [(e[0], e[1]) for e in g.edges]
        assert ("keyword_gen", "search") in edges
        assert ("search", "lead_extract") in edges
        assert ("lead_extract", "evaluate") in edges

    def test_email_craft_connects_to_end(self):
        graph = build_graph()
        g = graph.get_graph()
        edges = [(e[0], e[1]) for e in g.edges]
        assert ("email_craft", "__end__") in edges

    def test_evaluate_has_conditional_edges(self):
        """Evaluate should have edges to keyword_gen (continue), email_craft, and __end__ (done)."""
        graph = build_graph()
        g = graph.get_graph()
        evaluate_targets = {e[1] for e in g.edges if e[0] == "evaluate"}
        assert "keyword_gen" in evaluate_targets
        assert "email_craft" in evaluate_targets
        assert "__end__" in evaluate_targets


class TestGraphWithCustomNodes:
    """Verify custom node functions are wired correctly."""

    def test_custom_should_continue_finish(self):
        """When should_continue always returns 'finish', graph goes to email_craft."""
        call_log = []

        def fake_insight(state):
            call_log.append("insight")
            return {"insight": {"summary": "test"}, "current_stage": "insight"}

        def fake_keyword_gen(state):
            call_log.append("keyword_gen")
            return {"keywords": ["kw1"], "used_keywords": ["kw1"], "current_stage": "keyword_gen"}

        def fake_search(state):
            call_log.append("search")
            return {"search_results": [{"url": "https://x.com"}], "current_stage": "search"}

        def fake_lead_extract(state):
            call_log.append("lead_extract")
            return {"leads": [{"company": "X"}], "current_stage": "lead_extract"}

        def fake_evaluate(state):
            call_log.append("evaluate")
            return {"hunt_round": 2, "current_stage": "evaluate"}

        def fake_email_craft(state):
            call_log.append("email_craft")
            return {"email_sequences": [{"id": 1}], "current_stage": "email_craft"}

        def always_finish(state):
            return "finish"

        from langgraph.checkpoint.memory import MemorySaver

        graph = build_graph(
            insight_node=fake_insight,
            keyword_gen_node=fake_keyword_gen,
            search_node=fake_search,
            lead_extract_node=fake_lead_extract,
            evaluate_node=fake_evaluate,
            should_continue_fn=always_finish,
            email_craft_node=fake_email_craft,
            checkpointer=MemorySaver(),
        )

        result = graph.invoke(
            {
                "website_url": "https://example.com",
                "product_keywords": [],
                "target_regions": [],
                "uploaded_files": [],
                "target_lead_count": 100,
                "max_rounds": 5,
                "enable_email_craft": True,
                "insight": None,
                "keywords": [],
                "used_keywords": [],
                "search_results": [],
                "matched_platforms": [],
                "keyword_search_stats": {},
                "leads": [],
                "email_sequences": [],
                "hunt_round": 1,
                "prev_round_lead_count": 0,
                "round_feedback": None,
                "current_stage": "start",
                "messages": [],
            },
            config={"configurable": {"thread_id": "test-1"}},
        )

        # Should go: insight → keyword_gen → search → lead_extract → evaluate → email_craft
        assert call_log == ["insight", "keyword_gen", "search", "lead_extract", "evaluate", "email_craft"]

    def test_custom_should_continue_loop_once(self):
        """When should_continue returns 'continue' once then 'finish', graph loops."""
        call_log = []
        loop_count = {"n": 0}

        def fake_insight(state):
            call_log.append("insight")
            return {"insight": {"summary": "test"}, "current_stage": "insight"}

        def fake_keyword_gen(state):
            call_log.append("keyword_gen")
            return {"keywords": ["kw"], "used_keywords": state.get("used_keywords", []) + ["kw"]}

        def fake_search(state):
            call_log.append("search")
            return {"search_results": state.get("search_results", []) + [{"url": "x"}]}

        def fake_lead_extract(state):
            call_log.append("lead_extract")
            return {"leads": state.get("leads", []) + [{"company": "X"}]}

        def fake_evaluate(state):
            call_log.append("evaluate")
            loop_count["n"] += 1
            return {"hunt_round": loop_count["n"] + 1, "prev_round_lead_count": len(state.get("leads", []))}

        def fake_email_craft(state):
            call_log.append("email_craft")
            return {"email_sequences": []}

        def continue_once(state):
            if state.get("hunt_round", 1) <= 2:
                return "continue"
            return "finish"

        from langgraph.checkpoint.memory import MemorySaver

        graph = build_graph(
            insight_node=fake_insight,
            keyword_gen_node=fake_keyword_gen,
            search_node=fake_search,
            lead_extract_node=fake_lead_extract,
            evaluate_node=fake_evaluate,
            should_continue_fn=continue_once,
            email_craft_node=fake_email_craft,
            checkpointer=MemorySaver(),
        )

        result = graph.invoke(
            {
                "website_url": "https://example.com",
                "product_keywords": [],
                "target_regions": [],
                "uploaded_files": [],
                "target_lead_count": 100,
                "max_rounds": 10,
                "enable_email_craft": True,
                "insight": None,
                "keywords": [],
                "used_keywords": [],
                "search_results": [],
                "matched_platforms": [],
                "keyword_search_stats": {},
                "leads": [],
                "email_sequences": [],
                "hunt_round": 1,
                "prev_round_lead_count": 0,
                "round_feedback": None,
                "current_stage": "start",
                "messages": [],
            },
            config={"configurable": {"thread_id": "test-loop-1"}},
        )

        # Should loop once: insight → kw → search → lead → eval → kw → search → lead → eval → email
        expected = [
            "insight",
            "keyword_gen", "search", "lead_extract", "evaluate",  # round 1
            "keyword_gen", "search", "lead_extract", "evaluate",  # round 2 (loop)
            "email_craft",
        ]
        assert call_log == expected
        assert loop_count["n"] == 2

    def test_email_craft_skipped_when_disabled(self):
        """When enable_email_craft is False, graph skips email_craft and ends directly."""
        call_log = []

        def fake_insight(state):
            call_log.append("insight")
            return {"insight": {"summary": "test"}, "current_stage": "insight"}

        def fake_keyword_gen(state):
            call_log.append("keyword_gen")
            return {"keywords": ["kw1"], "used_keywords": ["kw1"], "current_stage": "keyword_gen"}

        def fake_search(state):
            call_log.append("search")
            return {"search_results": [{"url": "https://x.com"}], "current_stage": "search"}

        def fake_lead_extract(state):
            call_log.append("lead_extract")
            return {"leads": [{"company": "X"}], "current_stage": "lead_extract"}

        def fake_evaluate(state):
            call_log.append("evaluate")
            return {"hunt_round": 2, "current_stage": "evaluate"}

        def fake_email_craft(state):
            call_log.append("email_craft")
            return {"email_sequences": [{"id": 1}], "current_stage": "email_craft"}

        def always_finish(state):
            return "finish"

        from langgraph.checkpoint.memory import MemorySaver

        graph = build_graph(
            insight_node=fake_insight,
            keyword_gen_node=fake_keyword_gen,
            search_node=fake_search,
            lead_extract_node=fake_lead_extract,
            evaluate_node=fake_evaluate,
            should_continue_fn=always_finish,
            email_craft_node=fake_email_craft,
            checkpointer=MemorySaver(),
        )

        result = graph.invoke(
            {
                "website_url": "https://example.com",
                "product_keywords": [],
                "target_regions": [],
                "uploaded_files": [],
                "target_lead_count": 100,
                "max_rounds": 5,
                "enable_email_craft": False,
                "insight": None,
                "keywords": [],
                "used_keywords": [],
                "search_results": [],
                "matched_platforms": [],
                "keyword_search_stats": {},
                "leads": [],
                "email_sequences": [],
                "hunt_round": 1,
                "prev_round_lead_count": 0,
                "round_feedback": None,
                "current_stage": "start",
                "messages": [],
            },
            config={"configurable": {"thread_id": "test-no-email"}},
        )

        # email_craft should NOT be called
        assert call_log == ["insight", "keyword_gen", "search", "lead_extract", "evaluate"]
        assert result.get("email_sequences") == []
