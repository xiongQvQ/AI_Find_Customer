"""
B2B Flow Page — full automated pipeline
  Keyword Generation → Search → B2B Platform Queries → LLM Scoring & Filtering
"""
import streamlit as st
import pandas as pd
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.b2b_flow import B2BFlow, get_platform_labels
from core.llm_client import is_llm_available, get_llm_model
from core.search_client import get_search_provider, is_search_available
from components.common import display_api_status, display_quick_links

st.set_page_config(page_title="B2B Flow", page_icon="🚀", layout="wide")

st.title("🚀 B2B Discovery Flow")
st.markdown(
    "Fully automated pipeline: **AI Keywords → Web Search → B2B Platform Queries → LLM Scoring**"
)

# ── Config checks ──────────────────────────────────────────────────────────
_llm_ok = is_llm_available()
_search_ok = is_search_available()
_provider = get_search_provider()
_model = get_llm_model()

if not _search_ok:
    st.error(
        f"⚠️ Search provider `{_provider}` is not configured. "
        f"Please set `{'SERPER_API_KEY' if _provider == 'serper' else 'TAVILY_API_KEY'}` in `.env`."
    )
    with st.expander("📝 How to configure search provider"):
        st.markdown("""
**Option A — Serper.dev (default, recommended):**
```
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_api_key
```
Get a free key at [serper.dev](https://serper.dev)

**Option B — Tavily:**
```
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-your_tavily_key
```
Get a free key at [app.tavily.com](https://app.tavily.com/home)
        """)
    st.stop()

# ── Layout ─────────────────────────────────────────────────────────────────
col_cfg, col_results = st.columns([1, 2])

with col_cfg:
    st.subheader("⚙️ Configuration")

    product = st.text_input(
        "Product / Service *",
        placeholder="e.g. solar inverter, hydraulic pump",
        help="Describe your product or service. Be specific.",
    )

    region_input = st.text_input(
        "Target Regions *",
        placeholder="e.g. Germany, Poland, France",
        help="Comma-separated target markets.",
    )

    st.divider()
    st.markdown("**Keyword Generation**")
    kw_count = st.slider("Number of AI keywords", 5, 20, 10, 5)

    extra_kw = st.text_area(
        "Extra keywords (optional)",
        placeholder="One per line",
        height=70,
        help="Manually add keywords on top of AI-generated ones.",
    )

    st.divider()
    st.markdown("**Search Settings**")
    gl = st.text_input("Geo locale (gl)", value="us", help="e.g. us, de, fr, cn")
    num_results = st.slider("Results per query", 5, 20, 10, 5)

    st.divider()
    st.markdown("**B2B Platform Queries**")
    all_platforms = get_platform_labels()
    run_b2b = st.checkbox("Enable B2B platform site: queries", value=True)
    if run_b2b:
        selected_platforms = st.multiselect(
            "Platforms to search",
            options=all_platforms,
            default=all_platforms[:5],
            help="Will run site:<platform> searches with your product name.",
        )
    else:
        selected_platforms = []

    st.divider()
    st.markdown("**LLM Scoring**")
    if _llm_ok:
        run_llm = st.checkbox("Enable LLM relevance scoring", value=True)
        min_score = st.slider(
            "Min score to include (0–10)", 0.0, 10.0, 5.0, 0.5,
            disabled=not run_llm,
        )
        st.caption(f"Using: `{_model}`")
    else:
        run_llm = False
        min_score = 0.0
        st.warning(
            "LLM scoring disabled — LLM_MODEL not configured or API key missing. "
            "Results will be shown unfiltered.",
            icon="⚠️",
        )

    st.divider()
    run_btn = st.button("🚀 Run B2B Flow", type="primary", use_container_width=True)

# ── Results area ───────────────────────────────────────────────────────────

