import streamlit as st
import os
import concurrent.futures
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from fpdf import FPDF # ensure this is fpdf2 installed via pip
from openai import OpenAI

# =========================
# ENV SETUP & PAGE CONFIG
# =========================
load_dotenv()
st.set_page_config(page_title="AI Resume Optimizer", page_icon="🚀", layout="wide")
st.title("🚀 AI Resume Optimizer")
st.markdown("Optimize your resume, generate cover letters, and LinkedIn content instantly.")

# =========================
# STATE MANAGEMENT
# =========================
if "optimized_resume" not in st.session_state:
    st.session_state.optimized_resume = None
if "cover_letter" not in st.session_state:
    st.session_state.cover_letter = None
if "linkedin_content" not in st.session_state:
    st.session_state.linkedin_content = None

# =========================
# SIDEBAR (API KEY)
# =========================
with st.sidebar:
    st.header("⚙️ Settings")
    user_api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.markdown("*Your key is not stored and is only used for this session.*")
    
# Fallback to local .env if user doesn't provide one
api_key = user_api_key if user_api_key else os.getenv("OPENAI_API_KEY")

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
        st.error(f"Error reading file: {e}")
    return text.strip()

# =========================
# AI ENGINE
# =========================
def generate_ai_response(prompt, api_key):
    if not api_key:
        return "⚠️ No OpenAI API key provided."
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# =========================
# PROMPTS
# =========================
def resume_prompt(resume, jd):
    return f"You are an expert ATS resume optimizer. Rewrite this resume to match the job description. Output pure plain text, NO markdown asterisks for bolding. Use standard bullet points (-). Job Description:\n{jd}\n\nResume:\n{resume}"

def cover_letter_prompt(resume, jd):
    return f"Write a professional cover letter as plain text. Do not use markdown bolding. Job Description:\n{jd}\n\nResume:\n{resume}\n\nRules: 3-4 paragraphs, strong introduction, highlight relevant skills, professional tone."

def linkedin_prompt(resume, jd):
    return f"Generate a LinkedIn Summary and a LinkedIn Post based on the resume and job description. Job Description:\n{jd}\n\nResume:\n{resume}"

# =========================
# PDF EXPORT (Safeguarded)
# =========================
def save_pdf(text, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Arial", "", "arial.ttf", uni=True) # Recommended: Add a local unicode font file if available
    pdf.set_font("Arial", size=10)
    
    # Safe encoding to prevent FPDF crash on emojis/weird characters
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, safe_text)

    path = f"{filename}.pdf"
    pdf.output(path)
    return path

# =========================
# UI LAYOUT
# =========================
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("📄 Upload Resume (PDF/DOCX)", type=["pdf", "docx"])
with col2:
    job_description = st.text_area("🧾 Paste Target Job Description", height=200, placeholder="E.g., Data Engineer or Business Analyst responsibilities...")

# =========================
# MAIN ACTION
# =========================
if st.button("✨ Optimize Resume", type="primary"):
    if not uploaded_file or not job_description:
        st.warning("Please upload a resume and enter a job description.")
    elif not api_key:
        st.error("Please enter your OpenAI API Key in the sidebar.")
    else:
        with st.spinner("Analyzing and Generating (this will take a few seconds)..."):
            resume_text = extract_text(uploaded_file)
            
            if not resume_text:
                st.error("Could not extract text from the document. Please try a different file.")
                st.stop()

            # Using ThreadPoolExecutor to run all 3 API calls concurrently
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_resume = executor.submit(generate_ai_response, resume_prompt(resume_text, job_description), api_key)
                future_cover = executor.submit(generate_ai_response, cover_letter_prompt(resume_text, job_description), api_key)
                future_linkedin = executor.submit(generate_ai_response, linkedin_prompt(resume_text, job_description), api_key)

                st.session_state.optimized_resume = future_resume.result()
                st.session_state.cover_letter = future_cover.result()
                st.session_state.linkedin_content = future_linkedin.result()
            
            st.success("✅ Optimization Complete!")

# =========================
# OUTPUT DISPLAY
# =========================
# Check if data exists in session state to display it
if st.session_state.optimized_resume:
    tab1, tab2, tab3 = st.tabs(["📄 Resume", "✉️ Cover Letter", "💼 LinkedIn"])

    with tab1:
        st.text_area("Review your new Resume points", st.session_state.optimized_resume, height=350)
        pdf_path = save_pdf(st.session_state.optimized_resume, "optimized_resume")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download Resume PDF", f, file_name="optimized_resume.pdf", mime="application/pdf")

    with tab2:
        st.text_area("Review your Cover Letter", st.session_state.cover_letter, height=350)
        pdf_path = save_pdf(st.session_state.cover_letter, "cover_letter")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download Cover Letter", f, file_name="cover_letter.pdf", mime="application/pdf")

    with tab3:
        st.text_area("Review your LinkedIn Content", st.session_state.linkedin_content, height=350)
        pdf_path = save_pdf(st.session_state.linkedin_content, "linkedin_content")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇ Download LinkedIn PDF", f, file_name="linkedin_content.pdf", mime="application/pdf")
