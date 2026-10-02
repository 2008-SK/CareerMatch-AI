import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast
from urllib.parse import quote_plus

try:
    import numpy as np
except ImportError:
    np = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


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
# USER DATA FILE
# =====================================================

USER_FILE = "user_data.json"


def load_user():

    if os.path.exists(USER_FILE):

        try:
            with open(USER_FILE, "r") as file:
                return json.load(file)

        except:
            return None

    return None


def save_user(user):

    with open(USER_FILE, "w") as file:
        json.dump(user, file)


def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# =====================================================
# SESSION STATE
# =====================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


if "page" not in st.session_state:
    st.session_state.page = "Login"


# =====================================================
# LOGIN SYSTEM
# =====================================================

if not st.session_state.logged_in:

    st.title("🔐 CareerMatch AI")

    option = st.radio(
        "Choose an option",
        ["Login", "Register", "Forgot Password"],
        horizontal=True
    )


    # =================================================
    # REGISTER
    # =================================================

    if option == "Register":

        st.subheader("Create Account")

        email = st.text_input("Email")

        username = st.text_input("Username")

        password = st.text_input(
            "Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )


        if st.button(
            "Register",
            use_container_width=True
        ):

            if not email or not username or not password:

                st.warning(
                    "Please fill all fields."
                )

            elif password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            elif len(password) < 6:

                st.error(
                    "Password must contain at least 6 characters."
                )

            else:

                user = {
                    "email": email,
                    "username": username,
                    "password": hash_password(password)
                }

                save_user(user)

                st.success(
                    "Registration successful! "
                    "You can now login."
                )


    # =================================================
    # LOGIN
    # =================================================

    elif option == "Login":

        st.subheader("Login")

        login_id = st.text_input(
            "Email or Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )


        if st.button(
            "Login",
            use_container_width=True
        ):

            user = load_user()


            if user is None:

                st.warning(
                    "No account found. Please register first."
                )


            elif (
                login_id == user["email"]
                or
                login_id == user["username"]
            ) and (
                hash_password(password)
                ==
                user["password"]
            ):

                st.session_state.logged_in = True

                st.success(
                    "Login successful!"
                )

                st.rerun()


            else:

                st.error(
                    "Incorrect email/username or password."
                )


    # =================================================
    # FORGOT PASSWORD
    # =================================================

    else:

        st.subheader("🔑 Forgot Password")

        email = st.text_input(
            "Enter your registered email"
        )

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )


        if st.button(
            "Reset Password",
            use_container_width=True
        ):

            user = load_user()


            if user is None:

                st.error(
                    "No registered account found."
                )


            elif email != user["email"]:

                st.error(
                    "Email does not match the registered email."
                )


            elif len(new_password) < 6:

                st.error(
                    "Password must contain at least 6 characters."
                )


            elif new_password != confirm_password:

                st.error(
                    "Passwords do not match."
                )


            else:

                user["password"] = hash_password(
                    new_password
                )

                save_user(user)

                st.success(
                    "Password reset successfully! "
                    "You can now login."
                )


    st.stop()


# =====================================================
# LOGOUT
# =====================================================

if st.sidebar.button("Logout"):

    st.session_state.logged_in = False

    st.rerun()


# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_csv(
    "Cleaned_New_Data.csv"
)


# =====================================================
# BASIC DATA CLEANING
# =====================================================

required_columns = [
    "job_id",
    "category",
    "job_title",
    "job_description",
    "job_skill_set"
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    st.error(
        "Dataset is missing required columns: "
        + ", ".join(missing_columns)
    )

    st.stop()


df["category"] = (
    df["category"]
    .fillna("")
    .astype(str)
    .str.strip()
)


df["job_title"] = (
    df["job_title"]
    .fillna("")
    .astype(str)
    .str.strip()
)


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
    padding: 35px;
    border-radius: 22px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 30px;
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
    font-size: 18px;
}

.step-card {
    padding: 20px;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,0.25);
    min-height: 150px;
    text-align: center;
    background: rgba(128,128,128,0.03);
}

.step-icon {
    font-size: 30px;
}

