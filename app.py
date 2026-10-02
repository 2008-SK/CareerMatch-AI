
import streamlit as st
import pandas as pd
import numpy as np
import re
import json
import os
import hashlib
import ast
import io
from urllib.parse import quote_plus

# Optional resume libraries are imported safely when used.
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    from docx import Document
except Exception:
    Document = None

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="CareerMatch AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# CONSTANTS / SESSION STATE
# =====================================================
USER_FILE = "user_data.json"

PAGES = [
    "🏠 Home",
    "📝 Manual Skill Search",
    "📄 Resume Matching",
    "🏆 Job Recommendations",
    "🔍 Skill Gap & Learning",
]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"

if st.session_state.page not in PAGES:
    st.session_state.page = "🏠 Home"

if "recommendations" not in st.session_state:
    st.session_state.recommendations = None

if "profile_skills" not in st.session_state:
    st.session_state.profile_skills = set()

if "profile_source" not in st.session_state:
    st.session_state.profile_source = ""

if "selected_category" not in st.session_state:
    st.session_state.selected_category = ""

if "selected_position" not in st.session_state:
    st.session_state.selected_position = ""

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "resume_skills" not in st.session_state:
    st.session_state.resume_skills = set()

# =====================================================
# USER DATA / AUTHENTICATION
# =====================================================
def load_user():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return None
    return None


def save_user(user):
    with open(USER_FILE, "w", encoding="utf-8") as file:
        json.dump(user, file)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =====================================================
