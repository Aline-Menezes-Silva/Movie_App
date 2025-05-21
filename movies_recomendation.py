import streamlit as st
import subprocess

st.title("App Diagnostic")

st.subheader("Installed Packages:")
result = subprocess.run(["pip", "list"], capture_output=True, text=True)
st.text(result.stdout)