with col_results:
    st.subheader("📊 Results")

    if run_btn:
        if not product.strip():
            st.error("Please enter a product or service description.")
        elif not region_input.strip():
            st.error("Please enter at least one target region.")
        else:
            regions = [r.strip() for r in region_input.split(",") if r.strip()]
            extra_keywords = [k.strip() for k in extra_kw.splitlines() if k.strip()]

            # Progress tracking
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def _progress(step: str, pct: float):
                progress_bar.progress(min(pct, 1.0))
                status_text.text(step)

            start_ts = time.time()
            flow = B2BFlow(product=product.strip(), regions=regions)

            with st.spinner("Running B2B flow…"):
                result = flow.run(
                    keyword_count=kw_count,
                    num_search_results=num_results,
                    gl=gl.strip() or "us",
                    run_b2b_platforms=run_b2b,
                    b2b_platforms=selected_platforms if selected_platforms else None,
                    llm_filter=run_llm,
                    min_llm_score=min_score,
                    extra_keywords=extra_keywords or None,
                    progress_cb=_progress,
                )

            elapsed = time.time() - start_ts
            progress_bar.progress(1.0)
            status_text.empty()

            if not result["success"]:
                st.error(f"Flow failed: {result['error']}")
            else:
                st.session_state["b2b_flow_result"] = result
                st.success(f"✅ Done in {elapsed:.1f}s")

    # ── Show stored results ────────────────────────────────────────────────
    if "b2b_flow_result" in st.session_state:
        res = st.session_state["b2b_flow_result"]
        stats = res["stats"]

        # ── Stats row ──────────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Keywords", stats.get("keywords_generated", 0))
        c2.metric("Searches run", stats.get("searches_run", 0))
        c3.metric("After dedup", stats.get("after_dedup", 0))
        c4.metric("Qualified leads", stats.get("filtered", stats.get("after_dedup", 0)))

        # ── Keywords generated ─────────────────────────────────────────────
        if res.get("keywords"):
            with st.expander(f"🔑 Keywords used ({len(res['keywords'])})"):
                for i, kw in enumerate(res["keywords"], 1):
                    st.write(f"{i}. {kw}")

        # ── Results tabs ───────────────────────────────────────────────────
        has_scored = bool(res.get("scored_results"))
        has_filtered = bool(res.get("filtered_results"))

        tab_labels = ["🏆 Qualified Leads"]
        if has_scored:
            tab_labels.append("📋 All Scored")
        tab_labels.append("🌐 All Raw Results")

        tabs = st.tabs(tab_labels)
        tab_idx = 0

        with tabs[tab_idx]:
            tab_idx += 1
            display_data = res.get("filtered_results") or res.get("all_results", [])
            _render_results_table(display_data, show_scores=has_scored)

        if has_scored:
            with tabs[tab_idx]:
                tab_idx += 1
                _render_results_table(res["scored_results"], show_scores=True)

        with tabs[tab_idx]:
            _render_results_table(res["all_results"], show_scores=False)

        # ── Download ───────────────────────────────────────────────────────
        st.divider()
        st.subheader("📥 Download")
        dcol1, dcol2 = st.columns(2)

        export_rows = res.get("filtered_results") or res.get("all_results", [])
        if export_rows:
            df_export = pd.DataFrame(export_rows)
            with dcol1:
                st.download_button(
                    "📄 Download CSV",
                    data=df_export.to_csv(index=False),
                    file_name=f"b2b_flow_{int(time.time())}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with dcol2:
                st.download_button(
                    "📦 Download JSON",
                    data=json.dumps(export_rows, ensure_ascii=False, indent=2),
                    file_name=f"b2b_flow_{int(time.time())}.json",
                    mime="application/json",
                    use_container_width=True,
                )
    else:
        st.info("Configure options on the left, then click **Run B2B Flow**.")
        with st.expander("📖 How the flow works"):
            st.markdown("""
1. **AI Keyword Generation** — LLM generates targeted B2B keywords for your product + regions
2. **Web Search** — Each keyword is searched via Serper or Tavily
3. **B2B Platform Queries** — Dedicated `site:` queries on Alibaba, Europages, ThomasNet, etc.
4. **Deduplication** — Results merged and deduplicated by domain
5. **LLM Scoring** — Each result scored 0-10 for company relevance and B2B fit
6. **Filtered output** — Only leads above your minimum score threshold are shown
            """)


# ── Helper to render a results table ──────────────────────────────────────

def _render_results_table(rows: list, show_scores: bool = False):
    if not rows:
        st.info("No results in this category.")
        return

    df = pd.DataFrame(rows)

    # Pick columns to display
    base_cols = ["title", "url", "domain", "snippet", "source_type", "platform", "source_keyword"]
    score_cols = ["llm_score", "is_company", "is_relevant", "llm_reason"]
    keep = [c for c in base_cols if c in df.columns]
    if show_scores:
        keep += [c for c in score_cols if c in df.columns]

    df_show = df[keep].copy()

    # Rename for display
    rename = {
        "title": "Title",
        "url": "URL",
        "domain": "Domain",
        "snippet": "Snippet",
        "source_type": "Source",
        "platform": "Platform",
        "source_keyword": "Keyword",
        "llm_score": "Score",
        "is_company": "Company?",
        "is_relevant": "Relevant?",
        "llm_reason": "Reason",
    }
    df_show.rename(columns={k: v for k, v in rename.items() if k in df_show.columns}, inplace=True)

    col_cfg = {}
    if "URL" in df_show.columns:
        col_cfg["URL"] = st.column_config.LinkColumn("URL", width="medium")
    if "Score" in df_show.columns:
        col_cfg["Score"] = st.column_config.NumberColumn("Score", format="%.1f", width="small")
    if "Snippet" in df_show.columns:
        col_cfg["Snippet"] = st.column_config.TextColumn("Snippet", width="large")
    if "Reason" in df_show.columns:
        col_cfg["Reason"] = st.column_config.TextColumn("Reason", width="large")
    if "Keyword" in df_show.columns:
        col_cfg["Keyword"] = st.column_config.TextColumn("Keyword", width="medium")

    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        height=min(600, 55 + len(df_show) * 35),
        column_config=col_cfg,
    )
    st.caption(f"{len(df_show)} results")


# ── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    display_api_status()
    display_quick_links()

    st.divider()
    st.subheader("🔌 Search Provider")
    provider_icon = "✅" if _search_ok else "❌"
    st.write(f"{provider_icon} `{_provider.upper()}`")

    st.divider()
    st.subheader("📖 Flow Steps")
    st.markdown("""
1. 🔑 **Keywords** — AI generates targeted queries
2. 🔍 **Search** — Serper or Tavily web search
3. 🏭 **B2B Platforms** — site: queries on trade directories
4. 🔁 **Dedup** — merge by domain
5. 🤖 **LLM Score** — 0-10 relevance rating
6. ✅ **Filter** — keep leads above threshold
    """)

    st.divider()
    st.subheader("🏭 B2B Platforms")
    st.markdown("\n".join(f"- {p}" for p in get_platform_labels()))
