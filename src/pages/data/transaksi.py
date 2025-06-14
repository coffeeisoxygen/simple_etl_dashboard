# """Page untuk laporan transaksi - sederhana dengan date filter dan overview metrics."""

# import pandas as pd
# import streamlit as st
# from loguru import logger

# from utils.csv_processor import combine_daily_files, load_sample_files

# # Config untuk transaksi
# TRANSAKSI_CONFIG = {
#     "header_signature": ["DateTime", "Transaction Type", "Channel"],
#     "expected_headers": [
#         "DateTime",
#         "Transaction Type",
#         "Channel",
#         "Region",
#         "Area",
#         "Sales Area",
#         "Cluster",
#         "Additional Territory",
#         "Transaction ID",
#         "Transaction Channel",
#         "Organization Type",
#         "Organization ID",
#         "Organization Name",
#         "Operator ID",
#         "Operator Name",
#         "Operator Type",
#         "MSISDN",
#         "User Name",
#         "B# MSISDN",
#         "Dompetku MSISDN",
#         "Product Group",
#         "Product Name",
#         "Voucher Type",
#         "Bill Company",
#         "Bill Number",
#         "Main Price",
#         "Discount(IDR)",
#         "Amount_Debit(IDR)",
#         "Final transaction status",
#         "Surrouding Status",
#         "Reversal Transaction ID",
#         "Reversed DateTime",
#         "Reversed Status",
#         "ACommissionResult",
#         "BCommissionResult",
#         "ADIscountResult",
#         "BDiscountResult",
#         "DiscountRuleName",
#         "CommissionSchema",
#         "MSISDNTerritoryVerificationResult",
#         "A_LAC",
#         "A_CI",
#         "B_LAC",
#         "B_CI",
#         "Wallet Type",
#         "SP Status",
#         "Service Type",
#     ],
# }


# def load_sample_data():
#     """Load sample data untuk testing."""
#     if "transaksi_data_loaded" in st.session_state:
#         return

#     try:
#         sample_files = load_sample_files("temp/sample/ds_transaksi_jan_25/CSV")

#         if sample_files:
#             with st.spinner("Loading sample transaksi data..."):
#                 df = combine_daily_files(sample_files, TRANSAKSI_CONFIG)

#                 # Convert DateTime column untuk filtering
#                 if "DateTime" in df.columns:
#                     df["DateTime"] = pd.to_datetime(df["DateTime"])
#                     df["Date"] = df["DateTime"].dt.date

#                 st.session_state.transaksi_data = df
#                 st.session_state.transaksi_data_loaded = True
#                 logger.info(f"Sample transaksi data berhasil dimuat: {len(df)} rows")
#         else:
#             st.session_state.transaksi_data = pd.DataFrame()
#             st.session_state.transaksi_data_loaded = True
#             logger.warning("Tidak ada sample transaksi files ditemukan")

#     except Exception as e:
#         st.session_state.transaksi_data = pd.DataFrame()
#         st.session_state.transaksi_data_loaded = True
#         logger.error(f"Error loading sample data: {str(e)}")
#         st.error(f"Error loading data: {str(e)}")


# def apply_date_filter(df: pd.DataFrame):
#     """Apply simple date filter saja."""
#     if df.empty or "Date" not in df.columns:
#         return df

#     st.subheader("📅 Date Filter")

#     # Get min/max dates from dataframe
#     min_date = df["Date"].min()
#     max_date = df["Date"].max()

#     # Date picker
#     col1, col2 = st.columns(2)

#     with col1:
#         start_date = st.date_input(
#             "Start Date", value=min_date, min_value=min_date, max_value=max_date
#         )

#     with col2:
#         end_date = st.date_input(
#             "End Date", value=max_date, min_value=min_date, max_value=max_date
#         )

#     # Apply date filter
#     df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

#     return df_filtered


# def apply_filters(df: pd.DataFrame):
#     """Apply date filter dan transaction type selector."""
#     if df.empty:
#         return df

