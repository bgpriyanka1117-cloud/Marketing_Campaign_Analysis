import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="📊 Marketing Analytics Pro + SQL Runner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://streamlit.io",
        "Report a bug": None,
        "About": "Marketing Analytics Dashboard + SQL Runner by Priyanka Kumari 🚀"
    }
)

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    return pd.read_csv("../data/EDA_Analysis.csv")

df = load_data()

# =========================
# FEATURE ENGINEERING
# =========================
df["Age_Band"] = pd.cut(df["Age"], bins=[0, 30, 45, 60, 100],
                        labels=["<30", "30-45", "45-60", "60+"])

df["Income_Band"] = pd.cut(df["Income"], bins=[0, 30000, 60000, 90000, 200000],
                           labels=["Low", "Mid", "High", "Very High"])

# =========================
# SIDEBAR MODE SWITCH
# =========================
st.sidebar.title("⚙ Navigation")
mode = st.sidebar.radio("Choose Mode", ["📊 Dashboard", "🗄 SQL Query Runner"])

# =========================
# =========================
# 📊 DASHBOARD MODE
# =========================
# =========================
if mode == "📊 Dashboard":

    st.title("📊 Marketing Campaign Dashboard")
    st.markdown("---")

    # Filters
    st.sidebar.subheader("🎛 Filters")

    country = st.sidebar.multiselect("Country", df["Country"].unique(), df["Country"].unique())
    education = st.sidebar.multiselect("Education", df["Education"].unique(), df["Education"].unique())
    marital = st.sidebar.multiselect("Marital Status", df["Marital_Status"].unique(), df["Marital_Status"].unique())
    age_band = st.sidebar.multiselect("Age Band", df["Age_Band"].dropna().unique(), df["Age_Band"].dropna().unique())
    income_band = st.sidebar.multiselect("Income Band", df["Income_Band"].dropna().unique(), df["Income_Band"].dropna().unique())

    df_f = df[
        (df["Country"].isin(country)) &
        (df["Education"].isin(education)) &
        (df["Marital_Status"].isin(marital)) &
        (df["Age_Band"].isin(age_band)) &
        (df["Income_Band"].isin(income_band))
    ]

    # KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers", f"{df_f.shape[0]:,}")
    c2.metric("Avg Income", f"${df_f['Income'].mean():,.0f}")
    c3.metric("Avg Spend", f"${df_f['Total_Spend'].mean():,.0f}")
    c4.metric("Response Rate", f"{df_f['Response'].mean()*100:.1f}%")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Spending", "Response", "Segments"])

    # -------- TAB 1 --------
    with tab1:
        st.subheader("Customer Overview")

        fig = px.histogram(df_f, x="Income")
        st.plotly_chart(fig, use_container_width=True)

        fig = px.histogram(df_f, x="Age")
        st.plotly_chart(fig, use_container_width=True)

        fig = px.histogram(df_f, x="Total_Spend")
        st.plotly_chart(fig, use_container_width=True)

    # -------- TAB 2 --------
    with tab2:
        st.subheader("Spending Analysis")

        fig = px.scatter(df_f, x="Income", y="Total_Spend", color="Response",
                         size="Total_Purchases", hover_data=["Age", "Country"])
        st.plotly_chart(fig, use_container_width=True)

        fig = px.box(df_f, x="Age_Band", y="Total_Spend")
        st.plotly_chart(fig, use_container_width=True)

    # -------- TAB 3 --------
    with tab3:
        st.subheader("Response Analysis")

        fig = px.box(df_f, x="Response", y="Income")
        st.plotly_chart(fig, use_container_width=True)

        fig = px.box(df_f, x="Response", y="Recency")
        st.plotly_chart(fig, use_container_width=True)

    # -------- TAB 4 --------
    with tab4:
        st.subheader("Segments")

        segment = st.selectbox(
            "Select Segment",
            ["Customer_Segment", "Spending_Segment", "Engagement_Segment", "Response_Segment"]
        )

        seg = df_f[segment].value_counts().reset_index()
        seg.columns = [segment, "Count"]

        fig = px.bar(seg, x=segment, y="Count", color=segment)
        st.plotly_chart(fig, use_container_width=True)
    

    # MAP
    st.markdown("---")
    st.subheader("🌍 Country Map")

    map_df = df_f.groupby("Country", as_index=False).mean(numeric_only=True)

    fig = px.choropleth(
        map_df,
        locations="Country",
        locationmode="country names",
        color="Total_Spend",
        hover_data=["Income", "Response"]
    )
    st.plotly_chart(fig, use_container_width=True)

     # =========================
    # 📄 AUTO REPORT SECTION
    # =========================
    st.markdown("---")
    st.subheader("📄 Auto Business Insights Report")

    if df_f.empty:
        st.warning("No data available for selected filters.")
    else:

        def safe_mode(col):
            m = df_f[col].mode()
            return m.iloc[0] if not m.empty else "N/A"

        def safe_mean(col):
            return df_f[col].mean() if len(df_f) > 0 else 0

        report = f"""
📊 MARKETING ANALYTICS REPORT
=============================

👥 CUSTOMER OVERVIEW
- Total Customers: {df_f.shape[0]}
- Top Country: {safe_mode("Country")}
- Top Education: {safe_mode("Education")}
- Top Marital Status: {safe_mode("Marital_Status")}

💰 FINANCIAL INSIGHTS
- Avg Income: ${safe_mean("Income"):,.2f}
- Avg Spending: ${safe_mean("Total_Spend"):,.2f}

🛒 BEHAVIOR INSIGHTS
- Avg Purchases: {safe_mean("Total_Purchases"):,.2f}
- Avg Recency: {safe_mean("Recency"):,.2f}

🎯 CAMPAIGN PERFORMANCE
- Response Rate: {safe_mean("Response")*100:.2f}%
"""

        st.text_area("Generated Report", report, height=300)

        st.download_button(
            label="📥 Download Report",
            data=report,
            file_name="marketing_insights_report.txt",
            mime="text/plain"
        )


# =========================
# =========================
# 🗄 SQL RUNNER MODE
# =========================
# =========================
elif mode == "🗄 SQL Query Runner":

    st.title("🗄 MySQL Query Runner App")

    def get_connection():
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="mysql",
            database="Marketing_campaign_analysis_DB",
            port=3305
        )

    query = st.text_area("Write SQL Query", height=150)

    if st.button("Run Query"):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query)

            if query.strip().lower().startswith("select"):
                rows = cursor.fetchall()
                cols = [c[0] for c in cursor.description]
                df_sql = pd.DataFrame(rows, columns=cols)

                st.success("Query executed successfully")
                st.dataframe(df_sql)
            else:
                conn.commit()
                st.success("Query executed (No output)")

            cursor.close()
            conn.close()

        except Exception as e:
            st.error(f"Error: {e}")


# =========================
# FOOTER
# =========================
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:15px;
background:linear-gradient(90deg,#0f2027,#203a43,#2c5364);
color:white; border-radius:10px;">
🚀 Developed by <b style="color:#00d4ff;">Priyanka Kumari</b> <br>
📊 Marketing Analytics + SQL Runner App
</div>
""", unsafe_allow_html=True)