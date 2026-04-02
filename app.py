import streamlit as st
import os
import re
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from fpdf import FPDF
from groq import Groq

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
for key in ["optimized_resume", "cover_letter", "linkedin_content"]:
    if key not in st.session_state:
        st.session_state[key] = None

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("⚙️ Settings")
    user_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    st.markdown("*Your key is used only for this session.*")

api_key = user_api_key if user_api_key else os.getenv("GROQ_API_KEY")

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
# GROQ AI ENGINE
# =========================
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

# =========================
# PROMPTS
# =========================
def resume_prompt(resume_text, jd):
    return f"""You are an expert ATS resume writer.
Rewrite this resume to perfectly match the job description.
Use clear section headings in ALL CAPS (EXPERIENCE, EDUCATION, SKILLS, PROJECTS, etc.).
Use simple bullet points (-). Keep it clean and professional. Do NOT use markdown bolding (**) or italics.

Job Description:
{jd}

Resume:
{resume_text}"""

def cover_letter_prompt(resume_text, jd):
    return f"""Write a professional cover letter in plain text. Do NOT use markdown bolding.
Job Description:
{jd}

Resume:
{resume_text}"""

def linkedin_prompt(resume_text, jd):
    return f"""Generate a strong LinkedIn Summary and one ready-to-post LinkedIn post. Do NOT use markdown bolding.
Job Description:
{jd}

Resume:
{resume_text}"""

# =========================
# PDF SANITIZATION & EXPORT
# =========================
def clean_text_for_pdf(text):
    """Strips markdown and replaces unsupported unicode characters to prevent FPDF crashes."""
    # Remove markdown bolding and italics
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Replace smart quotes, em-dashes, and unsupported bullets
    replacements = {
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "–": "-", "—": "-", "…": "...", "•": "-"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    # Final safety net: encode to latin-1 and ignore remaining unmappable characters
    return text.encode('latin-1', 'ignore').decode('latin-1')

# =========================
# PDF SANITIZATION & EXPORT
# =========================
def clean_text_for_pdf(text):
    """Strips markdown and replaces unsupported unicode characters to prevent FPDF crashes."""
    # Remove markdown bolding and italics
    import re
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Replace smart quotes, em-dashes, and unsupported bullets
    replacements = {
        "“": '"', "”": '"', "‘": "'", "’": "'",
        "–": "-", "—": "-", "…": "...", "•": "-"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    # Final safety net: encode to latin-1 and ignore remaining unmappable characters
    return text.encode('latin-1', 'ignore').decode('latin-1')

def save_pdf(text, filename):
    pdf = FPDF()
    pdf.add_page()
    
    # Sanitize the text before processing
    safe_text = clean_text_for_pdf(text)
    lines = [line.strip() for line in safe_text.split('\n') if line.strip()]
    
    for line in lines:
        if line.isupper() and len(line) > 3:          
            # Headings like EXPERIENCE, SKILLS
            pdf.set_font("Arial", "B", 14)
            pdf.multi_cell(0, 10, line, align="L")
            pdf.ln(2)
            
        elif line.startswith("- ") or line.startswith("* "):  
            # Bullet points (FIXED LAYOUT)
            pdf.set_font("Arial", size=11)
            # Reconstruct the text to be handled by a single multi_cell
            clean_bullet_text = "- " + line[2:].strip()
            pdf.multi_cell(0, 8, clean_bullet_text)
            
        else:
            # Standard paragraph text
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, line)
            pdf.ln(1)
            
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
    job_description = st.text_area(
        "🧾 Paste Target Job Description", 
        height=200, 
        placeholder="E.g., Seeking a Data Engineer with strong Python and SQL skills, or a Business Analyst with dashboarding experience..."
    )

# =========================
# MAIN ACTION
# =========================
if st.button("✨ Optimize Resume", type="primary"):
    if not uploaded_file or not job_description:
        st.warning("Please upload a resume and paste a job description.")
    elif not api_key:
        st.error("Please enter your Groq API Key in the sidebar.")
    else:
        with st.spinner("Optimizing with AI (Groq is processing)..."):
            resume_text = extract_text(uploaded_file)
            
            if not resume_text:
                st.error("Could not extract text from the file.")
                st.stop()
            
            # Executed sequentially to respect Groq's aggressive free-tier rate limits
            st.session_state.optimized_resume = generate_ai_response(resume_prompt(resume_text, job_description), api_key)
            st.session_state.cover_letter = generate_ai_response(cover_letter_prompt(resume_text, job_description), api_key)
            st.session_state.linkedin_content = generate_ai_response(linkedin_prompt(resume_text, job_description), api_key)

            st.success("✅ Optimization Complete!")

# =========================
# OUTPUT DISPLAY
# =========================
if st.session_state.optimized_resume:
    tab1, tab2, tab3 = st.tabs(["📄 Resume", "✉️ Cover Letter", "💼 LinkedIn"])
    
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