#     st.subheader("🔍 Filters")

#     col1, col2, col3 = st.columns(3)

#     # Initialize variables
#     start_date = None
#     end_date = None
#     selected_types = []

#     # Date filter
#     with col1:
#         if "Date" in df.columns:
#             min_date = df["Date"].min()
#             max_date = df["Date"].max()

#             start_date = st.date_input(
#                 "Start Date", value=min_date, min_value=min_date, max_value=max_date
#             )

#     with col2:
#         if "Date" in df.columns:
#             min_date = df["Date"].min()
#             max_date = df["Date"].max()

#             end_date = st.date_input(
#                 "End Date", value=max_date, min_value=min_date, max_value=max_date
#             )  # Transaction Type selector
#     with col3:
#         if "Transaction Type" in df.columns:
#             all_types = list(df["Transaction Type"].unique())
#             selected_types = st.multiselect(
#                 "Transaction Type",
#                 all_types,
#                 default=all_types,  # Show all by default
#                 help="Kosongkan untuk show all, pilih untuk filter specific types",
#             )

#             # Jika tidak ada yang dipilih, show all
#             if not selected_types:
#                 selected_types = all_types  # Apply filters
#     df_filtered = df.copy()

#     # Apply date filter - use explicit None checks
#     if "Date" in df.columns and start_date is not None and end_date is not None:
#         date_mask = (df_filtered["Date"] >= start_date) & (
#             df_filtered["Date"] <= end_date
#         )
#         df_filtered = df_filtered[date_mask]

#     # Apply transaction type filter - use len() check
#     if "Transaction Type" in df.columns and len(selected_types) > 0:
#         type_mask = df_filtered["Transaction Type"].isin(selected_types)
#         df_filtered = df_filtered[type_mask]

#     return df_filtered


# def show_overview_metrics(df: pd.DataFrame):
#     """Show overview metrics berdasarkan filtered data."""
#     if df.empty:
#         st.warning("Tidak ada data untuk ditampilkan")
#         return st.subheader("📊 Overview Metrics")

#     # Calculate failed count once for reuse
#     failed_count = 0
#     success_rate = 0
#     if "Final transaction status" in df.columns:
#         success_count = (df["Final transaction status"] == "Completed").sum()
#         failed_count = len(df) - success_count
#         success_rate = (success_count / len(df)) * 100 if len(df) > 0 else 0

#     # Basic metrics - rearrange order untuk currency di akhir
#     col1, col2, col3, col4, col5 = st.columns(5)

#     with col1:
#         st.metric("Total Transaksi", f"{len(df):,}")

#     with col2:
#         if "Transaction Type" in df.columns:
#             unique_types = df["Transaction Type"].nunique()
#             st.metric("Transaction Types", unique_types)

#     # Success rate metrics
#     with col3:
#         if "Final transaction status" in df.columns:
#             st.metric("Success Rate", f"{success_rate:.1f}%")

#     # Currency metrics di akhir dengan label yang lebih pendek
#     with col4:
#         if "Amount_Debit(IDR)" in df.columns:
#             avg_amount = df["Amount_Debit(IDR)"].mean()
#             st.metric("Avg Amount", f"Rp {avg_amount:,.0f}")

#     with col5:
#         if "Amount_Debit(IDR)" in df.columns:
#             total_amount = df["Amount_Debit(IDR)"].sum()
#             # Format dengan K/M untuk angka besar
#             if total_amount >= 1_000_000:
#                 display_amount = f"Rp {total_amount / 1_000_000:.1f}M"
#             elif total_amount >= 1_000:
#                 display_amount = f"Rp {total_amount / 1_000:.0f}K"
#             else:
#                 display_amount = f"Rp {total_amount:,.0f}"

#             delta_text = f"{failed_count} failed" if failed_count > 0 else None
#             st.metric("Total Amount", display_amount, delta=delta_text)

#     # Transaction Type breakdown - this IS the visualization
#     if "Transaction Type" in df.columns and "Amount_Debit(IDR)" in df.columns:
#         st.subheader("💳 Transaction Type Breakdown")

