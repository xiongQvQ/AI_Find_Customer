"""
Keyword Generator Page - Streamlit
Generate B2B search keywords using AI based on product description and target regions.
"""
import streamlit as st
import pandas as pd
import json
import os
import sys

# Add project root to path so keyword_generator module can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keyword_generator import generate_keywords, save_keywords
from components.common import display_api_status, display_quick_links
from core.llm_client import is_llm_available, get_llm_model

st.set_page_config(page_title="Keyword Generator", page_icon="🎯", layout="wide")

st.title("🎯 B2B Keyword Generator")
st.markdown("Generate targeted search keywords using AI — then use them directly in Company Search")

# Check LLM config
_llm_ready = is_llm_available()
_llm_model = get_llm_model()
if not _llm_ready:
    if _llm_model:
        st.error(f"⚠️ LLM_MODEL is set to `{_llm_model}` but the required API key is missing.")
    else:
        st.error("⚠️ LLM_MODEL is not configured. Keyword generation requires an LLM.")
    with st.expander("📝 How to configure LLM (via litellm)"):
        st.markdown("""
        Set `LLM_MODEL` in your `.env` file to any litellm-supported model:

        **International:**
        ```
        LLM_MODEL=openai/gpt-4o-mini
        OPENAI_API_KEY=your_key_here
        ```

        **DeepSeek (国内推荐):**
        ```
        LLM_MODEL=deepseek/deepseek-chat
        DEEPSEEK_API_KEY=your_key_here
        ```

        **Volcano Engine / 豆包 (国内):**
        ```
        LLM_MODEL=volcengine/doubao-1-5-pro-256k-250115
        VOLCENGINE_API_KEY=your_key_here
        ```

        **Zhipu GLM / MiniMax / OpenRouter / Grok:** see `.env.example` for all options.
        """)
    st.stop()

# ── Layout ────────────────────────────────────────────────────────────────

col_input, col_results = st.columns([1, 2])

with col_input:
    st.subheader("🔧 Configuration")

    product = st.text_input(
        "Product / Service *",
        placeholder="e.g. solar inverter, hydraulic pump, LED lighting",
        help="Describe your product or service. Be specific for better results.",
    )

    region_input = st.text_input(
        "Target Regions *",
        placeholder="e.g. Germany, Poland, France",
        help="Enter one or more target markets, separated by commas.",
    )

    count = st.slider(
        "Number of Keywords",
        min_value=10,
        max_value=30,
        value=20,
        step=5,
        help="How many keywords to generate. More keywords = more API search coverage.",
    )

    extra_context = st.text_area(
        "Additional Context (Optional)",
        placeholder="e.g. focus on wholesalers and distributors, exclude retailers",
        height=80,
        help="Narrow down the type of buyers, use case, or any other relevant context.",
    )

    generate_btn = st.button("✨ Generate Keywords", type="primary", use_container_width=True)

    st.divider()
    st.caption(
        "💡 **Tip:** These keywords are designed to be used as **Custom Query** input "
        "in the Company Search page. Each keyword targets a different buyer angle."
    )
    st.caption(
        "🚀 Want keywords that **auto-adapt** based on real search performance? "
        "Try [B2BInsights.io](https://b2binsights.io) for the full AI agent experience."
    )

# ── Results ───────────────────────────────────────────────────────────────

