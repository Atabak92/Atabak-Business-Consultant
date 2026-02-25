import streamlit as st
import pandas as pd
from groq import Groq
from datetime import datetime
import os
# -----------------------------
# 1) Page Config + Simple Styling
# -----------------------------
st.set_page_config(page_title="Atabak Business Consultant", page_icon="👔", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #f4f6f9; }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.06);
        border-left: 5px solid #00838f;
    }
    .stButton button { width: 100%; border-radius: 10px; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("👔 Atabak Business Consultant Bot")
st.caption("AI-Powered Executive Management & Financial Strategy Advisor")
st.divider()

# -----------------------------
# 2) Session State
# -----------------------------
if "mode" not in st.session_state:
    st.session_state.mode = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""
if "data_profile" not in st.session_state:
    st.session_state.data_profile = ""  # textual summary of uploaded data (KPIs, etc.)


GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if GROQ_API_KEY is None:
    st.warning("Put your GROQ_API_KEY line back here (copy from your old code) to run.")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# 4) Helper: Prompts
# -----------------------------
GENERAL_SYSTEM_PROMPT = """
You are “Atabak Business Consultant”, a practical executive advisor.

SCOPE:
- Business strategy, management, finance, operations, startups, negotiation, leadership, pricing, go-to-market, budgeting, KPIs.

STRICT REFUSAL RULE:
If the user asks anything NOT related to business/management/finance/startups/workplace, reply EXACTLY:
"This question is not related to business or management. I cannot answer."

STYLE (very important):
- If needed, ask 2–4 clarifying questions before giving a recommendation.
- Avoid generic advice. Provide concrete actions, trade-offs, and examples.
- Use this structure:
  1) Situation (1–2 lines)
  2) Options (2–3) with pros/cons + risks
  3) Recommendation (one clear choice) + rationale
  4) 30/60/90-day action plan
  5) KPIs to track
Keep answers concise but executive-grade.
"""

def build_data_system_prompt(data_profile: str) -> str:
    return f"""
You are “Atabak Business Consultant”, an executive financial advisor for a manufacturing SME.

You MUST base your answers on the provided financial summary below.
If data is missing for a calculation, ask the user for the missing fields instead of inventing.

STRICT REFUSAL RULE:
If the user asks anything NOT related to business/management/finance/startups/workplace, reply EXACTLY:
"This question is not related to business or management. I cannot answer."

STYLE:
- Ask clarifying questions if needed.
- Provide options + recommendation + action plan + KPIs.
- Use numbers from the provided summary whenever relevant.

FINANCIAL SUMMARY:
{data_profile}
"""

# -----------------------------
# 5) Helper: Data Loading & KPI Summary
# -----------------------------
@st.cache_data(show_spinner=False)
def read_excel_sheets(file) -> list[str]:
    xls = pd.ExcelFile(file)
    return xls.sheet_names

@st.cache_data(show_spinner=False)
def read_sheet(file, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(file, sheet_name=sheet_name)

def safe_sum(series) -> float:
    return pd.to_numeric(series, errors="coerce").fillna(0).sum()

def make_data_profile(df_sales: pd.DataFrame, df_exp: pd.DataFrame) -> str:
    """
    Tries to build a useful KPI summary even if columns differ.
    Expected (preferred) columns:
      Sales: Total_Revenue, Date, Customer, Product
      Expenses: Amount, Date, Category
    """
    profile_lines = []

    # Revenue
    if "Total_Revenue" in df_sales.columns:
        total_revenue = safe_sum(df_sales["Total_Revenue"])
        profile_lines.append(f"- Total Revenue: {total_revenue:,.2f}")
    else:
        profile_lines.append("- Total Revenue: (missing column 'Total_Revenue')")

    # Expenses
    if "Amount" in df_exp.columns:
        total_exp = safe_sum(df_exp["Amount"])
        profile_lines.append(f"- Total Operating Expenses: {total_exp:,.2f}")
    else:
        profile_lines.append("- Total Operating Expenses: (missing column 'Amount')")

    # Profit & Margin
    if ("Total_Revenue" in df_sales.columns) and ("Amount" in df_exp.columns):
        net_profit = total_revenue - total_exp
        margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        profile_lines.append(f"- Net Profit: {net_profit:,.2f}")
        profile_lines.append(f"- Profit Margin: {margin:.2f}%")

    # Monthly trend (if Date exists)
    if "Date" in df_sales.columns and "Total_Revenue" in df_sales.columns:
        d = df_sales.copy()
        d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
        d = d.dropna(subset=["Date"])
        if len(d) > 0:
            d["Month"] = d["Date"].dt.to_period("M").astype(str)
            monthly = d.groupby("Month")["Total_Revenue"].sum().sort_index()
            if len(monthly) > 0:
                last3 = monthly.tail(3)
                profile_lines.append("- Revenue (last 3 months): " + ", ".join([f"{k}: {v:,.0f}" for k, v in last3.items()]))

    # Top customers
    if "Customer" in df_sales.columns and "Total_Revenue" in df_sales.columns:
        top_c = df_sales.groupby("Customer")["Total_Revenue"].sum().sort_values(ascending=False).head(5)
        if len(top_c) > 0:
            profile_lines.append("- Top Customers (by revenue): " + ", ".join([f"{idx} ({val:,.0f})" for idx, val in top_c.items()]))

    # Expense category mix
    if "Category" in df_exp.columns and "Amount" in df_exp.columns:
        mix = df_exp.groupby("Category")["Amount"].sum().sort_values(ascending=False).head(5)
        if len(mix) > 0:
            profile_lines.append("- Top Expense Categories: " + ", ".join([f"{idx} ({val:,.0f})" for idx, val in mix.items()]))

    return "\n".join(profile_lines)

# -----------------------------
# 6) Mode Selection
# -----------------------------
if st.session_state.mode is None:
    st.subheader("Please select the consultation mode:")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 I have Financial Data (Excel Analysis)"):
            st.session_state.mode = "data"
            st.session_state.messages = []
            st.session_state.system_prompt = ""
            st.session_state.data_profile = ""
            st.rerun()

    with col2:
        if st.button("💬 No Data (General Business Consulting)"):
            st.session_state.mode = "general"
            st.session_state.system_prompt = GENERAL_SYSTEM_PROMPT
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello. I am the Atabak Business Consultant. Ask your business, management, finance, or startup question."}
            ]
            st.rerun()

# -----------------------------
# 7) DATA MODE UI + KPI
# -----------------------------
if st.session_state.mode == "data":
    uploaded_file = st.file_uploader("📁 Upload the factory's financial data (Excel format)", type=["xlsx"])

    if uploaded_file:
        sheet_names = read_excel_sheets(uploaded_file)

        st.caption("Select which sheets contain Sales and Expenses (names can vary).")
        cA, cB = st.columns(2)
        with cA:
            sales_sheet = st.selectbox("Sales sheet", sheet_names, index=0)
        with cB:
            exp_sheet = st.selectbox("Expenses sheet", sheet_names, index=min(1, len(sheet_names)-1))

        try:
            df_sales = read_sheet(uploaded_file, sales_sheet)
            df_exp = read_sheet(uploaded_file, exp_sheet)

            # Basic metrics if columns exist
            total_revenue = safe_sum(df_sales["Total_Revenue"]) if "Total_Revenue" in df_sales.columns else None
            total_expenses = safe_sum(df_exp["Amount"]) if "Amount" in df_exp.columns else None

            st.subheader("📊 Financial Overview")
            c1, c2, c3, c4 = st.columns(4)

            if total_revenue is not None:
                c1.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
            else:
                c1.metric("💰 Total Revenue", "N/A")

            if total_expenses is not None:
                c2.metric("📉 Operating Expenses", f"${total_expenses:,.0f}")
            else:
                c2.metric("📉 Operating Expenses", "N/A")

            if (total_revenue is not None) and (total_expenses is not None):
                net_profit = total_revenue - total_expenses
                profit_margin = (net_profit / total_revenue) * 100 if total_revenue > 0 else 0
                c3.metric("💵 Net Profit", f"${net_profit:,.0f}")
                c4.metric("📈 Profit Margin", f"{profit_margin:.1f}%")
            else:
                c3.metric("💵 Net Profit", "N/A")
                c4.metric("📈 Profit Margin", "N/A")

            st.divider()

            # Build data profile summary (KPIs) for the model
            data_profile = make_data_profile(df_sales, df_exp)
            st.session_state.data_profile = data_profile

            with st.expander("🔎 Data summary sent to the AI (KPIs)"):
                st.code(data_profile)

            if not st.session_state.system_prompt:
                st.session_state.system_prompt = build_data_system_prompt(data_profile)
                st.session_state.messages = [
                    {"role": "assistant", "content": "Your data has been analyzed. Ask your management/finance questions and I will answer using the KPI summary above."}
                ]

        except Exception as e:
            st.error(f"Error processing file: {e}")

# -----------------------------
# 8) Chat Rendering + Completion Call
# -----------------------------
if st.session_state.mode in ["general", "data"]:
    if st.session_state.mode == "data" and not st.session_state.system_prompt:
        st.warning("Please upload the Excel file first to activate the consulting system.")
    else:
        # Render chat
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        # Input
        if prompt := st.chat_input("Ask your business or management question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            try:
                # Send a bit more history for consistency
                history = st.session_state.messages[-12:]

                ai_payload = [{"role": "system", "content": st.session_state.system_prompt}] + history

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=ai_payload,
                    temperature=0.2,
                    max_tokens=900
                )

                bot_reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                st.chat_message("assistant").write(bot_reply)

            except Exception as e:
                st.error(f"Error: {e}")