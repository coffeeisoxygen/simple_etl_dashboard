import pandas as pd
import pygwalker as pyg
import streamlit as st
import streamlit.components.v1 as components

# Add Title
st.title("Use Pygwalker In Streamlit")

# Sample DataFrame
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

pyg_html = pyg.walk(df, return_html=True)

components.html(pyg_html, height=800, scrolling=True)
