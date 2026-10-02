
import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast
from urllib.parse import quote_plus

# Optional libraries used only when the related feature is used.
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

USER_FILE = "user_data.json"
DATA_FILE = "Cleaned_New_Data.csv"


# =====================================================
# USER ACCOUNT FUNCTIONS
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
        json.dump(user, file, indent=2)


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# =====================================================
# SESSION STATE
# =====================================================

defaults = {
    "logged_in": False,
    "page": "Home",
    "recommendations": pd.DataFrame(),
    "candidate_skills": set(),
    "resume_text": "",
    "resume_name": "",
    "search_source": "Manual Skills",
    "last_category": "",
    "last_position": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# LOGIN / REGISTER / FORGOT PASSWORD
# =====================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div class="login-box">
            <h1>💼 CareerMatch AI</h1>
            <p>AI-Assisted Smart Job Recommendation System</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    option = st.radio(
        "Choose an option",
        ["Login", "Register", "Forgot Password"],
        horizontal=True
    )

    if option == "Register":

        st.subheader("📝 Create Account")

        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button("Register", use_container_width=True):

            existing = load_user()

            if not email or not username or not password:
                st.warning("Please fill all fields.")

            elif password != confirm_password:
                st.error("Passwords do not match.")

            elif len(password) < 6:
                st.error("Password must contain at least 6 characters.")

            elif existing is not None:
                st.error("An account already exists. Please login.")

            else:
                save_user({
                    "email": email.strip(),
                    "username": username.strip(),
                    "password": hash_password(password)
                })
                st.success("Registration successful! Please login.")

    elif option == "Login":

        st.subheader("🔐 Login")

        login_id = st.text_input("Email or Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):

            user = load_user()

            if user is None:
                st.warning("No account found. Please register first.")

            elif (
                (login_id.strip() == user.get("email", "")) or
                (login_id.strip() == user.get("username", ""))
            ) and hash_password(password) == user.get("password", ""):

                st.session_state.logged_in = True
                st.session_state.page = "Home"
                st.rerun()

            else:
                st.error("Incorrect email/username or password.")

    else:

        st.subheader("🔑 Forgot Password")

        email = st.text_input("Registered Email")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        if st.button("Reset Password", use_container_width=True):

            user = load_user()

            if user is None:
                st.error("No registered account found.")

            elif email.strip() != user.get("email", ""):
                st.error("Email does not match the registered email.")

            elif len(new_password) < 6:
                st.error("Password must contain at least 6 characters.")

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            else:
                user["password"] = hash_password(new_password)
                save_user(user)
                st.success("Password reset successfully. Please login.")

    st.stop()


# =====================================================
# DATA LOADING
# =====================================================

@st.cache_data
def load_dataset():
    return pd.read_csv(DATA_FILE)


try:
    df = load_dataset()
except Exception as error:
    st.error(f"Unable to load {DATA_FILE}.")
    st.exception(error)
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
    df[column] = df[column].fillna("").astype(str).str.strip()


# =====================================================
# STYLING
# =====================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }

    .hero {
        padding: 34px;
        border-radius: 22px;
        border: 1px solid rgba(128,128,128,.25);
        margin-bottom: 22px;
        text-align: center;
        background: linear-gradient(
            135deg,
            rgba(128,128,128,.10),
            rgba(128,128,128,.03)
        );
    }

    .hero h1 {
        font-size: 42px;
        margin-bottom: 8px;
    }

    .hero p {
        font-size: 18px;
        margin: 4px;
    }

    .section-card {
        padding: 22px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,.25);
        background: rgba(128,128,128,.035);
        margin-bottom: 18px;
    }

    .job-card {
        padding: 22px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,.25);
        margin-bottom: 14px;
        background: rgba(128,128,128,.025);
    }

    .job-title {
        font-size: 24px;
        font-weight: 700;
    }

    .score {
        font-size: 25px;
        font-weight: 700;
    }

    .skill-tag {
        display: inline-block;
        padding: 6px 10px;
        margin: 4px;
        border-radius: 14px;
        border: 1px solid rgba(128,128,128,.30);
        font-size: 14px;
    }

    .missing-tag {
        display: inline-block;
        padding: 7px 11px;
        margin: 4px;
        border-radius: 14px;
        border: 1px solid rgba(220,80,80,.35);
        font-size: 14px;
    }

    .footer {
        text-align: center;
        padding: 25px;
        opacity: .7;
    }

    .stButton > button {
        border-radius: 11px;
        min-height: 45px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# BASIC HELPERS
# =====================================================

def clean_skill(skill):
    if skill is None:
        return ""

    skill = str(skill).lower().strip()
    skill = skill.replace("_", " ")
    skill = skill.replace("-", " ")
    skill = re.sub(r"\s+", " ", skill)
    return skill.strip()


def display_skill(skill):
    return str(skill).strip().title()


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

    except (ValueError, SyntaxError):
        pass

    text = text.replace(",", "|")
    text = text.replace(";", "|")
    text = text.replace("/", "|")

    return {
        clean_skill(skill)
        for skill in text.split("|")
        if clean_skill(skill)
    }


def extract_user_skills(user_text):
    if not user_text or not str(user_text).strip():
        return set()

    return {
        clean_skill(skill)
        for skill in str(user_text).split(",")
        if clean_skill(skill)
    }


# =====================================================
# DATASET SKILL VOCABULARY
# =====================================================

@st.cache_data
def build_skill_vocabulary(dataframe):
    vocabulary = set()

    for value in dataframe["job_skill_set"]:
        vocabulary.update(extract_required_skills(value))

    return sorted(vocabulary)


SKILL_VOCABULARY = build_skill_vocabulary(df)


# Common aliases help resume extraction recognize
# equivalent wording without changing the dataset.
SKILL_ALIASES = {
    "python programming": "python",
    "python programming language": "python",
    "sql programming": "sql",
    "structured query language": "sql",
    "machine learning": "machine learning",
    "ml": "machine learning",
    "artificial intelligence": "artificial intelligence",
    "ai": "artificial intelligence",
    "data analytics": "data analysis",
    "data analyst": "data analysis",
    "power bi": "power bi",
    "microsoft power bi": "power bi",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "spreadsheet": "excel",
}


def extract_skills_from_text(text):
    """
    Resume skill extraction:
    1. Looks for known skills from the project dataset.
    2. Uses common aliases for equivalent resume wording.
    """
    if not text:
        return set()

    normalized_text = clean_skill(text)
    found = set()

    # Longest phrases first.
    vocabulary = sorted(
        SKILL_VOCABULARY,
        key=len,
        reverse=True
    )

    for skill in vocabulary:
        if len(skill) < 2:
            continue

        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"

        if re.search(pattern, normalized_text):
            found.add(skill)

    for alias, canonical in SKILL_ALIASES.items():

        if canonical not in SKILL_VOCABULARY:
            continue

        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"

        if re.search(pattern, normalized_text):
            found.add(canonical)

    return found


# =====================================================
# RESUME TEXT EXTRACTION
# =====================================================

def extract_resume_text(uploaded_file):

    if uploaded_file is None:
        return ""

    file_name = uploaded_file.name.lower()

    try:

        if file_name.endswith(".pdf"):

            if PdfReader is None:
                raise RuntimeError(
                    "pypdf is not installed. Run: pip install pypdf"
                )

            reader = PdfReader(uploaded_file)

            pages = []

            for page in reader.pages:
                pages.append(page.extract_text() or "")

            return "\n".join(pages)

        if file_name.endswith(".docx"):

            if Document is None:
                raise RuntimeError(
                    "python-docx is not installed. Run: pip install python-docx"
                )

            document = Document(uploaded_file)

            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            return "\n".join(paragraphs)

        if file_name.endswith(".txt"):
            return uploaded_file.getvalue().decode(
                "utf-8",
                errors="ignore"
            )

        raise ValueError(
            "Unsupported file type. Please upload PDF, DOCX or TXT."
        )

    except Exception as error:
        st.error(f"Could not read the resume: {error}")
        return ""


# =====================================================
# POSITION SIMILARITY
# =====================================================

def calculate_position_similarity(user_position, job_position):

    user_position = clean_skill(user_position)
    job_position = clean_skill(job_position)

    if not user_position or not job_position:
        return 0.0

    if user_position == job_position:
        return 100.0

    user_words = set(user_position.split())
    job_words = set(job_position.split())

    common_words = user_words.intersection(job_words)
    union_words = user_words.union(job_words)

    if not common_words or not union_words:
        return 0.0

    return round(
        (len(common_words) / len(union_words)) * 100,
        2
    )


# =====================================================
# EXACT SKILL SCORE
# =====================================================

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


# =====================================================
# NLP MODEL
# =====================================================

@st.cache_resource
def load_nlp_model():

    if SentenceTransformer is None:
        raise RuntimeError(
            "sentence-transformers is not installed. "
            "Run: pip install sentence-transformers"
        )

    return SentenceTransformer(
        "all-MiniLM-L6-v2",
        device="cpu"
    )


def calculate_semantic_scores(
    candidate_profile,
    job_texts
):

    if np is None:
        raise RuntimeError(
            "numpy is required for NLP semantic matching."
        )

    model = load_nlp_model()

    texts = [candidate_profile] + job_texts

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    user_embedding = embeddings[0]
    job_embeddings = embeddings[1:]

    scores = np.dot(
        job_embeddings,
        user_embedding
    ) * 100

    return [
        round(float(max(0.0, min(score, 100.0))), 2)
        for score in scores
    ]


# =====================================================
# RECOMMENDATION ENGINE
# =====================================================

def get_recommendations(
    category,
    job_title,
    user_skill_set,
    source_text=""
):

    category_data = df[
        df["category"] == category
    ].copy()

    if category_data.empty or not user_skill_set:
        return category_data.iloc[0:0]

    results = []

    # First pass: exact skill + position relevance.
    # This keeps the system fast even for large datasets.
    for index, row in category_data.iterrows():

        required_skills = extract_required_skills(
            row["job_skill_set"]
        )

        if not required_skills:
            continue

        (
            skill_score,
            precision_percentage,
            recall_percentage,
            matched_skills
        ) = calculate_skill_score(
            user_skill_set,
            required_skills
        )

        position_score = calculate_position_similarity(
            job_title,
            row["job_title"]
        )

        preliminary_score = (
            skill_score * 0.85
            + position_score * 0.15
        )

        results.append({
            "index": index,
            "skill_score": skill_score,
            "precision_percentage": precision_percentage,
            "recall_percentage": recall_percentage,
            "position_relevance": position_score,
            "matched_skills": matched_skills,
            "required_skill_count": len(required_skills),
            "matched_skill_count": len(matched_skills),
            "preliminary_score": round(preliminary_score, 2)
        })

    if not results:
        return category_data.iloc[0:0]

    result_df = pd.DataFrame(results)

    # Use NLP on the strongest preliminary candidates.
    semantic_candidates = (
        result_df
        .sort_values(
            by=[
                "preliminary_score",
                "skill_score",
                "position_relevance"
            ],
            ascending=False
        )
        .head(100)
        .copy()
    )

    candidate_rows = category_data.loc[
        semantic_candidates["index"]
    ]

    profile_parts = [
        f"Career category: {category}",
        f"Preferred job position: {job_title}",
        "Candidate skills: " + ", ".join(
            sorted(user_skill_set)
        )
    ]

    if source_text:
        # Only a compact portion is used to keep semantic input focused.
        profile_parts.append(
            "Resume profile: " + source_text[:4000]
        )

    candidate_profile = ". ".join(profile_parts)

    job_texts = []

    for _, row in candidate_rows.iterrows():
        job_texts.append(
            f"Job title: {row['job_title']}. "
            f"Job description: {row['job_description'][:2500]}. "
            f"Required skills: {row['job_skill_set']}."
        )

    try:
        semantic_scores = calculate_semantic_scores(
            candidate_profile,
            job_texts
        )
    except Exception as error:
        # If model is unavailable, the exact existing matching
        # remains usable and the user gets a clear message.
        st.warning(
            "NLP model could not be loaded. "
            "Showing skill-based recommendations instead."
        )
        semantic_scores = [
            0.0
            for _ in range(len(candidate_rows))
        ]

    semantic_map = dict(
        zip(
            semantic_candidates["index"].tolist(),
            semantic_scores
        )
    )

    result_df["semantic_score"] = result_df["index"].map(
        semantic_map
    ).fillna(0.0)

    # AI-assisted score:
    # 65% direct skill match
    # 25% NLP semantic similarity
    # 10% position relevance
    result_df["match_percentage"] = (
        result_df["skill_score"] * 0.65
        + result_df["semantic_score"] * 0.25
        + result_df["position_relevance"] * 0.10
    )

    result_df["match_percentage"] = (
        result_df["match_percentage"]
        .clip(0, 100)
        .round(2)
    )

    recommendations = category_data.merge(
        result_df,
        left_index=True,
        right_on="index"
    )

    recommendations = (
        recommendations
        .sort_values(
            by=[
                "match_percentage",
                "skill_score",
                "semantic_score",
                "position_relevance"
            ],
            ascending=False
        )
        .head(5)
        .copy()
    )

    # Calculate missing skills for every recommended job.
    recommendations["missing_skills"] = recommendations.apply(
        lambda row: (
            extract_required_skills(row["job_skill_set"])
            - set(user_skill_set)
        ),
        axis=1
    )

    return recommendations


# =====================================================
# YOUTUBE LEARNING LINK
# =====================================================

def youtube_search_url(skill):

    query = f"{display_skill(skill)} tutorial for beginners"
    return (
        "https://www.youtube.com/results?search_query="
        + quote_plus(query)
    )


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================

st.sidebar.title("💼 CareerMatch AI")
st.sidebar.caption("AI-Assisted Smart Job Recommendation System")

page_options = [
    "🏠 Home",
    "📝 Manual Skill Search",
    "📄 Resume Matching",
    "🏆 Job Recommendations",
    "🔍 Skill Gap & Learning"
]

# Keep navigation robust on Streamlit Cloud.
# The previous version calculated the radio index from session state,
# which could raise ValueError when an old/invalid page value existed.
if "page" not in st.session_state or st.session_state.page not in page_options:
    st.session_state.page = page_options[0]

current_page_label = st.sidebar.radio(
    "Navigate",
    page_options,
    index=page_options.index(st.session_state.page),
    key="main_navigation"
)

st.session_state.page = current_page_label

st.sidebar.divider()

if st.sidebar.button("🗑️ Clear Current Results", use_container_width=True):
    st.session_state.recommendations = pd.DataFrame()
    st.session_state.candidate_skills = set()
    st.session_state.resume_text = ""
    st.session_state.resume_name = ""
    st.session_state.search_source = "Manual Skills"
    st.rerun()

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.recommendations = pd.DataFrame()
    st.rerun()


# =====================================================
# HOME
# =====================================================

if current_page_label == "🏠 Home":

    st.markdown(
        """
        <div class="hero">
            <h1>💼 CareerMatch AI</h1>
            <p><b>AI-Assisted Smart Job Recommendation System</b></p>
            <p>Find suitable jobs based on your skills, resume and career preference.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("🎯 What does CareerMatch AI do?")

    st.write(
        "CareerMatch AI compares a candidate's skills and career "
        "preference with job requirements and recommends the top "
        "5 relevant jobs. It also uses NLP semantic matching, "
        "resume skill extraction and skill gap analysis to make "
        "the recommendation more useful."
    )

    st.divider()

    st.subheader("🚀 How to use the project")

    steps = [
        ("1️⃣", "Choose Input", "Enter your skills manually or upload your resume."),
        ("2️⃣", "Set Career Preference", "Select your category and preferred position."),
        ("3️⃣", "AI Job Matching", "The system compares your profile with job information."),
        ("4️⃣", "Top 5 Jobs", "View recommended jobs with match percentages."),
        ("5️⃣", "Skill Gap", "See skills required for a selected job that you do not have."),
        ("6️⃣", "Learn", "Open YouTube learning searches for missing skills.")
    ]

    cols = st.columns(3)

    for index, (icon, title, description) in enumerate(steps):
        with cols[index % 3]:
            st.markdown(
                f"""
                <div class="section-card">
                    <h3>{icon} {title}</h3>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

    st.subheader("🧠 Main Technology")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Job Recommendation", "Top 5")
    col2.metric("NLP", "Semantic Matching")
    col3.metric("Resume", "Skill Extraction")
    col4.metric("Learning", "YouTube Links")


# =====================================================
# MANUAL SKILL SEARCH
# =====================================================

elif current_page_label == "📝 Manual Skill Search":

    st.title("📝 Manual Skill Search")

    st.write(
        "Enter your skills and career preference. "
        "The system will generate the top 5 job recommendations."
    )

    st.divider()

    categories = sorted([
        value for value in df["category"].unique()
        if value
    ])

    if not categories:
        st.error("No categories found in the dataset.")
        st.stop()

    category = st.selectbox(
        "1️⃣ Select Career Category",
        categories
    )

    category_data = df[
        df["category"] == category
    ]

    positions = sorted([
        value for value in category_data["job_title"].unique()
        if value
    ])

    if not positions:
        st.error("No job positions found for this category.")
        st.stop()

    position = st.selectbox(
        "2️⃣ Select Job Position",
        positions
    )

    skills_text = st.text_area(
        "3️⃣ Enter Your Skills",
        placeholder=(
            "Example: Python, SQL, Pandas, Excel, Machine Learning"
        ),
        height=110
    )

    st.caption(
        "Enter multiple skills separated by commas."
    )

    if st.button(
        "🚀 Find My Top 5 Jobs",
        use_container_width=True
    ):

        user_skill_set = extract_user_skills(skills_text)

        if not user_skill_set:
            st.warning("Please enter at least one skill.")

        else:

            with st.spinner("Analyzing your skills with NLP..."):

                recommendations = get_recommendations(
                    category,
                    position,
                    user_skill_set
                )

            if recommendations.empty:
                st.warning("No suitable jobs could be generated.")

            else:
                st.session_state.recommendations = recommendations
                st.session_state.candidate_skills = user_skill_set
                st.session_state.resume_text = ""
                st.session_state.resume_name = ""
                st.session_state.search_source = "Manual Skills"
                st.session_state.last_category = category
                st.session_state.last_position = position

                st.success(
                    "Top 5 recommendations generated successfully."
                )

                st.info(
                    "Open **🏆 Job Recommendations** from the sidebar "
                    "to view the results."
                )


# =====================================================
# RESUME MATCHING
# =====================================================

elif current_page_label == "📄 Resume Matching":

    st.title("📄 Resume-Based Job Matching")

    st.write(
        "Upload your resume. CareerMatch AI will extract skills "
        "from the document and use them for job recommendation."
    )

    st.divider()

    categories = sorted([
        value for value in df["category"].unique()
        if value
    ])

    category = st.selectbox(
        "1️⃣ Select Career Category",
        categories,
        key="resume_category"
    )

    category_data = df[
        df["category"] == category
    ]

    positions = sorted([
        value for value in category_data["job_title"].unique()
        if value
    ])

    position = st.selectbox(
        "2️⃣ Select Preferred Job Position",
        positions,
        key="resume_position"
    )

    uploaded_file = st.file_uploader(
        "3️⃣ Upload Resume",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, DOCX and TXT."
    )

    manual_extra_skills = st.text_area(
        "Optional: Add extra skills manually",
        placeholder="Example: Power BI, Tableau",
        height=90
    )

    if st.button(
        "🤖 Analyze Resume & Find Jobs",
        use_container_width=True
    ):

        if uploaded_file is None:
            st.warning("Please upload your resume first.")

        else:

            with st.spinner("Reading and analyzing your resume..."):

                resume_text = extract_resume_text(
                    uploaded_file
                )

                resume_skills = extract_skills_from_text(
                    resume_text
                )

                manual_skills = extract_user_skills(
                    manual_extra_skills
                )

                combined_skills = (
                    resume_skills
                    .union(manual_skills)
                )

            if not resume_text.strip():

                st.error(
                    "No readable text was found in the uploaded resume."
                )

            elif not combined_skills:

                st.warning(
                    "No project-dataset skills were identified. "
                    "Try adding skills manually."
                )

            else:

                with st.spinner(
                    "Running NLP semantic job matching..."
                ):

                    recommendations = get_recommendations(
                        category,
                        position,
                        combined_skills,
                        source_text=resume_text
                    )

                st.session_state.recommendations = recommendations
                st.session_state.candidate_skills = combined_skills
                st.session_state.resume_text = resume_text
                st.session_state.resume_name = uploaded_file.name
                st.session_state.search_source = "Resume"
                st.session_state.last_category = category
                st.session_state.last_position = position

                st.success("Resume analysis completed.")

                st.subheader("🤖 Skills Identified from Resume")

                skill_text = ", ".join(
                    display_skill(skill)
                    for skill in sorted(combined_skills)
                )

                st.write(skill_text)

                st.info(
                    "These identified skills were used as the candidate "
                    "skill profile for job matching."
                )

                if not recommendations.empty:
                    st.success(
                        "Top 5 recommendations are ready. "
                        "Open **🏆 Job Recommendations**."
                    )


# =====================================================
# JOB RECOMMENDATIONS
# =====================================================

elif current_page_label == "🏆 Job Recommendations":

    st.title("🏆 Job Recommendations")

    recommendations = st.session_state.recommendations
    candidate_skills = st.session_state.candidate_skills

    if recommendations is None or recommendations.empty:

        st.info(
            "No recommendations available yet. "
            "Use **Manual Skill Search** or **Resume Matching** first."
        )

    else:

        st.write(
            f"**Source:** {st.session_state.search_source}  |  "
            f"**Category:** {st.session_state.last_category}  |  "
            f"**Position:** {st.session_state.last_position}"
        )

        st.divider()

        st.subheader("Top 5 Recommended Jobs")

        for number, (_, row) in enumerate(
            recommendations.iterrows(),
            start=1
        ):

            match_percentage = float(
                row["match_percentage"]
            )

            matched_skills = row["matched_skills"]

            if not isinstance(matched_skills, set):
                matched_skills = set()

            matched_text = ", ".join(
                display_skill(skill)
                for skill in sorted(matched_skills)
            ) or "No direct skill match"

            st.markdown(
                f"""
                <div class="job-card">
                    <div class="job-title">
                        {number}. 💼 {row["job_title"]}
                    </div>
                    <br>
                    <div class="score">
                        🎯 Match: {match_percentage:.1f}%
                    </div>
                    <br>
                    📂 <b>Category:</b> {row["category"]}
                    <br><br>
                    🆔 <b>Job ID:</b> {row["job_id"]}
                    <br><br>
                    ✅ <b>Matching Skills:</b> {matched_text}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.progress(
                int(max(0, min(100, round(match_percentage))))
            )

            with st.expander(
                f"📄 View Details — {row['job_title']}"
            ):

                st.markdown("### 📝 Job Description")
                st.write(row["job_description"])

                st.markdown("### 🛠️ Required Skills")
                st.write(row["job_skill_set"])

                st.markdown("### 📊 Match Score Breakdown")

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Overall Match",
                    f"{match_percentage:.1f}%"
                )

                c2.metric(
                    "Skill Match",
                    f"{float(row['skill_score']):.1f}%"
                )

                c3.metric(
                    "NLP Match",
                    f"{float(row['semantic_score']):.1f}%"
                )

                c4.metric(
                    "Position Match",
                    f"{float(row['position_relevance']):.1f}%"
                )

                st.write(
                    f"**Matched skills:** "
                    f"{int(row['matched_skill_count'])} / "
                    f"{int(row['required_skill_count'])}"
                )


# =====================================================
# SKILL GAP + LEARNING
# =====================================================

elif current_page_label == "🔍 Skill Gap & Learning":

    st.title("🔍 Skill Gap Analysis")

    recommendations = st.session_state.recommendations
    candidate_skills = st.session_state.candidate_skills

    if recommendations is None or recommendations.empty:

        st.info(
            "Generate recommendations first using Manual Skill Search "
            "or Resume Matching."
        )

    else:

        job_names = recommendations["job_title"].tolist()

        selected_job_name = st.selectbox(
            "Select a recommended job",
            job_names
        )

        selected_rows = recommendations[
            recommendations["job_title"] == selected_job_name
        ]

        if selected_rows.empty:
            st.warning("Selected job details are unavailable.")
            st.stop()

        row = selected_rows.iloc[0]

        required_skills = extract_required_skills(
            row["job_skill_set"]
        )

        matched_skills = set(candidate_skills).intersection(
            required_skills
        )

        missing_skills = required_skills.difference(
            set(candidate_skills)
        )

        st.divider()

        st.subheader("💼 Selected Job")

        st.write(
            f"**{row['job_title']}** — "
            f"Match: **{float(row['match_percentage']):.1f}%**"
        )

        st.subheader("✅ Skills You Have")

        if matched_skills:
            st.markdown(
                " ".join(
                    f'<span class="skill-tag">✓ {display_skill(skill)}</span>'
                    for skill in sorted(matched_skills)
                ),
                unsafe_allow_html=True
            )
        else:
            st.info("No direct required skills were matched.")

        st.subheader("❌ Skills You Need to Develop")

        if missing_skills:

            st.markdown(
                " ".join(
                    f'<span class="missing-tag">+ {display_skill(skill)}</span>'
                    for skill in sorted(missing_skills)
                ),
                unsafe_allow_html=True
            )

            st.divider()

            st.subheader("📚 Learning Recommendations")

            st.write(
                "Use the links below to search YouTube for tutorials "
                "related to your missing skills."
            )

            for skill in sorted(missing_skills):

                url = youtube_search_url(skill)

                st.markdown(
                    f"**{display_skill(skill)}**  \n"
                    f"[▶️ Learn {display_skill(skill)} on YouTube]({url})"
                )

        else:

            st.success(
                "🎉 No missing skills found for this selected job "
                "based on the current skill profile."
            )


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        <b>💼 CareerMatch AI</b><br>
        AI-Assisted Smart Job Recommendation System<br><br>
        Python • Pandas • Streamlit • NLP • Sentence Transformers
    </div>
    """,
    unsafe_allow_html=True
)
