"""
Company Search Page - Streamlit
Search for companies by industry, region, custom queries, or batch keyword list.
"""
import streamlit as st
import pandas as pd
import os
import json
from core.company_search import CompanySearcher
from components.common import (
    display_api_status,
    show_usage_tips,
    create_download_buttons,
    display_metrics,
    format_dataframe_columns,
)

st.set_page_config(page_title="Company Search", page_icon="🔍", layout="wide")

st.title("🔍 Smart Company Search")
st.markdown("Search for target companies by industry, region, custom queries, or batch keyword list")


def get_searcher():
    try:
        return CompanySearcher()
    except ValueError as e:
        st.error(f"Error initializing searcher: {str(e)}")
        return None


searcher = get_searcher()

if not searcher:
    st.error("Cannot initialize company searcher. Please check your API configuration.")
    st.stop()


def _show_results(result: dict, filename_prefix: str):
    """Shared helper to display search results and download buttons."""
    if result["success"]:
        companies = result["data"]
        if companies:
            stats = result.get("stats", {})
            if stats:
                st.success(
                    f"✅ Searched {stats.get('keywords_searched', 0)} keywords — "
                    f"{stats.get('total_raw', 0)} raw results → "
                    f"**{stats.get('after_dedup', len(companies))} unique companies** after dedup"
                )
            else:
                st.success(f"✅ Found {len(companies)} companies!")

            df = pd.DataFrame(companies)
            metrics = {
                "Total Companies": len(companies),
                "Unique Domains": df["domain"].dropna().nunique() if "domain" in df else 0,
                "LinkedIn Profiles": df["linkedin"].notna().sum() if "linkedin" in df else 0,
            }
            display_metrics(metrics)

            st.dataframe(
                df,
                use_container_width=True,
                height=400,
                column_config=format_dataframe_columns(df),
                hide_index=True,
            )

            st.divider()
            st.subheader("📥 Download Results")
            create_download_buttons(df, filename_prefix, "both")

            if result.get("output_file"):
                st.info(f"💾 Saved to: `{result['output_file']}`")

            if stats.get("errors"):
                with st.expander("⚠️ Partial errors"):
                    for err in stats["errors"]:
                        st.warning(err)
        else:
            st.warning("No companies found matching your criteria")
    else:
        st.error(f"❌ Search failed: {result['error']}")


# ── Tabs ──────────────────────────────────────────────────────────────────

tab_single, tab_batch = st.tabs(["🔍 Single Search", "📋 Batch Keyword Search"])

# ── Tab 1: Single Search (original behaviour) ─────────────────────────────

with tab_single:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Search Criteria")

        search_mode = st.radio(
            "Search Mode",
            ["General Search", "LinkedIn Company Search", "Custom Query"],
            help="Choose different search modes",
        )

        if search_mode == "Custom Query":
            custom_query = st.text_area(
                "Custom Search Query",
                placeholder="Enter complete search query, e.g.: renewable energy companies California",
                height=100,
            )
            industry = None
            region = None
        else:
            custom_query = None
            industry = st.text_input(
                "Industry Keywords",
                placeholder="e.g.: solar energy, software, manufacturing",
            )
            region = st.text_input(
                "Region/Location",
                placeholder="e.g.: California, New York, London",
            )
            keywords = st.text_input(
                "Additional Keywords (Optional)",
                placeholder="Separate multiple keywords with commas",
            )

        with st.expander("Advanced Options"):
            gl = st.selectbox(
                "Target Market",
                options=["us", "uk", "cn", "de", "fr", "jp", "au", "ca", "in", "br"],
                index=0,
            )
            num_results = st.slider(
                "Number of Results", min_value=10, max_value=100, value=30, step=10
            )

        search_button = st.button("🚀 Start Search", type="primary", use_container_width=True)

    with col2:
        st.subheader("Search Results")
        if search_button:
            if search_mode == "Custom Query" and not custom_query:
                st.error("Please enter a custom query")
            elif search_mode != "Custom Query" and not industry and not region:
                st.error("Please enter at least industry or region")
            else:
                with st.spinner("Searching for companies..."):
                    search_params = {
                        "search_mode": "linkedin" if search_mode == "LinkedIn Company Search" else "general",
                        "gl": gl,
                        "num_results": num_results,
                    }
                    if search_mode == "Custom Query":
                        search_params["custom_query"] = custom_query
                    else:
                        search_params["industry"] = industry
                        search_params["region"] = region
                        if "keywords" in locals() and keywords:
                            search_params["keywords"] = [k.strip() for k in keywords.split(",")]

                    result = searcher.search_companies(**search_params)
                _show_results(result, f"companies_{search_mode.lower().replace(' ', '_')}_{gl}")

# ── Tab 2: Batch Keyword Search ────────────────────────────────────────────

