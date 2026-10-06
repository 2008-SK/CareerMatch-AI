import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast
import time
from io import BytesIO
from urllib.parse import quote_plus

# Optional PDF/OCR libraries
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    fitz = None
    HAS_PYMUPDF = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    Image = None
    HAS_PIL = False

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    pytesseract = None
    HAS_OCR = False

# Optional library for course certificates
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# Optional libraries for Resume + NLP features
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None

try:
    from sentence_transformers import SentenceTransformer, util
    HAS_NLP = True
except ImportError:
    HAS_NLP = False


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="CareerBridge AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# MODERN UI THEME
# =====================================================
# Additional professional UI polish
st.markdown("""
<style>
.block-container { max-width: 1400px; padding-top: 1.4rem; padding-bottom: 2.5rem; }
[data-testid="stTabs"] button { font-weight: 700; padding: 0.75rem 1rem; }
[data-testid="stMetric"] { background: rgba(255,255,255,.78); border: 1px solid rgba(99,102,241,.12); border-radius: 16px; padding: 12px; box-shadow: 0 6px 18px rgba(15,23,42,.06); }
.stButton > button, .stDownloadButton > button { border-radius: 12px !important; font-weight: 700 !important; min-height: 44px; }
div[data-testid="stExpander"] { border-radius: 16px; border: 1px solid rgba(99,102,241,.14); overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f7f9ff 0%, #eef4ff 45%, #f9f5ff 100%);
    }
    [data-testid="stHeader"] { background: rgba(255,255,255,0); }
    .hero-card {
        padding: 30px 34px;
        border-radius: 24px;
        background: linear-gradient(135deg, #172554, #4338ca 55%, #7c3aed);
        color: white;
        box-shadow: 0 14px 35px rgba(67,56,202,.20);
        margin-bottom: 22px;
    }
    .hero-card h1 { margin: 0; font-size: 2.45rem; }
    .hero-card p { margin: 7px 0 0; font-size: 1.05rem; opacity: .92; }
    .course-card {
        padding: 20px;
        border-radius: 18px;
        background: white;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 24px rgba(15,23,42,.07);
        margin: 10px 0;
    }
    .video-card {
        padding: 18px 20px;
        border-radius: 18px;
        background: white;
        border-left: 6px solid #6366f1;
        box-shadow: 0 7px 22px rgba(15,23,42,.07);
        margin: 10px 0 14px;
    }
    .video-done { border-left-color: #16a34a; background: linear-gradient(90deg,#f0fdf4,#ffffff); }
    .video-wait { border-left-color: #f59e0b; background: linear-gradient(90deg,#fffbeb,#ffffff); }
    .badge {
        display:inline-block; padding:5px 11px; border-radius:999px;
        font-size:.82rem; font-weight:700; margin-bottom:7px;
    }
    .badge-green { background:#dcfce7; color:#166534; }
    .badge-blue { background:#dbeafe; color:#1e40af; }
    .badge-orange { background:#fef3c7; color:#92400e; }
    .progress-wrap {
        padding: 16px 18px; border-radius: 16px; background:#ffffff;
        box-shadow: 0 7px 20px rgba(15,23,42,.06); margin: 12px 0 20px;
    }
    div.stButton > button[kind="primary"] {
        border-radius: 12px; font-weight: 700;
        background: linear-gradient(90deg,#4f46e5,#7c3aed);
        border: none;
    }
    .certificate-note {
        padding: 15px 18px; border-radius: 14px;
        background: linear-gradient(90deg,#eff6ff,#f5f3ff);
        border:1px solid #c7d2fe; color:#312e81;
    }
    .auth-card { max-width:720px; margin:35px auto 22px; padding:38px 30px; text-align:center; border-radius:28px; color:white; background:linear-gradient(135deg,#111827,#3730a3 55%,#7c3aed); box-shadow:0 18px 45px rgba(55,48,163,.25); }
    .auth-card h1 { margin:8px 0 5px; font-size:2.6rem; }
    .auth-card p { margin:0; opacity:.9; font-size:1rem; }
    .auth-icon { font-size:3rem; }
    .feature-chip { display:inline-block; padding:7px 12px; margin:4px; border-radius:999px; background:#eef2ff; color:#3730a3; font-weight:700; font-size:.82rem; }
    .course-hero { padding:26px 28px; border-radius:24px; color:white; margin:10px 0 22px; background:linear-gradient(135deg,#0f172a,#4f46e5 58%,#9333ea); box-shadow:0 14px 35px rgba(79,70,229,.20); }
    .course-hero h2 { margin:0 0 6px; }
    .course-hero p { margin:0; opacity:.9; }
    .status-complete { color:#15803d; font-weight:800; }
</style>
""", unsafe_allow_html=True)

# =====================================================
# USER DATA / AUTHENTICATION
# =====================================================

USER_FILE = "user_data.json"


def load_user():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r") as file:
                return json.load(file)
        except Exception:
            return None
    return None


def save_user(user):
    with open(USER_FILE, "w", encoding="utf-8") as file:
        json.dump(user, file, indent=2)


def ensure_user_history(user):
    """Add history fields to older user_data.json files safely."""
    changed = False
    if "login_history" not in user or not isinstance(user.get("login_history"), list):
        user["login_history"] = []
        changed = True
    if "course_history" not in user or not isinstance(user.get("course_history"), list):
        user["course_history"] = []
        changed = True
    if changed:
        save_user(user)
    return user


def record_login_history(user):
    """Save login history with username and date only (no time)."""
    user = ensure_user_history(user)
    user["login_history"].insert(0, {
        "username": user.get("username", "User"),
        "date": pd.Timestamp.now().strftime("%d %B %Y")
    })
    user["login_history"] = user["login_history"][:30]
    save_user(user)


def record_course_completion(user, course_title, score, certificate_id):
    user = ensure_user_history(user)
    # Keep the history clean: one completion record per course/certificate.
    existing = [
        item for item in user["course_history"]
        if item.get("course_title") == course_title
    ]
    if not existing:
        user["course_history"].insert(0, {
            "course_title": course_title,
            "score": score,
            "certificate_id": certificate_id,
            "completed_on": pd.Timestamp.now().strftime("%d %B %Y, %I:%M %p")
        })
        user["course_history"] = user["course_history"][:50]
        save_user(user)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "resume_skills" not in st.session_state:
    st.session_state.resume_skills = set()

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "recommendations" not in st.session_state:
    st.session_state.recommendations = None

if "recommendation_source" not in st.session_state:
    st.session_state.recommendation_source = "Manual Skills"

if "active_skill_course" not in st.session_state:
    st.session_state.active_skill_course = None

if "course_progress" not in st.session_state:
    st.session_state.course_progress = {}

if "course_quiz_results" not in st.session_state:
    st.session_state.course_quiz_results = {}

if "course_certificates" not in st.session_state:
    st.session_state.course_certificates = {}

if "independent_active_course" not in st.session_state:
    st.session_state.independent_active_course = None

if "independent_course_data" not in st.session_state:
    st.session_state.independent_course_data = None

if "independent_course_title" not in st.session_state:
    st.session_state.independent_course_title = None


# =====================================================
# LOGIN SYSTEM
# =====================================================

