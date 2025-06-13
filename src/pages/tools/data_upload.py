"""Page untuk upload data."""

import streamlit as st

st.title("📤 Data Upload")
st.write("Placeholder untuk fitur upload data.")

# Basic file uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
if uploaded_file is not None:
    st.success("File uploaded successfully!")