# LOGIN / REGISTER / FORGOT PASSWORD
# =====================================================
if not st.session_state.logged_in:
    st.markdown(
        """
        <div class="auth-hero">
            <div class="brand-icon">💼</div>
            <h1>CareerMatch AI</h1>
            <p>AI-Assisted Smart Job Recommendation System</p>
            <span>Find suitable jobs • Understand your skill gaps • Keep learning</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    option = st.radio(
        "Choose an option",
        ["Login", "Register", "Forgot Password"],
        horizontal=True
    )

    if option == "Register":
        st.subheader("Create Your Account")
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Create Account", use_container_width=True):
            existing = load_user()
            if not email or not username or not password:
                st.warning("Please fill all fields.")
            elif existing is not None:
                st.error("An account already exists. Please login or reset the password.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must contain at least 6 characters.")
            else:
                save_user({
                    "email": email,
                    "username": username,
                    "password": hash_password(password)
                })
                st.success("Registration successful! You can now login.")

    elif option == "Login":
        st.subheader("Welcome Back")
        login_id = st.text_input("Email or Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            user = load_user()

            if user is None:
                st.warning("No account found. Please register first.")
            elif (
                login_id == user.get("email")
                or login_id == user.get("username")
            ) and hash_password(password) == user.get("password"):
                st.session_state.logged_in = True
                st.session_state.page = "🏠 Home"
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Incorrect email/username or password.")

    else:
        st.subheader("🔑 Reset Password")
        email = st.text_input("Enter your registered email")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        if st.button("Reset Password", use_container_width=True):
            user = load_user()

            if user is None:
                st.error("No registered account found.")
            elif email != user.get("email"):
                st.error("Email does not match the registered email.")
            elif len(new_password) < 6:
                st.error("Password must contain at least 6 characters.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                user["password"] = hash_password(new_password)
                save_user(user)
                st.success("Password reset successfully! You can now login.")

    st.stop()

# =====================================================
# LOAD DATASET
# =====================================================
try:
    df = pd.read_csv("Cleaned_New_Data.csv")
except Exception as exc:
    st.error("Could not load Cleaned_New_Data.csv.")
    st.caption(f"Details: {exc}")
    st.stop()

required_columns = [
    "job_id",
    "category",
    "job_title",
    "job_description",
    "job_skill_set"
]

missing_columns = [c for c in required_columns if c not in df.columns]

if missing_columns:
    st.error("Dataset is missing required columns: " + ", ".join(missing_columns))
    st.stop()

for col in ["category", "job_title", "job_description", "job_skill_set"]:
    df[col] = df[col].fillna("").astype(str).str.strip()

# =====================================================
# GLOBAL CSS
# =====================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2.5rem;
        max-width: 1450px;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,.20);
    }

    .brand {
        padding: 8px 4px 18px 4px;
    }

    .brand h2 {
        margin: 0;
        font-size: 25px;
    }

    .brand p {
        margin: 3px 0 0 0;
        opacity: .65;
        font-size: 13px;
    }

    .hero {
        padding: 38px 42px;
        border-radius: 26px;
        border: 1px solid rgba(128,128,128,.22);
        background: linear-gradient(135deg, rgba(99,102,241,.12), rgba(59,130,246,.04));
        margin-bottom: 26px;
    }

    .hero h1 {
        font-size: 46px;
        margin: 0 0 8px 0;
    }

    .hero .subtitle {
        font-size: 21px;
        margin-bottom: 10px;
    }

    .hero .small {
        opacity: .72;
        font-size: 15px;
    }

    .section-title {
        font-size: 28px;
        font-weight: 750;
        margin: 12px 0 5px 0;
    }

    .section-subtitle {
        opacity: .70;
        margin-bottom: 20px;
    }

    .feature-card, .result-card, .info-card, .gap-card {
        padding: 22px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,.22);
        background: rgba(128,128,128,.035);
        margin-bottom: 14px;
    }

    .feature-card {
        min-height: 175px;
    }

    .feature-icon {
        font-size: 30px;
        margin-bottom: 8px;
    }

    .feature-card h3 {
        margin: 0 0 7px 0;
    }

    .result-card {
        padding: 24px;
    }

    .job-heading {
        font-size: 23px;
        font-weight: 750;
    }

    .score {
        font-size: 28px;
        font-weight: 800;
    }

    .metric-box {
        text-align: center;
        padding: 18px 10px;
        border: 1px solid rgba(128,128,128,.20);
        border-radius: 15px;
        background: rgba(128,128,128,.035);
    }

    .metric-number {
        font-size: 25px;
        font-weight: 800;
    }

    .metric-label {
        opacity: .68;
        font-size: 13px;
    }

    .skill-chip {
        display: inline-block;
        padding: 7px 11px;
        margin: 4px 5px 4px 0;
        border-radius: 999px;
        border: 1px solid rgba(128,128,128,.22);
        background: rgba(128,128,128,.06);
        font-size: 13px;
    }

    .matched-chip {
        border-color: rgba(34,197,94,.45);
        background: rgba(34,197,94,.09);
    }

    .missing-chip {
        border-color: rgba(239,68,68,.40);
        background: rgba(239,68,68,.08);
    }

    .workflow {
        text-align: center;
        padding: 18px;
        border-radius: 17px;
        border: 1px solid rgba(128,128,128,.20);
        min-height: 125px;
        background: rgba(128,128,128,.03);
    }

    .workflow .icon {
        font-size: 29px;
    }

    .empty-state {
        text-align: center;
        padding: 45px 20px;
        border: 1px dashed rgba(128,128,128,.35);
        border-radius: 20px;
        opacity: .8;
    }

    .footer {
        text-align: center;
        padding: 28px 0 5px 0;
        opacity: .60;
    }

    .stButton > button {
        border-radius: 11px;
        min-height: 45px;
        font-weight: 650;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================
# HELPER FUNCTIONS
# =====================================================
def clean_skill(skill):
    if skill is None:
        return ""
    skill = str(skill).lower().strip()
    skill = skill.replace("_", " ").replace("-", " ")
    skill = re.sub(r"\s+", " ", skill)
    return skill.strip()


def extract_required_skills(skill_text):
    if pd.isna(skill_text):
        return set()

    text = str(skill_text).strip()
    if not text:
        return set()

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple, set)):
            return {
                clean_skill(skill)
                for skill in parsed
                if clean_skill(skill)
            }
    except (ValueError, SyntaxError, TypeError):
        pass

    text = text.replace(",", "|").replace(";", "|").replace("/", "|")
    return {
        clean_skill(skill)
        for skill in text.split("|")
        if clean_skill(skill)
    }


def extract_user_skills(user_text):
    if not user_text or not user_text.strip():
        return set()

    return {
        clean_skill(skill)
        for skill in user_text.split(",")
        if clean_skill(skill)
    }


def skills_to_text(skills):
    return ", ".join(sorted(skills)) if skills else "None identified"


def skill_chips(skills, css_class="skill-chip"):
    if not skills:
        return "<span class='skill-chip'>None</span>"
    return "".join(
        f"<span class='{css_class}'>{skill.title()}</span>"
        for skill in sorted(skills)
    )


def calculate_position_similarity(user_position, job_position):
    user_position = clean_skill(user_position)
    job_position = clean_skill(job_position)

    if user_position == job_position:
        return 100.0

    user_words = set(user_position.split())
    job_words = set(job_position.split())

    if not user_words or not job_words:
        return 0.0

    common_words = user_words.intersection(job_words)
    if not common_words:
        return 0.0

    union_words = user_words.union(job_words)
    return round(min((len(common_words) / len(union_words)) * 100, 100.0), 2)


def calculate_skill_score(user_skill_set, required_skill_set):
    if not user_skill_set or not required_skill_set:
        return 0.0, 0.0, 0.0, set()

    matched_skills = user_skill_set.intersection(required_skill_set)
    matched_count = len(matched_skills)

    precision = matched_count / len(user_skill_set)
    recall = matched_count / len(required_skill_set)

    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = (2 * precision * recall) / (precision + recall)

    return (
        round(f1_score * 100, 2),
        round(precision * 100, 2),
        round(recall * 100, 2),
        matched_skills,
    )


@st.cache_resource(show_spinner=False)
def load_semantic_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


@st.cache_data(show_spinner=False)
def semantic_similarity(user_profile, job_texts):
    model = load_semantic_model()
    texts = [user_profile] + list(job_texts)
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    scores = np.dot(embeddings[1:], embeddings[0]) * 100
    return np.clip(scores, 0, 100)


def get_skill_vocabulary(dataframe):
    vocab = set()
    for value in dataframe["job_skill_set"].dropna():
        vocab.update(extract_required_skills(value))
    return vocab


def extract_resume_text(uploaded_file):
    if uploaded_file is None:
        return ""

    data = uploaded_file.getvalue()
    filename = uploaded_file.name.lower()

    try:
        if filename.endswith(".pdf"):
            if PdfReader is None:
                raise RuntimeError("pypdf is not installed.")
            reader = PdfReader(io.BytesIO(data))
            return "\n".join((page.extract_text() or "") for page in reader.pages)

        if filename.endswith(".docx"):
            if Document is None:
                raise RuntimeError("python-docx is not installed.")
            doc = Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)

        if filename.endswith(".txt"):
            return data.decode("utf-8", errors="ignore")

        raise ValueError("Unsupported file type.")
    except Exception as exc:
        raise RuntimeError(f"Could not read the resume: {exc}") from exc


def extract_skills_from_resume(resume_text, vocabulary):
    if not resume_text:
        return set()

    normalized_resume = clean_skill(resume_text)
    found = set()

    # Match longer phrases first; avoid one-letter noise.
    for skill in sorted(vocabulary, key=lambda x: (-len(x), x)):
        if len(skill) < 2:
            continue

        if " " in skill:
            if skill in normalized_resume:
                found.add(skill)
        else:
            pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
            if re.search(pattern, normalized_resume):
                found.add(skill)

    return found


def build_recommendations(category, job_title, user_skill_set, use_ai=True):
    category_data = df[df["category"] == category].copy()

    if category_data.empty or not user_skill_set:
        return pd.DataFrame()

    # First perform the fast existing matching for every job.
    results = []
    for index, row in category_data.iterrows():
        required_skills = extract_required_skills(row["job_skill_set"])
        if not required_skills:
            continue

        skill_score, precision, recall, matched = calculate_skill_score(
            user_skill_set, required_skills
        )
        position_score = calculate_position_similarity(
            job_title, row["job_title"]
        )

        base_score = skill_score * 0.85 + position_score * 0.15

        results.append({
            "index": index,
            "skill_score": skill_score,
            "precision_percentage": precision,
            "recall_percentage": recall,
            "position_relevance": position_score,
            "matched_skills": matched,
            "required_skills": required_skills,
            "matched_skill_count": len(matched),
            "required_skill_count": len(required_skills),
            "base_score": round(min(max(base_score, 0), 100), 2),
        })

    if not results:
        return pd.DataFrame()

    result_df = pd.DataFrame(results)

    # To keep the app responsive on large datasets, semantic AI is applied
    # to the strongest candidates from the existing matching stage.
    if use_ai:
        candidate = result_df.sort_values(
            ["base_score", "skill_score", "position_relevance"],
            ascending=False
        ).head(100).copy()

        user_profile = (
            f"Career category: {category}. "
            f"Preferred position: {job_title}. "
            f"Candidate skills: {skills_to_text(user_skill_set)}."
        )

        job_texts = [
            (
                f"Job title: {row['job_title']}. "
                f"Job category: {row['category']}. "
                f"Required skills: {row['job_skill_set']}. "
                f"Job description: {row['job_description']}"
            )
            for _, row in category_data.loc[candidate["index"]].iterrows()
        ]

        try:
            semantic_scores = semantic_similarity(
                user_profile,
                tuple(job_texts)
            )
            candidate["semantic_score"] = np.round(semantic_scores, 2)
        except Exception as exc:
            st.warning(
                "AI semantic matching could not be loaded. "
                "The system will continue with skill and position matching."
            )
            candidate["semantic_score"] = 0.0
            st.caption(f"AI model details: {exc}")

        # Transparent AI-assisted score:
        # 55% direct skills + 30% semantic meaning + 15% position.
        candidate["ai_match_percentage"] = np.round(
            candidate["skill_score"] * 0.55
            + candidate["semantic_score"] * 0.30
            + candidate["position_relevance"] * 0.15,
            2
        )

        result_df = result_df.merge(
            candidate[["index", "semantic_score", "ai_match_percentage"]],
            on="index",
            how="left"
        )
        result_df["semantic_score"] = result_df["semantic_score"].fillna(0.0)
        result_df["ai_match_percentage"] = result_df["ai_match_percentage"].fillna(
            result_df["base_score"]
        )
        score_column = "ai_match_percentage"
    else:
        result_df["semantic_score"] = 0.0
        result_df["ai_match_percentage"] = result_df["base_score"]
        score_column = "base_score"

    recommendations = category_data.merge(
        result_df,
        left_index=True,
        right_on="index"
    )

    recommendations["missing_skills"] = recommendations.apply(
        lambda row: row["required_skills"] - user_skill_set,
        axis=1
    )

    recommendations = (
        recommendations
        .sort_values(
            [score_column, "skill_score", "position_relevance"],
            ascending=False
        )
        .head(5)
        .copy()
    )

    recommendations["match_percentage"] = recommendations[score_column].round(2)

    return recommendations


def youtube_search_url(skill):
    query = quote_plus(f"{skill} tutorial for beginners")
    return f"https://www.youtube.com/results?search_query={query}"


def go_to(page):
    st.session_state.page = page
    st.rerun()


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <h2>💼 CareerMatch AI</h2>
            <p>Smart Job Recommendation System</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_page = st.radio(
        "Navigation",
        PAGES,
        index=PAGES.index(st.session_state.page),
    )

    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.rerun()

    st.divider()

    st.markdown("### 🔄 Your Current Profile")
    if st.session_state.profile_skills:
        st.caption(
            f"{len(st.session_state.profile_skills)} skills available"
        )
        st.write(
            ", ".join(
                s.title() for s in sorted(st.session_state.profile_skills)[:8]
            )
            + (" ..." if len(st.session_state.profile_skills) > 8 else "")
        )
    else:
        st.caption("No skills added yet.")

    if st.session_state.profile_source:
        st.caption(f"Source: {st.session_state.profile_source}")

    st.divider()

    if st.button("🗑️ Clear Current Results", use_container_width=True):
        st.session_state.recommendations = None
        st.session_state.profile_skills = set()
        st.session_state.profile_source = ""
        st.session_state.resume_text = ""
        st.session_state.resume_skills = set()
        st.rerun()

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.recommendations = None
        st.rerun()

# =====================================================
# HOME
# =====================================================
if st.session_state.page == "🏠 Home":
    st.markdown(
        """
        <div class="hero">
            <h1>💼 CareerMatch AI</h1>
            <div class="subtitle">
                AI-Assisted Smart Job Recommendation System
            </div>
            <div class="small">
                Find suitable jobs from your skills or resume, understand
                your skill gaps, and get learning resources for the next step.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='section-title'>What does CareerMatch AI do?</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        CareerMatch AI compares a candidate's skills and career preference
        with job requirements in the project dataset. It combines direct
        skill matching with NLP-based semantic matching to produce a ranked
        list of suitable jobs.
        """
    )

    st.markdown("### 🔄 Simple Project Workflow")

    cols = st.columns(6)
    workflow = [
        ("👤", "Your Profile", "Skills or Resume"),
        ("🧠", "AI Analysis", "Skill + NLP matching"),
        ("🏆", "Job Results", "Top 5 jobs"),
        ("📊", "Match Score", "Why the job matched"),
        ("🔍", "Skill Gap", "Missing skills"),
        ("▶️", "Learn", "YouTube resources"),
    ]

    for col, (icon, title, desc) in zip(cols, workflow):
        with col:
            st.markdown(
                f"""
                <div class="workflow">
                    <div class="icon">{icon}</div>
                    <b>{title}</b>
                    <br><small>{desc}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    st.markdown("### ✨ Main Features")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📝</div>
                <h3>Manual Skill Search</h3>
                <p>Enter your skills, choose a category and position, and
                receive the most relevant job recommendations.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🧠</div>
                <h3>NLP Semantic Matching</h3>
                <p>Uses a pretrained sentence-transformer model to compare
                the meaning of the candidate profile with job information.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <h3>Skill Gap Analysis</h3>
                <p>Shows which required skills are already matched and which
                skills are still missing for a recommended job.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📄</div>
                <h3>Resume Skill Extraction</h3>
                <p>Upload a PDF, DOCX or TXT resume and identify skills from
                the resume using the project's skill vocabulary.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>Explainable Match Score</h3>
                <p>See direct skill match, NLP semantic score, position
                relevance and the combined AI-assisted score.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">▶️</div>
                <h3>YouTube Learning Resources</h3>
                <p>For missing skills, the system creates YouTube tutorial
                searches so the user can continue learning.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info("Start with **Manual Skill Search** or **Resume Matching** from the sidebar.")

# =====================================================
# MANUAL SKILL SEARCH
# =====================================================
elif st.session_state.page == "📝 Manual Skill Search":
    st.markdown("<div class='section-title'>📝 Manual Skill Search</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Build your profile manually and find suitable jobs.</div>",
        unsafe_allow_html=True,
    )

    categories = sorted(
        df["category"].loc[lambda x: x != ""].unique()
    )

    if not categories:
        st.error("No career categories found in the dataset.")
        st.stop()

    category = st.selectbox(
        "📂 Career Category",
        categories,
        key="manual_category"
    )

    category_data = df[df["category"] == category]
    positions = sorted(
        category_data["job_title"].loc[lambda x: x != ""].unique()
    )

    position = st.selectbox(
        "💼 Preferred Job Position",
        positions,
        key="manual_position"
    )

    skills_text = st.text_input(
        "🛠️ Your Skills",
        placeholder="Example: Python, SQL, Pandas, Machine Learning",
        key="manual_skills"
    )

    if skills_text.strip():
        parsed_skills = extract_user_skills(skills_text)
        st.markdown("### Your Skill Profile")
        st.markdown(
            skill_chips(parsed_skills, "skill-chip matched-chip"),
            unsafe_allow_html=True
        )

    if st.button("🚀 Find My Top 5 Jobs", use_container_width=True):
        user_skills = extract_user_skills(skills_text)

        if not user_skills:
            st.warning("Please enter at least one skill.")
        else:
            with st.spinner("Analyzing your skills and matching jobs..."):
                recommendations = build_recommendations(
                    category,
                    position,
                    user_skills,
                    use_ai=True
                )

            st.session_state.recommendations = recommendations
            st.session_state.profile_skills = user_skills
            st.session_state.profile_source = "Manual Skills"
            st.session_state.selected_category = category
            st.session_state.selected_position = position

            if recommendations.empty:
                st.warning("No suitable jobs found. Try adding more relevant skills.")
            else:
                st.success("Top 5 recommendations generated successfully!")
                st.info("Open **🏆 Job Recommendations** from the sidebar to view the results.")

# =====================================================
# RESUME MATCHING
# =====================================================
elif st.session_state.page == "📄 Resume Matching":
    st.markdown("<div class='section-title'>📄 Resume Matching</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Upload your resume → extract skills → match jobs using AI/NLP.</div>",
        unsafe_allow_html=True,
    )

    categories = sorted(
        df["category"].loc[lambda x: x != ""].unique()
    )

    category = st.selectbox(
        "📂 Career Category",
        categories,
        key="resume_category"
    )

    category_data = df[df["category"] == category]
    positions = sorted(
        category_data["job_title"].loc[lambda x: x != ""].unique()
    )

    position = st.selectbox(
        "💼 Preferred Job Position",
        positions,
        key="resume_position"
    )

    uploaded = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, DOCX and TXT"
    )

    if uploaded is not None:
        st.caption(f"Selected file: **{uploaded.name}**")

        if st.button("🤖 Analyze Resume & Find Jobs", use_container_width=True):
            try:
                with st.spinner("Reading your resume..."):
                    resume_text = extract_resume_text(uploaded)

                if not resume_text.strip():
                    st.error(
                        "No readable text was found in this resume. "
                        "For scanned/image-only PDFs, use a text-based PDF or DOCX."
                    )
                else:
                    vocabulary = get_skill_vocabulary(df)

                    with st.spinner("Identifying skills from your resume..."):
                        found_skills = extract_skills_from_resume(
                            resume_text,
                            vocabulary
                        )

                    if not found_skills:
                        st.warning(
                            "No project-dataset skills were identified. "
                            "You can use Manual Skill Search to add skills."
                        )
                    else:
                        st.session_state.resume_text = resume_text
                        st.session_state.resume_skills = found_skills

                        with st.spinner("Running AI/NLP job matching..."):
                            recommendations = build_recommendations(
                                category,
                                position,
                                found_skills,
                                use_ai=True
                            )

                        st.session_state.recommendations = recommendations
                        st.session_state.profile_skills = found_skills
                        st.session_state.profile_source = "Resume"
                        st.session_state.selected_category = category
                        st.session_state.selected_position = position

                        st.success("Resume analyzed successfully!")

                        st.markdown("### 🤖 Skills Identified from Your Resume")
                        st.markdown(
                            skill_chips(found_skills, "skill-chip matched-chip"),
                            unsafe_allow_html=True
                        )

                        st.info(
                            f"Identified **{len(found_skills)}** skills. "
                            "Open **🏆 Job Recommendations** to view your results."
                        )

            except Exception as exc:
                st.error("Resume analysis failed.")
                st.caption(str(exc))

    if st.session_state.resume_skills:
        st.divider()
        st.markdown("### 📌 Current Resume Skill Profile")
        st.markdown(
            skill_chips(
                st.session_state.resume_skills,
                "skill-chip matched-chip"
            ),
            unsafe_allow_html=True
        )