#         type_summary = (
#             df.groupby("Transaction Type")
#             .agg({"Transaction ID": "count", "Amount_Debit(IDR)": ["sum", "mean"]})
#             .round(0)
#         )

#         # Flatten column names
#         type_summary.columns = ["Count", "Total_Amount", "Avg_Amount"]
#         type_summary = type_summary.reset_index()

#         # Format currency columns
#         type_summary["Total_Amount_Formatted"] = type_summary["Total_Amount"].apply(
#             lambda x: f"Rp {x:,.0f}"
#         )
#         type_summary["Avg_Amount_Formatted"] = type_summary["Avg_Amount"].apply(
#             lambda x: f"Rp {x:,.0f}"
#         )

#         # Display formatted table
#         display_summary = type_summary[
#             [
#                 "Transaction Type",
#                 "Count",
#                 "Total_Amount_Formatted",
#                 "Avg_Amount_Formatted",
#             ]
#         ]
#         display_summary.columns = [
#             "Transaction Type",
#             "Count",
#             "Total Amount",
#             "Average Amount",
#         ]

#         st.dataframe(display_summary, use_container_width=True, hide_index=True)


# def show_simple_data_table(df: pd.DataFrame):
#     """Show simple data table."""
#     if df.empty:
#         return

#     st.subheader("📋 Transaction Data")

#     # Show key columns only
#     key_columns = [
#         "DateTime",
#         "Transaction Type",
#         "Organization Name",
#         "Amount_Debit(IDR)",
#         "Final transaction status",
#     ]

#     # Filter columns yang ada
#     available_cols = [col for col in key_columns if col in df.columns]

#     if available_cols:
#         # Show first 500 rows untuk performance
#         display_df = df[available_cols].head(500)
#         st.dataframe(display_df, use_container_width=True, height=400)

#         if len(df) > 500:
#             st.info(f"Showing first 500 rows out of {len(df):,} total rows")
#     else:
#         st.warning("Key columns tidak ditemukan dalam data")


# # Main page content
# st.title("📊 Data Transaksi")
# st.info("Data ini bersumber dari CSV-Download di Web MOBO")

# # Load data
# load_sample_data()

# # Check if data loaded
# if st.session_state.get("transaksi_data_loaded", False):
#     df = st.session_state.get("transaksi_data", pd.DataFrame())

#     if not df.empty:  # Apply filters
#         df_filtered = apply_filters(df)

#         st.divider()

#         # Show overview metrics
#         show_overview_metrics(df_filtered)

#         st.divider()  # Create tabs for different views
#         tab1, tab2 = st.tabs(["📈 Analysis & Visualization", "🗂️ Raw Data"])

#         with tab1:
#             st.write("**Filtered Data Overview:**")
#             st.write(
#                 f"Showing {len(df_filtered):,} transactions out of {len(df):,} total"
#             )

#             # Retailer Ranking Analysis
#             if (
#                 "Organization Name" in df_filtered.columns
#                 and "Amount_Debit(IDR)" in df_filtered.columns
#             ):
#                 st.subheader("🏆 Retailer Productivity Ranking")

#                 # Calculate retailer performance
#                 retailer_stats = (
#                     df_filtered.groupby("Organization Name")
#                     .agg(
#                         {
#                             "Transaction ID": "count",
#                             "Amount_Debit(IDR)": ["sum", "mean"],
#                             "Final transaction status": lambda x: (
#                                 x == "Completed"
#                             ).sum(),
#                         }
#                     )
#                     .round(0)
#                 )

#                 # Flatten column names
#                 retailer_stats.columns = [
#                     "Total_Transactions",
#                     "Total_Revenue",
#                     "Avg_Transaction",
#                     "Successful_Transactions",
#                 ]
#                 retailer_stats = retailer_stats.reset_index()

