import streamlit as st
import os
from PyPDF2 import PdfReader
from docx import Document
from fpdf import FPDF
from groq import Groq

st.set_page_config(page_title="AI Resume Optimizer", page_icon="🚀", layout="wide")
st.title("🚀 AI Resume Optimizer")
st.markdown("Optimize your resume, generate cover letters, and LinkedIn content instantly.")

# Session State
for key in ["optimized_resume", "cover_letter", "linkedin_content", "analysis"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Sidebar
st.sidebar.header("🔑 Groq API Settings")
groq_api_key = st.sidebar.text_input("Enter Groq API Key", type="password")

# File Parser
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

# Groq Call
def call_groq(prompt):
    if not groq_api_key:
        return "⚠️ Please enter Groq API key in sidebar."
    try:
        client = Groq(api_key=groq_api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ API Error: {str(e)}"

# Prompts
def get_resume_prompt(resume, jd):
    return f"""You are an expert ATS resume writer.
Rewrite the resume to match the job description perfectly.
Use ALL CAPS for section headings (SUMMARY, SKILLS, EXPERIENCE, EDUCATION, PROJECTS).
Use clear bullet points.
Keep it clean and professional.

JOB DESCRIPTION:
{jd}

ORIGINAL RESUME:
{resume}"""

def get_cover_prompt(resume, jd):
    return f"""Write a professional cover letter (3-4 paragraphs).

JOB DESCRIPTION:
{jd}

RESUME:
{resume}"""

def get_linkedin_prompt(resume, jd):
    return f"""Generate:
1. LinkedIn Summary (About section)
2. One ready-to-post LinkedIn post

JOB DESCRIPTION:
{jd}

RESUME:
{resume}"""

def get_analysis_prompt(resume, jd):
    return f"""Analyze this resume against the job description.
Give:
1. ATS Compatibility Score (0-100)
2. Specific improvements needed (bullet points)

JOB DESCRIPTION:
{jd}

RESUME:
{resume}"""

# Professional PDF Generator
def save_pdf(text, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for line in lines:
        if line.isupper() and len(line) > 4:          # Headings
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 12, line, ln=1)
            pdf.ln(6)
        elif line.startswith("-") or line.startswith("•"):
            pdf.set_font("Arial", size=11)
            pdf.cell(8, 8, "•", ln=0)
            pdf.multi_cell(0, 8, line[1:].strip())
        else:
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, line)
            pdf.ln(3)
    
    path = f"{filename}.pdf"
    pdf.output(path)
    return path

# UI
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("📄 Upload Resume (PDF/DOCX)", type=["pdf", "docx"])
with col2:
    job_description = st.text_area("🧾 Paste Job Description", height=200, placeholder="Paste full job description here...")

if st.button("✨ Optimize Resume", type="primary"):
    if not uploaded_file or not job_description.strip():
        st.warning("Please upload resume and enter job description.")
    else:
        with st.spinner("Generating AI outputs..."):
            resume_text = extract_text(uploaded_file)
            
            st.session_state.optimized_resume = call_groq(get_resume_prompt(resume_text, job_description))
            st.session_state.cover_letter = call_groq(get_cover_prompt(resume_text, job_description))
            st.session_state.linkedin_content = call_groq(get_linkedin_prompt(resume_text, job_description))
            st.session_state.analysis = call_groq(get_analysis_prompt(resume_text, job_description))

            st.success("✅ All outputs generated successfully!")

# Display Tabs
if st.session_state.optimized_resume:
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Resume", "✉️ Cover Letter", "💼 LinkedIn", "📊 ATS Analysis"])

    with tab1:
        st.text_area("Optimized Resume", st.session_state.optimized_resume, height=400)
        pdf_path = save_pdf(st.session_state.optimized_resume, "optimized_resume")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download Resume PDF", f, "optimized_resume.pdf", mime="application/pdf")

    with tab2:
        st.text_area("Cover Letter", st.session_state.cover_letter, height=400)
        pdf_path = save_pdf(st.session_state.cover_letter, "cover_letter")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download Cover Letter PDF", f, "cover_letter.pdf", mime="application/pdf")

    with tab3:
        st.text_area("LinkedIn Content", st.session_state.linkedin_content, height=400)
        pdf_path = save_pdf(st.session_state.linkedin_content, "linkedin_content")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download LinkedIn PDF", f, "linkedin_content.pdf", mime="application/pdf")

    with tab4:
        st.text_area("ATS Analysis & Score", st.session_state.analysis, height=400)
        pdf_path = save_pdf(st.session_state.analysis, "ats_analysis")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download Analysis PDF", f, "ats_analysis.pdf", mime="application/pdf")