# =====================================================
# JOB RECOMMENDATIONS
# =====================================================
elif st.session_state.page == "🏆 Job Recommendations":
    st.markdown("<div class='section-title'>🏆 Job Recommendations</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Your top matching jobs with transparent AI-assisted scoring.</div>",
        unsafe_allow_html=True,
    )

    recommendations = st.session_state.recommendations

    if recommendations is None or recommendations.empty:
        st.markdown(
            """
            <div class="empty-state">
                <h2>🔎 No recommendations yet</h2>
                <p>Use Manual Skill Search or Resume Matching first.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info(
            f"📂 **Category:** {st.session_state.selected_category}  |  "
            f"💼 **Position:** {st.session_state.selected_position}  |  "
            f"👤 **Profile:** {st.session_state.profile_source}"
        )

        for number, (_, row) in enumerate(
            recommendations.iterrows(),
            start=1
        ):
            score = float(row["match_percentage"])
            matched = row["matched_skills"]
            missing = row["missing_skills"]

            st.markdown(
                f"""
                <div class="result-card">
                    <div class="job-heading">{number}. 💼 {row["job_title"]}</div>
                    <div style="margin-top:8px;">
                        📂 {row["category"]} &nbsp; • &nbsp; 🆔 Job ID: {row["job_id"]}
                    </div>
                    <div class="score" style="margin-top:12px;">
                        🎯 AI Match: {score:.1f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.progress(int(max(0, min(score, 100))))

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(
                    f"<div class='metric-box'><div class='metric-number'>{row['skill_score']:.1f}%</div><div class='metric-label'>Direct Skill Match</div></div>",
                    unsafe_allow_html=True
                )
            with m2:
                st.markdown(
                    f"<div class='metric-box'><div class='metric-number'>{row['semantic_score']:.1f}%</div><div class='metric-label'>NLP Semantic Match</div></div>",
                    unsafe_allow_html=True
                )
            with m3:
                st.markdown(
                    f"<div class='metric-box'><div class='metric-number'>{row['position_relevance']:.1f}%</div><div class='metric-label'>Position Relevance</div></div>",
                    unsafe_allow_html=True
                )
            with m4:
                st.markdown(
                    f"<div class='metric-box'><div class='metric-number'>{len(missing)}</div><div class='metric-label'>Missing Skills</div></div>",
                    unsafe_allow_html=True
                )

            with st.expander(f"📄 View {row['job_title']} Details"):
                st.markdown("### 📝 Job Description")
                st.write(row["job_description"])

                st.markdown("### ✅ Skills You Have")
                st.markdown(
                    skill_chips(matched, "skill-chip matched-chip"),
                    unsafe_allow_html=True
                )

                st.markdown("### ❌ Skills You May Need")
                st.markdown(
                    skill_chips(missing, "skill-chip missing-chip"),
                    unsafe_allow_html=True
                )

                st.markdown("### 🛠️ Required Skills")
                st.write(row["job_skill_set"])

                st.markdown("### 📊 Why This Job Matched")
                st.write(
                    f"Direct skill matching: **{row['skill_score']:.1f}%**"
                )
                st.write(
                    f"NLP semantic matching: **{row['semantic_score']:.1f}%**"
                )
                st.write(
                    f"Position relevance: **{row['position_relevance']:.1f}%**"
                )
                st.caption(
                    "AI-assisted score = 55% direct skill match + "
                    "30% NLP semantic match + 15% position relevance."
                )

        st.divider()
        st.success(
            "Your recommendations are based on the current project dataset "
            "and your selected career preference."
        )

# =====================================================
# SKILL GAP & LEARNING
# =====================================================
elif st.session_state.page == "🔍 Skill Gap & Learning":
    st.markdown("<div class='section-title'>🔍 Skill Gap & Learning</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Understand what you already have and what you can learn next.</div>",
        unsafe_allow_html=True,
    )

    recommendations = st.session_state.recommendations

    if recommendations is None or recommendations.empty:
        st.markdown(
            """
            <div class="empty-state">
                <h2>🔍 Skill gap is not available yet</h2>
                <p>Generate job recommendations first.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        labels = [
            f"{i+1}. {row['job_title']}"
            for i, (_, row) in enumerate(recommendations.iterrows())
        ]

        selected_label = st.selectbox(
            "Select a recommended job",
            labels
        )

        selected_index = labels.index(selected_label)
        selected_row = recommendations.iloc[selected_index]

        required = selected_row["required_skills"]
        user_skills = st.session_state.profile_skills

        matched = required.intersection(user_skills)
        missing = required - user_skills

        st.markdown(
            f"""
            <div class="info-card">
                <h2>💼 {selected_row["job_title"]}</h2>
                <p>AI Match: <b>{selected_row["match_percentage"]:.1f}%</b></p>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### ✅ Skills You Already Have")
            st.markdown(
                skill_chips(matched, "skill-chip matched-chip"),
                unsafe_allow_html=True
            )
            st.metric("Matched Skills", len(matched))

        with c2:
            st.markdown("### ❌ Skill Gap")
            st.markdown(
                skill_chips(missing, "skill-chip missing-chip"),
                unsafe_allow_html=True
            )
            st.metric("Missing Skills", len(missing))

        st.divider()

        st.markdown("### ▶️ Learning Recommendations")

        if not missing:
            st.success(
                "Excellent! All required dataset skills for this job are "
                "already present in your profile."
            )
        else:
            st.write(
                "Use the links below to find tutorials for the skills "
                "identified in your skill gap."
            )

            for skill in sorted(missing):
                url = youtube_search_url(skill)
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(
                        f"""
                        <div class="gap-card">
                            <b>📚 {skill.title()}</b>
                            <br>
                            <small>Suggested search: {skill.title()} tutorial for beginners</small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.link_button(
                        "▶️ Learn",
                        url,
                        use_container_width=True
                    )

        st.divider()
        st.caption(
            "YouTube links open a search for the missing skill rather than "
            "hard-coding one specific video, so the learning results can stay current."
        )

# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    """
    <div class="footer">
        <b>💼 CareerMatch AI</b><br>
        AI-Assisted Smart Job Recommendation System<br><br>
        Built with Python • Pandas • Streamlit • NLP • Sentence Transformers
    </div>
    """,
    unsafe_allow_html=True
)
