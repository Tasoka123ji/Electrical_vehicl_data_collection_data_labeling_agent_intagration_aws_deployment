import streamlit as st
import pandas as pd
import os
from google import genai
from google.genai import types
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------
st.set_page_config(
    page_title="EV Synthetic Data Explorer 2026",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stDataFrame {
        border-radius: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------
# 2. API & MODEL INITIALIZATION
# --------------------------------
API_KEY = os.getenv("Gemin_api") 
if API_KEY:
    client = genai.Client(api_key=API_KEY)
    MODEL_ID = "gemini-2.0-flash"
else:
    client = None
    st.warning("⚠️ Gemini API key not found. Chat functionality will be limited.")

# --------------------------------
# 3. DATA LOADING & NORMALIZATION
# --------------------------------
DATA_DIR = "./data"

@st.cache_data
def load_data():
    """Load and normalize all datasets"""
    try:
        # Load datasets
        base_df = pd.read_csv(
            "/home/karen/Desktop/data_collection/data/datasets--UrvishAhir1--Electric-Vehicle-Specs-Dataset-2025/snapshots/0f0663f5365230357a815f23eb815796bce15b64/electric_vehicles_spec_2025.csv"
        )
        gpt_df = pd.read_csv(f"{DATA_DIR}/gpt_ev_prompt_with_responses.csv")
        gemini_df = pd.read_csv(f"{DATA_DIR}/gemini_ev_prompt_with_responses.csv")

        # Cleanup column names
        for df in [base_df, gpt_df, gemini_df]:
            df.columns = df.columns.str.strip()
            if "brand" in df.columns:
                df["brand"] = df["brand"].astype(str).str.strip()

        # Normalize response columns
        if "gpt_response" in gpt_df.columns:
            gpt_df["response_text"] = gpt_df["gpt_response"]
        elif "response" in gpt_df.columns:
            gpt_df["response_text"] = gpt_df["response"]
            
        if "gemini_response" in gemini_df.columns:
            gemini_df["response_text"] = gemini_df["gemini_response"]
        elif "response" in gemini_df.columns:
            gemini_df["response_text"] = gemini_df["response"]

        # Add source labels
        gpt_df["source_model"] = "GPT"
        gemini_df["source_model"] = "Gemini"

        return base_df, gpt_df, gemini_df
    except Exception as e:
        st.error(f"⚠️ Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Load data
base_df, gpt_df, gemini_df = load_data()

# --------------------------------
# 4. HELPER FUNCTIONS
# --------------------------------
def create_summary_stats(df):
    """Create summary statistics cards"""
    if df.empty:
        return {}
    
    stats = {
        "Total Records": len(df),
        "Unique Brands": df["brand"].nunique() if "brand" in df.columns else 0,
        "Unique Models": df["model"].nunique() if "model" in df.columns else 0,
    }
    
    # Add more specific stats if columns exist
    if "range" in df.columns:
        stats["Avg Range (km)"] = f"{df['range'].mean():.0f}"
    if "battery_capacity" in df.columns:
        stats["Avg Battery (kWh)"] = f"{df['battery_capacity'].mean():.1f}"
        
    return stats

def create_brand_distribution_chart(df):
    """Create interactive brand distribution chart"""
    if df.empty or "brand" not in df.columns:
        return None
    
    brand_counts = df["brand"].value_counts().reset_index()
    brand_counts.columns = ["Brand", "Count"]
    
    fig = px.bar(
        brand_counts.head(15),
        x="Brand",
        y="Count",
        title="Top 15 Brands by Vehicle Count",
        color="Count",
        color_continuous_scale="viridis"
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400
    )
    return fig

def create_comparison_chart(gpt_df, gem_df):
    """Create comparison chart between GPT and Gemini responses"""
    if gpt_df.empty or gem_df.empty:
        return None
    
    data = {
        "Model": ["GPT", "Gemini"],
        "Response Count": [len(gpt_df), len(gem_df)]
    }
    
    if "prompt_type" in gpt_df.columns and "prompt_type" in gem_df.columns:
        data["Unique Prompt Types"] = [
            gpt_df["prompt_type"].nunique(),
            gem_df["prompt_type"].nunique()
        ]
    
    df_comparison = pd.DataFrame(data)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Response Count',
        x=df_comparison["Model"],
        y=df_comparison["Response Count"],
        marker_color=['#667eea', '#764ba2']
    ))
    
    fig.update_layout(
        title="GPT vs Gemini Response Statistics",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=350
    )
    return fig

def apply_filters(df, brand, prompt_type):
    """Apply filters to dataframe"""
    if df.empty:
        return df
    
    filtered = df.copy()
    
    if brand != "All Brands" and "brand" in filtered.columns:
        filtered = filtered[filtered["brand"] == brand]
    
    if prompt_type != "All Types" and "prompt_type" in filtered.columns:
        filtered = filtered[filtered["prompt_type"] == prompt_type]
    
    return filtered

def get_enhanced_context(base_df, gpt_df, gem_df, query):
    """Get enhanced context for RAG including all data"""
    context_parts = []
    
    # Add summary statistics
    context_parts.append(f"Dataset Overview:")
    context_parts.append(f"- Base dataset: {len(base_df)} vehicles")
    context_parts.append(f"- GPT responses: {len(gpt_df)} entries")
    context_parts.append(f"- Gemini responses: {len(gem_df)} entries")
    
    # Add sample from base dataset
    if not base_df.empty:
        context_parts.append("\nBase Dataset Sample (first 20 rows):")
        context_parts.append(base_df.head(20).to_string())
    
    # Add relevant synthetic data based on query
    combined_synthetic = pd.concat([gpt_df, gem_df], ignore_index=True)
    
    # Try to find relevant rows based on query keywords
    query_lower = query.lower()
    relevant_mask = combined_synthetic.apply(
        lambda row: any(str(val).lower().find(query_lower) > -1 for val in row if pd.notna(val)),
        axis=1
    )
    
    relevant_data = combined_synthetic[relevant_mask].head(20)
    
    if not relevant_data.empty:
        context_parts.append("\nRelevant Synthetic Data:")
        context_parts.append(relevant_data.to_string())
    else:
        # If no relevant data found, include sample
        context_parts.append("\nSynthetic Data Sample (first 20 rows):")
        context_parts.append(combined_synthetic.head(20).to_string())
    
    return "\n".join(context_parts)

# --------------------------------
# 5. SIDEBAR FILTERS
# --------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/electric-car.png", width=100)
    st.title("🔍 Filters & Settings")
    
    st.markdown("---")
    
    # Brand filter
    brand_list = ["All Brands"]
    if not base_df.empty and "brand" in base_df.columns:
        brand_list += sorted(base_df["brand"].unique().tolist())
    selected_brand = st.selectbox("🏷️ Select Brand", brand_list)

    # Prompt type filter
    prompt_types = ["All Types"]
    avail_prompts = []
    if not gpt_df.empty and "prompt_type" in gpt_df.columns:
        avail_prompts += gpt_df["prompt_type"].unique().tolist()
    if not gemini_df.empty and "prompt_type" in gemini_df.columns:
        avail_prompts += gemini_df["prompt_type"].unique().tolist()
    prompt_types += sorted(list(set(avail_prompts)))
    
    selected_type = st.selectbox("📝 Prompt Type", prompt_types)
    
    st.markdown("---")
    
    # Display settings
    st.subheader("⚙️ Display Settings")
    show_charts = st.checkbox("Show Charts", value=True)
    rows_per_page = st.slider("Rows per page", 10, 100, 20)
    
    st.markdown("---")
    st.caption("💡 Tip: Use filters to narrow down your analysis")

# --------------------------------
# 6. APPLY FILTERS
# --------------------------------
base_filtered = apply_filters(base_df, selected_brand, selected_type)
gpt_filtered = apply_filters(gpt_df, selected_brand, selected_type)
gem_filtered = apply_filters(gemini_df, selected_brand, selected_type)

# --------------------------------
# 7. MAIN UI
# --------------------------------
st.markdown('<h1 class="main-header">⚡ EV Synthetic Data Explorer 2026</h1>', unsafe_allow_html=True)

# Summary Statistics
st.subheader("📊 Overview Statistics")
col1, col2, col3, col4 = st.columns(4)

stats = create_summary_stats(base_filtered)
metrics = list(stats.items())

if len(metrics) > 0:
    col1.metric(metrics[0][0], metrics[0][1])
if len(metrics) > 1:
    col2.metric(metrics[1][0], metrics[1][1])
if len(metrics) > 2:
    col3.metric(metrics[2][0], metrics[2][1])
if len(metrics) > 3:
    col4.metric(metrics[3][0], metrics[3][1])

st.markdown("---")

# --------------------------------
# 8. TABS
# --------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Data Explorer", 
    "⚖️ AI Model Comparison", 
    "💬 Expert Chat",
    "📈 Analytics Dashboard"
])