.preference-card,
.skill-box {
    padding: 20px;
    border-radius: 17px;
    border: 1px solid rgba(128,128,128,0.25);
    background: rgba(128,128,128,0.03);
}

.job-card {
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 18px;
    background: rgba(128,128,128,0.025);
}

.job-title {
    font-size: 24px;
    font-weight: 700;
}

.match-score {
    font-size: 22px;
    font-weight: 700;
}

.stButton > button {
    height: 52px;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 600;
}

div[data-testid="stExpander"] {
    border-radius: 12px;
}

.footer {
    text-align: center;
    padding: 20px;
    opacity: 0.7;
}

.ai-section {
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,0.25);
    background: rgba(128,128,128,0.025);
    margin: 18px 0;
}

.feature-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    border: 1px solid rgba(128,128,128,0.25);
    margin: 3px;
    font-size: 14px;
}

.skill-pill {
    display: inline-block;
    padding: 6px 10px;
    margin: 4px;
    border-radius: 14px;
    border: 1px solid rgba(128,128,128,0.25);
}

.missing-pill {
    display: inline-block;
    padding: 6px 10px;
    margin: 4px;
    border-radius: 14px;
    border: 1px solid rgba(220,80,80,0.35);
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

<h1>💼 CareerMatch AI</h1>

<p>Find the right job for your career</p>

<p>Discover • Explore • Find Your Opportunity</p>

</div>
""",
    unsafe_allow_html=True
)


# =====================================================
# HOW IT WORKS
# =====================================================

st.subheader("🚀 How It Works")

st.write(
    "Choose your category, position and skills "
    "to find the most suitable job opportunities."
)


col1, col2, col3 = st.columns(3)


with col1:

    st.markdown(
        """
        <div class="step-card">

        <div class="step-icon">1️⃣</div>

        <h3>Choose Category</h3>

        <p>Select your preferred career field.</p>

        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        """
        <div class="step-card">

        <div class="step-icon">2️⃣</div>

        <h3>Choose Position</h3>

        <p>Select your preferred job position.</p>

        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        """
        <div class="step-card">

        <div class="step-icon">3️⃣</div>

        <h3>Enter Skills</h3>

        <p>Enter your skills to get job matches.</p>

        </div>
        """,
        unsafe_allow_html=True
    )


st.divider()


# =====================================================
# JOB SEARCH
# =====================================================

st.subheader("🔎 Find Your Job")

st.info(
    "👋 Select a **Category**, choose a **Position**, "
    "and enter your **Skills** to get the top 5 recommendations."
)


# =====================================================
# STEP 1 — CATEGORY
# =====================================================

st.markdown(
    "### 1️⃣ Select Your Career Category"
)


categories = sorted(
    df["category"]
    .dropna()
    .astype(str)
    .str.strip()
    .loc[lambda x: x != ""]
    .unique()
)


if not categories:

    st.error(
        "No career categories found in dataset."
    )

    st.stop()


category = st.selectbox(
    "📂 Career Category",
    categories
)


# =====================================================
# STEP 2 — POSITION
# =====================================================

category_data = df[
    df["category"] == category
].copy()


category_jobs = sorted(
    category_data["job_title"]
    .dropna()
    .astype(str)
    .str.strip()
    .loc[lambda x: x != ""]
    .unique()
)


st.markdown(
    "### 2️⃣ Select Your Job Position"
)


if not category_jobs:

    st.error(
        "No job positions found for this category."
    )

    st.stop()


job_title = st.selectbox(
    "💼 Available Positions",
    category_jobs
)


# =====================================================
# STEP 3 — USER SKILLS
# =====================================================

st.markdown(
    "### 3️⃣ Enter Your Skills"
)

st.caption(
    "Enter your skills separated by commas."
)


user_skills = st.text_input(
    "🛠️ Your Skills",
    placeholder=(
        "Example: Python, SQL, Pandas, "
        "Machine Learning"
    )
)


# =====================================================
# PROGRESS
# =====================================================

if user_skills.strip():

    st.progress(100)

    st.caption(
        "✅ Category selected  |  "
        "✅ Position selected  |  "
        "✅ Skills added  |  "
        "🚀 Ready to find jobs"
    )

else:

    st.progress(66)

    st.caption(
        "✅ Category selected  |  "
        "✅ Position selected  |  "
        "⏳ Add your skills"
    )


# =====================================================
# POSITION PREVIEW
# =====================================================

st.subheader(
    "👀 Position Preview"
)


selected_job = df[
    (df["category"] == category)
    &
    (df["job_title"] == job_title)
]


if not selected_job.empty:

    first_job = selected_job.iloc[0]


    col1, col2 = st.columns(2)


    with col1:

        st.markdown(
            f"""
            <div class="preference-card">

            <b>📂 Career Category</b>

            <h3>{category}</h3>

            <b>💼 Selected Position</b>

            <h3>{job_title}</h3>

            </div>
            """,
            unsafe_allow_html=True
        )


    with col2:

        st.markdown(
            f"""
            <div class="skill-box">

            <b>🛠️ Example Required Skills</b>

            <br><br>

            {first_job["job_skill_set"]}

            </div>
            """,
            unsafe_allow_html=True
        )


st.divider()


# =====================================================
# SKILL NORMALIZATION
# =====================================================

def clean_skill(skill):

    if skill is None:
        return ""

    skill = str(skill).lower().strip()

    skill = skill.replace("_", " ")

    skill = skill.replace("-", " ")

    skill = re.sub(
        r"\s+",
        " ",
        skill
    )

    return skill.strip()


# =====================================================
# EXTRACT REQUIRED SKILLS
# =====================================================

def extract_required_skills(skill_text):

    if pd.isna(skill_text):

        return set()


    text = str(skill_text).strip()


    if not text:

        return set()


    # -------------------------------------------------
    # Dataset list format
    # Example:
    # ['Python', 'SQL', 'Pandas']
    # -------------------------------------------------

    try:

        parsed = ast.literal_eval(text)


        if isinstance(parsed, (list, tuple, set)):

            skills = set()

            for skill in parsed:

                cleaned = clean_skill(skill)

                if cleaned:

                    skills.add(cleaned)

            return skills


    except (ValueError, SyntaxError):

        pass


    # -------------------------------------------------
    # Normal text format
    # -------------------------------------------------

    text = text.replace(
        ",",
        "|"
    )

    text = text.replace(
        ";",
        "|"
    )

    text = text.replace(
        "/",
        "|"
    )

    skills = text.split("|")


    result = set()


    for skill in skills:

        cleaned = clean_skill(skill)

        if cleaned:

            result.add(cleaned)


    return result


# =====================================================
# EXTRACT USER SKILLS
# =====================================================

def extract_user_skills(user_text):

    if not user_text:

        return set()


    if not user_text.strip():

        return set()


    skills = user_text.split(",")


    result = set()


    for skill in skills:

        cleaned = clean_skill(skill)

        if cleaned:

            result.add(cleaned)


    return result


# =====================================================
# POSITION SIMILARITY
# =====================================================

def calculate_position_similarity(
    user_position,
    job_position
):

    user_position = clean_skill(
        user_position
    )

    job_position = clean_skill(
        job_position
    )


    # -------------------------------------------------
    # Exact position
    # -------------------------------------------------

    if user_position == job_position:

        return 100.0


    user_words = set(
        user_position.split()
    )


    job_words = set(
        job_position.split()
    )


    if not user_words or not job_words:

        return 0.0


    common_words = (
        user_words
        .intersection(job_words)
    )


    if not common_words:

        return 0.0


    # -------------------------------------------------
    # Position similarity
    # -------------------------------------------------
    #
    # Use Jaccard-style word similarity.
    #
    # Example:
    #
    # Business Development Manager
    # Business Development Executive
    #
    # Common:
    # Business, Development
    #
    # -------------------------------------------------

    union_words = (
        user_words
        .union(job_words)
    )


    similarity = (
        len(common_words)
        /
        len(union_words)
    ) * 100


    return round(
        min(similarity, 100.0),
        2
    )


# =====================================================
# CORRECT SKILL MATCH SCORE
# =====================================================

def calculate_skill_score(
    user_skill_set,
    required_skill_set
):

    if not user_skill_set:

        return 0.0, 0.0, 0.0, set()


    if not required_skill_set:

        return 0.0, 0.0, 0.0, set()


    # -------------------------------------------------
    # DIRECT SKILL INTERSECTION
    # -------------------------------------------------

    matched_skills = (
        user_skill_set
        .intersection(
            required_skill_set
        )
    )


    matched_count = len(
        matched_skills
    )


    # -------------------------------------------------
    # PRECISION
    #
    # Of user's entered skills,
    # how many are relevant to this job?
    #
    # -------------------------------------------------

    precision = (
        matched_count
        /
        len(user_skill_set)
    )


    # -------------------------------------------------
    # RECALL
    #
    # Of job's required skills,
    # how many does the user have?
    #
    # -------------------------------------------------

    recall = (
        matched_count
        /
        len(required_skill_set)
    )


    # -------------------------------------------------
    # F1-STYLE BALANCED SCORE
    #
    # This prevents one side from artificially
    # increasing the percentage.
    #
    # -------------------------------------------------

    if (
        precision + recall
    ) == 0:

        f1_score = 0.0

    else:

        f1_score = (
            2
            * precision
            * recall
            /
            (precision + recall)
        )


    skill_percentage = (
        f1_score * 100
    )


    precision_percentage = (
        precision * 100
    )


    recall_percentage = (
        recall * 100
    )


    return (
        round(skill_percentage, 2),
        round(precision_percentage, 2),
        round(recall_percentage, 2),
        matched_skills
    )


# =====================================================
# JOB RECOMMENDATION FUNCTION
# =====================================================

def get_recommendations(
    category,
    job_title,
    user_skills
):

    # -------------------------------------------------
    # FILTER CATEGORY
    # -------------------------------------------------

    category_data = df[
        df["category"] == category
    ].copy()


    if category_data.empty:

        return category_data


    # -------------------------------------------------
    # USER SKILLS
    # -------------------------------------------------

    user_skill_set = (
        extract_user_skills(
            user_skills
        )
    )


    if not user_skill_set:

        return category_data.iloc[0:0]


    results = []


    # -------------------------------------------------
    # PROCESS EVERY JOB IN CATEGORY
    # -------------------------------------------------

    for index, row in category_data.iterrows():

        required_skills = (
            extract_required_skills(
                row["job_skill_set"]
            )
        )


        if not required_skills:

            continue


        # -------------------------------------------------
        # SKILL SCORE
        # -------------------------------------------------

        (
            skill_score,
            precision_percentage,
            recall_percentage,
            matched_skills
        ) = calculate_skill_score(
            user_skill_set,
            required_skills
        )


        # -------------------------------------------------
        # POSITION SCORE
        # -------------------------------------------------

        position_score = (
            calculate_position_similarity(
                job_title,
                row["job_title"]
            )
        )


        # -------------------------------------------------
        # FINAL SCORE
        #
        # Skills     = 85%
        # Position   = 15%
        #
        # -------------------------------------------------

        final_score = (
            skill_score * 0.85
            +
            position_score * 0.15
        )


        # -------------------------------------------------
        # SAFETY LIMIT
        # -------------------------------------------------

        final_score = max(
            0.0,
            min(
                final_score,
                100.0
            )
        )


        results.append(
            {
                "index": index,

                "match_percentage":
                    round(
                        final_score,
                        2
                    ),

                "matched_skills":
                    matched_skills,

                "skill_score":
                    skill_score,

                "precision_percentage":
                    precision_percentage,

                "recall_percentage":
                    recall_percentage,

                "position_relevance":
                    position_score,

                "required_skill_count":
                    len(required_skills),

                "matched_skill_count":
                    len(matched_skills)
            }
        )


    # -------------------------------------------------
    # NO RESULTS
    # -------------------------------------------------

    if not results:

        return category_data.iloc[0:0]


    result_df = pd.DataFrame(
        results
    )


    # -------------------------------------------------
    # MERGE ORIGINAL DATA
    # -------------------------------------------------

    recommendations = category_data.merge(
        result_df,
        left_index=True,
        right_on="index"
    )


    # -------------------------------------------------
    # SORT
    # -------------------------------------------------

    recommendations = (
        recommendations
        .sort_values(
            by=[
                "match_percentage",
                "skill_score",
                "position_relevance"
            ],
            ascending=False
        )
        .head(5)
    )


    return recommendations


# =====================================================
# AI / RESUME / LEARNING HELPERS
# =====================================================

def read_resume_text(uploaded_file):

    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    try:
        if file_name.endswith(".pdf"):
            if PdfReader is None:
                return ""
            reader = PdfReader(uploaded_file)
            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        if file_name.endswith(".docx"):
            if Document is None:
                return ""
            document = Document(uploaded_file)
            return "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

        if file_name.endswith(".txt"):
            return uploaded_file.getvalue().decode(
                "utf-8", errors="ignore"
            )

    except Exception:
        return ""

    return ""


def build_skill_vocabulary(dataframe):

    vocabulary = set()

    for value in dataframe["job_skill_set"].dropna():
        vocabulary.update(extract_required_skills(value))

    return vocabulary


def extract_resume_skills(resume_text, skill_vocabulary):

    if not resume_text:
        return set()

    normalized_text = clean_skill(resume_text)
    found = set()

    # Direct/NLP-friendly vocabulary matching.
    # Longer skills are checked first so multi-word skills are preserved.
    for skill in sorted(skill_vocabulary, key=len, reverse=True):
        if not skill:
            continue

        pattern = r"(?<![a-z0-9+#.])" + re.escape(skill) + r"(?![a-z0-9+#.])"

        if re.search(pattern, normalized_text):
            found.add(skill)

    return found


def youtube_search_url(skill):

    query = quote_plus(
        f"{skill} tutorial for beginners"
    )

    return (
        "https://www.youtube.com/results?search_query="
        + query
    )


@st.cache_resource(show_spinner=False)
def load_semantic_model():

    if SentenceTransformer is None:
        return None

    return SentenceTransformer(
        "all-MiniLM-L6-v2"
    )


def calculate_semantic_scores(
    user_profile,
    job_rows
):

    if SentenceTransformer is None or np is None:
        return [0.0] * len(job_rows), False

    try:
        model = load_semantic_model()

        if model is None:
            return [0.0] * len(job_rows), False

        job_texts = []

        for _, row in job_rows.iterrows():
            job_texts.append(
                f"Job title: {row['job_title']}. "
                f"Description: {row['job_description']}. "
                f"Required skills: {row['job_skill_set']}"
            )

        texts = [user_profile] + job_texts

        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        scores = np.dot(
            embeddings[1:],
            embeddings[0]
        ) * 100

        return [
            round(
                float(max(0.0, min(100.0, score))),
                2
            )
            for score in scores
        ], True

    except Exception:
        return [0.0] * len(job_rows), False


def get_enhanced_recommendations(
    category,
    job_title,
    combined_skills,
    use_semantic=True
):

    base = get_recommendations(
        category,
        job_title,
        ",".join(sorted(combined_skills))
    )

    if base.empty:
        return base, False

    if not use_semantic:
        base["semantic_score"] = 0.0
        base["ai_match_percentage"] = base[
            "match_percentage"
        ]
        return base, False

    user_profile = (
        f"Career category: {category}. "
        f"Preferred position: {job_title}. "
        f"Candidate skills: {', '.join(sorted(combined_skills))}"
    )

    semantic_scores, ai_available = calculate_semantic_scores(
        user_profile,
        base
    )

    base = base.copy()
    base["semantic_score"] = semantic_scores

    # Preserve the original recommendation score and add an
    # AI-assisted score rather than replacing the existing logic.
    base["ai_match_percentage"] = (
        base["match_percentage"] * 0.70
        + base["semantic_score"] * 0.20
        + base["position_relevance"] * 0.10
    ).clip(0, 100).round(2)

    base = base.sort_values(
        by=[
            "ai_match_percentage",
            "match_percentage",
            "skill_score"
        ],
        ascending=False
    ).head(5)

    return base, ai_available


# =====================================================
# OPTIONAL RESUME + AI INPUT
# =====================================================

st.markdown("## 🤖 AI-Assisted Matching")
st.caption(
    "Your original manual input and Top 5 recommendation flow remain unchanged. "
    "The following features add resume analysis, NLP matching and learning support."
)

with st.expander("📄 Resume Skill Extraction (Optional)", expanded=False):

    resume_file = st.file_uploader(
        "Upload your resume",
        type=["pdf", "docx", "txt"],
        help="PDF, DOCX or TXT resume"
    )

    resume_skills = set()
    resume_text = ""

    if resume_file is not None:

        resume_text = read_resume_text(resume_file)

        if resume_text.strip():

            skill_vocabulary = build_skill_vocabulary(df)

            resume_skills = extract_resume_skills(
                resume_text,
                skill_vocabulary
            )

            st.success(
                "✅ Resume text extracted successfully."
            )

            if resume_skills:

                st.markdown("**🤖 Skills identified from your resume:**")

                st.write(
                    ", ".join(
                        sorted(resume_skills)
                    )
                )

            else:

                st.info(
                    "No dataset-matching skills were identified. "
                    "You can still use manual skills below."
                )

        else:

            st.warning(
                "⚠️ Could not extract readable text from this resume."
            )

st.markdown("### 🧠 Enable NLP Semantic Matching")

use_semantic = st.checkbox(
    "Use AI/NLP semantic matching in addition to the existing skill matching",
    value=True
)

if use_semantic:
    st.caption(
        "NLP compares your candidate profile with job title, description and required skills. "
        "The original skill-match score is still retained."
    )


# =====================================================
# FIND JOBS
# =====================================================

st.subheader(
    "🎯 Find Your Jobs"
)


st.write(
    "Get the top 5 jobs that best match your "
    "category, position and skills."
)


st.info(
    f"🔎 **Category:** {category}  |  "
    f"**Position:** {job_title}"
)


if st.button(
    "🚀 FIND MY TOP 5 JOBS",
    use_container_width=True
):


    # -------------------------------------------------
    # CHECK SKILLS
    # -------------------------------------------------

    if not user_skills.strip():

        st.warning(
            "⚠️ Please enter your skills first."
        )


    else:

        manual_skill_set = extract_user_skills(
            user_skills
        )

        combined_skill_set = set(
            manual_skill_set
        )

        if "resume_skills" in locals():
            combined_skill_set.update(
                resume_skills
            )

        if not combined_skill_set:

            st.warning(
                "⚠️ No skills were identified. Please enter skills or upload a readable resume."
            )
            st.stop()

        recommendations, ai_available = get_enhanced_recommendations(
            category,
            job_title,
            combined_skill_set,
            use_semantic=use_semantic
        )

        if use_semantic and ai_available:
            st.success(
                "🧠 NLP semantic matching applied successfully. "
                "Your original recommendation score is also preserved below."
            )
        elif use_semantic:
            st.warning(
                "NLP model could not be loaded, so the original skill-based recommendation was used."
            )

        st.markdown("### 👤 Candidate Skill Profile")
        st.write(
            ", ".join(sorted(combined_skill_set))
        )


        # -------------------------------------------------
        # NO RESULTS
        # -------------------------------------------------

        if recommendations.empty:

            st.warning(
                "😔 No suitable jobs found."
            )

            st.info(
                "💡 Try entering more relevant skills."
            )


        else:

            st.success(
                "🎉 Top 5 matching jobs generated!"
            )


            st.subheader(
                "🏆 Your Best Job Recommendations"
            )


            st.caption(
                "The percentage represents the "
                "combined relevance of your skills "
                "and selected job position."
            )


            # =================================================
            # DISPLAY TOP 5
            # =================================================

            for number, (_, row) in enumerate(
                recommendations.iterrows(),
                start=1
            ):


                original_match_percentage = round(
                    float(
                        row["match_percentage"]
                    ),
                    1
                )

                ai_match_percentage = round(
                    float(
                        row.get(
                            "ai_match_percentage",
                            original_match_percentage
                        )
                    ),
                    1
                )

                match_percentage = ai_match_percentage


                matched_skills = (
                    row["matched_skills"]
                )


                # -------------------------------------------------
                # MATCHED SKILLS TEXT
                # -------------------------------------------------

                if isinstance(
                    matched_skills,
                    set
                ):

                    if matched_skills:

                        matched_skills_text = (
                            ", ".join(
                                sorted(
                                    matched_skills
                                )
                            )
                        )

                    else:

                        matched_skills_text = (
                            "No direct skill match"
                        )

                else:

                    matched_skills_text = str(
                        matched_skills
                    )


                # -------------------------------------------------
                # JOB CARD
                # -------------------------------------------------

                st.markdown(
                    f"""
                    <div class="job-card">

                    <div class="job-title">

                    {number}. 💼 {row["job_title"]}

                    </div>

                    <br>

                    <div class="match-score">

                    🎯 AI-Assisted Match: {match_percentage}%

                    <br>

                    📌 <b>Original Skill/Position Match:</b> {original_match_percentage}%

                    </div>

                    <br>

                    📂 <b>Category:</b>
                    {row["category"]}

                    <br><br>

                    🆔 <b>Job ID:</b>
                    {row["job_id"]}

                    <br><br>

                    ✅ <b>Matching Skills:</b>
                    {matched_skills_text}

                    <br><br>

                    🛠️ <b>Required Skills:</b>

                    <br><br>

                    {row["job_skill_set"]}

                    </div>
                    """,
                    unsafe_allow_html=True
                )


                # -------------------------------------------------
                # MATCH PROGRESS
                # -------------------------------------------------

                st.progress(
                    int(
                        min(
                            max(
                                match_percentage,
                                0
                            ),
                            100
                        )
                    )
                )


                # -------------------------------------------------
                # FULL DETAILS
                # -------------------------------------------------

                with st.expander(
                    f"📄 View Full Details - Job {number}"
                ):

                    st.markdown(
                        "### 📝 Job Description"
                    )

                    st.write(
                        row["job_description"]
                    )


                    st.markdown(
                        "### 🛠️ Required Skills"
                    )

                    st.write(
                        row["job_skill_set"]
                    )


                    st.markdown(
                        "### 🎯 Match Details"
                    )

                    st.write(
                        f"**Final Match:** "
                        f"{match_percentage}%"
                    )


                    st.write(
                        f"**Skill Match:** "
                        f"{row['skill_score']:.1f}%"
                    )

                    st.write(
                        f"**NLP Semantic Match:** "
                        f"{row.get('semantic_score', 0.0):.1f}%"
                    )

                    st.write(
                        f"**Position Match:** "
                        f"{row['position_relevance']:.1f}%"
                    )


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

                    # =================================================
                    # SKILL GAP ANALYSIS
                    # =================================================

                    required_skill_set = extract_required_skills(
                        row["job_skill_set"]
                    )

                    candidate_skill_set = set(
                        combined_skill_set
                    )

                    missing_skills = sorted(
                        required_skill_set.difference(
                            candidate_skill_set
                        )
                    )

                    st.markdown("### 🔍 Skill Gap Analysis")

                    if missing_skills:

                        st.write(
                            "These required skills are not currently present in your candidate profile:"
                        )

                        for missing_skill in missing_skills:

                            st.markdown(
                                f"❌ **{missing_skill.title()}**"
                            )

                    else:

                        st.success(
                            "🎉 No missing skills found for this recommendation."
                        )

                    # =================================================
                    # YOUTUBE LEARNING
                    # =================================================

                    if missing_skills:

                        st.markdown("### ▶️ Learn Missing Skills")

                        for missing_skill in missing_skills:

                            url = youtube_search_url(
                                missing_skill
                            )

                            st.markdown(
                                f"[▶ Learn {missing_skill.title()} on YouTube]({url})"
                            )


                    st.info(
                        "The final percentage is calculated "
                        "using balanced skill matching and "
                        "selected-position relevance."
                    )


# =====================================================
# FOOTER
# =====================================================

st.markdown("---")


st.markdown(
    """
    <div class="footer">

    <b>💼 CareerMatch AI</b>

    <br>

    Smart Job Recommendation System

    <br><br>

    Built with Python • Pandas • Streamlit

    </div>
    """,
    unsafe_allow_html=True
)
