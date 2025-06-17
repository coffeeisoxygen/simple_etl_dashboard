"""Page for uploading and processing CSV/Excel files."""

import pandas as pd
import streamlit as st
from stqdm import stqdm

# st.set_page_config(
#     page_title="Upload Laporan",
#     page_icon="📁",
#     layout="centered",
# )

st.title("📁 Upload & Proses Laporan")

# ✅ Section 1: File Upload
with st.container():
    st.markdown("### 📤 Upload Files")
    uploaded_files = st.file_uploader(
        "Select CSV/Excel Files",
        type=["csv", "xls", "xlsx"],
        accept_multiple_files=True,
        help="Bisa upload banyak file sekaligus",
        label_visibility="collapsed",
    )

# ✅ Section 2: Configuration (Only show if files uploaded)
if uploaded_files:
    st.markdown("### ⚙️ Configuration")

    # Two column layout for better organization
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📋 File & Database Settings**")
        jenis_file = st.selectbox(
            "File Type",
            ["Transaksi", "Komisi", "Retailer", "Penjualan", "Lainnya"],
            help="Select the type of data you're uploading",
        )

        table_header = st.text_input(
            "Database Table Name",
            placeholder="e.g: sales_header",
            help="Name for the database table",
        )

    with col2:
        st.markdown("**🔧 Processing Options**")

        # Group checkboxes in a container for better visual hierarchy
        with st.container():
            auto_detect = st.checkbox(
                "🔍 Auto detect file names",
                value=True,
                help="Automatically extract information from filename",
            )
            detect_laporan = st.checkbox(
                "📂 Auto detect report type",
                value=True,
                help="Automatically categorize report based on content",
            )

    # ✅ Section 3: Action Buttons (centered)
    st.markdown("---")

    # Center the process button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("▶️ Proses Data", use_container_width=True, type="primary"):
            if not uploaded_files:
                st.warning("⚠️ Belum ada file yang diupload")
            elif not table_header:
                st.warning("⚠️ Header table harus diisi")
            else:
                data_preview = []

                with st.spinner("⏳ Memproses file..."):
                    for file in stqdm(uploaded_files, desc="Memproses"):
                        filename = file.name

                        if filename.endswith(".csv"):
                            df = pd.read_csv(file)
                        else:
                            df = pd.read_excel(file)

                        # Apply processing options
                        if detect_laporan:
                            df["detected_laporan"] = jenis_file

                        if auto_detect:
                            df["source_file"] = filename

                        data_preview.append((filename, df))

                st.success("✅ Semua file berhasil diproses!")

                # ✅ Section 4: Preview Results
                with st.expander("👀 Preview Data", expanded=True):
                    for fname, df in data_preview:
                        st.markdown(f"**📄 {fname}**")
                        st.dataframe(df.head(10), use_container_width=True)

                # ✅ Section 5: Save Data
                st.markdown("---")
                col_save1, col_save2, col_save3 = st.columns([1, 2, 1])
                with col_save2:
                    if st.button(
                        "💾 Simpan ke Database",
                        use_container_width=True,
                        type="secondary",
                    ):
                        st.success("✅ Data disimpan ke database (demo)")
                        # TODO: implement actual database save
else:
    # Show helpful message when no files uploaded
    st.info("📁 Upload file CSV atau Excel untuk memulai proses ETL")


# NOTE: This page handles file upload and basic ETL processing
# TODO: Implement actual database integration
# PINNED: Add data validation and error handling
# REMINDER: Support multiple file formats and large files
