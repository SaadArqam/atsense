import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Backend Configuration ──────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "https://atsense-4kiz.onrender.com")
ANALYZE_ENDPOINT = f"{BACKEND_URL}/api/v1/analyze"

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResuMind AI",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS (Premium Minimalist SaaS Theme) ─────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Base Theme */
    .stApp {
        background-color: #0E1117;
        color: #E6E6E6;
    }

    /* Hide Streamlit default elements */
    #MainMenu, footer, header { visibility: hidden; }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #E6E6E6 !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: #E6E6E6;
    }
    .tagline {
        color: #9CA3AF;
        font-size: 1.1rem;
        margin-bottom: 2.5rem;
        font-weight: 400;
    }

    /* Cards */
    .saas-card {
        background-color: #161A22;
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    /* Buttons */
    .stButton > button {
        background-color: #10B981 !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #059669 !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
    }
    .stButton > button:disabled {
        background-color: #374151 !important;
        color: #9CA3AF !important;
        cursor: not-allowed;
    }

    /* Score styling */
    .score-container {
        text-align: center;
        padding: 2rem 0;
    }
    .score-value {
        font-size: 4.5rem;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    .score-label {
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9CA3AF;
        font-weight: 500;
    }
    .score-excellent { color: #10B981; }
    .score-good { color: #F59E0B; }
    .score-poor { color: #EF4444; }

    /* Badges */
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .badge {
        padding: 0.35rem 0.85rem;
        border-radius: 6px;
        font-size: 0.875rem;
        font-weight: 500;
        border: 1px solid;
    }
    .badge-match {
        background-color: rgba(16, 185, 129, 0.1);
        color: #10B981;
        border-color: rgba(16, 185, 129, 0.2);
    }
    .badge-missing {
        background-color: rgba(239, 68, 68, 0.1);
        color: #EF4444;
        border-color: rgba(239, 68, 68, 0.2);
    }
    .badge-empty {
        background-color: rgba(156, 163, 175, 0.1);
        color: #9CA3AF;
        border-color: rgba(156, 163, 175, 0.2);
    }

    /* List items */
    .suggestion-item {
        padding: 1rem;
        border-bottom: 1px solid #2D3748;
        color: #E6E6E6;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .suggestion-item:last-child {
        border-bottom: none;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #161A22 !important;
        border-radius: 8px;
        color: #E6E6E6 !important;
        font-weight: 500 !important;
    }
    .streamlit-expanderContent {
        background-color: #0E1117;
        border: 1px solid #2D3748;
        border-top: none;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        color: #9CA3AF;
        padding: 1rem !important;
    }

    /* Input Fields */
    .stTextArea > div > div > textarea {
        background-color: #0E1117;
        border: 1px solid #2D3748;
        color: #E6E6E6;
        border-radius: 8px;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #10B981;
        box-shadow: 0 0 0 1px #10B981;
    }
    .stFileUploader > div > div {
        background-color: #0E1117;
        border: 1px dashed #2D3748;
        border-radius: 8px;
    }
    
    /* Error Message Customization */
    .stAlert {
        background-color: rgba(239, 68, 68, 0.1) !important;
        color: #EF4444 !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        border-radius: 8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── UI Components ──────────────────────────────────────────────────────────

def render_card_start():
    st.markdown('<div class="saas-card">', unsafe_allow_html=True)

def render_card_end():
    st.markdown('</div>', unsafe_allow_html=True)

def render_badges(items: list[str], badge_type: str):
    if not items:
        st.markdown(f'<div class="badge-container"><span class="badge badge-empty">None identified</span></div>', unsafe_allow_html=True)
        return
        
    badges_html = "".join([f'<span class="badge badge-{badge_type}">{item}</span>' for item in items])
    st.markdown(f'<div class="badge-container">{badges_html}</div>', unsafe_allow_html=True)

def get_score_class(score: float) -> str:
    if score >= 75: return "score-excellent"
    if score >= 50: return "score-good"
    return "score-poor"

# ── API Interaction ────────────────────────────────────────────────────────

def analyze_resume_api(resume_bytes: bytes, filename: str, job_description: str) -> dict:
    files = {"resume": (filename, resume_bytes, "application/pdf")}
    data = {"job_description": job_description}
    response = requests.post(ANALYZE_ENDPOINT, files=files, data=data, timeout=120)
    response.raise_for_status()
    return response.json()

# ── Main Application ───────────────────────────────────────────────────────

def main():
    # Header
    st.markdown('<div class="main-title">ResuMind AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Intelligent resume analysis and ATS scoring.</div>', unsafe_allow_html=True)
    
    st.markdown('<hr style="border-color: #2D3748; margin-bottom: 2rem;">', unsafe_allow_html=True)

    # State management
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "is_analyzing" not in st.session_state:
        st.session_state.is_analyzing = False

    # Input Section
    render_card_start()
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("<h4 style='margin-bottom: 1rem;'>Document Upload</h4>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Resume (PDF)", 
            type=["pdf"], 
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("<h4 style='margin-bottom: 1rem;'>Job Description</h4>", unsafe_allow_html=True)
        job_description = st.text_area(
            "Job Description",
            height=150,
            placeholder="Paste the target job description here...",
            label_visibility="collapsed"
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CTA Button
    if st.button("Analyze Resume", disabled=st.session_state.is_analyzing):
        if not uploaded_file:
            st.error("Please upload a PDF resume document.")
        elif len(job_description.strip()) < 50:
            st.error("Please provide a more detailed job description (minimum 50 characters).")
        else:
            st.session_state.is_analyzing = True
            st.rerun()

    render_card_end()

    # Processing State
    if st.session_state.is_analyzing:
        with st.spinner("Analyzing document metrics..."):
            try:
                resume_bytes = uploaded_file.getvalue()
                result = analyze_resume_api(resume_bytes, uploaded_file.name, job_description)
                st.session_state.analysis_result = result
            except requests.exceptions.ConnectionError:
                st.error("Unable to connect to the analysis engine. Please ensure the backend service is running.")
            except requests.exceptions.HTTPError as e:
                try:
                    err_msg = e.response.json().get("detail", str(e))
                except:
                    err_msg = str(e)
                st.error(f"Analysis failed: {err_msg}")
            except Exception as e:
                st.error("An unexpected error occurred during analysis.")
            finally:
                st.session_state.is_analyzing = False
                st.rerun()

    # Results Dashboard
    result = st.session_state.analysis_result
    if result and not st.session_state.is_analyzing:
        st.markdown("<h3 style='margin-bottom: 1.5rem; margin-top: 2rem;'>Analysis Dashboard</h3>", unsafe_allow_html=True)
        
        # Row 1: Score & Skills
        col_score, col_skills = st.columns([1, 2], gap="large")
        
        with col_score:
            render_card_start()
            score = result.get("score", 0)
            score_class = get_score_class(score)
            st.markdown(
                f"""
                <div class="score-container">
                    <div class="score-value {score_class}">{score:.0f}</div>
                    <div class="score-label">Match Score</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            render_card_end()
            
        with col_skills:
            render_card_start()
            st.markdown("<h4 style='margin-bottom: 1rem;'>Skill Assessment</h4>", unsafe_allow_html=True)
            
            st.markdown("<div style='color: #9CA3AF; font-size: 0.875rem; margin-bottom: 0.25rem;'>Identified Matches</div>", unsafe_allow_html=True)
            render_badges(result.get("matched_skills", []), "match")
            
            st.markdown("<div style='color: #9CA3AF; font-size: 0.875rem; margin-top: 1.25rem; margin-bottom: 0.25rem;'>Identified Gaps</div>", unsafe_allow_html=True)
            render_badges(result.get("missing_skills", []), "missing")
            render_card_end()

        # Row 2: Suggestions & Section Feedback
        render_card_start()
        st.markdown("<h4 style='margin-bottom: 1rem;'>Actionable Recommendations</h4>", unsafe_allow_html=True)
        
        suggestions = result.get("suggestions", [])
        if suggestions:
            for item in suggestions:
                st.markdown(f'<div class="suggestion-item">{item}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="suggestion-item" style="color: #9CA3AF;">No critical recommendations identified.</div>', unsafe_allow_html=True)
        render_card_end()

        # Row 3: Section Analysis
        section_fb = result.get("section_feedback", {})
        if any(v for v in section_fb.values() if v and v.lower() not in ('null', 'none', '')):
            st.markdown("<h4 style='margin-bottom: 1rem; margin-top: 1.5rem;'>Section Analysis</h4>", unsafe_allow_html=True)
            
            sections_to_display = [
                ("Experience", section_fb.get("experience")),
                ("Projects", section_fb.get("projects")),
                ("Skills", section_fb.get("skills")),
                ("Summary", section_fb.get("summary")),
                ("Education", section_fb.get("education"))
            ]
            
            for title, feedback in sections_to_display:
                if feedback and feedback.lower() not in ('null', 'none', ''):
                    with st.expander(title):
                        st.markdown(f"<div style='color: #E6E6E6; font-size: 0.95rem; line-height: 1.6;'>{feedback}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