if not st.session_state.logged_in:

    st.markdown("""
    <div class="auth-card">
        <div class="auth-icon">💼</div>
        <h1>CareerBridge AI</h1>
        <p>Smart Job Recommendation & Skill Development Platform</p>
    </div>
    """, unsafe_allow_html=True)

    option = st.radio(
        "Choose an option",
        ["Login", "Register", "Forgot Password"],
        horizontal=True
    )

    if option == "Register":
        st.subheader("Create Account")

        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button("Register", use_container_width=True):
            if not email or not username or not password:
                st.warning("Please fill all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must contain at least 6 characters.")
            else:
                save_user({
                    "email": email,
                    "username": username,
                    "password": hash_password(password),
                    "login_history": [],
                    "course_history": []
                })
                st.success(
                    "Registration successful! You can now login."
                )

    elif option == "Login":
        st.subheader("Login")

        login_id = st.text_input("Email or Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            user = load_user()

            if user is None:
                st.warning("No account found. Please register first.")
            elif (
                login_id == user["email"]
                or login_id == user["username"]
            ) and hash_password(password) == user["password"]:
                user = ensure_user_history(user)
                record_login_history(user)
                st.session_state.logged_in = True
                st.session_state.current_user = user
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Incorrect email/username or password.")

    else:
        st.subheader("🔑 Forgot Password")

        email = st.text_input("Enter your registered email")
        new_password = st.text_input(
            "New Password",
            type="password"
        )
        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        if st.button("Reset Password", use_container_width=True):
            user = load_user()

            if user is None:
                st.error("No registered account found.")
            elif email != user["email"]:
                st.error("Email does not match the registered email.")
            elif len(new_password) < 6:
                st.error("Password must contain at least 6 characters.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                user["password"] = hash_password(new_password)
                save_user(user)
                st.success(
                    "Password reset successfully! You can now login."
                )

    st.stop()


# =====================================================
# LOGOUT + USER HISTORY
# =====================================================

current_user = ensure_user_history(load_user() or {})
st.session_state.current_user = current_user

st.sidebar.markdown("### 👤 Account")
st.sidebar.caption(f"Signed in as **{current_user.get('username', 'User')}**")

st.sidebar.caption("📜 View Login & Course History from the History tab.")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()


# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data
def load_dataset():
    if not os.path.exists("Cleaned_New_Data.csv"):
        return pd.DataFrame()
    return pd.read_csv("Cleaned_New_Data.csv")


df = load_dataset()

if df.empty:
    st.error(
        "Cleaned_New_Data.csv was not found or contains no data."
    )
    st.stop()


required_columns = [
    "job_id",
    "category",
    "job_title",
    "job_description",
    "job_skill_set"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    st.error(
        "Dataset is missing required columns: "
        + ", ".join(missing_columns)
    )
    st.stop()


for column in ["category", "job_title", "job_description", "job_skill_set"]:
    df[column] = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
    )


# =====================================================
# NLP MODEL
# =====================================================

@st.cache_resource
def load_nlp_model():
    if not HAS_NLP:
        return None
    try:
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


nlp_model = load_nlp_model()


# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown(
    """
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

.hero {
    text-align: center;
    padding: 32px;
    border-radius: 22px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 25px;
    background: linear-gradient(
        135deg,
        rgba(128,128,128,0.08),
        rgba(128,128,128,0.02)
    );
}

.hero h1 {
    font-size: 42px;
    margin-bottom: 8px;
}

.hero p {
    font-size: 17px;
    opacity: 0.85;
}

.section-box {
    padding: 18px;
    border-radius: 16px;
    border: 1px solid rgba(128,128,128,0.22);
    margin: 12px 0 20px 0;
    background: rgba(128,128,128,0.025);
}

.job-card {
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 16px;
    background: rgba(128,128,128,0.025);
}

.job-title {
    font-size: 23px;
    font-weight: 700;
}

.match-score {
    font-size: 22px;
    font-weight: 700;
}

.skill-tag {
    display: inline-block;
    padding: 5px 10px;
    margin: 3px;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 600;
}

.skill-matched {
    background-color: #d4edda;
    color: #155724;
}

.skill-missing {
    background-color: #f8d7da;
    color: #721c24;
}

.stButton > button {
    min-height: 48px;
    border-radius: 12px;
    font-weight: 600;
}

.footer {
    text-align: center;
    padding: 20px;
    opacity: 0.7;
}
</style>
""",
    unsafe_allow_html=True
)


# =====================================================
# HEADER
# =====================================================

st.markdown(
    """
<div class="hero">
    <h1>💼 CareerBridge AI</h1>
    <p><b>AI-Assisted Smart Job Recommendation System</b></p>
    <p>Find suitable jobs using your skills, resume and NLP-based matching.</p>
</div>
""",
    unsafe_allow_html=True
)


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def clean_skill(skill):
    if not skill:
        return ""

    skill = str(skill).lower().strip()
    skill = skill.replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", skill).strip()


def extract_required_skills(skill_text):
    if pd.isna(skill_text) or not str(skill_text).strip():
        return set()

    text = str(skill_text).strip()

    try:
        parsed = ast.literal_eval(text)

        if isinstance(parsed, (list, tuple, set)):
            return {
                clean_skill(s)
                for s in parsed
                if clean_skill(s)
            }
    except (ValueError, SyntaxError):
        pass

    text = (
        text
        .replace(",", "|")
        .replace(";", "|")
        .replace("/", "|")
    )

    return {
        clean_skill(s)
        for s in text.split("|")
        if clean_skill(s)
    }


def extract_user_skills(user_text):
    if not user_text or not user_text.strip():
        return set()

    return {
        clean_skill(s)
        for s in user_text.split(",")
        if clean_skill(s)
    }


def calculate_skill_score(user_skill_set, required_skill_set):
    if not user_skill_set or not required_skill_set:
        return 0.0, 0.0, 0.0, set()

    matched_skills = user_skill_set.intersection(
        required_skill_set
    )

    matched_count = len(matched_skills)

    precision = matched_count / len(user_skill_set)
    recall = matched_count / len(required_skill_set)

    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = (
            2 * precision * recall
            / (precision + recall)
        )

    return (
        round(f1_score * 100, 2),
        round(precision * 100, 2),
        round(recall * 100, 2),
        matched_skills
    )


def _reset_uploaded_file(uploaded_file):
    """Safely move Streamlit's uploaded-file pointer back to the beginning."""
    try:
        uploaded_file.seek(0)
    except Exception:
        pass


def _clean_extracted_text(text):
    """Normalize extracted resume text while preserving useful punctuation."""
    if not text:
        return ""

    text = str(text).replace("\x00", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pdf_text_pymupdf(file_bytes):
    """Extract text from normal/text PDFs using PyMuPDF."""
    if not HAS_PYMUPDF:
        return ""

    text_parts = []
    document = None
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
        for page in document:
            page_text = page.get_text("text", sort=True) or ""
            if page_text.strip():
                text_parts.append(page_text)
    except Exception:
        return ""
    finally:
        if document is not None:
            try:
                document.close()
            except Exception:
                pass

    return _clean_extracted_text("\n".join(text_parts))


def _extract_pdf_text_pdfplumber(file_bytes):
    """Second PDF text-extraction fallback."""
    if pdfplumber is None:
        return ""

    text_parts = []
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
                if page_text.strip():
                    text_parts.append(page_text)
    except Exception:
        return ""

    return _clean_extracted_text("\n".join(text_parts))


def _ocr_pdf(file_bytes):
    """OCR scanned/image PDFs when Tesseract is available."""
    if not (HAS_PYMUPDF and HAS_OCR and HAS_PIL):
        return ""

    text_parts = []
    document = None
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
        for page in document:
            # 2x rendering gives OCR much better accuracy for resumes.
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_text = pytesseract.image_to_string(image, config="--psm 6") or ""
            if page_text.strip():
                text_parts.append(page_text)
    except Exception:
        return ""
    finally:
        if document is not None:
            try:
                document.close()
            except Exception:
                pass

    return _clean_extracted_text("\n".join(text_parts))


def _extract_docx_text(file_bytes):
    """Extract text from paragraphs, tables, headers and footers in DOCX."""
    if docx is None:
        return ""

    text_parts = []
    try:
        document = docx.Document(BytesIO(file_bytes))

        for paragraph in document.paragraphs:
            if paragraph.text and paragraph.text.strip():
                text_parts.append(paragraph.text)

        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    text_parts.append(" | ".join(cells))

        for section in document.sections:
            for paragraph in section.header.paragraphs:
                if paragraph.text and paragraph.text.strip():
                    text_parts.append(paragraph.text)
            for paragraph in section.footer.paragraphs:
                if paragraph.text and paragraph.text.strip():
                    text_parts.append(paragraph.text)

    except Exception:
        return ""

    return _clean_extracted_text("\n".join(text_parts))


def parse_resume(uploaded_file):
    """Robust resume parser for PDF, DOCX and TXT.

    PDF extraction uses multiple fallbacks and OCR for scanned resumes.
    """
    if uploaded_file is None:
        return ""

    file_type = uploaded_file.name.rsplit(".", 1)[-1].lower()

    try:
        _reset_uploaded_file(uploaded_file)
        file_bytes = uploaded_file.getvalue()
    except Exception:
        _reset_uploaded_file(uploaded_file)
        file_bytes = uploaded_file.read()

    if not file_bytes:
        return ""

    try:
        if file_type == "pdf":
            # 1) Fast and reliable text extraction for normal PDFs.
            extracted_text = _extract_pdf_text_pymupdf(file_bytes)

            # 2) Fallback for PDFs that PyMuPDF cannot parse well.
            if len(re.sub(r"\s+", "", extracted_text)) < 40:
                fallback_text = _extract_pdf_text_pdfplumber(file_bytes)
                if len(fallback_text) > len(extracted_text):
                    extracted_text = fallback_text

            # 3) OCR fallback for scanned/image-only resumes.
            if len(re.sub(r"\s+", "", extracted_text)) < 40:
                ocr_text = _ocr_pdf(file_bytes)
                if len(ocr_text) > len(extracted_text):
                    extracted_text = ocr_text

            return _clean_extracted_text(extracted_text)

        if file_type == "docx":
            return _extract_docx_text(file_bytes)

        if file_type == "txt":
            return _clean_extracted_text(
                file_bytes.decode("utf-8", errors="ignore")
            )

    except Exception as exc:
        st.error(f"Unable to read resume: {exc}")
        return ""

    return ""


def _normalize_resume_for_skill_matching(text):
    """Normalize resume text for reliable skill matching."""
    text = str(text).lower()
    replacements = {
        "machine-learning": "machine learning",
        "machinelearning": "machine learning",
        "power-bi": "power bi",
        "powerbi": "power bi",
        "ms-excel": "excel",
        "microsoft excel": "excel",
        "microsoft sql server": "sql server",
        "scikit-learn": "scikit learn",
        "sklearn": "scikit learn",
        "c sharp": "c#",
        "c plus plus": "c++",
        "node.js": "nodejs",
        "react.js": "react",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[\u2010-\u2015\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _skill_aliases(skill):
    """Return common resume spellings for a canonical dataset skill."""
    canonical = clean_skill(skill)
    aliases = {canonical}
    alias_map = {
        "python": {"python", "python3", "python 3"},
        "sql": {"sql", "structured query language"},
        "machine learning": {"machine learning", "ml", "machinelearning"},
        "deep learning": {"deep learning", "dl"},
        "artificial intelligence": {"artificial intelligence", "ai"},
        "data analysis": {"data analysis", "data analytics"},
        "data science": {"data science", "data scientist"},
        "excel": {"excel", "ms excel", "microsoft excel", "msexcel"},
        "power bi": {"power bi", "powerbi", "microsoft power bi"},
        "tableau": {"tableau"},
        "pandas": {"pandas"},
        "numpy": {"numpy"},
        "scikit learn": {"scikit learn", "scikit-learn", "sklearn"},
        "c++": {"c++", "cpp", "c plus plus"},
        "c#": {"c#", "c sharp"},
        "javascript": {"javascript", "java script", "js"},
        "typescript": {"typescript", "ts"},
        "html": {"html", "html5"},
        "css": {"css", "css3"},
        "react": {"react", "reactjs", "react.js"},
        "nodejs": {"nodejs", "node js", "node.js"},
        "git": {"git", "github"},
        "github": {"github"},
    }
    aliases.update(alias_map.get(canonical, set()))
    return aliases


def _contains_skill(normalized_text, skill_variant):
    """Match a skill variant without failing on symbols such as C++, C# or .NET."""
    variant = clean_skill(skill_variant)
    if not variant:
        return False

    if variant in {"c++", "c#", ".net", "r", "go"}:
        compact_text = re.sub(r"\s+", "", normalized_text)
        compact_variant = re.sub(r"\s+", "", variant)
        return compact_variant in compact_text

    variant = re.sub(r"\s+", " ", variant)
    pattern = r"(?<![a-z0-9])" + re.escape(variant).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
    return re.search(pattern, normalized_text, flags=re.IGNORECASE) is not None


def extract_skills_from_resume(raw_text, dataset_skills):
    """Extract dataset-recognized skills with aliases and robust boundaries."""
    if not raw_text:
        return set()

    normalized_text = _normalize_resume_for_skill_matching(raw_text)
    found = set()

    for skill in sorted(dataset_skills, key=lambda x: len(str(x)), reverse=True):
        canonical = clean_skill(skill)
        if not canonical:
            continue

        if any(_contains_skill(normalized_text, alias) for alias in _skill_aliases(canonical)):
            found.add(canonical)

    return found

def calculate_semantic_score(
    user_profile,
    job_title,
    job_description,
    required_skills
):
    if not nlp_model or not user_profile.strip():
        return 0.0

    job_profile = (
        f"Job Title: {job_title}. "
        f"Required Skills: {', '.join(sorted(required_skills))}. "
        f"Job Description: {job_description[:700]}"
    )

    try:
        embeddings = nlp_model.encode(
            [user_profile, job_profile],
            convert_to_tensor=True,
            normalize_embeddings=True
        )

        similarity = util.cos_sim(
            embeddings[0],
            embeddings[1]
        ).item()

        # Cosine similarity can theoretically be below 0.
        # Convert to a safe 0-100 score.
        return round(
            max(0.0, min(1.0, similarity)) * 100,
            2
        )

    except Exception:
        return 0.0


# =====================================================
# CORE RECOMMENDATION ENGINE
# POSITION INPUT REMOVED
# =====================================================

def get_recommendations(
    category,
    user_skills,
    semantic_enabled=True
):
    category_data = df[
        df["category"] == category
    ].copy()

    if category_data.empty:
        return category_data

    user_skill_set = extract_user_skills(user_skills)

    if not user_skill_set:
        return category_data.iloc[0:0]

    results = []

    for index, row in category_data.iterrows():

        required_skills = extract_required_skills(
            row["job_skill_set"]
        )

        if not required_skills:
            continue

        # DIRECT SKILL SCORE
        (
            skill_score,
            precision_percentage,
            recall_percentage,
            matched_skills
        ) = calculate_skill_score(
            user_skill_set,
            required_skills
        )

        # Position input removed.
        # Skill score is now the main direct matching score.
        original_final_score = skill_score

        # NEW AI/NLP SCORE
        semantic_score = 0.0

        if semantic_enabled:
            semantic_score = calculate_semantic_score(
                user_skills,
                row["job_title"],
                row["job_description"],
                required_skills
            )

        # AI-assisted score
        ai_assisted_score = (
            original_final_score * 0.75
            + semantic_score * 0.25
        ) if semantic_enabled and nlp_model else original_final_score

        results.append({
            "index": index,
            "match_percentage": round(
                original_final_score,
                2
            ),
            "ai_assisted_score": round(
                ai_assisted_score,
                2
            ),
            "matched_skills": matched_skills,
            "missing_skills": required_skills - matched_skills,
            "skill_score": skill_score,
            "precision_percentage": precision_percentage,
            "recall_percentage": recall_percentage,
            "semantic_score": semantic_score,
            "required_skill_count": len(required_skills),
            "matched_skill_count": len(matched_skills)
        })

    if not results:
        return category_data.iloc[0:0]

    result_df = pd.DataFrame(results)

    recommendations = category_data.merge(
        result_df,
        left_index=True,
        right_on="index"
    )

    # Rank based on skill matching.
    recommendations = (
        recommendations
        .sort_values(
            by=[
                "match_percentage",
                "skill_score",
                "semantic_score"
            ],
            ascending=False
        )
        .head(5)
    )

    return recommendations


def get_course_for_skill(skill):
    """Safely map a missing job skill to one of the fixed learning courses."""
    normalized = clean_skill(skill)

    skill_map = {
        "python": "python",
        "sql": "sql",
        "pandas": "pandas",
        "machine learning": "machine_learning",
        "ml": "machine_learning",
        "java": "java",
        "javascript": "javascript",
        "js": "javascript",
        "excel": "excel",
        "microsoft excel": "excel",
    }

    course_key = skill_map.get(normalized)

    if course_key is None:
        # Try a safe partial match for skills such as "python programming".
        for skill_name, mapped_key in skill_map.items():
            if skill_name in normalized or normalized in skill_name:
                course_key = mapped_key
                break

    if course_key is None or course_key not in VIDEO_COURSES:
        # Always return a valid fallback course instead of raising NameError/KeyError.
        course_key = "python"

    course = VIDEO_COURSES[course_key]
    return course_key, {
        "title": course.get("title", "Python Programming Fundamentals"),
        "duration": course.get("duration", "3–4 hours"),
        "level": course.get("level", "Beginner"),
    }


def show_selected_skill_course():
    """Show a fixed course selected from Skill Improvement Resources."""
    active = st.session_state.get("active_skill_course")
    if not active:
        return

    job_title, missing_skill = active
    course_key, course_info = get_course_for_skill(missing_skill)
    course = VIDEO_COURSES[course_key].copy()
    course_instance_key = f"skill_gap::{course_key}::{job_title}::{missing_skill}"

    st.divider()
    st.markdown("### 🎓 Recommended Skill Course")
    st.info(
        f"This course was selected because **{missing_skill.title()}** is a skill gap for **{job_title}**."
    )
    st.markdown(
        f"**{course_info['title']}**  •  {course_info['level']}  •  {course_info['duration']}"
    )

    if st.button(
        "▶️ Open Skill Course",
        key="open_selected_skill_course",
        type="primary",
        use_container_width=True
    ):
        st.session_state.active_skill_course_open = True

    if st.session_state.get("active_skill_course_open", False):
        show_video_course(course_key, course, course_instance_key)


def youtube_search_url(skill):
    query = quote_plus(
        f"{skill} tutorial for beginners"
    )
    return (
        "https://www.youtube.com/results"
        f"?search_query={query}"
    )


# =====================================================
# COURSES & SKILL DEVELOPMENT — FIXED VIDEO COURSES
# =====================================================

# IMPORTANT:
# - Every course contains exactly 6 FIXED YouTube videos.
# - No YouTube search results are shown.
# - There is NO "Mark Video Completed" button.
# - Certificate unlocks only after the final assessment is passed.
# - YouTube watch time cannot be automatically verified by a normal
#   Streamlit app, so the final quiz is used as the course completion check.

VIDEO_COURSES = {
    "python": {
        "title": "Python Programming Fundamentals",
        "category": "Information Technology",
        "level": "Beginner",
        "duration": "3–4 hours",
        "videos": [
            ("Python Introduction & Setup", "https://www.youtube.com/watch?v=rfscVS0vtbw"),
            ("Python Variables & Data Types", "https://www.youtube.com/watch?v=khKv-8q7YmY"),
            ("Python Conditions & Loops", "https://www.youtube.com/watch?v=6iF8Xb7Z3wQ"),
            ("Python Functions", "https://www.youtube.com/watch?v=u-OmVr_fT4s"),
            ("Python Lists, Tuples & Sets", "https://www.youtube.com/watch?v=W8KRzm-HUcc"),
            ("Python Dictionaries & Practical Basics", "https://www.youtube.com/watch?v=daefaLgNkw0"),
        ],
        "quiz": [
            ("Which keyword defines a function in Python?", ["function", "def", "fun", "define"], "B"),
            ("Which collection stores key-value pairs?", ["List", "Tuple", "Dictionary", "Set"], "C"),
            ("Which loop is commonly used to iterate over a sequence?", ["for", "switch", "case", "goto"], "A"),
            ("Which symbol starts a Python comment?", ["//", "<!--", "#", "/*"], "C"),
            ("What does len() return?", ["The last item", "The number of items", "The data type", "The memory size"], "B"),
        ],
    },
    "sql": {
        "title": "SQL for Data Analysis",
        "category": "Information Technology",
        "level": "Beginner",
        "duration": "3–4 hours",
        "videos": [
            ("SQL Introduction & SELECT", "https://www.youtube.com/watch?v=HXV3zeQKqGY"),
            ("SQL WHERE, AND & OR", "https://www.youtube.com/watch?v=7S_tz1z_5bA"),
            ("SQL ORDER BY & Filtering", "https://www.youtube.com/watch?v=qw--VYLpxG4"),
            ("SQL GROUP BY & Aggregate Functions", "https://www.youtube.com/watch?v=9yeOJ0ZMUYw"),
            ("SQL JOINs", "https://www.youtube.com/watch?v=9yeOJ0ZMUYw"),
            ("SQL Practical Data Analysis", "https://www.youtube.com/watch?v=7mz73uXD9DA"),
        ],
        "quiz": [
            ("Which command retrieves data?", ["SELECT", "INSERT", "DELETE", "DROP"], "A"),
            ("Which clause filters rows?", ["GROUP BY", "WHERE", "ORDER BY", "JOIN"], "B"),
            ("Which function calculates an average?", ["COUNT", "SUM", "AVG", "MAX"], "C"),
            ("Which clause groups records?", ["GROUP BY", "WHERE", "VALUES", "SET"], "A"),
            ("Which operation combines related tables?", ["JOIN", "SORT", "PRINT", "LOOP"], "A"),
        ],
    },
    "pandas": {
        "title": "Pandas & Data Analysis",
        "category": "Information Technology",
        "level": "Beginner",
        "duration": "3–4 hours",
        "videos": [
            ("Pandas Introduction & DataFrames", "https://www.youtube.com/watch?v=vmEHCJofslg"),
            ("Reading CSV Files with Pandas", "https://www.youtube.com/watch?v=dcqPhpY7tWk"),
            ("Selecting & Filtering Data", "https://www.youtube.com/watch?v=2wMfQ7jL6oI"),
            ("Cleaning Data with Pandas", "https://www.youtube.com/watch?v=rlNwJ7xF9Y0"),
            ("GroupBy & Data Analysis", "https://www.youtube.com/watch?v=9d9BM3oY3i0"),
            ("Pandas Practical Data Analysis", "https://www.youtube.com/watch?v=R67XuYc9NQ4"),
        ],
        "quiz": [
            ("Which library provides DataFrame?", ["NumPy", "Pandas", "Matplotlib", "Flask"], "B"),
            ("Which function reads a CSV file?", ["read_csv", "load_csv", "open_csv", "csv_read"], "A"),
            ("Which method removes duplicate rows?", ["drop_duplicates", "remove_rows", "unique_rows", "delete_duplicates"], "A"),
            ("Which attribute gives column names?", ["df.columns", "df.names", "df.fields", "df.headers"], "A"),
            ("Which method shows the first rows?", ["tail", "head", "first", "top"], "B"),
        ],
    },
    "machine_learning": {
        "title": "Machine Learning Fundamentals",
        "category": "Information Technology",
        "level": "Beginner",
        "duration": "4–5 hours",
        "videos": [
            ("What is Machine Learning?", "https://www.youtube.com/watch?v=ukzFI9rgwfU"),
            ("Supervised vs Unsupervised Learning", "https://www.youtube.com/watch?v=1FZ0A1QCMWc"),
            ("Features, Labels & Training Data", "https://www.youtube.com/watch?v=0Lt9w-BxKFQ"),
            ("Train-Test Split & Preprocessing", "https://www.youtube.com/watch?v=fwY9Qv96DJY"),
            ("Model Training & Prediction", "https://www.youtube.com/watch?v=7eh4d6sabA0"),
            ("Model Evaluation Basics", "https://www.youtube.com/watch?v=85dtiMz9tSo"),
        ],
        "quiz": [
            ("What is a feature?", ["Input variable", "Final report", "Password", "Output format"], "A"),
            ("Which learning type uses labelled data?", ["Supervised", "Unsupervised", "Random", "Manual"], "A"),
            ("What does model.fit() generally do?", ["Deletes data", "Trains the model", "Prints data", "Creates a database"], "B"),
            ("Why split train and test data?", ["To test generalization", "To increase file size", "To remove labels", "To rename columns"], "A"),
            ("Accuracy is mainly used for?", ["Measuring predictions", "Sorting files", "Creating folders", "Parsing PDFs"], "A"),
        ],
    },
    "java": {
        "title": "Java Programming Fundamentals",
        "category": "Information Technology",
        "level": "Beginner",
        "duration": "4–5 hours",
        "videos": [
            ("Java Introduction & First Program", "https://www.youtube.com/watch?v=eIrMbAQSU34"),
            ("Java Variables & Data Types", "https://www.youtube.com/watch?v=GoXwIVyNvX0"),
            ("Java Conditions & Loops", "https://www.youtube.com/watch?v=ldYLYRNaucM"),
            ("Java Methods & Arrays", "https://www.youtube.com/watch?v=G1I3HF4YWEw"),
            ("Java Classes & Objects", "https://www.youtube.com/watch?v=KJgsSFOSQv0"),
            ("Java OOP Fundamentals", "https://www.youtube.com/watch?v=Zs342ePFvRI"),
        ],
        "quiz": [
            ("Which method is the entry point of a Java program?", ["start()", "main()", "run()", "begin()"], "B"),
            ("Which keyword creates a class?", ["class", "object", "define", "struct"], "A"),
            ("Which concept hides internal data?", ["Encapsulation", "Compilation", "Iteration", "Casting"], "A"),
            ("Which structure repeats code?", ["Loop", "Package", "Import", "Class"], "A"),
            ("An object is an instance of a...", ["Method", "Class", "Loop", "Variable"], "B"),
        ],
    },
    "javascript": {
        "title": "JavaScript Fundamentals",
        "category": "Information Technology",
        "level": "Beginner",
        "duration": "3–4 hours",
        "videos": [
            ("JavaScript Introduction & Basics", "https://www.youtube.com/watch?v=W6NZfCO5SIk"),
            ("JavaScript Variables & Data Types", "https://www.youtube.com/watch?v=9emXNzqCKyg"),
            ("JavaScript Functions & Scope", "https://www.youtube.com/watch?v=xUI5Tsl2JpY"),
            ("JavaScript Arrays & Objects", "https://www.youtube.com/watch?v=R8rmfD9Y5-c"),
            ("JavaScript Loops & Conditions", "https://www.youtube.com/watch?v=IsG4Xd6LlsM"),
            ("JavaScript DOM Basics", "https://www.youtube.com/watch?v=5fb2aPlgoys"),
        ],
        "quiz": [
            ("Which keyword declares a constant?", ["const", "fixed", "constant", "let"], "A"),
            ("Which method selects an element by ID?", ["getElementById", "selectId", "findId", "idElement"], "A"),
            ("Which structure stores key-value pairs?", ["Object", "Loop", "Function", "String"], "A"),
            ("Which keyword defines a function traditionally?", ["function", "def", "fun", "method"], "A"),
            ("Which symbol is used for strict equality?", ["=", "==", "===", "=>"], "C"),
        ],
    },
    "excel": {
        "title": "Excel for Data Analysis",
        "category": "Finance",
        "level": "Beginner",
        "duration": "3–4 hours",
        "videos": [
            ("Excel Basics for Beginners", "https://www.youtube.com/watch?v=VT479YDPB0I"),
            ("Excel Formulas & Functions", "https://www.youtube.com/watch?v=8Y0dY5g0p4k"),
            ("Excel Sorting & Filtering", "https://www.youtube.com/watch?v=7KXw3n8n8zQ"),
            ("Excel Pivot Tables", "https://www.youtube.com/watch?v=UsdedFoTA68"),
            ("Excel Charts & Data Visualization", "https://www.youtube.com/watch?v=8n7wY2w9y9M"),
            ("Excel Data Cleaning & Analysis", "https://www.youtube.com/watch?v=9NUjHBNWe9M"),
        ],
        "quiz": [
            ("Which feature summarizes data by categories?", ["PivotTable", "Paint", "Mail", "Slide"], "A"),
            ("Which function adds values?", ["SUM", "TEXT", "LEFT", "IFERROR"], "A"),
            ("What is a chart used for?", ["Data visualization", "Password storage", "File compression", "Code execution"], "A"),
            ("What does filtering do?", ["Shows selected records", "Deletes the workbook", "Installs Excel", "Creates passwords"], "A"),
            ("Which tool is useful for removing repeated records?", ["Remove Duplicates", "WordArt", "Themes", "Comments"], "A"),
        ],
    },
}

# Category-wise course catalogue. Each displayed course maps to one fixed
# six-video course above, so the same topic never opens random YouTube results.
CATEGORY_COURSES = {
    "Business Development": [
        ("Python for Business Data", "python"),
        ("SQL for Business Data", "sql"),
        ("Excel for Business Analysis", "excel"),
    ],
    "Finance": [
        ("Excel for Finance", "excel"),
        ("SQL for Finance Data", "sql"),
        ("Python for Finance", "python"),
    ],
    "HR": [
        ("Excel for HR Analytics", "excel"),
        ("SQL for HR Data", "sql"),
        ("Python for HR Analytics", "python"),
    ],
    "Sales": [
        ("Excel for Sales Analytics", "excel"),
        ("SQL for Sales Data", "sql"),
        ("Python for Sales Analytics", "python"),
    ],
    "Information Technology": [
        ("Python Programming Fundamentals", "python"),
        ("SQL for Data Analysis", "sql"),
        ("Pandas & Data Analysis", "pandas"),
        ("Machine Learning Fundamentals", "machine_learning"),
        ("Java Programming Fundamentals", "java"),
        ("JavaScript Fundamentals", "javascript"),
        ("Excel for Data Analysis", "excel"),
    ],
}


def certificate_pdf_bytes(user_name, course_title, skill, score):
    """Create a print-ready landscape A4 certificate with a professional design."""
    if not HAS_REPORTLAB:
        return None

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    certificate_id = (
        "CMAI-" + hashlib.sha256(
            (user_name + course_title + skill).encode()
        ).hexdigest()[:10].upper()
    )

    navy = colors.HexColor("#172554")
    indigo = colors.HexColor("#4F46E5")
    violet = colors.HexColor("#7C3AED")
    gold = colors.HexColor("#D4AF37")
    dark = colors.HexColor("#111827")
    gray = colors.HexColor("#4B5563")

    # Elegant double border
    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setStrokeColor(navy); c.setLineWidth(7)
    c.rect(24, 24, width-48, height-48, fill=0, stroke=1)
    c.setStrokeColor(gold); c.setLineWidth(2)
    c.rect(37, 37, width-74, height-74, fill=0, stroke=1)

    # Top accent band
    c.setFillColor(navy)
    c.roundRect(65, height-92, width-130, 36, 18, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height-79, "CAREERMATCH AI  •  SKILL DEVELOPMENT PROGRAM")

    c.setFillColor(indigo)
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(width/2, height-135, "CERTIFICATE OF COMPLETION")

    c.setFillColor(gray)
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, height-165, "This certificate is proudly presented to")

    c.setFillColor(dark)
    c.setFont("Helvetica-Bold", 29)
    c.drawCentredString(width/2, height-210, user_name)

    # Decorative divider
    c.setStrokeColor(gold); c.setLineWidth(2)
    c.line(width/2-105, height-228, width/2+105, height-228)

    c.setFillColor(gray)
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, height-258, "for successfully completing the course")

    c.setFillColor(violet)
    c.setFont("Helvetica-Bold", 21)
    c.drawCentredString(width/2, height-294, course_title)

    c.setFillColor(navy)
    c.roundRect(width/2-105, height-337, 210, 30, 15, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height-327, f"FINAL ASSESSMENT  •  {score}%")

    completion_date = pd.Timestamp.now().strftime('%d %B %Y')
    c.setFillColor(gray)
    c.setFont("Helvetica", 9.5)
    c.drawString(65, 67, f"Certificate ID: {certificate_id}")
    c.drawRightString(width-65, 67, f"Completion Date: {completion_date}")

    c.setFillColor(indigo)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width/2, 67, "CareerBridge AI")

    c.save()
    buffer.seek(0)
    return buffer.getvalue(), certificate_id


def show_video_course(course_key, course, course_instance_key):
    """Display six fixed embedded videos with automatic timer-based completion."""
    st.divider()
    completed = sum(st.session_state.get(f"video_done::{course_instance_key}::{i}", False) for i in range(1, 7))

    st.markdown(f"""
    <div class="course-hero">
        <h2>🎓 {course['title']}</h2>
        <p>Watch all 6 fixed lessons → complete the final assessment → earn your professional certificate.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Level", course["level"])
    c2.metric("Lessons", "6")
    c3.metric("Duration", course["duration"])
    c4.metric("Completed", f"{completed}/6")
    st.progress(completed / 6)

    if completed == 6:
        st.success("🎉 All 6 lessons completed — Final Assessment unlocked!")
    else:
        st.info("▶️ Play each embedded lesson. Completion is recorded automatically after the lesson timer finishes. There is no Mark Completed button.")

    watch_seconds = 90

    for number, (video_title, video_url) in enumerate(course["videos"], start=1):
        done_key = f"video_done::{course_instance_key}::{number}"
        start_key = f"video_start::{course_instance_key}::{number}"
        started_at = st.session_state.get(start_key)
        is_done = st.session_state.get(done_key, False)

        if not is_done and started_at:
            elapsed = int(time.time() - started_at)
            if elapsed >= watch_seconds:
                st.session_state[done_key] = True
                is_done = True
                st.session_state.pop(start_key, None)
                st.rerun()

        css = "video-done" if is_done else ("video-wait" if started_at else "")
        st.markdown(f'<div class="video-card {css}">', unsafe_allow_html=True)

        if is_done:
            st.markdown('<span class="badge badge-green">✅ VIDEO COMPLETED</span>', unsafe_allow_html=True)
        elif started_at:
            remaining = max(0, watch_seconds - int(time.time() - started_at))
            st.markdown(f'<span class="badge badge-orange">⏳ WATCHING • {remaining//60}:{remaining%60:02d} remaining</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge badge-blue">🔵 READY TO WATCH</span>', unsafe_allow_html=True)

        st.markdown(f"### {number}. {video_title}")
        video_id = video_url.split("v=")[-1].split("&")[0]

        if is_done or started_at:
            iframe = f'''<iframe width="100%" height="390" src="https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1" title="{video_title}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>'''
            st.components.v1.html(iframe, height=405, scrolling=False)
        else:
            st.caption("Click Start Lesson to load the fixed YouTube video inside the course.")

        if not is_done and not started_at:
            if st.button(f"▶️ Start Lesson {number}", key=f"video_start_button::{course_instance_key}::{number}", use_container_width=True, type="primary"):
                st.session_state[start_key] = time.time()
                st.rerun()
        elif not is_done:
            st.caption("The completion indicator is automatic. Keep the lesson open and return after the timer finishes.")
        else:
            st.markdown('<span class="status-complete">✓ Lesson completed — you can rewatch it anytime.</span>', unsafe_allow_html=True)
            st.link_button("↗️ Rewatch on YouTube", video_url, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    all_done = all(st.session_state.get(f"video_done::{course_instance_key}::{i}", False) for i in range(1, 7))
    quiz_pass_key = f"video_course_passed::{course_instance_key}"
    score_key = f"video_course_score::{course_instance_key}"
    certificate_key = f"video_course_certificate::{course_instance_key}"

    st.divider()
    if not all_done:
        st.markdown("### 🔒 Final Course Assessment")
        st.warning("Complete all 6 lessons first. The assessment will unlock automatically after all six green ticks appear.")
        return

    st.markdown("### 📝 Final Course Assessment")
    st.caption("Answer all 5 questions. You need at least 4/5 (80%) to pass and unlock the certificate.")

    answers = []
    for i, (question, options, correct) in enumerate(course["quiz"]):
        answers.append(st.radio(question, options, index=None, key=f"video_course_quiz::{course_instance_key}::{i}"))

    if st.button("🎯 Submit Final Assessment", key=f"video_course_submit::{course_instance_key}", type="primary", use_container_width=True):
        if any(answer is None for answer in answers):
            st.warning("Please answer all 5 questions before submitting.")
        else:
            score = sum(1 for answer, (_, options, correct) in zip(answers, course["quiz"]) if answer == options[ord(correct) - 65])
            percent = int(score / len(course["quiz"]) * 100)
            st.session_state[score_key] = percent
            st.session_state[quiz_pass_key] = score >= 4
            if score >= 4:
                st.success(f"🏆 Passed: {score}/5 ({percent}%). Certificate unlocked!")
            else:
                st.warning(f"Score: {score}/5 ({percent}%). You need at least 4/5 to pass. Review the lessons and try again.")

    if st.session_state.get(quiz_pass_key, False):
        score = st.session_state.get(score_key, 80)
        st.markdown('<div class="certificate-note">🏆 <b>Course completed successfully.</b> Your professional print-ready certificate is ready.</div>', unsafe_allow_html=True)
        certificate_name = st.text_input("👤 Name for Certificate", key=f"video_course_certificate_name::{course_instance_key}")
        if not HAS_REPORTLAB:
            st.error("Certificate generation requires reportlab. Add `reportlab` to requirements.txt.")
        elif st.button("✨ Generate Professional Certificate", key=f"video_course_generate_certificate::{course_instance_key}", use_container_width=True, type="primary"):
            if not certificate_name.strip():
                st.warning("Please enter your name first.")
            else:
                st.session_state[certificate_key] = certificate_pdf_bytes(certificate_name.strip(), course["title"], course["title"], score)
                certificate = st.session_state[certificate_key]
                if certificate:
                    _, certificate_id = certificate
                    record_course_completion(
                        current_user,
                        course["title"],
                        score,
                        certificate_id
                    )
                    st.session_state.current_user = ensure_user_history(load_user() or current_user)
                st.success("Professional certificate generated successfully! Your course completion has been saved to History.")

        certificate = st.session_state.get(certificate_key)
        if certificate:
            pdf_data, certificate_id = certificate
            st.success(f"Certificate ID: {certificate_id}")
            st.download_button("📜 Download Professional Certificate (Print Ready PDF)", data=pdf_data, file_name=f"CareerMatch_{course['title'].replace(' ', '_')}_Certificate.pdf", mime="application/pdf", key=f"video_course_download::{course_instance_key}", use_container_width=True)

def show_independent_courses():
    st.markdown("""
    <div class="course-hero">
        <h2>🎓 Courses & Skill Development</h2>
        <p>Learn through guided fixed lessons, test your knowledge, and earn a professional certificate.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        '<span class="feature-chip">🎥 Fixed Videos</span>'
        '<span class="feature-chip">⚡ Auto Completion</span>'
        '<span class="feature-chip">📝 Final Quiz</span>'
        '<span class="feature-chip">🏆 Certificate</span>',
        unsafe_allow_html=True
    )

    course_category = st.selectbox(
        "📂 Select Course Category",
        list(CATEGORY_COURSES.keys()),
        key="independent_course_category"
    )

    course_items = CATEGORY_COURSES[course_category]
    course_labels = [item[0] for item in course_items]

    selected_course_title = st.selectbox(
        "📚 Select a Course",
        course_labels,
        key="independent_course_selector"
    )

    selected_title, course_key = next(
        item for item in course_items
        if item[0] == selected_course_title
    )

    course = VIDEO_COURSES[course_key].copy()
    course["title"] = selected_title
    course_instance_key = (
        f"{course_category}::{course_key}::{selected_title}"
    )

    st.markdown(f"### 📘 {selected_title}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Level", course["level"])
    c2.metric("Fixed Videos", "6")
    c3.metric("Duration", course["duration"])

    st.caption(
        "The videos below are pre-selected for this course. "
        "YouTube search results are not used."
    )

    if st.button(
        "🚀 Start This Course",
        key="start_independent_video_course",
        type="primary",
        use_container_width=True
    ):
        st.session_state.independent_active_course = course_instance_key
        st.session_state.independent_course_key = course_key
        st.session_state.independent_course_title = selected_title
        st.rerun()

    if st.session_state.get("independent_active_course") == course_instance_key:
        active_key = st.session_state.get("independent_course_key", course_key)
        active_title = st.session_state.get(
            "independent_course_title",
            selected_title
        )
        active_course = VIDEO_COURSES[active_key].copy()
        active_course["title"] = active_title
        show_video_course(
            active_key,
            active_course,
            course_instance_key
        )


# =====================================================
# END OF FIXED VIDEO COURSE SYSTEM
# =====================================================

# =====================================================
# HISTORY TAB
# =====================================================

def show_history():
    current_user = ensure_user_history(load_user() or {})

    st.markdown("""
    <div class="course-hero">
        <h2>📜 My Activity & Learning History</h2>
        <p>View your login activity and completed courses in one place.</p>
    </div>
    """, unsafe_allow_html=True)

    login_history = current_user.get("login_history", [])
    course_history = current_user.get("course_history", [])

    login_col, course_col = st.columns(2)

    with login_col:
        st.markdown("### 🔐 Login History")
        if login_history:
            for item in login_history[:30]:
                st.markdown(
                    f"**👤 {item.get('username', current_user.get('username', 'User'))}** "
                    f"— {item.get('date', 'Date not available')}"
                )
                st.divider()
        else:
            st.info("No login history available yet.")

    with course_col:
        st.markdown("### 🎓 Course Completion History")
        if course_history:
            for item in course_history[:50]:
                st.markdown(f"**📘 {item.get('course_title', 'Course')}**")
                st.caption(
                    f"Score: {item.get('score', 0)}%  •  "
                    f"Completed: {item.get('completed_on', '—')}"
                )
                st.caption(f"Certificate ID: {item.get('certificate_id', '—')}")
                st.divider()
        else:
            st.info("No course has been completed yet.")



# =====================================================
# INTERVIEW PREPARATION
# =====================================================

INTERVIEW_QUESTIONS = {
    "General / HR": [
        {
            "q": "Tell me about yourself.",
            "answer": "Give a short introduction covering your education, key skills, project or internship experience, strengths, and the type of role you want.",
            "keywords": ["education", "skills", "project", "internship", "strength", "career", "role"]
        },
        {
            "q": "Why should we hire you?",
            "answer": "Connect your strongest skills and practical experience with the requirements of the role and explain how you can contribute to the organization.",
            "keywords": ["skills", "experience", "learn", "contribute", "team", "role"]
        },
        {
            "q": "What are your strengths?",
            "answer": "Mention two or three relevant strengths and support them with a short example from academics, projects, internship, or teamwork.",
            "keywords": ["strength", "problem solving", "communication", "teamwork", "learning", "adapt"]
        },
        {
            "q": "Where do you see yourself in five years?",
            "answer": "Show a realistic growth plan: stronger technical or professional skills, more responsibility, meaningful contribution, and continuous learning.",
            "keywords": ["growth", "skills", "learning", "responsibility", "career", "contribute"]
        },
        {
            "q": "Describe a challenge you faced and how you solved it.",
            "answer": "Use the STAR structure: Situation, Task, Action, and Result. Focus on your own actions and the outcome.",
            "keywords": ["situation", "task", "action", "result", "problem", "solution"]
        }
    ],
    "Information Technology": [
        {
            "q": "Explain one technical project you have worked on.",
            "answer": "Explain the problem, technologies used, your role, important features, challenges, and final result in a clear sequence.",
            "keywords": ["problem", "technology", "python", "project", "features", "role", "result"]
        },
        {
            "q": "What is the difference between supervised and unsupervised learning?",
            "answer": "Supervised learning uses labelled data to learn a mapping for prediction or classification, while unsupervised learning works with unlabelled data to discover patterns such as clusters.",
            "keywords": ["supervised", "unsupervised", "labelled", "unlabelled", "classification", "clustering"]
        },
        {
            "q": "What is SQL and why is it used?",
            "answer": "SQL is a language used to store, retrieve, update, and manage data in relational databases. It is commonly used for querying and analysing structured data.",
            "keywords": ["sql", "database", "query", "data", "table", "relational"]
        },
        {
            "q": "What is the purpose of data preprocessing?",
            "answer": "Data preprocessing improves data quality by handling missing values, duplicates, inconsistent formats, irrelevant data, and other issues before analysis or machine learning.",
            "keywords": ["preprocessing", "missing", "duplicate", "clean", "data", "quality"]
        },
        {
            "q": "Why is testing important in software development?",
            "answer": "Testing helps find defects, verify that requirements are met, reduce failures, and improve the reliability and quality of software.",
            "keywords": ["testing", "bugs", "requirements", "quality", "reliability", "software"]
        }
    ],
    "Business Development": [
        {
            "q": "How would you identify a new business opportunity?",
            "answer": "Study customer needs, market trends, competitors, gaps in existing solutions, and the potential value of the opportunity before proposing an approach.",
            "keywords": ["customer", "market", "trend", "competitor", "need", "opportunity"]
        },
        {
            "q": "How would you handle a difficult client?",
            "answer": "Listen carefully, understand the concern, communicate calmly, offer realistic solutions, and follow up to make sure the issue is resolved.",
            "keywords": ["listen", "client", "communication", "solution", "follow", "resolve"]
        },
        {
            "q": "What is lead generation?",
            "answer": "Lead generation is the process of identifying and attracting potential customers who may be interested in a product or service.",
            "keywords": ["lead", "customer", "potential", "product", "service", "interest"]
        }
    ],
    "Finance": [
        {
            "q": "Why is financial data analysis important?",
            "answer": "It helps organizations understand performance, control costs, identify trends, manage risks, and make informed financial decisions.",
            "keywords": ["financial", "data", "analysis", "cost", "risk", "decision", "trend"]
        },
        {
            "q": "What is the difference between revenue and profit?",
            "answer": "Revenue is the total income generated from business activities, while profit is the amount remaining after deducting relevant expenses from revenue.",
            "keywords": ["revenue", "profit", "income", "expenses", "business"]
        },
        {
            "q": "How can Excel help in finance?",
            "answer": "Excel can be used for calculations, financial models, budgeting, forecasting, data analysis, dashboards, and reporting.",
            "keywords": ["excel", "calculation", "budget", "forecast", "analysis", "report"]
        }
    ],
    "HR": [
        {
            "q": "What is the role of HR in an organization?",
            "answer": "HR manages people-related processes such as recruitment, onboarding, employee development, performance, engagement, and workplace policies.",
            "keywords": ["hr", "recruitment", "employee", "development", "performance", "engagement"]
        },
        {
            "q": "How would you handle a conflict between two employees?",
            "answer": "Listen to both sides objectively, understand the facts, encourage respectful communication, identify a fair solution, and follow up afterwards.",
            "keywords": ["conflict", "listen", "employee", "communication", "fair", "solution"]
        },
        {
            "q": "What is employee onboarding?",
            "answer": "Onboarding is the process of helping a new employee understand the organization, role, team, policies, tools, and expectations so they can become productive.",
            "keywords": ["onboarding", "employee", "role", "team", "policy", "training"]
        }
    ],
    "Sales": [
        {
            "q": "How would you convince a customer to consider a product?",
            "answer": "First understand the customer's needs, then explain the product's relevant benefits, handle objections honestly, and guide the customer toward a suitable decision.",
            "keywords": ["customer", "needs", "product", "benefits", "objection", "communication"]
        },
        {
            "q": "What is the difference between a lead and a customer?",
            "answer": "A lead is a potential customer who may be interested in a product or service, while a customer has actually purchased or engaged with the offering.",
            "keywords": ["lead", "customer", "potential", "purchase", "product", "service"]
        },
        {
            "q": "How do you handle rejection in sales?",
            "answer": "Stay professional, understand the reason for rejection, learn from it, improve the approach when appropriate, and continue working with other prospects.",
            "keywords": ["rejection", "professional", "reason", "learn", "improve", "prospect"]
        }
    ]
}


def interview_feedback(answer, question_data):
    text = (answer or "").strip()
    if not text:
        return 0, [], "Please write your answer first."

    words = re.findall(r"[a-zA-Z0-9+#.]+", text.lower())
    word_count = len(words)
    answer_words = set(words)
    keywords = set(k.lower() for k in question_data.get("keywords", []))
    matched = sorted(answer_words.intersection(keywords))
    keyword_score = min(70, int((len(matched) / max(1, min(5, len(keywords)))) * 70))
    length_score = 20 if word_count >= 45 else 15 if word_count >= 25 else 8 if word_count >= 12 else 3

    semantic_score = 0
    if nlp_model and text:
        try:
            emb = nlp_model.encode([text, question_data["answer"]], convert_to_tensor=True)
            semantic_score = int(float(util.cos_sim(emb[0], emb[1]).item()) * 100)
            semantic_score = max(0, min(100, semantic_score))
        except Exception:
            semantic_score = 0

    if semantic_score:
        score = int(keyword_score * 0.45 + length_score + semantic_score * 0.35)
    else:
        score = keyword_score + length_score
    score = max(0, min(100, score))

    if score >= 80:
        feedback = "Excellent answer. Keep it concise and support it with a real example when possible."
    elif score >= 60:
        feedback = "Good start. Add a specific example and connect your answer more directly to the role."
    elif score >= 40:
        feedback = "Needs improvement. Include more relevant points and explain your actions or reasoning clearly."
    else:
        feedback = "Try again. Structure the answer around the question and include relevant skills, examples, or results."

    return score, matched, feedback


def build_job_interview_questions(job_title, category, required_skills, missing_skills):
    """Build interview practice questions directly from a recommended job."""
    clean_required = [str(x).strip() for x in required_skills if str(x).strip()]
    clean_missing = [str(x).strip() for x in missing_skills if str(x).strip()]

    questions = [
        {
            "q": f"Why are you a good fit for the {job_title} role?",
            "answer": (
                f"Connect your strongest skills and experience with the {job_title} role. "
                f"Mention relevant skills such as {', '.join(clean_required[:5]) or 'the required skills'} "
                "and support your answer with a project, internship, or practical example."
            ),
            "keywords": clean_required[:8] + ["experience", "project", "skills", "role", "learn"]
        },
        {
            "q": f"What technical or professional skills are important for a {job_title}?",
            "answer": (
                f"Explain the most important skills for the role: "
                f"{', '.join(clean_required[:8]) or 'relevant role skills'}. "
                "Explain how you have used some of them and how you plan to improve the others."
            ),
            "keywords": clean_required[:10] + ["skills", "experience", "improve"]
        },
        {
            "q": f"How would you handle a real task in a {job_title} position?",
            "answer": (
                "First understand the requirement, break the task into smaller steps, select the appropriate "
                "tools or skills, complete and test the work, and communicate the result clearly."
            ),
            "keywords": clean_required[:8] + ["task", "problem", "solution", "result", "test"]
        },
        {
            "q": "Tell me about a project or practical experience related to this role.",
            "answer": (
                "Explain the problem, your role, technologies or skills used, important actions, challenges, "
                "and the final result. Focus on what you personally contributed."
            ),
            "keywords": clean_required[:7] + ["project", "problem", "role", "result", "experience"]
        }
    ]

    if clean_missing:
        questions.append({
            "q": f"You currently need to improve {clean_missing[0]}. How would you prepare for this skill?",
            "answer": (
                f"Acknowledge the gap and give a practical learning plan for {clean_missing[0]}: "
                "learn the fundamentals, practise with small tasks or projects, review mistakes, "
                "and apply the skill in a realistic example."
            ),
            "keywords": [clean_missing[0], "learn", "practice", "project", "improve", "fundamentals"]
        })
    else:
        questions.append({
            "q": "How would you use your matching skills to contribute from your first month?",
            "answer": (
                "Explain how you would understand the team's process, apply your existing skills to real tasks, "
                "learn the organization's tools, and gradually take more responsibility."
            ),
            "keywords": clean_required[:8] + ["team", "skills", "contribute", "learn", "tasks"]
        })

    # Remove duplicate keywords while keeping the question set focused.
    for q in questions:
        q["keywords"] = list(dict.fromkeys([str(k).lower() for k in q["keywords"] if str(k).strip()]))
    return questions


def show_interview_preparation():
    st.markdown("""
    <div class="course-hero">
        <h2>🎤 Interview Preparation Studio</h2>
        <p>Prepare specifically for the jobs recommended to you — not generic interview questions.</p>
    </div>
    """, unsafe_allow_html=True)

    recommendations = st.session_state.get("recommendations")

    if recommendations is None or recommendations.empty:
        st.warning(
            "🔎 First generate your Top 5 Job Recommendations. "
            "Your interview preparation will then be created automatically from those jobs and their required skills."
        )
        st.info("Go to **💼 Job Recommendation**, enter your skills or upload your resume, and click **FIND MY TOP 5 JOBS**.")
        return

    st.success("🎯 Your interview preparation is now personalized to your recommended jobs.")

    job_options = [row["job_title"] for _, row in recommendations.iterrows()]
    selected_job = st.selectbox(
        "💼 Select a Recommended Job to Prepare For",
        job_options,
        key="interview_job_selector"
    )

    selected_row = recommendations[recommendations["job_title"] == selected_job].iloc[0]
    required_skills = extract_required_skills(selected_row["job_skill_set"])
    matched_skills = sorted(selected_row["matched_skills"]) if isinstance(selected_row["matched_skills"], set) else []
    missing_skills = sorted(selected_row["missing_skills"]) if isinstance(selected_row["missing_skills"], set) else []

    st.markdown(f"### 🏆 Preparing for: {selected_job}")
    st.caption(f"Category: {selected_row['category']} • Job Match: {float(selected_row['match_percentage']):.1f}%")

    c1, c2, c3 = st.columns(3)
    c1.metric("Job Match", f"{float(selected_row['match_percentage']):.1f}%")
    c2.metric("Matching Skills", len(matched_skills))
    c3.metric("Skills to Improve", len(missing_skills))

    with st.expander("🛠️ Skills this interview will focus on", expanded=True):
        st.write(", ".join(skill.title() for skill in required_skills) or "Role-specific skills")
        if matched_skills:
            st.success("Your matching skills: " + ", ".join(skill.title() for skill in matched_skills))
        if missing_skills:
            st.warning("Priority skill gaps: " + ", ".join(skill.title() for skill in missing_skills))

    interview_questions = build_job_interview_questions(
        selected_job,
        selected_row["category"],
        required_skills,
        missing_skills
    )

    q_index = st.selectbox(
        "📝 Choose a Job-Specific Interview Question",
        range(len(interview_questions)),
        format_func=lambda i: f"Question {i + 1}: {interview_questions[i]['q']}",
        key=f"interview_question_{selected_job}"
    )

    q_data = interview_questions[q_index]
    st.markdown(f"### ❓ {q_data['q']}")
    st.caption("Answer as if you are speaking directly to the interviewer.")

    answer = st.text_area(
        "Your Answer",
        height=170,
        placeholder="Write your answer here...",
        key=f"interview_answer_{selected_job}_{q_index}"
    )

    if st.button("🤖 Evaluate My Answer", type="primary", use_container_width=True):
        score, matched, feedback = interview_feedback(answer, q_data)
        st.session_state.interview_feedback = {
            "score": score,
            "matched": matched,
            "feedback": feedback,
            "question": q_data["q"],
            "answer": q_data["answer"],
            "job": selected_job
        }

    result = st.session_state.get("interview_feedback")
    if result and result.get("question") == q_data["q"] and result.get("job") == selected_job:
        st.divider()
        score = result["score"]
        a, b, c = st.columns(3)
        a.metric("Interview Score", f"{score}%")
        b.metric("Relevant Points", len(result["matched"]))
        c.metric("Answer Status", "Strong" if score >= 80 else "Improve")
        st.progress(score / 100)
        st.success(result["feedback"])

        if result["matched"]:
            st.markdown("**✅ Relevant points detected:** " + ", ".join(x.title() for x in result["matched"]))

        with st.expander("💡 Suggested Answer Structure"):
            st.write(result["answer"])

    st.divider()
    st.subheader("🚀 Preparation Plan for This Job")
    plan = [
        f"Understand the responsibilities of the {selected_job} role.",
        "Prepare a 60–90 second self-introduction connected to this role.",
        f"Revise the required skills: {', '.join(sorted(str(x).strip() for x in required_skills if str(x).strip())[:8]) or 'role-specific skills'}.",
        "Prepare one project or internship example that demonstrates your relevant skills.",
        "Practise explaining your problem-solving approach using Situation, Task, Action and Result.",
        "Review your skill gaps before the interview and prepare an honest improvement plan."
    ]
    for item in plan:
        st.markdown(f"☐ {item}")


# =====================================================
# MAIN APPLICATION TABS
# =====================================================

job_tab, course_tab, history_tab, interview_tab = st.tabs([
    "💼 Job Recommendation",
    "🎓 Courses & Skill Development",
    "📜 My History",
    "🎤 Interview Preparation"
])

with job_tab:
    # =====================================================
    # MAIN JOB SEARCH
    # POSITION INPUT REMOVED
    # =====================================================

    st.subheader("🔎 Find Your Job")

    st.info(
        "Select a category, enter your skills, "
        "and click **FIND MY TOP 5 JOBS**."
    )


    # STEP 1
    st.markdown("### 1️⃣ Select Your Career Category")

    categories = sorted(
        df["category"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda x: x != ""]
        .unique()
    )

    if not categories:
        st.error("No career categories found in dataset.")
        st.stop()

    category = st.selectbox(
        "📂 Career Category",
        categories
    )


    # STEP 2
    st.markdown("### 2️⃣ Enter Your Skills")

    user_skills = st.text_input(
        "🛠️ Your Skills",
        placeholder=(
            "Example: Python, SQL, Pandas, "
            "Machine Learning"
        )
    )

    st.caption(
        "Enter skills separated by commas."
    )


    # =====================================================
    # RESUME FEATURE — SEPARATE SECTION
    # =====================================================

    st.divider()
    st.subheader("📄 Resume Skill Extraction")

    st.write(
        "Upload your resume to automatically identify skills "
        "and use them for job matching."
    )

    resume_file = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, DOCX and TXT. Scanned PDFs are handled with OCR when available."
    )

    status_cols = st.columns(3)
    with status_cols[0]:
        st.markdown("**📄 PDF text**  ")
        st.caption("PyMuPDF + pdfplumber")
    with status_cols[1]:
        st.markdown("**🔍 Scanned PDF**  ")
        st.caption("OCR fallback")
    with status_cols[2]:
        st.markdown("**🧠 Skill matching**  ")
        st.caption("Aliases + robust matching")

    all_dataset_skills = set()

    for skill_text in df["job_skill_set"].dropna():
        all_dataset_skills.update(
            extract_required_skills(skill_text)
        )

    if resume_file is not None:

        # Clear previous resume data whenever a new file is uploaded.
        st.session_state.resume_text = ""
        st.session_state.resume_skills = set()

        resume_text = parse_resume(resume_file)

        if resume_text:
            resume_skills = extract_skills_from_resume(
                resume_text,
                all_dataset_skills
            )

            st.session_state.resume_text = resume_text
            st.session_state.resume_skills = resume_skills

            st.success(
                f"📄 Resume text extracted successfully ({len(resume_text):,} characters)."
            )

            with st.expander("👀 Preview extracted resume text", expanded=False):
                st.text_area(
                    "Extracted text",
                    resume_text[:5000],
                    height=220,
                    disabled=True,
                    label_visibility="collapsed"
                )

            if resume_skills:
                st.success(
                    f"✅ {len(resume_skills)} skills identified from your resume."
                )

                skill_html = "".join(
                    [
                        f'<span class="skill-tag skill-matched">'
                        f'✓ {skill.title()}</span>'
                        for skill in sorted(resume_skills)
                    ]
                )

                st.markdown(
                    skill_html,
                    unsafe_allow_html=True
                )

                st.caption(
                    "These skills can be combined with your manually entered skills."
                )

            else:
                st.warning(
                    "No matching dataset skills were identified from this resume. "
                    "You can still enter skills manually."
                )

        else:
            st.error(
                "❌ Resume text could not be extracted. The file may be empty, corrupted, password-protected, or an image-only PDF without OCR support."
            )
            if resume_file.name.lower().endswith(".pdf") and not HAS_OCR:
                st.info(
                    "💡 OCR fallback is not installed in this deployment. Add `pytesseract` to requirements.txt and `tesseract-ocr` to packages.txt for scanned PDF resumes."
                )


    # =====================================================
    # NLP STATUS
    # =====================================================

    st.divider()
    st.subheader("🧠 NLP Semantic Matching")

    if nlp_model:
        semantic_enabled = st.checkbox(
            "Enable AI/NLP Semantic Matching",
            value=True,
            help=(
                "Compares the user's skill profile with job "
                "information using a Sentence Transformer model."
            )
        )
        st.caption(
            "AI model: all-MiniLM-L6-v2"
        )
    else:
        semantic_enabled = False
        st.warning(
            "NLP model is unavailable. The original skill-based "
            "recommendation system will continue to work."
        )


    # =====================================================
    # FIND TOP 5
    # =====================================================

    st.divider()

    st.subheader("🎯 Find Your Jobs")

    st.write(
        "Your manual skills and extracted resume skills can be used together."
    )

    # Combine manual + resume skills without changing dataset.
    manual_set = extract_user_skills(user_skills)
    combined_skill_set = manual_set.union(
        st.session_state.resume_skills
    )
    combined_skills_text = ", ".join(
        sorted(combined_skill_set)
    )

    if combined_skill_set:
        st.success(
            f"✅ Skills ready for matching: "
            f"{', '.join(sorted(combined_skill_set))}"
        )

    if st.button(
        "🚀 FIND MY TOP 5 JOBS",
        use_container_width=True,
        type="primary"
    ):

        if not combined_skill_set:
            st.warning(
                "⚠️ Please enter your skills or upload a resume first."
            )

        else:
            with st.spinner(
                "🔎 Finding your best job recommendations..."
            ):
                recommendations = get_recommendations(
                    category,
                    combined_skills_text,
                    semantic_enabled=semantic_enabled
                )

            st.session_state.recommendations = recommendations
            st.session_state.recommendation_source = (
                "Manual + Resume Skills"
                if st.session_state.resume_skills
                and manual_set
                else "Resume Skills"
                if st.session_state.resume_skills
                else "Manual Skills"
            )


    # =====================================================
    # RECOMMENDATION OUTPUT
    # =====================================================

    recommendations = st.session_state.recommendations

    if recommendations is not None:

        st.divider()

        if recommendations.empty:
            st.warning(
                "😔 No suitable jobs found. "
                "Try adding more relevant skills."
            )

        else:
            st.success(
                "🎉 Top 5 matching jobs generated successfully!"
            )

            st.subheader(
                "🏆 Your Best Job Recommendations"
            )

            st.caption(
                f"Based on: {st.session_state.recommendation_source} | "
                f"Category: {category}"
            )

            for number, (_, row) in enumerate(
                recommendations.iterrows(),
                start=1
            ):

                match_percentage = round(
                    float(row["match_percentage"]),
                    1
                )

                matched_skills = row["matched_skills"]

                if isinstance(matched_skills, set):
                    matched_skills_text = (
                        ", ".join(
                            sorted(matched_skills)
                        )
                        if matched_skills
                        else "No direct skill match"
                    )
                else:
                    matched_skills_text = str(
                        matched_skills
                    )

                st.markdown(
                    f"""
    <div class="job-card">
        <div class="job-title">
            {number}. 💼 {row["job_title"]}
        </div>
        <br>
        <div class="match-score">
            🎯 Best Match: {match_percentage}%
        </div>
        <br>
        📂 <b>Category:</b> {row["category"]}
        <br><br>
        🆔 <b>Job ID:</b> {row["job_id"]}
        <br><br>
        ✅ <b>Matching Skills:</b> {matched_skills_text}
        <br><br>
        🛠️ <b>Required Skills:</b> {row["job_skill_set"]}
    </div>
    """,
                    unsafe_allow_html=True
                )

                st.progress(
                    int(
                        min(
                            max(match_percentage, 0),
                            100
                        )
                    )
                )

                with st.expander(
                    f"📄 View Full Details - Job {number}"
                ):

                    m1, m2, m3 = st.columns(3)

                    m1.metric(
                        "Final Match",
                        f"{match_percentage}%"
                    )

                    m2.metric(
                        "Skill Match",
                        f"{row['skill_score']:.1f}%"
                    )

                    m3.metric(
                        "NLP Semantic",
                        f"{row['semantic_score']:.1f}%"
                    )

                    st.markdown("### 📝 Job Description")
                    st.write(row["job_description"])

                    st.markdown("### 🛠️ Required Skills")
                    st.write(row["job_skill_set"])

                    st.markdown("### 🎯 Match Details")

                    st.write(
                        f"**Matched Skills:** "
                        f"{row['matched_skill_count']} "
                        f"out of "
                        f"{row['required_skill_count']} "
                        f"required skills"
                    )

                    st.write(
                        f"**Matching Skills:** "
                        f"{matched_skills_text}"
                    )

                    st.write(
                        f"**AI-Assisted Semantic Score:** "
                        f"{row['semantic_score']:.1f}%"
                    )


    # =====================================================
    # SKILL GAP ANALYSIS — SEPARATE SECTION
    # =====================================================

    if recommendations is not None and not recommendations.empty:

        st.divider()
        st.subheader("🔍 Skill Gap Analysis")

        st.write(
            "See which skills you already have and which skills "
            "are missing for the recommended jobs."
        )

        gap_job_names = [
            row["job_title"]
            for _, row in recommendations.iterrows()
        ]

        selected_gap_job = st.selectbox(
            "Select a recommended job",
            gap_job_names,
            key="gap_job_selector"
        )

        selected_row = recommendations[
            recommendations["job_title"] == selected_gap_job
        ].iloc[0]

        matched = sorted(
            selected_row["matched_skills"]
        )

        missing = sorted(
            selected_row["missing_skills"]
        )

        left, right = st.columns(2)

        with left:
            st.markdown("### ✅ Skills You Have")

            if matched:
                tags = "".join(
                    [
                        f'<span class="skill-tag skill-matched">'
                        f'✓ {skill.title()}</span>'
                        for skill in matched
                    ]
                )
                st.markdown(
                    tags,
                    unsafe_allow_html=True
                )
            else:
                st.info(
                    "No direct required skills matched."
                )

        with right:
            st.markdown("### ❌ Skills You Need")

            if missing:
                tags = "".join(
                    [
                        f'<span class="skill-tag skill-missing">'
                        f'✗ {skill.title()}</span>'
                        for skill in missing
                    ]
                )
                st.markdown(
                    tags,
                    unsafe_allow_html=True
                )
            else:
                st.success(
                    "🎉 You have all directly required skills!"
                )


    # =====================================================
    # LEARNING RESOURCES — YOUTUBE + COURSE FOR EVERY GAP
    # =====================================================

    if recommendations is not None and not recommendations.empty:

        st.divider()
        st.subheader("📚 Skill Improvement Resources")
        st.write(
            "For every missing skill, choose either a YouTube tutorial for quick learning "
            "or start the related CareerBridge AI course for structured learning and certification."
        )

        for job_number, (_, resource_row) in enumerate(
            recommendations.iterrows(),
            start=1
        ):
            required = extract_required_skills(resource_row["job_skill_set"])
            candidate = set(combined_skill_set)
            resource_missing = sorted(required.difference(candidate))

            with st.expander(
                f"💼 Job {job_number}: {resource_row['job_title']} — Skill Resources",
                expanded=False
            ):
                if resource_missing:
                    st.caption(
                        f"{len(resource_missing)} missing skill(s) for this job"
                    )

                    for skill_number, missing_skill in enumerate(resource_missing, start=1):
                        youtube_url = youtube_search_url(missing_skill)
                        _, course_info = get_course_for_skill(missing_skill)

                        st.markdown(f"### {skill_number}. 🛠️ {missing_skill.title()}")
                        st.caption(
                            f"Related course: {course_info['title']} • "
                            f"{course_info['duration']}"
                        )

                        r1, r2 = st.columns(2)
                        with r1:
                            st.link_button(
                                "▶️ Watch YouTube Tutorial",
                                youtube_url,
                                use_container_width=True
                            )
                        with r2:
                            if st.button(
                                "🎓 Start Skill Course",
                                key=f"start_course_{job_number}_{skill_number}_{hashlib.md5(missing_skill.encode()).hexdigest()}",
                                use_container_width=True,
                                type="primary"
                            ):
                                st.session_state.active_skill_course = (
                                    resource_row["job_title"],
                                    missing_skill
                                )
                                st.rerun()

                        st.markdown("---")
                else:
                    st.success(
                        "🎉 No missing skills for this job. You are ready for this skill set!"
                    )

        # The course appears only after the user clicks Start Skill Course.
        show_selected_skill_course()




with course_tab:
    show_independent_courses()

with history_tab:
    show_history()

with interview_tab:
    show_interview_preparation()

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

st.markdown(
    """
<div class="footer">
    <b>💼 CareerBridge AI</b>
    <br>
    AI-Assisted Smart Job Recommendation System
    <br><br>
    Built with Python • Pandas • Streamlit • NLP
</div>
""",
    unsafe_allow_html=True
)
