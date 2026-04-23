"""
AI Resume Analyzer + ATS Scorer — Streamlit Frontend

Design goals:
- Clean dark-mode UI with a professional gradient palette
- Colour-coded ATS score gauge (red → yellow → green)
- Tabbed results view: Overview | Skills | Suggestions | Section Feedback
- No raw JSON exposed to the user
"""

import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Backend URL ────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ANALYZE_ENDPOINT = f"{BACKEND_URL}/api/v1/analyze"

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Dark background ── */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
        min-height: 100vh;
    }

    /* ── Hero header ── */
    .hero-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.3rem;
        line-height: 1.2;
    }
    .hero-subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 2.5rem;
    }

    /* ── Score gauge card ── */
    .score-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 2rem 1.5rem;
        text-align: center;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .score-number {
        font-size: 5rem;
        font-weight: 800;
        line-height: 1;
        margin: 0.5rem 0;
    }
    .score-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #94a3b8;
        margin-bottom: 0.5rem;
    }
    .score-badge {
        display: inline-block;
        padding: 0.3rem 1rem;
        border-radius: 99px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    /* ── Skill pill ── */
    .skill-matched {
        display: inline-block;
        background: rgba(52, 211, 153, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.4);
        border-radius: 99px;
        padding: 0.25rem 0.75rem;
        margin: 0.2rem;
        font-size: 0.82rem;
        font-weight: 500;
    }
    .skill-missing {
        display: inline-block;
        background: rgba(248, 113, 113, 0.15);
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.4);
        border-radius: 99px;
        padding: 0.25rem 0.75rem;
        margin: 0.2rem;
        font-size: 0.82rem;
        font-weight: 500;
    }

    /* ── Section card ── */
    .section-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(8px);
    }
    .section-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #a78bfa;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .section-body {
        color: #cbd5e1;
        font-size: 0.92rem;
        line-height: 1.6;
    }

    /* ── Suggestion item ── */
    .suggestion-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        background: rgba(96, 165, 250, 0.08);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 12px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.6rem;
        color: #e2e8f0;
        font-size: 0.92rem;
        line-height: 1.5;
    }
    .suggestion-icon {
        color: #60a5fa;
        font-size: 1rem;
        flex-shrink: 0;
        margin-top: 0.05rem;
    }

    /* ── Summary box ── */
    .summary-box {
        background: linear-gradient(135deg, rgba(167,139,250,0.12), rgba(96,165,250,0.08));
        border: 1px solid rgba(167,139,250,0.25);
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        color: #e2e8f0;
        font-size: 0.96rem;
        line-height: 1.7;
        margin-bottom: 1.5rem;
    }

    /* ── Upload area ── */
    .upload-container {
        background: rgba(255,255,255,0.03);
        border: 1.5px dashed rgba(167,139,250,0.4);
        border-radius: 16px;
        padding: 1.5rem;
    }

    /* ── Tab tweaks ── */
    .stTabs [data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        color: #a78bfa !important;
        border-bottom-color: #a78bfa !important;
    }

    /* ── Button ── */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #2563eb);
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.88;
    }

    /* ── Progress bar colour ── */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #7c3aed, #2563eb, #059669);
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helper functions ───────────────────────────────────────────────────────

def score_color(score: float) -> str:
    """Return a CSS colour string based on ATS score."""
    if score >= 75:
        return "#34d399"   # green
    elif score >= 50:
        return "#fbbf24"   # amber
    else:
        return "#f87171"   # red


def score_label(score: float) -> str:
    """Human-readable band label."""
    if score >= 80:
        return "🏆 Excellent Match"
    elif score >= 65:
        return "✅ Good Match"
    elif score >= 45:
        return "⚠️ Moderate Match"
    else:
        return "❌ Low Match"


def score_badge_style(score: float) -> str:
    """Inline badge background colours."""
    if score >= 75:
        return "background:rgba(52,211,153,0.2);color:#34d399;border:1px solid rgba(52,211,153,0.5);"
    elif score >= 50:
        return "background:rgba(251,191,36,0.2);color:#fbbf24;border:1px solid rgba(251,191,36,0.5);"
    else:
        return "background:rgba(248,113,113,0.2);color:#f87171;border:1px solid rgba(248,113,113,0.5);"


def render_skills(skills: list[str], kind: str) -> str:
    """Render a list of skills as coloured pills."""
    css_class = "skill-matched" if kind == "matched" else "skill-missing"
    pills = "".join(f'<span class="{css_class}">{s}</span>' for s in skills)
    return pills or "<span style='color:#64748b;font-size:0.9rem;'>None detected</span>"