#                 # Calculate success rate
#                 retailer_stats["Success_Rate"] = (
#                     retailer_stats["Successful_Transactions"]
#                     / retailer_stats["Total_Transactions"]
#                     * 100
#                 ).round(1)

#                 # Sort by total revenue (most productive)
#                 retailer_stats = retailer_stats.sort_values(
#                     "Total_Revenue", ascending=False
#                 )  # Display options
#                 col1, col2, col3 = st.columns(3)

#                 with col1:
#                     ranking_metric = st.selectbox(
#                         "Ranking berdasarkan:",
#                         ["Total_Revenue", "Total_Transactions", "Avg_Transaction"],
#                         format_func=lambda x: {
#                             "Total_Revenue": "Total Revenue",
#                             "Total_Transactions": "Jumlah Transaksi",
#                             "Avg_Transaction": "Rata-rata Transaksi",
#                         }[x],
#                     )

#                 with col2:
#                     top_n = st.slider(
#                         "Tampilkan Top/Bottom N", 3, min(15, len(retailer_stats)), 8
#                     )

#                 with col3:
#                     show_both = st.checkbox(
#                         "Show Top & Bottom",
#                         value=True,
#                         help="Tampilkan top performers dan bottom performers",
#                     )

#                 # Re-sort based on selected metric
#                 retailer_sorted = retailer_stats.sort_values(
#                     ranking_metric, ascending=False
#                 )

#                 if show_both and len(retailer_stats) > top_n * 2:
#                     # Show top and bottom performers
#                     col1, col2 = st.columns(2)

#                     with col1:
#                         st.subheader(f"🏆 Top {top_n} Performers")
#                         top_retailers = retailer_sorted.head(top_n)

#                         # Format for display
#                         top_display = top_retailers.copy()
#                         top_display["Total_Revenue_Formatted"] = top_display[
#                             "Total_Revenue"
#                         ].apply(lambda x: f"Rp {x:,.0f}")
#                         top_display["Avg_Transaction_Formatted"] = top_display[
#                             "Avg_Transaction"
#                         ].apply(lambda x: f"Rp {x:,.0f}")

#                         # Display ranking table
#                         display_cols = [
#                             "Organization Name",
#                             "Total_Transactions",
#                             "Total_Revenue_Formatted",
#                             "Avg_Transaction_Formatted",
#                             "Success_Rate",
#                         ]
#                         display_names = [
#                             "Retailer",
#                             "Transactions",
#                             "Total Revenue",
#                             "Avg/Transaction",
#                             "Success %",
#                         ]

#                         top_table = top_display[display_cols].copy()
#                         top_table.columns = display_names
#                         top_table.insert(0, "Rank", range(1, len(top_table) + 1))

#                         st.dataframe(
#                             top_table, use_container_width=True, hide_index=True
#                         )

#                         # Chart for top performers
#                         st.subheader(f"📊 Top by {ranking_metric.replace('_', ' ')}")
#                         chart_data = top_retailers.set_index("Organization Name")[
#                             ranking_metric
#                         ]
#                         st.bar_chart(chart_data)

#                     with col2:
#                         st.subheader(f"⚠️ Bottom {top_n} Performers")
#                         bottom_retailers = retailer_sorted.tail(top_n).sort_values(
#                             ranking_metric, ascending=True
#                         )

#                         # Format for display
#                         bottom_display = bottom_retailers.copy()
#                         bottom_display["Total_Revenue_Formatted"] = bottom_display[
#                             "Total_Revenue"
#                         ].apply(lambda x: f"Rp {x:,.0f}")
#                         bottom_display["Avg_Transaction_Formatted"] = bottom_display[
#                             "Avg_Transaction"
#                         ].apply(lambda x: f"Rp {x:,.0f}")

#                         bottom_table = bottom_display[display_cols].copy()
#                         bottom_table.columns = display_names
#                         bottom_table.insert(
#                             0,
#                             "Rank",
#                             range(
#                                 len(retailer_stats) - top_n + 1, len(retailer_stats) + 1
#                             ),
#                         )

