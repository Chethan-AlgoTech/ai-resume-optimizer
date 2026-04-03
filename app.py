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
# SIDEBAR (API KEY ONLY)
# =========================
st.sidebar.header("🔑 Settings")
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
# SAFE TEXT FOR PDF (FIX UNICODE ERRORS)
# =========================
def clean_text(text):
    return text.encode("latin-1", "replace").decode("latin-1")

# =========================
# PDF GENERATOR (PROFESSIONAL FORMAT)
# =========================
class ProfessionalPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.ln(5)

def save_pdf(text, filename):
    try:
        pdf = ProfessionalPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=10)

        text = clean_text(text)

        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            if not line:
                pdf.ln(4)
                continue

            # Detect headings (ALL CAPS)
            if line.isupper() and len(line) < 40:
                pdf.set_font("Arial", "B", 12)
                pdf.ln(3)
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
def generate_ai(prompt):
    try:
        if not groq_api_key:
            return "⚠️ Please enter your Groq API key in the sidebar."

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
def resume_prompt(resume, jd):
    return f"""
You are a senior ATS resume expert.

Rewrite the resume to match the job description.

STRICT RULES:
- Use clean sections: SUMMARY, SKILLS, EXPERIENCE, PROJECTS, EDUCATION
- Use bullet points
- Use strong action verbs
- Quantify results
- No repeated names
- No extra titles
- ATS optimized keywords
- Clean formatting

JOB DESCRIPTION:
{jd}

RESUME:
{resume}
"""

def cover_prompt(resume, jd):
    return f"""
Write a professional cover letter.

RULES:
- 3–4 paragraphs
- Strong opening
- Relevant skills
- Confident tone
- No repetition

JOB DESCRIPTION:
{jd}

RESUME:
{resume}
"""

def linkedin_prompt(resume, jd):
    return f"""
Generate:
1. LinkedIn Summary
2. LinkedIn Post

RULES:
- Professional
- Engaging
- Keyword optimized
- No fluff

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
        with st.spinner("Processing with AI..."):
            progress = st.progress(0)

            resume_text = extract_text(uploaded_file)
            progress.progress(20)

            optimized_resume = generate_ai(resume_prompt(resume_text, job_description))
            progress.progress(50)

            cover_letter = generate_ai(cover_prompt(resume_text, job_description))
            progress.progress(75)

            linkedin = generate_ai(linkedin_prompt(resume_text, job_description))
            progress.progress(100)

        st.success("✅ All outputs generated successfully!")

        # =========================
        # TABS
        # =========================
        tab1, tab2, tab3 = st.tabs([
            "📄 Optimized Resume",
            "✉️ Cover Letter",
            "💼 LinkedIn"
        ])

        with tab1:
            st.text_area("Optimized Resume", optimized_resume, height=400)

            pdf_path = save_pdf(optimized_resume, "optimized_resume")
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "⬇ Download Resume PDF",
                        f,
                        file_name="optimized_resume.pdf"
                    )

        with tab2:
            st.text_area("Cover Letter", cover_letter, height=400)

            pdf_path = save_pdf(cover_letter, "cover_letter")
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "⬇ Download Cover Letter PDF",
                        f,
                        file_name="cover_letter.pdf"
                    )

        with tab3:
            st.text_area("LinkedIn Content", linkedin, height=400)

            pdf_path = save_pdf(linkedin, "linkedin_content")
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "⬇ Download LinkedIn PDF",
                        f,
                        file_name="linkedin_content.pdf"
                    )
