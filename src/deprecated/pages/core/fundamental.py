"""core data fundamental : harus di input oleh user pertama kali untuk mempersiapkan dashbaord."""

# Multi tabs untuk fundamental Info dan summary
import streamlit as st

tab_info, tab_profile, tab_territory, tab_site, tab_population, tab_retailer = st.tabs(
    [
        "Informasi Bisnis",
        "Profil Usaha",
        "Wilayah",
        "Site",
        "Populasi",
        "Retailer",
    ]
)

with tab_info:
    """ini adalah summary dari bisnis yang sudah di input oleh user.
    """
    st.header("Informasi Bisnis")
    st.write("Ini adalah ringkasan informasi bisnis yang telah diinput.")
    # Tambahkan elemen-elemen yang relevan untuk informasi bisnis


with tab_profile:
    st.header("Profil Usaha")
    st.write("Ini adalah ringkasan profil usaha yang telah diinput.")
    # Tambahkan elemen-elemen yang relevan untuk profil usaha

with tab_territory:
    st.header("Wilayah")
    st.write("Ini adalah ringkasan wilayah yang telah diinput.")
    # Tambahkan elemen-elemen yang relevan untuk wilayah

with tab_site:
    st.header("Site")
    st.write("Ini adalah ringkasan site yang telah diinput.")
    # Tambahkan elemen-elemen yang relevan untuk site

with tab_population:
    st.header("Populasi")
    st.write("Ini adalah ringkasan populasi yang telah diinput.")
    # Tambahkan elemen-elemen yang relevan untuk populasi

with tab_retailer:
    st.header("Retailer")
    st.write("Ini adalah ringkasan retailer yang telah diinput.")
    # Tambahkan elemen-elemen yang relevan untuk retailer
