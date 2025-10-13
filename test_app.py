# test_app.py
import streamlit as st

st.set_page_config(
    page_title="Test App",
    page_icon="favicon.svg",
    layout="wide"
)

st.title("🧬 POLO-GGB RESEARCH ASSISTANT")
st.write("This is a test to see if the basic app works.")

if st.button("Test Button"):
    st.success("✅ App is working!")
else:
    st.info("Click the button to test the app.")
