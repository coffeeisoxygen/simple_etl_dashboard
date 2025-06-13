import io
import os
import sqlite3
import sys
from datetime import datetime

import pandas as pd
import streamlit as st
from loguru import logger

# Global counter untuk tracking inisialisasi
_loguru_init_count = 0

# Setup Loguru (hanya dijalankan sekali saat modul diimport)
_loguru_init_count += 1
logger.remove()  # Remove default handler
logger.add(
    sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO"
)
logger.add(
    "logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG",
    rotation="10 MB",
)

logger.info(f"Module imported - Loguru configured (Init count: {_loguru_init_count})")
# TODO : something wrong here
# BUG :
# FIX
# REVIEW : this is the main file for ETL dashboard
# [x] todo : this is the sample of list showed
# TASK : Implement error handling for unsupported file formats
# TODO : [x] this should show in todo +


# ETL Functions
@st.cache_data
def process_uploaded_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """ETL processing untuk file yang diupload"""
    logger.info(f"Processing uploaded file: {filename}")

    try:
        # Extract - baca file berdasarkan extension
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Unsupported file format")

        logger.info(f"Extracted {len(df)} rows from {filename}")

        # Transform - cleaning dan processing
        df_cleaned = transform_data(df)

        logger.info(f"Transformed to {len(df_cleaned)} clean rows")
        return df_cleaned

    except Exception as e:
        logger.error(f"Error processing {filename}: {str(e)}")
        st.error(f"Error processing file: {str(e)}")
        return pd.DataFrame()


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform dan clean data"""
    logger.info("Starting data transformation")

    df_clean = df.copy()

    # 1. Remove duplicates
    initial_count = len(df_clean)
    df_clean = df_clean.drop_duplicates()
    duplicates_removed = initial_count - len(df_clean)

    # 2. Handle missing values
    df_clean = df_clean.dropna()

    # 3. Data type conversion
    for col in df_clean.columns:
        if "date" in col.lower():
            df_clean[col] = pd.to_datetime(df_clean[col], errors="coerce")
        elif df_clean[col].dtype == "object":
            # Try to convert to numeric
            numeric_col = pd.to_numeric(df_clean[col], errors="coerce")
            if not numeric_col.isna().all():
                df_clean[col] = numeric_col

    # 4. Add metadata
    df_clean["processed_at"] = datetime.now()
    df_clean["batch_id"] = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info(f"Transformation complete: removed {duplicates_removed} duplicates")
    return df_clean


def save_to_database(df: pd.DataFrame, table_name: str = "etl_data"):
    """Save processed data ke database"""
    if df.empty:
        return False

    try:
        # Ensure database directory exists
        os.makedirs("data", exist_ok=True)

        conn = sqlite3.connect("data/etl_database.db")
        df.to_sql(table_name, conn, if_exists="append", index=False)
        conn.close()

        logger.info(f"Saved {len(df)} rows to database table: {table_name}")
        return True

    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
        return False


@st.cache_data(ttl=300)  # Cache 5 menit
def load_from_database(table_name: str = "etl_data", limit: int = 1000):
    """Load data dari database when needed"""
    try:
        conn = sqlite3.connect("data/etl_database.db")

        query = f"""
        SELECT * FROM {table_name}
        ORDER BY processed_at DESC
        LIMIT {limit}
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        logger.info(f"Loaded {len(df)} rows from database")
        return df

    except Exception as e:
        logger.error(f"Error loading from database: {str(e)}")
        return pd.DataFrame()


