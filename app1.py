import streamlit as st
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="Interactive Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Title ---
st.title("📊 Interactive Sales Dashboard")

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "Upload your sales file to begin",
    type=["csv", "xlsx"]
)

# --- Data Loading and Caching ---
@st.cache_data(ttl=600)
def load_data(file):
    try:
        file.seek(0)
        if file.name.endswith(".csv"):
            df = pd.read_csv(file, encoding="utf-8")
        elif file.name.endswith(".xlsx"):
            df = pd.read_excel(file, engine="openpyxl")
        else:
            st.error("❌ Unsupported file type. Please upload a CSV or Excel file.")
            return pd.DataFrame()
        return df
    except pd.errors.EmptyDataError:
        st.error("❌ The uploaded file is empty or invalid.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error while reading the file: {e}")
        return pd.DataFrame()

# --- Main Section ---
if uploaded_file is not None:
    df = load_data(uploaded_file)

    if not df.empty:
        st.subheader("📄 Raw Data Preview")
        st.dataframe(df.head())

        # --- Normalize column names ---
        df.columns = df.columns.str.strip().str.lower()

        # --- Flexible Sales/Revenue Handling ---
        if "sales" in df.columns:
            df["sales_amount"] = df["sales"]
        elif "revenue" in df.columns:
            df["sales_amount"] = df["revenue"]
        else:
            st.error("❌ Neither 'Sales' nor 'Revenue' column found in the file.")
            st.stop()

        # --- Determine Product Column ---
        product_column = None
        if "productline" in df.columns:
            product_column = "productline"
        elif "product_category" in df.columns:
            product_column = "product_category"
        elif "product" in df.columns:
            product_column = "product"
        elif "products" in df.columns:
            product_column = "products"

        # --- Determine Region/Country Column ---
        region_column = None
        if "region" in df.columns:
            region_column = "region"
        elif "country" in df.columns:
            region_column = "country"

        # --- Sidebar Filters ---
        st.sidebar.header("🔎 Filters")

        # Product Filter
        if product_column:
            product_filter = st.sidebar.multiselect(
                f"Select {product_column.replace('_', ' ').title()}(s):",
                options=df[product_column].unique(),
                default=df[product_column].unique()
            )
            df = df[df[product_column].isin(product_filter)]

        # Region or Country Filter
        if region_column:
            region_filter = st.sidebar.multiselect(
                f"Select {region_column.replace('_', ' ').title()}(s):",
                options=df[region_column].unique(),
                default=df[region_column].unique()
            )
            df = df[df[region_column].isin(region_filter)]

        # Status Filter (if exists)
        if "status" in df.columns:
            status_filter = st.sidebar.multiselect(
                "Select Status:",
                options=df["status"].unique(),
                default=df["status"].unique()
            )
            df = df[df["status"].isin(status_filter)]

        # Year Filter (if exists)
        if "year_id" in df.columns:
            year_filter = st.sidebar.multiselect(
                "Select Year(s):",
                options=sorted(df["year_id"].unique()),
                default=sorted(df["year_id"].unique())
            )
            df = df[df["year_id"].isin(year_filter)]

        # --- KPIs ---
        total_sales = df["sales_amount"].sum()
        avg_sales = df["sales_amount"].mean()
        num_transactions = df.shape[0]

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("💰 Total Sales", f"${total_sales:,.2f}")
        kpi2.metric("📈 Average Sales", f"${avg_sales:,.2f}")
        kpi3.metric("🧾 Transactions", f"{num_transactions:,}")

        st.markdown("---")

        # --- Sales by Product ---
        if product_column:
            sales_by_product = (
                df.groupby(product_column)["sales_amount"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
            )
            fig_product = px.bar(
                sales_by_product,
                x=product_column,
                y="sales_amount",
                title=f"💼 Sales by {product_column.replace('_', ' ').title()}",
                text_auto=True
            )
            st.plotly_chart(fig_product, use_container_width=True)

        # --- Sales by Region/Country ---
        if region_column:
            sales_by_region = (
                df.groupby(region_column)["sales_amount"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
            )
            fig_region = px.pie(
                sales_by_region,
                values="sales_amount",
                names=region_column,
                title=f"🌍 Sales by {region_column.replace('_', ' ').title()}"
            )
            st.plotly_chart(fig_region, use_container_width=True)

        # --- Sales Trend (Order Date) ---
        if "orderdate" in df.columns:
            df["orderdate"] = pd.to_datetime(df["orderdate"], errors="coerce")
            df = df.dropna(subset=["orderdate"])

            sales_trend = (
                df.groupby("orderdate")["sales_amount"]
                .sum()
                .reset_index()
                .sort_values("orderdate")
            )
            fig_trend = px.line(
                sales_trend,
                x="orderdate",
                y="sales_amount",
                title="📅 Sales Trend Over Time"
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    else:
        st.warning("⚠️ No data loaded. Please upload a valid file.")
else:
    st.info("📥 Please upload a CSV or Excel file to get started.")