def call_backend(resume_bytes: bytes, filename: str, job_description: str) -> dict:
    """
    POST to the FastAPI backend and return parsed JSON.
    Raises on HTTP errors or connection issues.
    """
    files = {"resume": (filename, resume_bytes, "application/pdf")}
    data = {"job_description": job_description}

    resp = requests.post(ANALYZE_ENDPOINT, files=files, data=data, timeout=120)
    resp.raise_for_status()
    return resp.json()


# ── Main UI ────────────────────────────────────────────────────────────────

def main():
    # ── Hero ──────────────────────────────────────────────────────────────
    st.markdown('<h1 class="hero-title">🎯 AI Resume Analyzer</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-subtitle">ATS score · skill gap analysis · LLM-powered improvement suggestions</p>',
        unsafe_allow_html=True,
    )

    # ── Input columns ─────────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("#### 📄 Upload Resume")
        uploaded_file = st.file_uploader(
            "Drop your PDF resume here",
            type=["pdf"],
            key="resume_upload",
            label_visibility="collapsed",
        )
        if uploaded_file:
            st.success(f"✅ **{uploaded_file.name}** — {uploaded_file.size / 1024:.1f} KB")

    with col_right:
        st.markdown("#### 📋 Job Description")
        job_description = st.text_area(
            "Paste the job description",
            height=200,
            placeholder="Paste the full job description here…\n\nInclude skills, responsibilities, and requirements for best results.",
            key="jd_input",
            label_visibility="collapsed",
        )
        char_count = len(job_description)
        color = "#34d399" if char_count >= 100 else "#fbbf24" if char_count > 0 else "#64748b"
        st.markdown(
            f'<p style="color:{color};font-size:0.8rem;margin-top:-0.5rem;">'
            f'{char_count} characters {"✓" if char_count >= 100 else "(at least 100 recommended)"}</p>',
            unsafe_allow_html=True,
        )

    # ── Analyse button ────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    btn_col = st.columns([1, 2, 1])[1]
    with btn_col:
        analyse_clicked = st.button("🚀 Analyze Resume", key="analyse_btn")

    # ── Run analysis ──────────────────────────────────────────────────────
    if analyse_clicked:
        if not uploaded_file:
            st.error("⚠️ Please upload a PDF resume.")
            return
        if len(job_description.strip()) < 50:
            st.error("⚠️ Job description must be at least 50 characters.")
            return

        with st.spinner("🔍 Analysing your resume… this may take 15–30 seconds"):
            progress = st.progress(0, text="Parsing PDF…")
            try:
                resume_bytes = uploaded_file.getvalue()
                progress.progress(20, text="Computing embeddings…")
                time.sleep(0.3)
                progress.progress(40, text="Building FAISS index…")
                result = call_backend(resume_bytes, uploaded_file.name, job_description)
                progress.progress(80, text="Processing LLM response…")
                time.sleep(0.3)
                progress.progress(100, text="Done!")
                time.sleep(0.4)
                progress.empty()
            except requests.exceptions.ConnectionError:
                progress.empty()
                st.error(
                    "❌ **Cannot connect to the backend.**\n\n"
                    "Make sure the FastAPI server is running:\n"
                    "```\ncd backend && python app.py\n```"
                )
                return
            except requests.exceptions.HTTPError as exc:
                progress.empty()
                try:
                    detail = exc.response.json().get("detail", str(exc))
                except Exception:
                    detail = str(exc)
                st.error(f"❌ Backend error: {detail}")
                return
            except Exception as exc:
                progress.empty()
                st.error(f"❌ Unexpected error: {exc}")
                return

        # ── Store result in session state to persist across reruns ────────
        st.session_state["result"] = result

    # ── Render results ────────────────────────────────────────────────────
    if "result" in st.session_state:
        render_results(st.session_state["result"])