with col_results:
    st.subheader("📋 Generated Keywords")

    if generate_btn:
        if not product.strip():
            st.error("Please enter a product or service description.")
        elif not region_input.strip():
            st.error("Please enter at least one target region.")
        else:
            regions = [r.strip() for r in region_input.split(",") if r.strip()]

            with st.spinner(f"Generating {count} keywords using {_llm_model}..."):
                try:
                    keywords = generate_keywords(
                        product=product.strip(),
                        regions=regions,
                        count=count,
                        extra_context=extra_context.strip(),
                    )
                except ValueError as e:
                    st.error(f"Configuration error: {e}")
                    keywords = []
                except Exception as e:
                    st.error(f"Generation failed: {e}")
                    keywords = []

            if keywords:
                st.success(f"✅ Generated {len(keywords)} keywords!")

                # Store in session state for reuse
                st.session_state["last_keywords"] = keywords
                st.session_state["last_product"] = product.strip()
                st.session_state["last_regions"] = regions

                # Display as interactive table
                df = pd.DataFrame(
                    {"#": range(1, len(keywords) + 1), "Keyword": keywords}
                )
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    height=min(400, 40 + len(keywords) * 35),
                    column_config={
                        "#": st.column_config.NumberColumn(width="small"),
                        "Keyword": st.column_config.TextColumn(width="large"),
                    },
                )

                # ── Download & Export ─────────────────────────────────────
                st.divider()
                st.subheader("📥 Export & Use")

                dl_col1, dl_col2 = st.columns(2)

                with dl_col1:
                    # Plain text — one keyword per line, easy to copy
                    kw_text = "\n".join(keywords)
                    st.download_button(
                        label="📄 Download as TXT",
                        data=kw_text,
                        file_name=f"keywords_{product.strip().replace(' ', '_')[:20]}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

                with dl_col2:
                    # JSON with metadata
                    import time as _time
                    json_data = json.dumps(
                        {
                            "product": product.strip(),
                            "regions": regions,
                            "count": len(keywords),
                            "keywords": keywords,
                            "generated_at": _time.strftime("%Y-%m-%d %H:%M:%S"),
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                    st.download_button(
                        label="📦 Download as JSON",
                        data=json_data,
                        file_name=f"keywords_{product.strip().replace(' ', '_')[:20]}.json",
                        mime="application/json",
                        use_container_width=True,
                    )

                # Save to output directory
                saved_path = save_keywords(keywords, product.strip(), regions)
                st.info(f"💾 Saved to: `{saved_path}`")

                # ── How to use ────────────────────────────────────────────
                st.divider()
                st.subheader("▶️ Next Step: Search Companies")
                st.markdown(
                    "Copy any keyword above and paste it into **Company Search → Custom Query** "
                    "to find matching companies."
                )

                # Show a quick example
                if keywords:
                    with st.expander("📖 Command-line usage"):
                        st.code(
                            f'python serper_company_search.py --general-search \\\n'
                            f'  --custom-query "{keywords[0]}" \\\n'
                            f'  --gl us',
                            language="bash",
                        )
                        st.markdown(
                            "Run this for **each keyword** to build a comprehensive company list, "
                            "then use `process_all_companies_en.py` to batch-extract contact info."
                        )

            else:
                st.warning("No keywords were generated. Check your LLM configuration.")

    elif "last_keywords" in st.session_state:
        # Show previous results while user hasn't clicked generate again
        keywords = st.session_state["last_keywords"]
        product_prev = st.session_state.get("last_product", "")
        regions_prev = st.session_state.get("last_regions", [])

        st.info(f"Showing previous results for: **{product_prev}** → {', '.join(regions_prev)}")
        df = pd.DataFrame({"#": range(1, len(keywords) + 1), "Keyword": keywords})
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(400, 40 + len(keywords) * 35),
            column_config={
                "#": st.column_config.NumberColumn(width="small"),
                "Keyword": st.column_config.TextColumn(width="large"),
            },
        )
    else:
        st.info("Configure your product and regions on the left, then click **Generate Keywords**.")

        # Show example output
        with st.expander("📖 What does the output look like?"):
            st.markdown("""
            For **solar inverter** targeting **Germany, Poland**:

            | # | Keyword |
            |---|---------|
            | 1 | solar inverter distributor Germany |
            | 2 | PV module importer Poland |
            | 3 | Solarwechselrichter Großhändler Deutschland |
            | 4 | renewable energy wholesaler Eastern Europe |
            | 5 | CE certified solar inverter buyer |
            | 6 | site:europages.com solar inverter |
            | 7 | off-grid solar installer Poland |
            | 8 | IEC 62109 compliant inverter distributor |
            | ... | ... |

            Each keyword targets a **different buyer angle**, maximising your company search coverage.
            """)

# ── Sidebar ───────────────────────────────────────────────────────────────

with st.sidebar:
    display_api_status()
    display_quick_links()

    st.divider()
    st.header("📖 Keyword Dimensions")
    st.markdown("""
    Generated keywords cover **7 dimensions**:

    1. 🏭 **Product + buyer role**  
       e.g. *solar inverter distributor*
    2. 🔧 **Industry + application**  
       e.g. *renewable energy wholesaler*
    3. 💎 **Value proposition**  
       e.g. *CE certified supplier*
    4. 🏢 **Buyer type**  
       e.g. *electrical equipment dealer*
    5. 🌍 **Region + trade term**  
       e.g. *PV importer export Poland*
    6. 🔗 **B2B platforms**  
       e.g. *site:europages.com inverter*
    7. 📋 **Certification/standard**  
       e.g. *IEC 62109 distributor*
    """)

    st.divider()
    st.header("💡 Workflow")
    st.markdown("""
    **Recommended flow:**

    1. 🎯 **Here** — Generate keywords
    2. 🔍 **Company Search** — Search each keyword
    3. 📧 **Contact Extraction** — Extract emails & phones
    4. 👥 **Employee Search** — Find decision makers
    """)
