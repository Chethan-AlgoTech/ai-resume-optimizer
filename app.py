import streamlit as st
import os
import re
import hashlib
from PyPDF2 import PdfReader
from docx import Document
from fpdf import FPDF

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="AI Resume Optimizer", layout="wide")
st.title("🚀 AI Resume Optimizer (Harvard ATS Format)")

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
# TEXT CLEANING
# =========================
def clean_text(text):
    replacements = {
        "•": "-",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "’": "'",
        "‘": "'",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = text.encode("latin-1", "ignore").decode("latin-1")
    return text.strip()

# =========================
# HARVARD STYLE PDF
# =========================
class HarvardPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)

def save_pdf(text, filename):
    try:
        pdf = HarvardPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=12)

        text = clean_text(text)
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            if not line:
                pdf.ln(4)
                continue

            # NAME (first line big)
            if pdf.page_no() == 1 and pdf.get_y() < 25:
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, line, ln=True)
                pdf.set_font("Arial", "", 10)

            # HEADINGS
            elif line.isupper():
                pdf.ln(4)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, line, ln=True)
                pdf.set_font("Arial", "", 10)

            # BULLETS
            elif line.startswith("-"):
                pdf.multi_cell(0, 6, f"  - {line[1:].strip()}")

            else:
                pdf.multi_cell(0, 6, line)

        path = f"{filename}.pdf"
        pdf.output(path)
        return path

    except Exception as e:
        st.error(f"PDF error: {e}")
        return None

# =========================
# GROQ API CALL (DETERMINISTIC)
# =========================
def call_groq(prompt):
    try:
        if not groq_api_key:
            return "⚠️ Enter Groq API key."

        from openai import OpenAI
        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,  # 🔥 deterministic
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"API Error: {e}"

# =========================
# ATS SCORE (CONSISTENT LOGIC)
# =========================
def compute_ats_score(resume, jd):
    resume_words = set(re.findall(r"\b\w+\b", resume.lower()))
    jd_words = set(re.findall(r"\b\w+\b", jd.lower()))

    if not jd_words:
        return 0

    match = resume_words.intersection(jd_words)
    score = int((len(match) / len(jd_words)) * 100)

    return min(score, 100)

def keyword_gap(resume, jd):
    resume_words = set(re.findall(r"\b\w+\b", resume.lower()))
    jd_words = set(re.findall(r"\b\w+\b", jd.lower()))
    missing = jd_words - resume_words
    return list(missing)[:15]

# =========================
# PROMPTS (HARVARD FORMAT)
# =========================
def resume_prompt(resume, jd):
    return f"""
Rewrite resume in HARVARD STYLE ATS format.

STRICT FORMAT:
NAME
CONTACT INFO

SUMMARY

SKILLS

EXPERIENCE
- bullet points with metrics

PROJECTS

EDUCATION

RULES:
- ALL CAPS headings
- clean spacing
- strong action verbs
- no repetition
- ATS optimized keywords

JOB DESCRIPTION:
{jd}

RESUME:
{resume}
"""

def cover_prompt(resume, jd):
    return f"""
Write a professional cover letter.

3-4 paragraphs
strong opening
relevant skills
confident tone

JD:
{jd}

RESUME:
{resume}
"""

def linkedin_prompt(resume, jd):
    return f"""
Generate:

LINKEDIN SUMMARY
LINKEDIN POST

Professional + engaging
"""

# =========================
# UI
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
# MAIN BUTTON
# =========================
if st.button("✨ Optimize Resume"):

    if not uploaded_file:
        st.warning("Upload resume.")
    elif not job_description.strip():
        st.warning("Enter job description.")
    else:
        with st.spinner("Processing..."):
            progress = st.progress(0)

            resume_text = extract_text(uploaded_file)
            progress.progress(20)

            optimized_resume = call_groq(resume_prompt(resume_text, job_description))
            progress.progress(50)

            cover_letter = call_groq(cover_prompt(resume_text, job_description))
            progress.progress(70)

            linkedin = call_groq(linkedin_prompt(resume_text, job_description))
            progress.progress(90)

            ats_score = compute_ats_score(optimized_resume, job_description)
            gaps = keyword_gap(optimized_resume, job_description)
            progress.progress(100)

        st.success(f"✅ Done! ATS Score: {ats_score}/100")

        tab1, tab2, tab3, tab4 = st.tabs([
            "📄 Resume",
            "✉️ Cover Letter",
            "💼 LinkedIn",
            "📊 ATS Analysis"
        ])

        with tab1:
            st.text_area("", optimized_resume, height=400)
            path = save_pdf(optimized_resume, "resume")
            if path:
                with open(path, "rb") as f:
                    st.download_button("⬇ Download PDF", f, "resume.pdf")

        with tab2:
            st.text_area("", cover_letter, height=400)
            path = save_pdf(cover_letter, "cover")
            if path:
                with open(path, "rb") as f:
                    st.download_button("⬇ Download PDF", f, "cover.pdf")

        with tab3:
            st.text_area("", linkedin, height=400)
            path = save_pdf(linkedin, "linkedin")
            if path:
                with open(path, "rb") as f:
                    st.download_button("⬇ Download PDF", f, "linkedin.pdf")

        with tab4:
            st.metric("ATS Score", f"{ats_score}/100")
            st.subheader("Missing Keywords")
            for kw in gaps:
                st.write(f"- {kw}")

# =========================
# REQUIREMENTS
# =========================
"""
streamlit
python-docx
PyPDF2
fpdf
openai
"""
