import streamlit as st
import os
from PyPDF2 import PdfReader
from docx import Document
from fpdf import FPDF

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="AI Resume Optimizer", layout="wide")
st.title("🚀 AI Resume Optimizer")

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
# CLEAN TEXT FOR PDF
# =========================
def clean_text(text):
    return text.encode("latin-1", "replace").decode("latin-1")

# =========================
# PROFESSIONAL PDF CLASS
# =========================
class ResumePDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.ln(5)

# =========================
# SAVE PDF FUNCTION
# =========================
def save_pdf(text, filename):
    try:
        pdf = ResumePDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=10)

        text = clean_text(text)
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            if not line:
                pdf.ln(4)
                continue

            # ALL CAPS headings
            if line.isupper() and len(line) < 50:
                pdf.set_font("Arial", "B", 12)
                pdf.ln(4)
                pdf.cell(0, 8, line, ln=True)
                pdf.set_font("Arial", "", 10)

            # Bullet points
            elif line.startswith("-") or line.startswith("•"):
                pdf.set_font("Arial", "", 10)
                pdf.multi_cell(0, 6, f"  • {line[1:].strip()}")

            else:
                pdf.set_font("Arial", "", 10)
                pdf.multi_cell(0, 6, line)

        path = f"{filename}.pdf"
        pdf.output(path)
        return path

    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None

# =========================
# GROQ API CALL
# =========================
def call_groq(prompt):
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
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ API Error: {str(e)}"

# =========================
# PROMPTS
# =========================
def get_resume_prompt(resume, jd):
    return f"""
You are an expert ATS resume writer.

Rewrite the resume to match the job description.

RULES:
- Use ALL CAPS section headings: SUMMARY, SKILLS, EXPERIENCE, PROJECTS, EDUCATION
- Use bullet points
- Strong action verbs
- Quantify results
- No repeated names
- No unnecessary titles
- ATS optimized keywords
- Clean professional formatting

JOB DESCRIPTION:
{jd}

RESUME:
{resume}
"""

def get_cover_prompt(resume, jd):
    return f"""
Write a professional cover letter.

RULES:
- 3-4 paragraphs
- Strong opening
- Highlight relevant skills
- Confident tone
- No repetition

JOB DESCRIPTION:
{jd}

RESUME:
{resume}
"""

def get_linkedin_prompt(resume, jd):
    return f"""
Generate:

1. LINKEDIN SUMMARY
2. LINKEDIN POST

RULES:
- Professional and engaging
- Keyword optimized
- Concise
- No fluff

JOB DESCRIPTION:
{jd}

RESUME:
{resume}
"""

def get_analysis_prompt(resume, jd):
    return f"""
Analyze resume vs job description.

Give:
1. ATS Compatibility Score (0-100)
2. Specific Improvements (bullet points)

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
    job_description = st.text_area("🧾 Job Description", height=200)

# =========================
# MAIN BUTTON
# =========================
if st.button("✨ Optimize Resume"):

    if not uploaded_file:
        st.warning("Please upload a resume.")
    elif not job_description.strip():
        st.warning("Please enter a job description.")
    else:
        with st.spinner("Generating AI outputs..."):
            progress = st.progress(0)

            resume_text = extract_text(uploaded_file)
            progress.progress(15)

            optimized_resume = call_groq(get_resume_prompt(resume_text, job_description))
            progress.progress(40)

            cover_letter = call_groq(get_cover_prompt(resume_text, job_description))
            progress.progress(60)

            linkedin = call_groq(get_linkedin_prompt(resume_text, job_description))
            progress.progress(80)

            analysis = call_groq(get_analysis_prompt(resume_text, job_description))
            progress.progress(100)

        st.success("✅ All outputs generated!")

        # =========================
        # TABS
        # =========================
        tab1, tab2, tab3, tab4 = st.tabs([
            "📄 Resume",
            "✉️ Cover Letter",
            "💼 LinkedIn",
            "📊 ATS Analysis"
        ])

        # Resume Tab
        with tab1:
            st.text_area("Optimized Resume", optimized_resume, height=400)
            pdf_path = save_pdf(optimized_resume, "optimized_resume")
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button("⬇ Download Resume PDF", f, "optimized_resume.pdf")

        # Cover Letter Tab
        with tab2:
            st.text_area("Cover Letter", cover_letter, height=400)
            pdf_path = save_pdf(cover_letter, "cover_letter")
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button("⬇ Download Cover Letter PDF", f, "cover_letter.pdf")

        # LinkedIn Tab
        with tab3:
            st.text_area("LinkedIn Content", linkedin, height=400)
            pdf_path = save_pdf(linkedin, "linkedin_content")
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button("⬇ Download LinkedIn PDF", f, "linkedin_content.pdf")

        # Analysis Tab
        with tab4:
            st.text_area("ATS Score & Improvements", analysis, height=400)
            pdf_path = save_pdf(analysis, "ats_analysis")
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button("⬇ Download Analysis PDF", f, "ats_analysis.pdf")

# =========================
# REQUIREMENTS.TXT
# =========================
"""
streamlit
python-docx
PyPDF2
fpdf
openai
"""
