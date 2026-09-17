import streamlit as st 

st.set_page_config(
    page_title="DataSage",
    layout="wide"
)
st.title("datasage")
st.subheader("")
st.write("Upload your file")
st.page_link("pages/01_upload.py" ,label="Get Started")