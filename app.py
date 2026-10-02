import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast
from urllib.parse import quote_plus

# Optional AI / resume libraries
try:
    import numpy as np
except ImportError:
    np = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
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
# USER DATA / LOGIN
# =====================================================
USER_FILE = "user_data.json"


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


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 CareerMatch AI")
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
        confirm_password = st.text_input("Confirm Password", type="password")

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
                    "password": hash_password(password)
                })
                st.success("Registration successful! You can now login.")

    elif option == "Login":
        st.subheader("Login")
        login_id = st.text_input("Email or Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            user = load_user()
            if user is None:
                st.warning("No account found. Please register first.")
            elif (
                (login_id == user.get("email") or login_id == user.get("username"))
                and hash_password(password) == user.get("password")
            ):
                st.session_state.logged_in = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Incorrect email/username or password.")

    else:
        st.subheader("🔑 Forgot Password")
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


if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()


# =====================================================
# DATASET
# =====================================================
try:
    df = pd.read_csv("Cleaned_New_Data.csv")
except Exception as e:
    st.error(f"Unable to load Cleaned_New_Data.csv: {e}")
    st.stop()

required_columns = [
    "job_id", "category", "job_title", "job_description", "job_skill_set"
]
missing_columns = [c for c in required_columns if c not in df.columns]
if missing_columns:
    st.error("Dataset is missing required columns: " + ", ".join(missing_columns))
    st.stop()

for column in required_columns:
    df[column] = df[column].fillna("").astype(str).str.strip()


# =====================================================
# CSS
# =====================================================
st.markdown(
    """
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
.hero { text-align:center; padding:35px; border-radius:22px; border:1px solid rgba(128,128,128,.25); margin-bottom:30px; background:linear-gradient(135deg,rgba(128,128,128,.08),rgba(128,128,128,.02)); }
.hero h1 { font-size:42px; margin-bottom:8px; }
.hero p { font-size:18px; }
.step-card,.feature-card,.skill-box,.job-card,.gap-card { padding:20px; border-radius:18px; border:1px solid rgba(128,128,128,.25); background:rgba(128,128,128,.03); }
.step-card { min-height:150px; text-align:center; }
.step-icon { font-size:30px; }
.job-card { margin-bottom:18px; }
.job-title { font-size:24px; font-weight:700; }
.match-score { font-size:22px; font-weight:700; }
.skill-tag { display:inline-block; padding:5px 10px; margin:3px; border-radius:12px; border:1px solid rgba(128,128,128,.25); }
.missing-tag { display:inline-block; padding:6px 11px; margin:3px; border-radius:12px; border:1px solid rgba(180,100,100,.35); }
.stButton > button { min-height:48px; border-radius:12px; font-size:16px; font-weight:600; }
.footer { text-align:center; padding:20px; opacity:.7; }
.small-note { opacity:.75; font-size:14px; }
</style>
""",
    unsafe_allow_html=True
)


# =====================================================
# HELPERS - DEFINED BEFORE ANY CALLS
# =====================================================
def clean_skill(skill):
    if skill is None:
        return ""
    skill = str(skill).lower().strip()
    skill = skill.replace("_", " ").replace("-", " ")
    skill = re.sub(r"\s+", " ", skill)
    return skill.strip()


def extract_required_skills(skill_text):
    if not skill_text or str(skill_text).strip().lower() in {"nan", "none"}:
        return set()

    text = str(skill_text).strip()
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple, set)):
            return {clean_skill(x) for x in parsed if clean_skill(x)}
    except (ValueError, SyntaxError):
        pass

    text = re.sub(r"[\[\]\"']", "", text)
    text = text.replace(",", "|").replace(";", "|").replace("/", "|")
    return {clean_skill(x) for x in text.split("|") if clean_skill(x)}


def extract_user_skills(user_text):
    if not user_text or not str(user_text).strip():
        return set()
    return {clean_skill(x) for x in str(user_text).split(",") if clean_skill(x)}


def calculate_position_similarity(user_position, job_position):
    user_position = clean_skill(user_position)
    job_position = clean_skill(job_position)
    if not user_position or not job_position:
        return 0.0
    if user_position == job_position:
        return 100.0
    user_words = set(user_position.split())
    job_words = set(job_position.split())
    union_words = user_words | job_words
    common_words = user_words & job_words
    if not union_words:
        return 0.0
    return round((len(common_words) / len(union_words)) * 100, 2)


def calculate_skill_score(user_skill_set, required_skill_set):
    if not user_skill_set or not required_skill_set:
        return 0.0, 0.0, 0.0, set()

    matched = user_skill_set.intersection(required_skill_set)
    matched_count = len(matched)
    precision = matched_count / len(user_skill_set)
    recall = matched_count / len(required_skill_set)
    f1 = 0.0 if precision + recall == 0 else (2 * precision * recall) / (precision + recall)
    return round(f1 * 100, 2), round(precision * 100, 2), round(recall * 100, 2), matched


