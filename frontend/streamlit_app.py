import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "https://atsense-4kiz.onrender.com")
ANALYZE_ENDPOINT = f"{BACKEND_URL}/api/v1/analyze"

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResuMind AI | Smart Resume Intelligence",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS (High-Polish SaaS Dashboard) ────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Background and Global Reset */
    .stApp {
        background-color: #0B0F14;
        color: #E5E7EB;
    }

    #MainMenu, footer, header { visibility: hidden; }

    /* Layout Containers */
    .block-container {
        padding-top: 4rem !important;
        padding-bottom: 5rem !important;
        max-width: 850px !important;
    }

    /* Hero Section */
    .hero-label {
        color: #10B981;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.75rem;
    }
    .hero-title {
        font-size: 2.75rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: #9CA3AF;
        font-weight: 400;
        margin-bottom: 3.5rem;
    }

    /* Unified Input Card */
    .unified-card {
        background-color: #121821;
        border: 1px solid #1F2937;
        border-radius: 16px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }

    /* Section Typography */
    .section-label {
        font-size: 0.875rem;
        font-weight: 600;
        color: #E5E7EB;
        margin-bottom: 1.25rem;
    }

    /* File Uploader Customization */
    .stFileUploader > label { display: none; }
    .stFileUploader section {
        background-color: #0B0F14 !important;
        border: 1px dashed #1F2937 !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        transition: all 0.2s ease;
    }
    .stFileUploader section:hover {
        border-color: #10B981 !important;
        background-color: rgba(16, 185, 129, 0.02) !important;
    }

    /* Textarea Customization */
    .stTextArea > label { display: none; }
    .stTextArea textarea {
        background-color: #0B0F14 !important;
        border: 1px solid #1F2937 !important;
        border-radius: 12px !important;
        color: #E5E7EB !important;
        padding: 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease;
    }
    .stTextArea textarea:focus {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 1px #10B981 !important;
    }

    /* CTA Button */
    .stButton > button {
        width: 100%;
        background-color: #10B981 !important;
        color: #0B0F14 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.875rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-top: 1rem;
    }
    .stButton > button:hover {
        background-color: #059669 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
    }
    .stButton > button:active {
        transform: translateY(0);
    }
    .stButton > button:disabled {
        background-color: #1F2937 !important;
        color: #4B5563 !important;
        cursor: not-allowed;
    }

    /* Result Components */
    .result-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 3rem 0 1.5rem 0;
    }

    .stat-card {
        background-color: #121821;
        border: 1px solid #1F2937;
        border-radius: 16px;
        padding: 2rem;
        height: 100%;
    }

    .score-display {
        text-align: center;
    }
    .score-value {
        font-size: 4rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.75rem;
    }
    .score-subtext {
        font-size: 0.75rem;
        font-weight: 600;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .text-emerald { color: #10B981; }
    .text-amber { color: #F59E0B; }
    .text-rose { color: #F43F5E; }

    /* Pill Badges */
    .pill-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin-top: 0.75rem;
    }
    .pill {
        padding: 0.4rem 0.9rem;
        border-radius: 99px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid transparent;
    }
    .pill-match {
        background-color: rgba(16, 185, 129, 0.08);
        color: #10B981;
        border-color: rgba(16, 185, 129, 0.2);
    }
    .pill-gap {
        background-color: rgba(244, 63, 94, 0.08);
        color: #F43F5E;
        border-color: rgba(244, 63, 94, 0.2);
    }

    /* Recommendation List */
    .rec-item {
        padding: 1.25rem 0;
        border-bottom: 1px solid #1F2937;
        color: #E5E7EB;
        font-size: 0.925rem;
        line-height: 1.6;
        display: flex;
        gap: 1rem;
    }
    .rec-item:last-child { border-bottom: none; }
    .rec-bullet {
        color: #10B981;
        font-weight: 800;
    }

    /* Custom Alert */
    .stAlert {
        background-color: rgba(244, 63, 94, 0.05) !important;
        color: #F43F5E !important;
        border: 1px solid rgba(244, 63, 94, 0.2) !important;
        border-radius: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Component Functions ────────────────────────────────────────────────────

def render_score(score: float):
    color_class = "text-emerald" if score >= 75 else "text-amber" if score >= 50 else "text-rose"
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="score-display">
                <div class="score-value {color_class}">{score:.0f}</div>
                <div class="score-subtext">ATS Compatibility Score</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_pills(items: list[str], mode: str):
    pill_class = "pill-match" if mode == "match" else "pill-gap"
    if not items:
        st.markdown('<div class="pill-container"><span style="color:#6B7280; font-size:0.875rem;">None identified</span></div>', unsafe_allow_html=True)
        return
    
    pills_html = "".join([f'<span class="pill {pill_class}">{item}</span>' for item in items])
    st.markdown(f'<div class="pill-container">{pills_html}</div>', unsafe_allow_html=True)

# ── API Logic ──────────────────────────────────────────────────────────────

def call_analysis(resume_bytes, filename, job_desc):
    files = {"resume": (filename, resume_bytes, "application/pdf")}
    data = {"job_description": job_desc}
    resp = requests.post(ANALYZE_ENDPOINT, files=files, data=data, timeout=120)
    resp.raise_for_status()
    return resp.json()

# ── Main UI ────────────────────────────────────────────────────────────────

def main():
    # Hero Section
    st.markdown('<div class="hero-label">AI Resume Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">ResuMind AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Optimize your professional profile for modern recruitment systems.</div>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color: #1F2937; margin-bottom: 4rem;">', unsafe_allow_html=True)

    # State
    if "result" not in st.session_state:
        st.session_state.result = None
    if "loading" not in st.session_state:
        st.session_state.loading = False

    # Unified Input Card
    st.markdown('<div class="unified-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown('<div class="section-label">Resume Document</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
        
    with col2:
        st.markdown('<div class="section-label">Target Job Description</div>', unsafe_allow_html=True)
        job_desc = st.text_area("Paste JD", height=140, placeholder="Paste requirements here...", label_visibility="collapsed")
    
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    if st.button("Analyze Resume", disabled=st.session_state.loading):
        if not uploaded_file:
            st.error("Document upload required")
        elif len(job_desc.strip()) < 50:
            st.error("Provide a detailed job description")
        else:
            st.session_state.loading = True
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

    # Execution
    if st.session_state.loading:
        with st.spinner("Processing analysis..."):
            try:
                bytes_data = uploaded_file.getvalue()
                res = call_analysis(bytes_data, uploaded_file.name, job_desc)
                st.session_state.result = res
            except Exception as e:
                st.error(f"Analysis system offline: {str(e)}")
            finally:
                st.session_state.loading = False
                st.rerun()

    # Results Section
    if st.session_state.result and not st.session_state.loading:
        data = st.session_state.result
        st.markdown('<div class="result-header">Analysis Result</div>', unsafe_allow_html=True)
        
        # Row 1: Score & Skills
        r1_col1, r1_col2 = st.columns([1, 1.5], gap="medium")
        
        with r1_col1:
            render_score(data.get("score", 0))
            
        with r1_col2:
            st.markdown('<div class="stat-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-label" style="margin-bottom:0.75rem;">Skill Matching</div>', unsafe_allow_html=True)
            
            st.markdown('<div style="color:#9CA3AF; font-size:0.75rem; font-weight:600; text-transform:uppercase; margin-top:1rem;">Matched Keywords</div>', unsafe_allow_html=True)
            render_pills(data.get("matched_skills", []), "match")
            
            st.markdown('<div style="color:#9CA3AF; font-size:0.75rem; font-weight:600; text-transform:uppercase; margin-top:1.5rem;">Identified Gaps</div>', unsafe_allow_html=True)
            render_pills(data.get("missing_skills", []), "gap")
            st.markdown('</div>', unsafe_allow_html=True)

        # Row 2: Recommendations
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="unified-card" style="padding: 2rem 2.5rem;">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Critical Recommendations</div>', unsafe_allow_html=True)
        
        recs = data.get("suggestions", [])
        if recs:
            for r in recs:
                st.markdown(f'<div class="rec-item"><span class="rec-bullet">•</span>{r}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="rec-item">No urgent recommendations identified.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Row 3: Sectional Analysis
        sec_data = data.get("section_feedback", {})
        if any(sec_data.values()):
            st.markdown('<div class="section-label" style="margin: 2rem 0 1rem 0;">Detailed Breakdown</div>', unsafe_allow_html=True)
            for name, content in sec_data.items():
                if content and content.lower() not in ("null", "none"):
                    with st.expander(name.capitalize()):
                        st.markdown(f"<div style='color:#9CA3AF; line-height:1.6;'>{content}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
