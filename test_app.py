#!/usr/bin/env python3
"""Simple test app to diagnose Streamlit Cloud issues"""

import streamlit as st
import os

st.title("⚖️ Legal Document Classifier - Deployment Test")

st.write("## Environment Check")
st.write(f"Streamlit version: {st.__version__}")
st.write(f"Current directory: {os.getcwd()}")
st.write(f"Files in directory:")

for file in os.listdir("."):
    st.write(f"- {file}")

st.write("## Import Test")
try:
    import requests
    import pandas as pd
    import plotly
    import numpy as np
    from fpdf import FPDF
    st.success("✅ All imports successful!")
except Exception as e:
    st.error(f"❌ Import error: {e}")

st.write("## App Test")
if st.button("Test Button"):
    st.balloons()
    st.success("Button works!")