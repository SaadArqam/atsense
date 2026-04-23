import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv

# ── Environment & Config ───────────────────────────────────────────────────
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "https://atsense-4kiz.onrender.com")
ANALYZE_ENDPOINT = f"{BACKEND_URL}/api/v1/analyze"

# ── Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResuMind AI",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── World-Class SaaS Design System (CSS) ───────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Reset & Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E5E7EB;
    }
    .stApp {
        background-color: #0B0F14;
    }

    /* Hide Default Elements */
    #MainMenu, footer, header { visibility: hidden; }

    /* Layout Spacing */
    .block-container {
        padding-top: 5rem !important;
        padding-bottom: 5rem !important;
        max-width: 820px !important;
    }

    /* Hero Section */
    .hero-container {
        text-align: left;
        margin-bottom: 4rem;
    }
    .hero-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #10B981;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 0.75rem;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.04em;
        line-height: 1.1;
        margin-bottom: 0.75rem;
    }
    .hero-subtitle {
        font-size: 1.125rem;
        color: #9CA3AF;
        font-weight: 400;
        letter-spacing: -0.01em;
    }

    /* SaaS Dashboard Cards */
    [data-testid="stVerticalBlock"] > div:has(div.card-style) {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 2.5rem;
        margin-bottom: 2rem;
    }
    
    /* Input Styling Customization */
    .stTextArea textarea {
        background-color: #0B0F14 !important;
        border: 1px solid #1F2937 !important;
        border-radius: 8px !important;
        color: #E5E7EB !important;
        padding: 1rem !important;
        font-size: 0.95rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 1px #10B981 !important;
    }

    .stFileUploader section {
        background-color: #0B0F14 !important;
        border: 1px dashed #1F2937 !important;
        border-radius: 8px !important;
        padding: 2rem !important;
        transition: border-color 0.2s ease;
    }
    .stFileUploader section:hover {
        border-color: #10B981 !important;
    }

    /* Primary CTA Button */
    .stButton > button {
        width: 100%;
        background-color: #10B981 !important;
        color: #0B0F14 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.8rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin-top: 1rem;
    }
    .stButton > button:hover {
        background-color: #34D399 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.2);
    }
    .stButton > button:disabled {
        background-color: #1F2937 !important;
        color: #4B5563 !important;
    }

    /* Results UI Components */
    .dashboard-section-title {
        font-size: 0.875rem;
        font-weight: 700;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1.5rem;
        margin-top: 3rem;
    }

    .score-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 2.5rem;
        text-align: center;
    }
    .score-value {
        font-size: 5rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.05em;
        margin-bottom: 0.5rem;
    }
    .score-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    /* Skill Pills */
    .pill-group {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .pill-item {
        padding: 0.4rem 0.9rem;
        border-radius: 6px;
        font-size: 0.8125rem;
        font-weight: 600;
        border: 1px solid;
    }
    .pill-match {
        background-color: rgba(16, 185, 129, 0.05);
        color: #10B981;
        border-color: rgba(16, 185, 129, 0.15);
    }
    .pill-missing {
        background-color: rgba(244, 63, 94, 0.05);
        color: #FB7185;
        border-color: rgba(244, 63, 94, 0.15);
    }

    /* Recommendation List */
    .rec-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        overflow: hidden;
    }
    .rec-item {
        padding: 1.25rem 1.5rem;
        border-bottom: 1px solid #1F2937;
        font-size: 0.9375rem;
        line-height: 1.6;
        color: #D1D5DB;
    }
    .rec-item:last-child { border-bottom: none; }

    /* Alerts */
    .stAlert {
        background-color: rgba(244, 63, 94, 0.05) !important;
        color: #FB7185 !important;
        border: 1px solid rgba(244, 63, 94, 0.2) !important;
        border-radius: 8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── UI Library Functions ───────────────────────────────────────────────────

def render_score(score: float):
    # Dynamic color mapping based on performance
    color = "#10B981" if score >= 75 else "#F59E0B" if score >= 50 else "#FB7185"
    st.markdown(
        f"""
        <div class="score-card">
            <div class="score-value" style="color: {color};">{score:.0f}</div>
            <div class="score-label">ATS Compatibility Index</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_pills(items: list[str], type: str):
    if not items:
        st.markdown('<div style="color: #6B7280; font-size: 0.875rem;">None identified</div>', unsafe_allow_html=True)
        return
    
    pill_class = "pill-match" if type == "match" else "pill-missing"
    pills_html = "".join([f'<div class="pill-item {pill_class}">{item}</div>' for item in items])
    st.markdown(f'<div class="pill-group">{pills_html}</div>', unsafe_allow_html=True)

# ── API Logic ──────────────────────────────────────────────────────────────

def perform_analysis(resume_bytes, filename, job_desc):
    files = {"resume": (filename, resume_bytes, "application/pdf")}
    payload = {"job_description": job_desc}
    response = requests.post(ANALYZE_ENDPOINT, files=files, data=payload, timeout=120)
    response.raise_for_status()
    return response.json()

# ── Application Main ───────────────────────────────────────────────────────

def main():
    # Hero Section
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-label">AI Resume Intelligence</div>
            <div class="hero-title">ResuMind AI</div>
            <div class="hero-subtitle">Optimize your professional narrative for modern algorithmic screening.</div>
        </div>
        <hr style="border: 0; border-top: 1px solid #1F2937; margin-bottom: 4rem;">
        """,
        unsafe_allow_html=True
    )

    # App State
    if "data" not in st.session_state:
        st.session_state.data = None
    if "processing" not in st.session_state:
        st.session_state.processing = False

    # Main Interaction Card
    with st.container():
        # Tag to identify container in CSS
        st.markdown('<div class="card-style"></div>', unsafe_allow_html=True)
        
        col_up, col_jd = st.columns(2, gap="large")
        
        with col_up:
            st.markdown('<div style="font-size: 0.875rem; font-weight: 600; margin-bottom: 1rem;">Document</div>', unsafe_allow_html=True)
            resume_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
            
        with col_jd:
            st.markdown('<div style="font-size: 0.875rem; font-weight: 600; margin-bottom: 1rem;">Job Description</div>', unsafe_allow_html=True)
            job_text = st.text_area("Paste JD", height=140, placeholder="Paste target requirements...", label_visibility="collapsed")

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        if st.button("Generate Analysis", disabled=st.session_state.processing):
            if not resume_file:
                st.error("Missing resume document")
            elif len(job_text.strip()) < 50:
                st.error("Provide a more detailed job description")
            else:
                st.session_state.processing = True
                st.rerun()

    # Processing Pipeline
    if st.session_state.processing:
        with st.spinner("Decoding document signals..."):
            try:
                raw_bytes = resume_file.getvalue()
                results = perform_analysis(raw_bytes, resume_file.name, job_text)
                st.session_state.data = results
            except Exception as e:
                st.error(f"System Offline: {str(e)}")
            finally:
                st.session_state.processing = False
                st.rerun()

    # Results Dashboard
    if st.session_state.data and not st.session_state.processing:
        res = st.session_state.data
        st.markdown('<div class="dashboard-section-title">Performance Analytics</div>', unsafe_allow_html=True)
        
        # Dashboard Grid
        grid_col1, grid_col2 = st.columns([1, 1.4], gap="medium")
        
        with grid_col1:
            render_score(res.get("score", 0))
            
        with grid_col2:
            with st.container():
                st.markdown('<div class="card-style"></div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size: 0.875rem; font-weight: 700; color: #9CA3AF; text-transform: uppercase;">Keyword Alignment</div>', unsafe_allow_html=True)
                
                st.markdown('<div style="margin-top: 1.5rem; font-size: 0.75rem; color: #6B7280; font-weight: 600; text-transform: uppercase;">Matched Skills</div>', unsafe_allow_html=True)
                render_pills(res.get("matched_skills", []), "match")
                
                st.markdown('<div style="margin-top: 1.5rem; font-size: 0.75rem; color: #6B7280; font-weight: 600; text-transform: uppercase;">Identified Gaps</div>', unsafe_allow_html=True)
                render_pills(res.get("missing_skills", []), "missing")

        # Recommendations
        st.markdown('<div class="dashboard-section-title">Strategic Improvements</div>', unsafe_allow_html=True)
        suggestions = res.get("suggestions", [])
        
        st.markdown('<div class="rec-card">', unsafe_allow_html=True)
        if suggestions:
            for s in suggestions:
                st.markdown(f'<div class="rec-item">{s}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="rec-item">No urgent improvements identified.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Section Feedback
        fb = res.get("section_feedback", {})
        if any(fb.values()):
            st.markdown('<div class="dashboard-section-title">Structural Audit</div>', unsafe_allow_html=True)
            for section, feedback in fb.items():
                if feedback and feedback.lower() not in ("null", "none"):
                    with st.expander(section.upper()):
                        st.markdown(f"<div style='color: #9CA3AF; line-height: 1.6; font-size: 0.9375rem;'>{feedback}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
