import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from fpdf import FPDF
from groq import Groq

load_dotenv()
st.set_page_config(page_title="AI Resume Optimizer", page_icon="🚀", layout="wide")

st.title("🚀 AI Resume Optimizer")
st.markdown("Optimize your resume, generate cover letters, and LinkedIn content instantly.")

# Session State
for key in ["optimized_resume", "cover_letter", "linkedin_content"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Sidebar - Only Groq API Key
with st.sidebar:
    st.header("⚙️ Settings")
    user_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    st.markdown("*Your key is used only for this session.*")

api_key = user_api_key if user_api_key else os.getenv("GROQ_API_KEY")

# File Parser Function
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
        st.error(f"Error reading file: {e}")
    return text.strip()

# Groq AI Function
def generate_ai_response(prompt, api_key):
    if not api_key:
        return "⚠️ Please enter your Groq API key in the sidebar."
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Prompts
def resume_prompt(resume_text, jd):
    return f"""You are an expert ATS resume optimizer.
Rewrite this resume to perfectly match the job description.
Output in clean plain text with proper bullet points (-). No markdown symbols.
Job Description:
{jd}

Resume:
{resume_text}"""

def cover_letter_prompt(resume_text, jd):
    return f"""Write a professional cover letter in plain text.
Job Description:
{jd}

Resume:
{resume_text}

Rules: 3-4 paragraphs, strong introduction, professional tone, no markdown."""

def linkedin_prompt(resume_text, jd):
    return f"""Generate:
1. A strong LinkedIn Summary (About section)
2. One ready-to-post LinkedIn post

Job Description:
{jd}

Resume:
{resume_text}"""

# Improved PDF Generator (Better Resume Look)
def save_pdf(text, filename, title=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=1, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, safe_text)
    path = f"{filename}.pdf"
    pdf.output(path)
    return path

# UI
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("📄 Upload Resume (PDF/DOCX)", type=["pdf", "docx"])
with col2:
    job_description = st.text_area("🧾 Paste Target Job Description", height=200, 
                                  placeholder="Paste the full job description here...")

# Main Button
if st.button("✨ Optimize Resume", type="primary"):
    if not uploaded_file or not job_description:
        st.warning("Please upload a resume and paste job description.")
    elif not api_key:
        st.error("Please enter Groq API Key in the sidebar.")
    else:
        with st.spinner("Optimizing with AI..."):
            resume_text = extract_text(uploaded_file)
            
            if not resume_text:
                st.error("Could not extract text from the file.")
                st.stop()
            
            st.session_state.optimized_resume = generate_ai_response(resume_prompt(resume_text, job_description), api_key)
            st.session_state.cover_letter = generate_ai_response(cover_letter_prompt(resume_text, job_description), api_key)
            st.session_state.linkedin_content = generate_ai_response(linkedin_prompt(resume_text, job_description), api_key)

            st.success("✅ Optimization Complete!")

# Display Results
if st.session_state.optimized_resume:
    tab1, tab2, tab3 = st.tabs(["📄 Resume", "✉️ Cover Letter", "💼 LinkedIn"])
    
    with tab1:
        st.text_area("Optimized Resume", st.session_state.optimized_resume, height=400)
        pdf_path = save_pdf(st.session_state.optimized_resume, "optimized_resume", "RESUME")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download Resume PDF", f, "optimized_resume.pdf", mime="application/pdf")

    with tab2:
        st.text_area("Cover Letter", st.session_state.cover_letter, height=400)
        pdf_path = save_pdf(st.session_state.cover_letter, "cover_letter", "COVER LETTER")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download Cover Letter PDF", f, "cover_letter.pdf", mime="application/pdf")

    with tab3:
        st.text_area("LinkedIn Content", st.session_state.linkedin_content, height=400)
        pdf_path = save_pdf(st.session_state.linkedin_content, "linkedin_content", "LINKEDIN")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download LinkedIn PDF", f, "linkedin_content.pdf", mime="application/pdf")