def extract_resume_text(uploaded_file):
    if uploaded_file is None:
        return ""
    file_name = uploaded_file.name.lower()
    try:
        if file_name.endswith(".pdf"):
            if PdfReader is None:
                return ""
            reader = PdfReader(uploaded_file)
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        if file_name.endswith(".docx"):
            if Document is None:
                return ""
            document = Document(uploaded_file)
            return "\n".join(p.text for p in document.paragraphs)
        if file_name.endswith(".txt"):
            return uploaded_file.getvalue().decode("utf-8", errors="ignore")
    except Exception:
        return ""
    return ""


def build_skill_vocabulary(dataframe):
    skills = set()
    for value in dataframe["job_skill_set"].tolist():
        skills.update(extract_required_skills(value))
    return skills


def extract_skills_from_resume(resume_text, skill_vocabulary):
    """AI-assisted resume extraction using the project's known skill vocabulary.
    It avoids inventing skills that do not exist in the dataset.
    """
    if not resume_text:
        return set()

    normalized_resume = clean_skill(resume_text)
    found = set()

    # Longest phrases first reduces partial-match problems.
    for skill in sorted(skill_vocabulary, key=len, reverse=True):
        if not skill:
            continue
        pattern = r"(?<![a-z0-9+#.])" + re.escape(skill) + r"(?![a-z0-9+#.])"
        if re.search(pattern, normalized_resume, flags=re.IGNORECASE):
            found.add(skill)

    return found


@st.cache_resource(show_spinner=False)
def load_semantic_model():
    if SentenceTransformer is None:
        return None
    try:
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


