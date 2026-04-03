import streamlit as st
import os
import re
from PyPDF2 import PdfReader
from docx import Document
from fpdf import FPDF

# =========================
# PAGE CONFIG & STATE
# =========================
st.set_page_config(page_title="AI Resume Optimizer", layout="wide")
st.title("🚀 AI Resume Optimizer")

# Initialize Session State to prevent UI vanishing on download
for key in ["optimized_resume", "cover_letter", "linkedin", "analysis"]:
    if key not in st.session_state:
        st.session_state[key] = None

# =========================
# SIDEBAR
# =========================
st.sidebar.header("🔑 API Settings")
groq_api_key = st.sidebar.text_input("Enter Groq API Key", type="password")

# =========================
# FILE PARSER
# =========================
def extract_text(file):
    text = ""
    try:
        if file.name.endswith(".pdf"):
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        elif file.name.endswith(".docx"):
            doc = Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        st.error(f"File parsing error: {e}")
    return text.strip()

# =========================
# CLEAN & NORMALIZE TEXT
# =========================
def clean_text(text):
    if not text:
        return ""

    replacements = {
        "•": "-", "–": "-", "—": "-",
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "✓": "OK", "✔": "OK", "●": "-",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    text = text.encode("latin-1", "ignore").decode("latin-1")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# =========================
# PROFESSIONAL PDF CLASS
# =========================
class ResumePDF(FPDF):
    pass

# =========================
# SAVE PDF (STABLE VERSION)
# =========================
def save_pdf(text, filename):
    try:
        pdf = ResumePDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=10)
        pdf.set_font("Arial", "", 10)

        text = clean_text(text)
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            if not line:
                pdf.ln(4)
                continue

            if line.isupper() and len(line) < 50:
                pdf.set_font("Arial", "B", 12)
                pdf.ln(3)
                pdf.cell(0, 8, line, ln=True)
                pdf.set_font("Arial", "", 10)
            elif line.startswith("-"):
                pdf.multi_cell(0, 6, f"  - {line[1:].strip()}")
            else:
                pdf.multi_cell(0, 6, line)

        path = f"{filename}.pdf"
        pdf.output(path)
        return path

    except Exception as e:
        print(f"PDF Error: {e}")
        return None

# =========================
# GROQ API CALL
# =========================
def call_groq(prompt, temp=0.7):  # Added temp parameter
    try:
        if not groq_api_key:
            return "⚠️ Please enter Groq API key."

        from openai import OpenAI
        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=temp,  # Use the variable here
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ API Error: {str(e)}"

def get_analysis_prompt(resume, jd):
    return f"""
Analyze the resume vs job description and calculate an ATS Compatibility Score.

STRICT SCORING RUBRIC (Out of 100):
1. Hard Skills (40 points): Do the programming languages/tools match?
2. Experience/Titles (30 points): Does the past experience align with the role?
3. Keywords (30 points): Are the specific industry keywords present?

Give:
1. ATS Compatibility Score: [Your calculated number]/100
2. Scoring Breakdown: (Briefly explain the points awarded for the 3 categories)
3. Specific Improvements: (3 bullet points on what keywords or skills to add)

JOB DESCRIPTION:
{jd}

RESUME:
{resume}
"""

# =========================
# UI INPUT
# =========================
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("📄 Upload Resume", type=["pdf", "docx"])

with col2:
    job_description = st.text_area(
        "🧾 Job Description", 
        height=200, 
        placeholder="E.g., Data Engineer, Business Analyst, or Backend Developer..."
    )

# =========================
# MAIN BUTTON (LOGIC ONLY)
# =========================
if st.button("✨ Optimize Resume", type="primary"):
    if not uploaded_file:
        st.warning("Please upload a resume.")
    elif not job_description.strip():
        st.warning("Please enter a job description.")
    elif not groq_api_key:
        st.error("Please enter your Groq API Key in the sidebar.")
    else:
        with st.spinner("Generating AI outputs..."):
            progress = st.progress(0)

            resume_text = extract_text(uploaded_file)
            progress.progress(15)

            if not resume_text:
                st.error("Could not extract text. Please try another file.")
                st.stop()

            # Store results in session state
            st.session_state.optimized_resume = call_groq(get_resume_prompt(resume_text, job_description))
            progress.progress(40)

            st.session_state.cover_letter = call_groq(get_cover_prompt(resume_text, job_description))
            progress.progress(60)

            st.session_state.linkedin = call_groq(get_linkedin_prompt(resume_text, job_description))
            progress.progress(80)

            # FORCE temperature to 0.0 for strict, consistent scoring
            st.session_state.analysis = call_groq(get_analysis_prompt(resume_text, job_description), temp=0.0)
            progress.progress(100)

# =========================
# DISPLAY UI (RENDERED FROM STATE)
# =========================
# This ensures the UI stays visible even when a download button is clicked
if st.session_state.optimized_resume:
    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Resume",
        "✉️ Cover Letter",
        "💼 LinkedIn",
        "📊 ATS Analysis"
    ])

    with tab1:
        st.text_area("Optimized Resume", st.session_state.optimized_resume, height=400)
        pdf_path = save_pdf(st.session_state.optimized_resume, "optimized_resume")
        if pdf_path:
            with open(pdf_path, "rb") as f:
                st.download_button("⬇ Download Resume PDF", f, "optimized_resume.pdf")

    with tab2:
        st.text_area("Cover Letter", st.session_state.cover_letter, height=400)
        pdf_path = save_pdf(st.session_state.cover_letter, "cover_letter")
        if pdf_path:
            with open(pdf_path, "rb") as f:
                st.download_button("⬇ Download Cover Letter PDF", f, "cover_letter.pdf")

    with tab3:
        st.text_area("LinkedIn Content", st.session_state.linkedin, height=400)
        pdf_path = save_pdf(st.session_state.linkedin, "linkedin_content")
        if pdf_path:
            with open(pdf_path, "rb") as f:
                st.download_button("⬇ Download LinkedIn PDF", f, "linkedin_content.pdf")

    with tab4:
        st.text_area("ATS Score & Improvements", st.session_state.analysis, height=400)
        pdf_path = save_pdf(st.session_state.analysis, "ats_analysis")
        if pdf_path:
            with open(pdf_path, "rb") as f:
                st.download_button("⬇ Download Analysis PDF", f, "ats_analysis.pdf")
