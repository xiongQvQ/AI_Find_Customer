"""
Contact Extraction Page - Streamlit
Extract contact information from company websites
"""
import streamlit as st
import pandas as pd
import os
import sys
import time
from components.common import (
    display_api_status, 
    show_usage_tips, 
    create_download_buttons,
    display_metrics
)

# Add parent directory to path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Contact Extraction", page_icon="📧", layout="wide")

st.title("📧 Contact Information Extraction")
st.markdown("Extract emails, phones, and other contact details from company websites")

# Import the refactored core module
try:
    from core.contact_extractor import ContactExtractor
    extractor_available = True
except ImportError as e:
    st.error(f"Error importing contact extractor: {str(e)}")
    extractor_available = False

# Main content area
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Input Options")
    
    # Input method selection
    input_method = st.radio(
        "Choose Input Method",
        ["Single URL", "CSV File", "Company Search Results"],
        help="Select how to provide websites for extraction"
    )
    
    if input_method == "Single URL":
        url_input = st.text_input(
            "Website URL",
            placeholder="https://example.com",
            help="Enter the full URL of the website"
        )
        
    elif input_method == "CSV File":
        # File upload
        uploaded_file = st.file_uploader(
            "Upload CSV File",
            type=['csv'],
            help="CSV should contain URL or Domain column"
        )
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.success(f"Loaded {len(df)} rows")
            
            # Column selection
            columns = df.columns.tolist()
            url_column = st.selectbox(
                "Select URL/Domain Column",
                options=columns,
                index=columns.index("Domain") if "Domain" in columns else 0
            )
    
    elif input_method == "Company Search Results":
        # List available company search results
        company_dir = os.path.join("output", "company")
        if os.path.exists(company_dir):
            csv_files = [f for f in os.listdir(company_dir) if f.endswith('.csv')]
            if csv_files:
                selected_file = st.selectbox(
                    "Select Company Search Result",
                    options=csv_files,
                    help="Choose from previous company search results"
                )
            else:
                st.warning("No company search results found. Please run a company search first.")
                selected_file = None
        else:
            st.warning("No output directory found. Please run a company search first.")
            selected_file = None
    
    # Extraction options
    with st.expander("Extraction Options"):
        visit_contact = st.checkbox(
            "Visit Contact Pages",
            value=False,
            help="Try to find and visit contact/about pages for better results"
        )
        
        use_llm = st.checkbox(
            "Use AI for Enhanced Extraction",
            value=os.getenv("LLM_PROVIDER", "none") != "none",
            help="Use LLM to improve contact information extraction accuracy"
        )
        
        headless = st.checkbox(
            "Run in Headless Mode",
            value=True,
            help="Run browser in background (faster but can't see what's happening)"
        )
        
        timeout = st.number_input(
            "Page Load Timeout (ms)",
            min_value=5000,
            max_value=60000,
            value=15000,
            step=5000,
            help="Maximum time to wait for page to load"
        )
    
    # Extract button
    extract_button = st.button("🔍 Start Extraction", type="primary", use_container_width=True)

# Results area
with col2:
    st.subheader("Extraction Results")
    
    if extract_button and extractor_available:
        # Validate input
        valid_input = False
        urls_to_process = []
        
        if input_method == "Single URL":
            if url_input:
                urls_to_process = [url_input]
                valid_input = True
            else:
                st.error("Please enter a URL")
                
        elif input_method == "CSV File":
            if 'df' in locals() and 'url_column' in locals():
                urls_to_process = df[url_column].dropna().tolist()
                valid_input = True
            else:
                st.error("Please upload a CSV file")
                
        elif input_method == "Company Search Results":
            if selected_file:
                file_path = os.path.join("output", "company", selected_file)
                df = pd.read_csv(file_path)
                
                # Try to find domain or URL column
                if "Domain" in df.columns:
                    urls_to_process = df["Domain"].dropna().tolist()
                elif "domain" in df.columns:
                    urls_to_process = df["domain"].dropna().tolist()
                elif "URL" in df.columns:
                    urls_to_process = df["URL"].dropna().tolist()
                elif "url" in df.columns:
                    urls_to_process = df["url"].dropna().tolist()
                else:
                    st.error("No Domain or URL column found in the selected file")
                    urls_to_process = []
                
                if urls_to_process:
                    valid_input = True
                    st.info(f"Found {len(urls_to_process)} URLs to process")
            else:
                st.error("Please select a company search result file")
        
        if valid_input and urls_to_process:
            # Initialize progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()
            
            # Process URLs
            all_results = []
            
            try:
                # Create extractor instance
                extractor = ContactExtractor(
                    headless=headless,
                    timeout=timeout,
                    visit_contact_page=visit_contact,
                    use_llm=use_llm
                )
                
                # Process each URL
                for i, url in enumerate(urls_to_process):
                    # Update progress
                    progress = (i + 1) / len(urls_to_process)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {i+1}/{len(urls_to_process)}: {url}")
                    
                    # Process URL
                    result = extractor.extract_from_url(url)
                    if result:
                        all_results.append(result)
                    
                    # Limit for demo (remove in production)
                    if i >= 4 and len(urls_to_process) > 5:
                        st.warning(f"Demo mode: Processing first 5 URLs only. {len(urls_to_process)-5} URLs skipped.")
                        break
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Display results
                if all_results:
                    with results_container:
                        st.success(f"✅ Extracted contact info from {len(all_results)} websites")
                        
                        # Convert to DataFrame
                        results_df = pd.DataFrame(all_results)
                        
                        # Display metrics
                        email_count = sum(1 for r in all_results if r.get('emails'))
                        phone_count = sum(1 for r in all_results if r.get('phones'))
                        social_count = sum(1 for r in all_results if r.get('social_media'))
                        
                        metrics = {
                            "Websites Processed": len(all_results),
                            "Emails Found": email_count,
                            "Phones Found": phone_count,
                            "Social Profiles": social_count
                        }
                        display_metrics(metrics)
                        
                        # Display results table
                        st.dataframe(
                            results_df,
                            use_container_width=True,
                            height=400,
                            hide_index=True
                        )
                        
                        # Download buttons
                        st.divider()
                        st.subheader("📥 Download Results")
                        
                        timestamp = int(time.time())
                        filename_prefix = f"contact_extraction_{timestamp}"
                        create_download_buttons(results_df, filename_prefix, "both")
                        
                        # Save results
                        output_file = extractor.save_results(all_results, filename_prefix)
                        st.info(f"💾 Results saved to: `{output_file}`")
                else:
                    st.warning("No contact information could be extracted")
                    
            except Exception as e:
                st.error(f"Error during extraction: {str(e)}")
            
            finally:
                # Clean up
                if 'extractor' in locals():
                    try:
                        extractor.close_browser()
                    except:
                        pass

# Sidebar
with st.sidebar:
    # API status
    display_api_status()
    
    # Usage tips
    show_usage_tips("contact_extraction")
    
    # Recent extractions
    st.divider()
    st.header("📁 Recent Extractions")
    
    contact_dir = os.path.join("output", "contact")
    if os.path.exists(contact_dir):
        csv_files = [f for f in os.listdir(contact_dir) if f.endswith('.csv')]
        csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(contact_dir, x)), reverse=True)
        
        if csv_files:
            recent_files = csv_files[:5]
            for file in recent_files:
                file_path = os.path.join(contact_dir, file)
                file_size = os.path.getsize(file_path) / 1024
                st.markdown(f"📄 {file[:30]}... ({file_size:.1f} KB)")
        else:
            st.info("No extraction results yet")