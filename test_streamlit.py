import streamlit as st

st.set_page_config(
    page_title="Test App",
    page_icon="favicon.svg",
    layout="wide"
)

st.title("🧬 Test App")
st.write("If you can see this, Streamlit Cloud is working.")

if st.button("Test Button"):
    st.success("✅ Streamlit Cloud is working!")
else:
    st.info("Click the button to test.")