def render_results(result: dict):
    """Render the full analysis results in a tabbed layout."""
    score: float = result.get("score", 0)
    matched: list = result.get("matched_skills", [])
    missing: list = result.get("missing_skills", [])
    suggestions: list = result.get("suggestions", [])
    section_fb: dict = result.get("section_feedback", {})
    top_chunks: list = result.get("top_matching_chunks", [])
    semantic_gaps: list = result.get("semantic_gaps", [])
    llm_summary: str = result.get("llm_summary", "")

    st.markdown("---")

    # ── Top score card + quick stats ──────────────────────────────────────
    card_col, stat_col = st.columns([1, 2], gap="large")

    with card_col:
        color = score_color(score)
        badge_style = score_badge_style(score)
        label = score_label(score)
        st.markdown(
            f"""
            <div class="score-card">
                <div class="score-label">ATS Score</div>
                <div class="score-number" style="color:{color};">{score:.0f}</div>
                <div style="color:#64748b;font-size:1.5rem;">/ 100</div>
                <span class="score-badge" style="{badge_style}">{label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with stat_col:
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("✅ Matched Skills", len(matched))
        with m2:
            st.metric("❌ Missing Skills", len(missing))
        with m3:
            st.metric("💡 Suggestions", len(suggestions))

        # Score progress bar
        st.markdown("<br/>", unsafe_allow_html=True)
        st.progress(int(score) / 100)
        if llm_summary:
            st.markdown(
                f'<div class="summary-box">💬 {llm_summary}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🎯 Overview", "🔧 Skills", "💡 Suggestions", "📝 Section Feedback", "🔬 Semantic Analysis"]
    )

    # ── Tab 1: Overview ───────────────────────────────────────────────────
    with tab1:
        st.markdown("### 📊 Match Overview")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### ✅ Matched Skills")
            st.markdown(render_skills(matched, "matched"), unsafe_allow_html=True)
        with col_b:
            st.markdown("#### ❌ Missing Skills")
            st.markdown(render_skills(missing, "missing"), unsafe_allow_html=True)

        if suggestions:
            st.markdown("#### 💡 Top Suggestion")
            st.markdown(
                f'<div class="suggestion-item">'
                f'<span class="suggestion-icon">→</span>{suggestions[0]}</div>',
                unsafe_allow_html=True,
            )

    # ── Tab 2: Skills ─────────────────────────────────────────────────────
    with tab2:
        st.markdown("### 🔧 Full Skills Breakdown")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"#### ✅ Matched ({len(matched)})",
            )
            if matched:
                st.markdown(render_skills(matched, "matched"), unsafe_allow_html=True)
            else:
                st.info("No common skills detected between resume and JD.")
        with c2:
            st.markdown(f"#### ❌ Missing ({len(missing)})")
            if missing:
                st.markdown(render_skills(missing, "missing"), unsafe_allow_html=True)
                st.markdown(
                    "<br/><small style='color:#94a3b8;'>💡 Add these skills to your resume "
                    "if you genuinely have them.</small>",
                    unsafe_allow_html=True,
                )
            else:
                st.success("🎉 Great — no critical skill gaps detected!")

    # ── Tab 3: Suggestions ────────────────────────────────────────────────
    with tab3:
        st.markdown("### 💡 Improvement Suggestions")
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                st.markdown(
                    f'<div class="suggestion-item">'
                    f'<span class="suggestion-icon">{i}.</span>{suggestion}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No specific suggestions generated. Your resume is well aligned!")

    # ── Tab 4: Section Feedback ───────────────────────────────────────────
    with tab4:
        st.markdown("### 📝 Section-wise Feedback")

        section_icons = {
            "summary": ("📋", "Summary / Objective"),
            "experience": ("💼", "Work Experience"),
            "skills": ("🔧", "Skills"),
            "education": ("🎓", "Education"),
            "projects": ("🚀", "Projects"),
            "certifications": ("🏅", "Certifications"),
        }

        has_feedback = False
        for key, (icon, label) in section_icons.items():
            feedback_text = section_fb.get(key)
            if feedback_text and feedback_text.lower() not in ("null", "none", ""):
                has_feedback = True
                st.markdown(
                    f"""
                    <div class="section-card">
                        <div class="section-title">{icon} {label}</div>
                        <div class="section-body">{feedback_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        if not has_feedback:
            st.info("No section-level feedback was generated.")

    # ── Tab 5: Semantic Analysis ──────────────────────────────────────────
    with tab5:
        st.markdown("### 🔬 Semantic Similarity Analysis")

        col_x, col_y = st.columns(2)

        with col_x:
            st.markdown("#### 🟢 Top Matching Passages")
            st.caption("Resume passages most aligned with the job description.")
            if top_chunks:
                for i, chunk in enumerate(top_chunks[:3], 1):
                    with st.expander(f"Match #{i}", expanded=(i == 1)):
                        st.write(chunk)
            else:
                st.info("No matching passages to display.")

        with col_y:
            st.markdown("#### 🔴 Semantic Gaps")
            st.caption("JD areas not well covered by your resume.")
            if semantic_gaps:
                for gap in semantic_gaps[:5]:
                    st.markdown(
                        f"""<div class="section-card">
                            <div class="section-body" style="color:#f87171;">⚠️ {gap}…</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
            else:
                st.success("✅ No significant semantic gaps detected.")


if __name__ == "__main__":
    main()
