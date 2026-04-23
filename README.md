# 🎯 AI Resume Analyzer + ATS Scorer

A production-quality resume analysis system that combines semantic embeddings, FAISS vector search, and Groq LLM to give ATS scores, skill gap analysis, and actionable improvement suggestions.

---

## 🏗️ Architecture

```
Resume Analyzer/
├── backend/
│   ├── app.py                  # FastAPI entry point
│   ├── routes/
│   │   └── analyze.py          # POST /api/v1/analyze
│   ├── services/
│   │   ├── parser.py           # PDF parsing (PyMuPDF)
│   │   ├── embedding.py        # sentence-transformers + FAISS
│   │   ├── scorer.py           # ATS scoring + skill extraction
│   │   └── llm.py              # Groq LLM integration
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   └── utils/
│       └── helpers.py          # Text normalization, chunking
├── frontend/
│   └── streamlit_app.py        # Streamlit UI
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| PDF Parsing | PyMuPDF (fitz) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector Search | FAISS (CPU) |
| LLM | Groq API (`llama-3.3-70b-versatile`) |
| Frontend | Streamlit |
| Validation | Pydantic v2 |

---

## 🚀 Quick Start

### 1. Clone & set up the environment

```bash
cd "Resume analyser"

# Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your Groq API key:

```env
GROQ_API_KEY=gsk_your_actual_key_here
```

> **Get a free Groq API key** at [console.groq.com](https://console.groq.com)

### 3. Start the backend

```bash
cd backend
python app.py
```

The API will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

> **First run**: The `all-MiniLM-L6-v2` model (~22 MB) will be downloaded automatically on startup.

### 4. Start the frontend (new terminal)

```bash
cd frontend
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

---

## 🔑 API Reference

### `POST /api/v1/analyze`

**Content-Type:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `resume` | `File` | PDF resume (max 10 MB) |
| `job_description` | `string` | Full job description text (min 50 chars) |

**Response:**

```json
{
  "score": 74.3,
  "matched_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
  "missing_skills": ["Kubernetes", "Terraform", "AWS"],
  "suggestions": [
    "Quantify achievements in experience section with metrics",
    "Add a dedicated skills section with proficiency levels",
    "Include links to GitHub projects relevant to the role"
  ],
  "section_feedback": {
    "summary": "Your summary is strong but lacks role-specific keywords.",
    "experience": "Good depth of experience but bullet points need action verbs.",
    "skills": "Missing cloud infrastructure skills required by this role.",
    "education": null,
    "projects": "Consider adding live deployment links to projects.",
    "certifications": null
  },
  "top_matching_chunks": ["..."],
  "semantic_gaps": ["..."],
  "llm_summary": "Overall strong candidate but lacks cloud skills..."
}
```

---

## 🧠 How It Works

### Pipeline (per request)

```
PDF Upload
    ↓
PyMuPDF text extraction + normalization
    ↓
sentence-transformers encode (resume + JD)
    ↓
┌─────────────────────────────────────────┐
│  FAISS IndexFlatIP (cosine similarity)  │
│  · document-level ATS score             │
│  · top matching chunks                  │
│  · semantic gap detection               │
└─────────────────────────────────────────┘
    ↓
Groq LLM (llama-3.3-70b-versatile)
│  · structured JSON prompt               │
│  · skill extraction (resume + JD)       │
│  · improvement suggestions              │
│  · section-wise feedback                │
    ↓
Hybrid skill comparison
(regex vocabulary ∪ LLM skills) → matched / missing
    ↓
Pydantic AnalysisResponse → Streamlit UI
```

### ATS Score Formula

```
doc_similarity = cosine_similarity(embed(resume), embed(jd))
raw_score      = clamp(doc_similarity, 0, 1)
ats_score      = round((raw_score ^ 0.75) * 100, 1)
```

The power curve (`^0.75`) prevents mid-range resumes from clustering too tightly near 50.

---

## 🔧 Configuration

All settings are controlled via environment variables (`.env`):

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Your Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model ID |
| `GROQ_MAX_TOKENS` | `2048` | Max LLM response tokens |
| `GROQ_TEMPERATURE` | `0.3` | Lower = more factual |
| `BACKEND_URL` | `http://localhost:8000` | Backend URL used by Streamlit |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot connect to backend` | Ensure `python app.py` is running in `backend/` |
| `GROQ_API_KEY is not set` | Copy `.env.example` → `.env` and add your key |
| `PDF has no extractable text` | Use a digital PDF, not a scanned image |
| `Model download slow` | One-time 22 MB download; cached afterwards |
| `faiss-cpu` import error | Run `pip install faiss-cpu` separately if needed |

---

## 📄 License

MIT — free to use, modify, and distribute.