# --- TAB 1: DATA EXPLORER ---
with tab1:
    st.subheader("🗂️ Master Dataset")
    
    if show_charts:
        chart = create_brand_distribution_chart(base_filtered)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
    
    # Search functionality
    search_term = st.text_input("🔍 Search in data", placeholder="Enter brand, model, or any keyword...")
    
    display_df = base_filtered.copy()
    if search_term:
        mask = display_df.apply(
            lambda row: row.astype(str).str.contains(search_term, case=False).any(),
            axis=1
        )
        display_df = display_df[mask]
    
    st.info(f"Showing {len(display_df)} of {len(base_filtered)} records")
    
    # Display with pagination
    st.dataframe(
        display_df.head(rows_per_page),
        use_container_width=True,
        height=500
    )
    
    # Download button
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data",
        data=csv,
        file_name=f"ev_data_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

# --- TAB 2: AI COMPARISON ---
with tab2:
    st.subheader("⚖️ Synthetic Content Comparison")
    
    if show_charts:
        comparison_chart = create_comparison_chart(gpt_filtered, gem_filtered)
        if comparison_chart:
            st.plotly_chart(comparison_chart, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    cols_to_show = ["brand", "model", "prompt_type", "response_text"]
    
    with col1:
        st.markdown("### 🤖 GPT Model")
        st.caption(f"Total responses: {len(gpt_filtered)}")
        
        existing_cols = [c for c in cols_to_show if c in gpt_filtered.columns]
        if existing_cols:
            st.dataframe(
                gpt_filtered[existing_cols].head(rows_per_page),
                use_container_width=True,
                height=500
            )
        else:
            st.warning("Missing required columns in GPT data")
            st.info("Available columns: " + ", ".join(gpt_filtered.columns.tolist()))

    with col2:
        st.markdown("### 💎 Gemini Model")
        st.caption(f"Total responses: {len(gem_filtered)}")
        
        existing_cols_gem = [c for c in cols_to_show if c in gem_filtered.columns]
        if existing_cols_gem:
            st.dataframe(
                gem_filtered[existing_cols_gem].head(rows_per_page),
                use_container_width=True,
                height=500
            )
        else:
            st.warning("Missing required columns in Gemini data")
            st.info("Available columns: " + ", ".join(gem_filtered.columns.tolist()))
    
    # Side-by-side comparison
    st.markdown("---")
    st.subheader("🔬 Side-by-Side Analysis")
    
    if not gpt_filtered.empty and not gem_filtered.empty:
        comparison_row = st.number_input(
            "Select row number for detailed comparison",
            min_value=0,
            max_value=min(len(gpt_filtered), len(gem_filtered)) - 1,
            value=0
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**GPT Response**")
            if "response_text" in gpt_filtered.columns:
                st.text_area(
                    "GPT",
                    gpt_filtered.iloc[comparison_row]["response_text"],
                    height=200,
                    label_visibility="collapsed"
                )
        
        with col2:
            st.markdown("**Gemini Response**")
            if "response_text" in gem_filtered.columns:
                st.text_area(
                    "Gemini",
                    gem_filtered.iloc[comparison_row]["response_text"],
                    height=200,
                    label_visibility="collapsed"
                )

# --- TAB 3: EXPERT CHAT ---
with tab3:
    st.subheader("💬 AI Expert Assistant")
    st.caption("Ask questions about your EV data - I can analyze all datasets!")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Clear chat button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask anything about the EV data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            if client:
                with st.spinner("🤔 Analyzing your data..."):
                    try:
                        # Get enhanced context from ALL data
                        context = get_enhanced_context(base_filtered, gpt_filtered, gem_filtered, prompt)
                        
                        # Create comprehensive system instruction
                        system_instruction = """You are an expert EV data analyst with deep knowledge of electric vehicles.
                        
Your role:
- Analyze the provided EV datasets (base data and synthetic responses)
- Answer questions with specific data insights and statistics
- Compare GPT and Gemini synthetic responses when relevant
- Provide actionable insights and recommendations
- Use exact numbers and facts from the data
- Be concise but thorough

When analyzing:
- Reference specific brands, models, and values
- Calculate statistics when needed
- Identify patterns and trends
- Compare different data sources
- Highlight interesting findings"""
                        
                        response = client.models.generate_content(
                            model=MODEL_ID,
                            contents=f"{context}\n\nUser Question: {prompt}",
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                temperature=0.7,
                                top_p=0.95,
                                max_output_tokens=2048
                            )
                        )
                        
                        answer = response.text
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        
                    except Exception as e:
                        error_msg = f"❌ Error generating response: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                error_msg = "⚠️ Gemini API is not configured. Please set the GEMINI_API_KEY environment variable."
                st.warning(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Example questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        - What are the top 5 EV brands by vehicle count?
        - Compare the average battery capacity across different brands
        - What's the difference between GPT and Gemini responses for [specific brand]?
        - Which models have the longest range?
        - Analyze the distribution of vehicle types
        - What insights can you provide about [specific brand]'s lineup?
        """)

# --- TAB 4: ANALYTICS DASHBOARD ---
with tab4:
    st.subheader("📈 Advanced Analytics")
    
    if not base_filtered.empty:
        # Create multiple visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Vehicle count by brand (pie chart)
            if "brand" in base_filtered.columns:
                brand_data = base_filtered["brand"].value_counts().head(10)
                fig_pie = px.pie(
                    values=brand_data.values,
                    names=brand_data.index,
                    title="Top 10 Brands - Market Share"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Range distribution (if available)
            if "range" in base_filtered.columns:
                fig_hist = px.histogram(
                    base_filtered,
                    x="range",
                    title="Range Distribution (km)",
                    nbins=30
                )
                st.plotly_chart(fig_hist, use_container_width=True)
        
        # Additional analytics
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if "battery_capacity" in base_filtered.columns:
                fig_box = px.box(
                    base_filtered,
                    y="battery_capacity",
                    title="Battery Capacity Distribution (kWh)"
                )
                st.plotly_chart(fig_box, use_container_width=True)
        
        with col2:
            # Prompt type distribution for synthetic data
            combined = pd.concat([gpt_filtered, gem_filtered], ignore_index=True)
            if "prompt_type" in combined.columns and "source_model" in combined.columns:
                fig_bar = px.bar(
                    combined.groupby(["prompt_type", "source_model"]).size().reset_index(name="count"),
                    x="prompt_type",
                    y="count",
                    color="source_model",
                    title="Prompt Types by AI Model",
                    barmode="group"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No data available for analytics. Adjust your filters to see visualizations.")

# --------------------------------
# 9. FOOTER
# --------------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>⚡ EV Synthetic Data Explorer 2026 | Built with Streamlit & Gemini AI</p>
    <p style='font-size: 0.8rem;'>Data updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)