def semantic_scores(user_profile, job_texts):
    """Return cosine-similarity scores in percentage form."""
    model = load_semantic_model()
    if model is None or not job_texts or np is None:
        return [0.0] * len(job_texts)
    try:
        embeddings = model.encode(
            [user_profile] + job_texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        scores = np.dot(embeddings[1:], embeddings[0]) * 100
        return [round(float(max(0.0, min(100.0, s))), 2) for s in scores]
    except Exception:
        return [0.0] * len(job_texts)


def combined_score(skill_score, semantic_score, position_score, ai_available):
    if ai_available:
        # Exact skill matching remains the strongest signal.
        score = (skill_score * 0.60) + (semantic_score * 0.30) + (position_score * 0.10)
    else:
        score = (skill_score * 0.85) + (position_score * 0.15)
    return round(max(0.0, min(100.0, score)), 2)


def youtube_search_url(skill):
    query = quote_plus(f"{skill} tutorial for beginners")
    return f"https://www.youtube.com/results?search_query={query}"


def display_skill_tags(skills, missing=False):
    if not skills:
        return "<span class='small-note'>None</span>"
    cls = "missing-tag" if missing else "skill-tag"
    return " ".join(f"<span class='{cls}'>{skill.title()}</span>" for skill in sorted(skills))


def get_recommendations(category, job_title, user_skill_set, manual_skill_count, use_ai=True):
    category_data = df[df["category"] == category].copy()
    if category_data.empty or not user_skill_set:
        return category_data.iloc[0:0], False

    # Build one profile for semantic matching.
    profile_skills = ", ".join(sorted(user_skill_set))
    user_profile = f"Career category: {category}. Desired position: {job_title}. Skills: {profile_skills}."

    job_texts = [
        f"Job title: {row['job_title']}. Job description: {row['job_description']}. Required skills: {row['job_skill_set']}."
        for _, row in category_data.iterrows()
    ]

    ai_scores = semantic_scores(user_profile, job_texts) if use_ai else [0.0] * len(job_texts)
    ai_available = use_ai and SentenceTransformer is not None and load_semantic_model() is not None

    results = []
    for position, (index, row) in enumerate(category_data.iterrows()):
        required_skills = extract_required_skills(row["job_skill_set"])
        if not required_skills:
            continue

        skill_score, precision, recall, matched = calculate_skill_score(user_skill_set, required_skills)
        position_score = calculate_position_similarity(job_title, row["job_title"])
        semantic_score = ai_scores[position] if position < len(ai_scores) else 0.0
        final_score = combined_score(skill_score, semantic_score, position_score, ai_available)
        missing = required_skills - matched

        results.append({
            "index": index,
            "match_percentage": final_score,
            "matched_skills": matched,
            "missing_skills": missing,
            "skill_score": skill_score,
            "precision_percentage": precision,
            "recall_percentage": recall,
            "semantic_score": semantic_score,
            "position_relevance": position_score,
            "required_skill_count": len(required_skills),
            "matched_skill_count": len(matched),
            "manual_skill_count": manual_skill_count
        })

    if not results:
        return category_data.iloc[0:0], ai_available

    result_df = pd.DataFrame(results)
    recommendations = category_data.merge(result_df, left_index=True, right_on="index")
    recommendations = recommendations.sort_values(
        by=["match_percentage", "skill_score", "semantic_score", "position_relevance"],
        ascending=False
    ).head(5)
    return recommendations, ai_available


# =====================================================
# HEADER
# =====================================================
st.markdown(
    """
<div class="hero">
<h1>💼 CareerMatch AI</h1>
<p>AI-Assisted Smart Job Recommendation System</p>
<p>Discover • Explore • Find Your Opportunity</p>
</div>
""",
    unsafe_allow_html=True
)

st.subheader("🚀 How It Works")
cols = st.columns(4)
steps = [
    ("1️⃣", "Resume / Skills", "Upload a resume or enter skills manually."),
    ("2️⃣", "AI Skill Extraction", "Identify relevant skills from the resume."),
    ("3️⃣", "NLP Matching", "Compare skills and job descriptions semantically."),
    ("4️⃣", "Career Insights", "See Top 5 jobs, skill gaps and learning links.")
]
for col, (icon, title, desc) in zip(cols, steps):
    with col:
        st.markdown(
            f"<div class='step-card'><div class='step-icon'>{icon}</div><h3>{title}</h3><p>{desc}</p></div>",
            unsafe_allow_html=True
        )

st.divider()


# =====================================================
# INPUTS
# =====================================================
st.subheader("🔎 Find Your Job")
st.info("Select a category and position, then use manual skills, a resume, or both.")

categories = sorted(df["category"].dropna().astype(str).str.strip().loc[lambda x: x != ""].unique())
if not categories:
    st.error("No career categories found in dataset.")
    st.stop()

category = st.selectbox("📂 Career Category", categories)

category_data = df[df["category"] == category].copy()
category_jobs = sorted(category_data["job_title"].dropna().astype(str).str.strip().loc[lambda x: x != ""].unique())
if not category_jobs:
    st.error("No job positions found for this category.")
    st.stop()

job_title = st.selectbox("💼 Available Positions", category_jobs)

col1, col2 = st.columns(2)
with col1:
    manual_skills_text = st.text_input(
        "🛠️ Your Skills",
        placeholder="Example: Python, SQL, Pandas, Machine Learning"
    )
with col2:
    resume_file = st.file_uploader(
        "📄 Upload Resume (PDF / DOCX / TXT)",
        type=["pdf", "docx", "txt"]
    )

use_ai = st.checkbox(
    "🤖 Enable NLP Semantic Matching",
    value=True,
    help="Uses a pretrained sentence-transformer model to compare your profile with job descriptions and required skills."
)


# =====================================================
# RESUME PROCESSING
# =====================================================
manual_skill_set = extract_user_skills(manual_skills_text)
resume_text = ""
resume_skills = set()

if resume_file is not None:
    resume_text = extract_resume_text(resume_file)
    if resume_text:
        skill_vocabulary = build_skill_vocabulary(df)
        resume_skills = extract_skills_from_resume(resume_text, skill_vocabulary)
        st.success(f"Resume processed successfully: {resume_file.name}")
        if resume_skills:
            st.markdown("### 🤖 AI/NLP Identified Skills")
            st.markdown(display_skill_tags(resume_skills), unsafe_allow_html=True)
        else:
            st.warning("No dataset-recognized skills were identified from the resume. You can add skills manually.")
    else:
        st.error("The resume could not be read. Please try another PDF, DOCX or TXT file.")

combined_skills = manual_skill_set | resume_skills

if combined_skills:
    st.markdown("### 👤 Candidate Skill Profile")
    st.markdown(display_skill_tags(combined_skills), unsafe_allow_html=True)
    st.caption(
        f"{len(manual_skill_set)} manual skill(s) + {len(resume_skills)} resume skill(s) → {len(combined_skills)} unique skill(s)"
    )


# =====================================================
# POSITION PREVIEW
# =====================================================
st.subheader("👀 Position Preview")
selected_job = df[(df["category"] == category) & (df["job_title"] == job_title)]
if not selected_job.empty:
    first_job = selected_job.iloc[0]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"<div class='feature-card'><b>📂 Career Category</b><h3>{category}</h3><b>💼 Selected Position</b><h3>{job_title}</h3></div>",
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"<div class='skill-box'><b>🛠️ Example Required Skills</b><br><br>{first_job['job_skill_set']}</div>",
            unsafe_allow_html=True
        )


