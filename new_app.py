from dotenv import load_dotenv
import streamlit as st
import os
import json
import google.generativeai as genai
import pdfplumber
import re

# Load environment variables
load_dotenv()

# Configure Google Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))



def input_pdf_text(uploaded_file):
    if uploaded_file is not None:
        text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""  # Ensure no NoneType error
                text += page_text

        # Remove problematic Unicode characters
        return text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    return None



# Function to get structured response from Gemini
def get_gemini_response(input_text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(input_text)

    response_text = response.text.strip()  # Ensure response is clean

    # Debugging: Print raw response before parsing
    st.text_area("🔍 Debug: Raw AI Response", response_text, height=200)

    # Try to extract JSON from the response
    try:
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        json_string = response_text[json_start:json_end]

        return json.loads(json_string)  # Convert JSON string to Python dictionary

    except (json.JSONDecodeError, ValueError):
        return {"error": "Invalid JSON response from AI", "raw_response": response_text}

# Streamlit UI
st.set_page_config(page_title="ATS Resume Checker")
st.header("📄 ATS Resume Screening")

# User Inputs
input_text = st.text_area("📌 Paste Job Description Here:", key="input")
uploaded_file = st.file_uploader("📤 Upload your Resume (PDF)", type=['pdf'])

if uploaded_file:
    st.success("✅ PDF Uploaded Successfully!")

# Submit button
submit = st.button("🚀 Analyze Resume")

# Input prompt for Gemini AI
if submit:
    if uploaded_file:
        resume_text = input_pdf_text(uploaded_file)

        input_prompt = f"""
        Hey Act Like a skilled or very experience ATS(Application Tracking System)
        with a deep understanding of tech field,software engineering,data science ,data analyst
        and big data engineer. Your task is to evaluate the resume based on the given job description.
        You must consider the job market is very competitive and you should provide 
        best assistance for improving thr resumes. Assign the percentage Matching based 
        on Jd and
        the missing keywords with high accuracy

        **Job Description:** {input_text}
        **Resume Extracted Text:** {resume_text}

        ### **Return JSON in this format:**
        ```json
        {{
            "JD Match": "XX%",
            "MissingKeywords": [],
            "Profile Summary": "Brief feedback on strengths & improvement areas."
        }}
        ```
        """

        # Get response from Gemini
        response = get_gemini_response(input_prompt)

        if "error" in response:
            st.error("⚠️ AI response was not in valid JSON format.")
            st.text(response["raw_response"])  # Show raw response for debugging
        else:
            # 📌 **Display Results**
            st.markdown("## 📌 Resume Analysis Results:")

            # ✅ JD Match
            st.markdown(f"**✅ JD Match:** `{response.get('JD Match', 'N/A')}`")

            # ✅ Missing Keywords
            missing_keywords = response.get("MissingKeywords", [])
            st.markdown("### 🚀 Missing Keywords:")
            if missing_keywords:
                st.markdown(", ".join([f"`{kw}`" for kw in missing_keywords]))
            else:
                st.markdown("*No missing keywords found!* 🎯")

            # ✅ Profile Summary
            st.markdown("### 📄 Profile Summary:")
            st.markdown(f"_{response.get('Profile Summary', 'No summary available.')}_")

    else:
        st.warning("⚠️ Please upload a resume before submitting.")