with tab_batch:
    st.markdown(
        "Paste a list of keywords (one per line) and search all of them at once. "
        "Results are automatically **deduplicated by domain**. "
        "Use the **🎯 Keyword Generator** page to generate your keyword list first."
    )

    col_b1, col_b2 = st.columns([1, 2])

    with col_b1:
        st.subheader("Keyword List")

        # Pre-fill from Keyword Generator session state if available
        default_kws = ""
        if "last_keywords" in st.session_state:
            default_kws = "\n".join(st.session_state["last_keywords"])

        batch_kw_input = st.text_area(
            "Keywords (one per line)",
            value=default_kws,
            height=250,
            placeholder="solar inverter distributor Germany\nPV module importer Poland\nrenewable energy wholesaler Europe\n...",
            help="Paste keywords here or use the Keyword Generator page to auto-generate them.",
        )

        with st.expander("Advanced Options"):
            batch_gl = st.selectbox(
                "Target Market",
                options=["us", "uk", "cn", "de", "fr", "jp", "au", "ca", "in", "br"],
                index=0,
                key="batch_gl",
            )
            batch_num = st.slider(
                "Results per keyword",
                min_value=5,
                max_value=20,
                value=10,
                step=5,
                help="Lower = faster and uses fewer API credits. Results are merged across all keywords.",
                key="batch_num",
            )
            batch_delay = st.slider(
                "Delay between requests (seconds)",
                min_value=0.5,
                max_value=5.0,
                value=1.5,
                step=0.5,
                help="Add a small delay to avoid hitting API rate limits.",
                key="batch_delay",
            )

        batch_button = st.button(
            "🚀 Batch Search All Keywords", type="primary", use_container_width=True
        )

        st.caption(
            "💡 **Tip:** Start with 5-10 keywords to test. Each keyword = 1 Serper API credit."
        )

    with col_b2:
        st.subheader("Batch Search Results")

        if batch_button:
            raw_lines = [ln.strip() for ln in batch_kw_input.splitlines() if ln.strip()]
            if not raw_lines:
                st.error("Please enter at least one keyword.")
            else:
                # Remove duplicate keywords (case-insensitive)
                seen: set = set()
                keywords_list = []
                for kw in raw_lines:
                    if kw.lower() not in seen:
                        seen.add(kw.lower())
                        keywords_list.append(kw)

                st.info(
                    f"Searching **{len(keywords_list)} keywords** × {batch_num} results each "
                    f"(~{len(keywords_list) * batch_num} raw results before dedup)..."
                )

                progress_bar = st.progress(0)
                status_text = st.empty()

                all_companies = []
                errors = []

                import time as _time
                for idx, kw in enumerate(keywords_list):
                    status_text.text(f"[{idx + 1}/{len(keywords_list)}] Searching: {kw}")
                    try:
                        companies = searcher._search_general_companies(
                            industry=None,
                            region=None,
                            keywords=None,
                            custom_query=kw,
                            gl=batch_gl,
                            num_results=batch_num,
                        )
                        all_companies.extend(companies)
                    except Exception as e:
                        errors.append(f"[{kw}] {e}")

                    progress_bar.progress((idx + 1) / len(keywords_list))
                    if idx < len(keywords_list) - 1:
                        _time.sleep(batch_delay)

                status_text.empty()
                progress_bar.empty()

                # Deduplicate
                seen_domains: set = set()
                seen_urls: set = set()
                deduped = []
                no_domain = []
                for c in all_companies:
                    domain = (c.get("domain") or "").strip().lower()
                    url = (c.get("url") or "").strip().lower()
                    if domain:
                        if domain not in seen_domains:
                            seen_domains.add(domain)
                            deduped.append(c)
                    else:
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            no_domain.append(c)
                merged = deduped + no_domain

                batch_result = {
                    "success": True,
                    "data": merged,
                    "error": "; ".join(errors) if errors else None,
                    "output_file": None,
                    "stats": {
                        "keywords_searched": len(keywords_list),
                        "total_raw": len(all_companies),
                        "after_dedup": len(merged),
                        "errors": errors,
                    },
                }

                # Save to file
                import time as _t
                ts = int(_t.time())
                out_csv = os.path.join("output", "company", f"batch_keywords_{batch_gl}_{ts}.csv")
                out_json = out_csv.replace(".csv", ".json")
                if merged:
                    import csv as _csv
                    with open(out_csv, "w", newline="", encoding="utf-8") as f:
                        writer = _csv.DictWriter(f, fieldnames=merged[0].keys())
                        writer.writeheader()
                        writer.writerows(merged)
                    with open(out_json, "w", encoding="utf-8") as f:
                        json.dump(merged, f, indent=2, ensure_ascii=False)
                    batch_result["output_file"] = out_csv

                _show_results(batch_result, f"batch_companies_{batch_gl}_{ts}")
        else:
            if default_kws:
                st.info(
                    f"✨ {len(default_kws.splitlines())} keywords loaded from Keyword Generator. "
                    "Click **Batch Search All Keywords** to start."
                )
            else:
                st.info(
                    "Paste keywords on the left or generate them with the **🎯 Keyword Generator** page first."
                )

# ── Sidebar ────────────────────────────────────────────────────────────────

with st.sidebar:
    display_api_status()
    show_usage_tips("company_search")

    st.divider()
    st.header("📁 Recent Searches")

    company_dir = os.path.join("output", "company")
    if os.path.exists(company_dir):
        csv_files = [f for f in os.listdir(company_dir) if f.endswith(".csv")]
        csv_files.sort(
            key=lambda x: os.path.getmtime(os.path.join(company_dir, x)), reverse=True
        )
        if csv_files:
            for file in csv_files[:5]:
                file_path = os.path.join(company_dir, file)
                file_size = os.path.getsize(file_path) / 1024
                st.markdown(f"📄 {file[:30]}... ({file_size:.1f} KB)")
        else:
            st.info("No search results yet")