# =====================================================
# FIND JOBS
# =====================================================
st.divider()
find_button = st.button("🚀 Find Top 5 AI Job Recommendations", use_container_width=True)

if find_button:
    if not combined_skills:
        st.warning("Please enter at least one skill manually or upload a resume containing relevant skills.")
        st.stop()

    with st.spinner("Analyzing skills and matching jobs..."):
        recommendations, ai_available = get_recommendations(
            category,
            job_title,
            combined_skills,
            len(manual_skill_set),
            use_ai=use_ai
        )

    if use_ai and not ai_available:
        st.warning(
            "NLP model is not available. Showing the existing skill-based recommendation logic. "
            "Install the packages from requirements.txt and restart the app to enable semantic matching."
        )

    if recommendations.empty:
        st.error("No suitable recommendations could be generated for the selected input.")
        st.stop()

    st.subheader("🏆 Top 5 Job Recommendations")
    st.caption("Recommendations combine direct skill matching, NLP semantic similarity and position relevance when AI mode is available.")

    for number, (_, row) in enumerate(recommendations.iterrows(), start=1):
        match_percentage = float(row["match_percentage"])
        matched = row["matched_skills"]
        missing = row["missing_skills"]
        matched_text = ", ".join(sorted(s.title() for s in matched)) if matched else "None"
        missing_text = ", ".join(sorted(s.title() for s in missing)) if missing else "None"

        st.markdown(
            f"""
            <div class='job-card'>
                <div class='job-title'>{number}. 💼 {row['job_title']}</div>
                <br>
                <div class='match-score'>🎯 AI Match: {match_percentage:.2f}%</div>
                <br>
                📂 <b>Category:</b> {row['category']}<br><br>
                🆔 <b>Job ID:</b> {row['job_id']}<br><br>
                ✅ <b>Matching Skills:</b> {matched_text}<br><br>
                ⚠️ <b>Missing Skills:</b> {missing_text}<br><br>
                🛠️ <b>Required Skills:</b> {row['job_skill_set']}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.progress(int(max(0, min(100, round(match_percentage)))))

        with st.expander(f"📄 View Full Details - Job {number}"):
            st.markdown("### 📝 Job Description")
            st.write(row["job_description"])

            st.markdown("### 📊 Match Score Breakdown")
            b1, b2, b3 = st.columns(3)
            b1.metric("Exact Skill Match", f"{row['skill_score']:.1f}%")
            b2.metric("NLP Semantic Match", f"{row['semantic_score']:.1f}%")
            b3.metric("Position Relevance", f"{row['position_relevance']:.1f}%")

            st.write(
                f"**Matched skills:** {row['matched_skill_count']} / {row['required_skill_count']} required skills"
            )
            st.write(f"**Matching skills:** {matched_text}")

            st.markdown("### 🔍 Skill Gap Analysis")
            if missing:
                st.markdown(
                    f"<div class='gap-card'><b>Skills to develop for this role:</b><br><br>{display_skill_tags(missing, missing=True)}</div>",
                    unsafe_allow_html=True
                )

                st.markdown("### 📚 Learning Recommendations")
                st.caption("Search for beginner-friendly tutorials and full courses for the missing skills.")
                for skill in sorted(missing):
                    url = youtube_search_url(skill)
                    st.markdown(f"▶️ **{skill.title()}** — [Learn on YouTube]({url})")
            else:
                st.success("🎉 No missing skills were identified for this job's listed skill set.")

            st.markdown("### 🛠️ Required Skills")
            st.write(row["job_skill_set"])


# =====================================================
# AI FEATURE INFORMATION
# =====================================================
st.divider()
st.subheader("🤖 AI Features in CareerMatch AI")
info_cols = st.columns(4)
features = [
    ("📄", "Resume Skill Extraction", "Reads PDF/DOCX/TXT resumes and identifies skills present in the project dataset."),
    ("🧠", "NLP Semantic Matching", "Uses a pretrained sentence-transformer to compare the candidate profile with job text."),
    ("🔍", "Skill Gap Analysis", "Shows required skills that are not present in the candidate skill profile."),
    ("▶️", "YouTube Learning Links", "Creates YouTube tutorial searches for missing skills to support learning."),
]
for col, (icon, title, desc) in zip(info_cols, features):
    with col:
        st.markdown(
            f"<div class='feature-card'><h3>{icon} {title}</h3><p>{desc}</p></div>",
            unsafe_allow_html=True
        )


# =====================================================
# FOOTER
# =====================================================
st.markdown("---")
st.markdown(
    """
<div class='footer'>
<b>💼 CareerMatch AI</b><br>
AI-Assisted Smart Job Recommendation System<br><br>
Built with Python • Pandas • Streamlit • NLP • Sentence Transformers
</div>
""",
    unsafe_allow_html=True
)