#                         st.dataframe(
#                             bottom_table, use_container_width=True, hide_index=True
#                         )

#                         # Chart for bottom performers
#                         st.subheader(f"📉 Bottom by {ranking_metric.replace('_', ' ')}")
#                         chart_data = bottom_retailers.set_index("Organization Name")[
#                             ranking_metric
#                         ]
#                         st.bar_chart(chart_data)

#                 else:
#                     # Show only top performers (original behavior)
#                     retailer_display = retailer_sorted.head(top_n)

#                     # Format for display
#                     retailer_display["Total_Revenue_Formatted"] = retailer_display[
#                         "Total_Revenue"
#                     ].apply(lambda x: f"Rp {x:,.0f}")
#                     retailer_display["Avg_Transaction_Formatted"] = retailer_display[
#                         "Avg_Transaction"
#                     ].apply(lambda x: f"Rp {x:,.0f}")

#                     # Display ranking table
#                     display_cols = [
#                         "Organization Name",
#                         "Total_Transactions",
#                         "Total_Revenue_Formatted",
#                         "Avg_Transaction_Formatted",
#                         "Success_Rate",
#                     ]
#                     display_names = [
#                         "Retailer",
#                         "Jumlah Transaksi",
#                         "Total Revenue",
#                         "Avg per Transaksi",
#                         "Success Rate (%)",
#                     ]

#                     ranking_table = retailer_display[display_cols].copy()
#                     ranking_table.columns = display_names
#                     ranking_table.insert(0, "Rank", range(1, len(ranking_table) + 1))

#                     st.dataframe(
#                         ranking_table, use_container_width=True, hide_index=True
#                     )

#                     # Charts
#                     col1, col2 = st.columns(2)

#                     with col1:
#                         st.subheader(f"📊 Top {top_n} by Revenue")
#                         chart_data = retailer_display.set_index("Organization Name")[
#                             "Total_Revenue"
#                         ]
#                         st.bar_chart(chart_data)

#                     with col2:
#                         st.subheader(f"📈 Top {top_n} by Transaction Count")
#                         chart_data = retailer_display.set_index("Organization Name")[
#                             "Total_Transactions"
#                         ]
#                         st.bar_chart(chart_data)

#                 # Performance insights
#                 with st.expander("💡 Retailer Performance Insights"):
#                     if len(retailer_stats) > 0:
#                         top_retailer = retailer_stats.iloc[0]
#                         avg_revenue = retailer_stats["Total_Revenue"].mean()
#                         avg_transactions = retailer_stats["Total_Transactions"].mean()

#                         col1, col2, col3 = st.columns(3)

#                         with col1:
#                             st.metric(
#                                 "Top Performer",
#                                 top_retailer["Organization Name"],
#                                 f"Rp {top_retailer['Total_Revenue']:,.0f}",
#                             )

#                         with col2:
#                             st.metric(
#                                 "Average Revenue per Retailer",
#                                 f"Rp {avg_revenue:,.0f}",
#                                 f"{len(retailer_stats)} total retailers",
#                             )

#                         with col3:
#                             st.metric(
#                                 "Average Transactions per Retailer",
#                                 f"{avg_transactions:.0f}",
#                                 f"Success rate: {retailer_stats['Success_Rate'].mean():.1f}%",
#                             )

#             # Placeholder for future visualizations
#             st.divider()
#             st.info(
#                 "📊 Additional visualizations (time series, geographic analysis, etc.) will be added here"
#             )

#         with tab2:
#             show_simple_data_table(df_filtered)

#         # Debug info
#         with st.expander("🔍 Debug Info"):
#             st.write(f"**Original Data:** {len(df):,} rows")
#             st.write(f"**Filtered Data:** {len(df_filtered):,} rows")
#             if "Date" in df.columns:
#                 st.write(f"**Date Range:** {df['Date'].min()} to {df['Date'].max()}")

#     else:
#         st.error("Data kosong atau gagal dimuat. Periksa path dan format file CSV.")

# else:
#     st.info("Loading data...")