def main():
    logger.info("Main function called - App rerun started")

    # Tampilkan berapa kali loguru diinisialisasi
    st.write(f"Loguru initialization count: {_loguru_init_count}")

    # === BAGIAN BARU: ETL Dashboard ===
    st.header("📊 ETL Dashboard")

    # Tabs untuk organize fitur
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload & ETL",
        "🔗 Query Params",
        "🔍 Context Info",
        "📋 Data View",
    ])

    with tab1:
        st.subheader("1. 📤 Upload Data")

        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            help="Upload your data file for ETL processing",
        )

        if uploaded_file is not None:
            st.success(
                f"File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔄 Process File", type="primary"):
                    with st.spinner("Processing file..."):
                        file_bytes = uploaded_file.getvalue()
                        processed_df = process_uploaded_file(
                            file_bytes, uploaded_file.name
                        )

                        if not processed_df.empty:
                            st.success(
                                f"✅ Processing complete! {len(processed_df)} rows ready"
                            )

                            # Store in session state
                            st.session_state.processed_data = processed_df

                            # Preview hasil ETL
                            st.subheader("📋 ETL Results Preview")
                            st.dataframe(processed_df.head())

                            # Data quality metrics
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Total Rows", len(processed_df))
                            with col_b:
                                st.metric("Columns", len(processed_df.columns))
                            with col_c:
                                null_count = processed_df.isnull().sum().sum()
                                st.metric("Null Values", null_count)
                        else:
                            st.error("❌ Failed to process file")

            with col2:
                if hasattr(st.session_state, "processed_data"):
                    if st.button("💾 Save to Database"):
                        with st.spinner("Saving to database..."):
                            success = save_to_database(st.session_state.processed_data)

                            if success:
                                st.success("✅ Data saved to database!")
                                st.session_state.data_saved = True
                            else:
                                st.error("❌ Failed to save data")

        # Load and display saved data
        st.subheader("📊 Load Saved Data")

        if st.button("🔍 Load Recent Data"):
            with st.spinner("Loading data..."):
                loaded_df = load_from_database()

                if not loaded_df.empty:
                    st.success(f"✅ Loaded {len(loaded_df)} rows")

                    # Store in session state for visualization
                    st.session_state.loaded_data = loaded_df

                    # Basic statistics
                    st.subheader("📈 Data Summary")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Records", f"{len(loaded_df):,}")
                    with col2:
                        unique_batches = (
                            loaded_df["batch_id"].nunique()
                            if "batch_id" in loaded_df.columns
                            else 0
                        )
                        st.metric("Batches", unique_batches)
                    with col3:
                        if "processed_at" in loaded_df.columns:
                            latest_date = loaded_df["processed_at"].max()
                            st.metric("Latest", latest_date.split()[0])
                    with col4:
                        numeric_cols = loaded_df.select_dtypes(
                            include=["number"]
                        ).columns
                        st.metric("Numeric Cols", len(numeric_cols))

                    # Show data sample
                    st.subheader("📋 Data Sample")
                    st.dataframe(loaded_df.head(10))

                    # Simple visualization if numeric data exists
                    if len(numeric_cols) > 0:
                        st.subheader("📊 Quick Chart")
                        chart_col = st.selectbox(
                            "Select column for chart", numeric_cols
                        )

                        if chart_col:
                            st.bar_chart(loaded_df[chart_col].head(20))
                else:
                    st.info("No data found. Upload and process some files first!")

    with tab2:
        # === Query Parameters Section (existing code) ===
        st.subheader("🔗 URL Query Parameters")

        # Tampilkan query params yang ada
        if st.query_params:
            st.write("**Current Query Parameters:**")
            for key, value in st.query_params.items():
                st.write(f"- `{key}`: `{value}`")
        else:
            st.write("No query parameters in URL")

        # Form untuk menambah query params
        with st.form("query_params_form"):
            st.write("**Add/Update Query Parameters:**")
            param_key = st.text_input("Parameter Key", value="page")
            param_value = st.text_input("Parameter Value", value="dashboard")

            col1, col2, col3 = st.columns(3)
            with col1:
                add_param = st.form_submit_button("Add/Update Param")
            with col2:
                clear_params = st.form_submit_button("Clear All Params")
            with col3:
                remove_param = st.form_submit_button("Remove This Param")

        # Handle form submissions
        if add_param and param_key:
            st.query_params[param_key] = param_value
            st.success(f"Added/Updated: {param_key} = {param_value}")
            logger.info(f"Query param added/updated: {param_key}={param_value}")
            st.rerun()

        if clear_params:
            st.query_params.clear()
            st.success("All query parameters cleared!")
            logger.info("All query parameters cleared")
            st.rerun()

        if remove_param and param_key and param_key in st.query_params:
            del st.query_params[param_key]
            st.success(f"Removed parameter: {param_key}")
            logger.info(f"Query param removed: {param_key}")
            st.rerun()

    with tab3:
        # === User Context Information (existing code) ===
        st.subheader("🔍 User Context Information")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**URL & Network Info:**")
            st.write(f"App URL: `{st.context.url}`")

            if st.context.ip_address:
                st.write(f"IP Address: `{st.context.ip_address}`")
                logger.debug(f"User IP: {st.context.ip_address}")
            else:
                st.write("IP Address: `localhost (development)`")

            # Headers yang berguna
            user_agent = st.context.headers.get("user-agent", "Not available")
            if user_agent != "Not available":
                browser_info = (
                    user_agent.split(")")[0] + ")"
                    if ") " in user_agent
                    else user_agent[:50] + "..."
                )
                st.write(f"Browser: `{browser_info}`")

        with col2:
            st.write("**Localization Info:**")
            st.write(f"Browser Locale: `{st.context.locale}`")
            st.write(f"Timezone: `{st.context.timezone}`")

            try:
                from datetime import datetime, timezone

                import pytz

                timezone_str = st.context.timezone or "UTC"
                tz = pytz.timezone(timezone_str)
                utc_now = datetime.now(timezone.utc)
                local_time = utc_now.astimezone(tz)
                st.write(f"Local Time: `{local_time.strftime('%Y-%m-%d %H:%M:%S')}`")
            except Exception as e:
                st.write(f"Local Time: Unable to calculate ({str(e)})")

        # Cookies analysis
        if st.context.cookies:
            with st.expander("🍪 Cookies Analysis"):
                for cookie_name, cookie_value in st.context.cookies.items():
                    display_value = (
                        cookie_value[:50] + "..."
                        if len(cookie_value) > 50
                        else cookie_value
                    )

                    if cookie_name == "ajs_anonymous_id":
                        st.write(f"**{cookie_name}** (Analytics): `{display_value}`")
                        st.caption("🔍 Segment.io analytics tracking")
                    elif cookie_name.startswith("Hm_"):
                        st.write(
                            f"**{cookie_name}** (Baidu Analytics): `{display_value}`"
                        )
                        st.caption("🔍 Baidu Analytics service")
                    elif cookie_name == "_streamlit_xsrf":
                        st.write(f"**{cookie_name}** (Security): `{display_value}`")
                        st.caption("🔒 CSRF protection token")
                    else:
                        st.write(f"**{cookie_name}**: `{display_value}`")
        else:
            st.write("🍪 No cookies available")

    with tab4:
        # === Session Information ===
        st.subheader("📋 Session Information")

        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx

            ctx = get_script_run_ctx()
            if ctx:
                session_id = ctx.session_id
                st.write(f"Session ID: `{session_id}`")
                logger.debug(f"Session ID retrieved: {session_id}")
        except Exception as e:
            st.write(f"Session ID: Unable to retrieve ({str(e)})")

        # Initialize session state
        if "counter" not in st.session_state:
            st.session_state.counter = 0

        if "user_settings" not in st.session_state:
            st.session_state.user_settings = {"theme": "light", "language": "id"}

        # Counter dan preferences
        st.session_state.counter += 1
        st.write(f"Page loaded {st.session_state.counter} times")

        # Theme selector
        theme = st.selectbox(
            "Theme",
            ["light", "dark"],
            index=0 if st.session_state.user_settings["theme"] == "light" else 1,
        )
        st.session_state.user_settings["theme"] = theme

        # Show session state status
        if hasattr(st.session_state, "data_saved") and st.session_state.data_saved:
            st.success("✅ Data saved in current session")

    logger.info("Dashboard render complete")


if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    main()
