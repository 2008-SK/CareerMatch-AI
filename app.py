import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast
from io import BytesIO
from urllib.parse import quote_plus

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

# Optional library for Course Certificates
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


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
    with open(USER_FILE, "w") as file:
        json.dump(user, file)


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
                    "password": hash_password(password)
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
                st.session_state.logged_in = True
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
# LOGOUT
# =====================================================

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
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
    <h1>💼 CareerMatch AI</h1>
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


def parse_resume(uploaded_file):
    if uploaded_file is None:
        return ""

    file_type = uploaded_file.name.rsplit(".", 1)[-1].lower()
    extracted_text = ""

    try:
        if file_type == "pdf":
            if pdfplumber is None:
                return ""

            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"

        elif file_type == "docx":
            if docx is None:
                return ""

            document = docx.Document(
                BytesIO(uploaded_file.read())
            )

            for paragraph in document.paragraphs:
                extracted_text += paragraph.text + "\n"

        elif file_type == "txt":
            extracted_text = uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )

    except Exception as exc:
        st.error(f"Unable to read resume: {exc}")
        return ""

    return extracted_text


def extract_skills_from_resume(raw_text, dataset_skills):
    if not raw_text:
        return set()

    text = raw_text.lower()
    found = set()

    # Longest skills first reduces partial-match issues.
    for skill in sorted(
        dataset_skills,
        key=len,
        reverse=True
    ):
        if not skill:
            continue

        # Flexible spaces between words.
        pattern = r"(?<!\w)" + re.escape(skill).replace(
            r"\ ",
            r"\s+"
        ) + r"(?!\w)"

        if re.search(pattern, text, flags=re.IGNORECASE):
            found.add(skill)

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


def youtube_search_url(skill):
    query = quote_plus(
        f"{skill} tutorial for beginners"
    )
    return (
        "https://www.youtube.com/results"
        f"?search_query={query}"
    )


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
    help="Supported formats: PDF, DOCX and TXT"
)

all_dataset_skills = set()

for skill_text in df["job_skill_set"].dropna():
    all_dataset_skills.update(
        extract_required_skills(skill_text)
    )

if resume_file is not None:

    resume_text = parse_resume(resume_file)

    if resume_text:
        resume_skills = extract_skills_from_resume(
            resume_text,
            all_dataset_skills
        )

        st.session_state.resume_text = resume_text
        st.session_state.resume_skills = resume_skills

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
            "Could not extract text from this resume."
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
# YOUTUBE LEARNING — SEPARATE SECTION
# =====================================================

if (
    recommendations is not None
    and not recommendations.empty
):

    st.divider()
    st.subheader("▶️ Learning Recommendations")

    st.write(
        "Use these YouTube search links to learn the skills "
        "identified in your skill gap."
    )

    learning_missing = sorted(
        selected_row["missing_skills"]
    )

    if learning_missing:

        for skill in learning_missing[:8]:
            url = youtube_search_url(skill)

            st.markdown(
                f"""
**{skill.title()}**

[▶️ Learn {skill.title()} on YouTube]({url})
"""
            )

    else:
        st.success(
            "No missing skills found. Keep improving your current skills!"
        )


# =====================================================
# ACTUAL COURSE LEARNING & CERTIFICATE MODULE
# =====================================================

# These are self-contained CareerMatch AI learning courses. They are
# available independently of Skill Gap, so a user can choose a course,
# study the lessons, complete the assessment and earn a certificate.
COURSES = {
    "python": {
        "title": "Python for Beginners",
        "level": "Beginner",
        "duration": "4-5 hours",
        "description": "Learn Python from the basics to a small practical project.",
        "modules": [
            ("Python Basics", "Learn what Python is, how a Python program is structured, variables, comments, input and output.", "Example: name = 'Asha' stores text in a variable. Use print(name) to display it.", "Create a program that asks for a user's name and age and prints a welcome message."),
            ("Data Types & Operators", "Learn strings, integers, floats, booleans and common arithmetic, comparison and logical operators.", "Example: total = 10 + 5 and is_valid = total > 10.", "Write a program that accepts two numbers and displays their sum, difference and product."),
            ("Conditions & Loops", "Learn if, elif, else, for loops, while loops, range and basic loop control.", "Example: for number in range(1, 6): print(number) prints 1 to 5.", "Print all even numbers from 1 to 20 using a loop."),
            ("Functions & Collections", "Learn functions, parameters, return values and the use of lists, tuples, sets and dictionaries.", "Example: def add(a, b): return a + b. A dictionary stores data as key-value pairs.", "Create a function that receives a list of marks and returns the highest mark."),
            ("Files, Errors & Practical Use", "Learn basic file handling, exceptions and how Python is used in data and automation tasks.", "Example: try/except can handle an invalid numeric input without crashing the program.", "Build a small student record program that saves a few records to a text file."),
            ("Mini Project", "Combine variables, conditions, loops, functions and collections in one small application.", "Project idea: Student Performance Analyzer using marks, average, grade and result.", "Create the Student Performance Analyzer and display total, average, grade and pass/fail status.")
        ],
        "quiz": [
            ("Which keyword defines a function in Python?", ["func", "def", "function", "method"], "B"),
            ("Which Python collection stores key-value pairs?", ["List", "Tuple", "Dictionary", "Set"], "C"),
            ("What does range(1, 4) produce when used in a for loop?", ["1, 2, 3", "1, 2, 3, 4", "0, 1, 2, 3", "Only 4"], "A"),
            ("Which block is used to handle an exception?", ["try/except", "if/else", "for/in", "def/return"], "A"),
            ("Which data type represents True or False?", ["String", "Boolean", "Float", "List"], "B")
        ]
    },
    "sql": {
        "title": "SQL for Data Analysis",
        "level": "Beginner",
        "duration": "3-4 hours",
        "description": "Learn how to retrieve, filter, summarize and combine data using SQL.",
        "modules": [
            ("Database & Table Basics", "Understand databases, tables, rows, columns, primary keys and why structured data is stored in tables.", "Example table: Students(id, name, marks). The id can uniquely identify each student.", "Design a simple table structure for employees with id, name, department and salary."),
            ("SELECT & WHERE", "Learn SELECT, FROM, WHERE and comparison operators to retrieve required records.", "Example: SELECT name FROM students WHERE marks >= 60;", "Write a query to display employees whose salary is greater than 50000."),
            ("Sorting & Filtering", "Learn ORDER BY, ASC, DESC, AND, OR, IN and BETWEEN.", "Example: ORDER BY salary DESC sorts employees from highest salary to lowest.", "Write a query to show employees from IT or HR sorted by salary."),
            ("Aggregate Functions", "Learn COUNT, SUM, AVG, MIN and MAX for basic data analysis.", "Example: SELECT AVG(salary) FROM employees; calculates average salary.", "Find the number of employees and the average salary in a department."),
            ("GROUP BY & JOIN", "Learn grouping and the basic idea of combining related tables with JOIN.", "Example: GROUP BY department calculates summaries for each department.", "Write a query that shows department-wise employee count."),
            ("Mini Project", "Use SQL to analyze a small employee or sales dataset using filters, summaries and sorting.", "Project idea: Employee Salary Analysis.", "Prepare queries for highest salary, average salary, department count and employees above average salary.")
        ],
        "quiz": [
            ("Which SQL command retrieves data?", ["INSERT", "SELECT", "UPDATE", "DELETE"], "B"),
            ("Which clause filters rows?", ["WHERE", "ORDER BY", "GROUP BY", "JOIN"], "A"),
            ("Which function calculates an average?", ["COUNT", "SUM", "AVG", "MAX"], "C"),
            ("Which clause sorts query results?", ["WHERE", "ORDER BY", "VALUES", "HAVING"], "B"),
            ("Which operation combines related rows from tables?", ["JOIN", "SORT", "PRINT", "LOOP"], "A")
        ]
    },
    "pandas": {
        "title": "Pandas & Data Analysis",
        "level": "Beginner",
        "duration": "4 hours",
        "description": "Learn practical data loading, cleaning, filtering and analysis with Pandas.",
        "modules": [
            ("Series & DataFrame", "Understand the two main Pandas structures and how tabular data is represented.", "Example: pd.DataFrame({'Name':['A','B'], 'Marks':[80,90]}) creates a table.", "Create a DataFrame containing five students and their marks."),
            ("Load & Inspect Data", "Learn read_csv, head, tail, info, shape and describe for understanding a dataset.", "Example: pd.read_csv('data.csv') loads a CSV file.", "Load a CSV and inspect its rows, columns, data types and summary statistics."),
            ("Cleaning Data", "Learn how to handle missing values, duplicates and inconsistent text.", "Example: df.drop_duplicates() removes duplicate rows.", "Find missing values and remove duplicate records from a sample dataset."),
            ("Filtering & Selecting", "Learn column selection, loc, conditions and sorting.", "Example: df[df['Marks'] >= 60] selects students with marks of at least 60.", "Filter a dataset to find records meeting two conditions."),
            ("Grouping & Analysis", "Learn groupby, aggregation and simple descriptive analysis.", "Example: df.groupby('Department')['Salary'].mean() gives average salary by department.", "Calculate group-wise count and average for a categorical column."),
            ("Mini Project", "Combine loading, cleaning, filtering and analysis into a small data-analysis workflow.", "Project idea: Student Performance Data Analyzer.", "Prepare a short analysis showing average, highest, lowest and category-wise performance.")
        ],
        "quiz": [
            ("Which Pandas object is two-dimensional?", ["Series", "DataFrame", "Index", "Array"], "B"),
            ("Which function reads a CSV file?", ["read_csv", "open_csv", "load_csv", "get_csv"], "A"),
            ("Which method removes duplicate rows?", ["dropna", "fillna", "drop_duplicates", "remove"], "C"),
            ("Which method gives descriptive statistics?", ["describe", "summary", "stats_only", "details"], "A"),
            ("Which operation is useful for category-wise aggregation?", ["groupby", "splitby", "categoryloop", "aggregateby"], "A")
        ]
    },
    "machine_learning": {
        "title": "Machine Learning Fundamentals",
        "level": "Beginner",
        "duration": "5 hours",
        "description": "Understand the complete beginner-level machine learning workflow from data to evaluation.",
        "modules": [
            ("What is Machine Learning?", "Understand machine learning, features, targets, training data and common applications.", "Example: predicting whether an email is spam is a classification problem.", "Identify the feature and target in a simple house-price prediction example."),
            ("Data Preparation", "Learn missing-value handling, categorical encoding, scaling and train-test splitting at a basic level.", "Example: a dataset is commonly split into training and testing portions before evaluation.", "List three preprocessing steps that may be required before model training."),
            ("Supervised Learning", "Understand classification and regression and learn examples of common algorithms.", "Example: predicting salary is regression; predicting pass/fail is classification.", "Classify five example problems as classification or regression."),
            ("Model Training", "Understand fitting a model to training data and why training data must represent the problem.", "Example: model.fit(X_train, y_train) is a common training pattern in scikit-learn.", "Explain in your own words why a model should not learn only from test data."),
            ("Evaluation", "Learn accuracy, precision, recall, MAE and the idea of comparing predictions with known outcomes.", "Example: MAE measures average absolute prediction error in regression.", "Choose a suitable evaluation metric for a binary classification example."),
            ("Mini Project", "Build a beginner workflow: load data, preprocess, split, train, predict and evaluate.", "Project idea: simple student result prediction or classification workflow.", "Document the six steps of your mini ML project and explain the final metric.")
        ],
        "quiz": [
            ("Which type of learning uses labelled target values?", ["Supervised learning", "Unsupervised learning", "Random learning", "Manual learning"], "A"),
            ("Predicting a house price is usually which task?", ["Classification", "Regression", "Clustering", "Association"], "B"),
            ("Why is a test set used?", ["To evaluate generalization", "To replace training", "To remove features", "To increase labels"], "A"),
            ("Which metric is commonly used for classification accuracy?", ["Accuracy", "MAE", "MSE only", "R-squared only"], "A"),
            ("Which library is commonly used for traditional ML in Python?", ["scikit-learn", "Pillow", "Tkinter", "BeautifulSoup"], "A")
        ]
    },
    "java": {
        "title": "Java Programming Fundamentals",
        "level": "Beginner",
        "duration": "4-5 hours",
        "description": "Learn Java syntax, control flow, methods, classes and basic object-oriented programming.",
        "modules": [
            ("Java Basics", "Understand Java programs, classes, the main method and compilation at a beginner level.", "Example: public static void main(String[] args) is the standard entry point.", "Write the basic structure of a Java program."),
            ("Variables & Data Types", "Learn int, double, char, boolean, String and variable declaration.", "Example: int marks = 85; stores an integer value.", "Declare variables for name, age, percentage and pass status."),
            ("Conditions & Loops", "Learn if-else, switch, for, while and do-while loops.", "Example: if (marks >= 40) can check a pass condition.", "Write a program to print numbers from 1 to 10 and identify even numbers."),
            ("Methods & Arrays", "Learn methods, parameters, return values and arrays.", "Example: a method can receive two integers and return their sum.", "Create a method that returns the largest value in an integer array."),
            ("Classes & Objects", "Understand classes, objects, constructors and basic encapsulation.", "Example: Student is a class and student1 can be an object of that class.", "Design a Student class with name and marks and a method to display details."),
            ("Mini Project", "Combine Java fundamentals in a small console-based application.", "Project idea: Student Management Console App.", "Create add, display and simple search functionality using classes and arrays.")
        ],
        "quiz": [
            ("Which keyword declares a class?", ["object", "class", "define", "struct"], "B"),
            ("What is the standard Java entry-point method?", ["start()", "run()", "main()", "execute()"], "C"),
            ("Which type stores true or false?", ["int", "String", "boolean", "char"], "C"),
            ("Which concept creates an object from a class?", ["Instantiation", "Compilation", "Iteration", "Filtering"], "A"),
            ("Which keyword is used to return a value from a method?", ["give", "return", "send", "yield"], "B")
        ]
    },
    "javascript": {
        "title": "JavaScript Fundamentals",
        "level": "Beginner",
        "duration": "4 hours",
        "description": "Learn JavaScript basics and build interactive web-page logic.",
        "modules": [
            ("JavaScript Basics", "Understand variables, values, operators and basic JavaScript syntax.", "Example: const name = 'Asha'; stores a value that should not be reassigned.", "Create variables for a user's name, age and course."),
            ("Conditions & Loops", "Learn if-else, switch, for and while loops.", "Example: if (score >= 50) can check a pass condition.", "Print numbers from 1 to 20 and identify multiples of five."),
            ("Functions", "Learn function declarations, parameters, return values and reusable logic.", "Example: function add(a,b){ return a+b; }.", "Create a function that calculates the average of three numbers."),
            ("Arrays & Objects", "Learn arrays, objects and common operations such as map, filter and property access.", "Example: const student = {name:'Asha', marks:85};", "Create an array of student objects and filter students with marks above 70."),
            ("DOM & Events", "Understand how JavaScript can select HTML elements and respond to user events.", "Example: a button click can trigger a JavaScript function.", "Design the logic for a button that changes a page message."),
            ("Mini Project", "Combine JavaScript concepts to create a small interactive browser feature.", "Project idea: interactive student result card.", "Create logic that accepts marks and displays grade and pass/fail status on a page.")
        ],
        "quiz": [
            ("Which keyword declares a block-scoped variable that can be reassigned?", ["let", "const", "static", "define"], "A"),
            ("Which structure stores an ordered collection of values?", ["Array", "Class only", "Boolean", "Event"], "A"),
            ("Which keyword defines a traditional function declaration?", ["method", "function", "def", "fun"], "B"),
            ("Which object represents the HTML document in browser JavaScript?", ["windowFile", "document", "htmlPage", "browser"], "B"),
            ("Which event commonly occurs when a user presses a button?", ["click", "loadData", "pressHTML", "runPage"], "A")
        ]
    },
    "data_science": {
        "title": "Data Science Fundamentals",
        "level": "Beginner",
        "duration": "5 hours",
        "description": "Learn the end-to-end basics of collecting, cleaning, analyzing and communicating data.",
        "modules": [
            ("Data Science Workflow", "Understand problem definition, data collection, cleaning, analysis, modelling and communication.", "Example workflow: Problem → Data → Cleaning → Analysis → Model → Insight.", "Write the steps you would follow to analyze student performance data."),
            ("Data Cleaning", "Understand missing values, duplicates, inconsistent values and why clean data matters.", "Example: duplicate customer records can distort counts and averages.", "List four common data-quality problems and one solution for each."),
            ("Exploratory Data Analysis", "Learn how summary statistics and visualizations help discover patterns and outliers.", "Example: mean, median and a distribution plot can reveal the shape of data.", "Choose suitable charts for category comparison, trends and distributions."),
            ("Feature Preparation", "Understand features, target variables, encoding and basic scaling concepts.", "Example: Department can be converted into numerical representation for a model.", "Identify features and target for a simple employee salary problem."),
            ("Modeling & Evaluation", "Understand the purpose of training, testing and evaluation in predictive data science.", "Example: compare predictions with actual outcomes using an appropriate metric.", "Explain why evaluation should use data that was not used to train the model."),
            ("Mini Project", "Plan a small data-science project from problem statement to final insight.", "Project idea: Student Performance Analysis and Prediction.", "Prepare a one-page project plan containing problem, data, preprocessing, analysis and outcome.")
        ],
        "quiz": [
            ("What should normally come first in a data-science project?", ["Problem definition", "Model deployment", "Certificate generation", "Random plotting"], "A"),
            ("Which activity identifies missing and duplicate records?", ["Data cleaning", "Deployment", "Prediction", "Presentation only"], "A"),
            ("Which chart is commonly useful for showing a trend over time?", ["Line chart", "Pie chart only", "Single number", "Text paragraph"], "A"),
            ("What is a target variable?", ["The value a model tries to predict", "A chart title", "A file name", "A duplicate row"], "A"),
            ("Why is data visualization useful?", ["To communicate patterns and insights", "To remove all data", "To replace every model", "To guarantee accuracy"], "A")
        ]
    }
}


def get_course_key(skill):
    skill = clean_skill(skill)
    aliases = {
        "ml": "machine_learning",
        "machine learning": "machine_learning",
        "data analysis": "pandas",
        "data science": "data_science"
    }
    if skill in aliases:
        return aliases[skill]
    for key, course in COURSES.items():
        if skill == key or skill == clean_skill(course["title"]):
            return key
        if any(skill == clean_skill(s) for s in course.get("skills", [])):
            return key
    return None


def create_course_certificate(user_name, course_title, score, certificate_id):
    if not HAS_REPORTLAB:
        return None

    file_name = "CareerMatch_AI_Certificate.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4

    c.setStrokeColor(colors.HexColor("#1f4e79"))
    c.setLineWidth(4)
    c.rect(28, 28, width - 56, height - 56)
    c.setStrokeColor(colors.HexColor("#4f81bd"))
    c.setLineWidth(1.5)
    c.rect(42, 42, width - 84, height - 84)

    c.setFillColor(colors.HexColor("#1f4e79"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 115, "CAREERMATCH AI")
    c.setFillColor(colors.HexColor("#444444"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 160, "Certificate of Completion")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 195, "This certificate is proudly presented to")
    c.setFillColor(colors.HexColor("#1f4e79"))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 245, user_name[:45])
    c.setFillColor(colors.HexColor("#444444"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 285, "for successfully completing")
    c.setFillColor(colors.HexColor("#1f4e79"))
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 325, course_title[:55])
    c.setFillColor(colors.HexColor("#444444"))
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, height - 365, f"Final Assessment Score: {score}%")
    c.drawCentredString(width / 2, height - 395, "CareerMatch AI Learning & Career Development Platform")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, 105, f"Certificate ID: {certificate_id}")
    c.drawCentredString(width / 2, 88, f"Completion Date: {pd.Timestamp.now().strftime('%d %B %Y')}")
    c.save()
    return file_name


def show_course_completion(missing_skills=None):
    st.divider()
    st.subheader("🎓 Learn & Certify")
    st.write(
        "Choose a complete CareerMatch AI course, study the lessons, "
        "finish the practice tasks, pass the final assessment and earn a certificate."
    )

    course_keys = list(COURSES.keys())
    course_titles = [COURSES[k]["title"] for k in course_keys]

    # Put skill-gap relevant courses first, but keep every course available.
    recommended_keys = []
    for skill in (missing_skills or []):
        key = get_course_key(skill)
        if key and key not in recommended_keys:
            recommended_keys.append(key)
    ordered_keys = recommended_keys + [k for k in course_keys if k not in recommended_keys]
    ordered_titles = [COURSES[k]["title"] for k in ordered_keys]

    selected_title = st.selectbox(
        "📚 Select a Course",
        ordered_titles,
        key="actual_course_selector"
    )
    selected_key = ordered_keys[ordered_titles.index(selected_title)]
    course = COURSES[selected_key]

    st.markdown(f"### {course['title']}")
    info1, info2, info3 = st.columns(3)
    info1.metric("Level", course["level"])
    info2.metric("Modules", len(course["modules"]))
    info3.metric("Duration", course["duration"])
    st.info(course["description"])

    progress_key = f"actual_course_progress_{selected_key}"
    quiz_key = f"actual_course_quiz_passed_{selected_key}"
    score_key = f"actual_course_score_{selected_key}"

    if progress_key not in st.session_state:
        st.session_state[progress_key] = set()
    if quiz_key not in st.session_state:
        st.session_state[quiz_key] = False

    completed = st.session_state[progress_key]
    total = len(course["modules"])
    progress = len(completed) / total if total else 0
    st.progress(progress)
    st.caption(f"Course Progress: {len(completed)}/{total} modules completed")

    for i, (title, content, example, practice) in enumerate(course["modules"]):
        done = i in completed
        with st.expander(f"{'✅' if done else '📘'} Module {i + 1}: {title}", expanded=(i == 0 and not done)):
            st.markdown("**Lesson**")
            st.write(content)
            st.markdown("**Example**")
            st.code(example, language="text")
            st.markdown("**Practice Task**")
            st.write(practice)
            if done:
                st.success("Module completed.")
            elif st.button("✅ Mark Module Complete", key=f"actual_complete_{selected_key}_{i}", use_container_width=True):
                completed.add(i)
                st.session_state[progress_key] = completed
                st.rerun()

    if len(completed) == total:
        st.success("🎉 All course modules completed. Now take the final assessment.")
        st.markdown("### 📝 Final Assessment")
        st.caption("Answer all 5 questions. You need at least 4/5 correct to pass and receive the certificate.")

        answers = []
        for i, (question, options, correct) in enumerate(course["quiz"]):
            answers.append(st.radio(question, options, key=f"actual_quiz_{selected_key}_{i}", index=None))

        if st.button("🎯 Submit Final Assessment", key=f"actual_submit_{selected_key}", use_container_width=True, type="primary"):
            score = sum(1 for answer, (_, options, correct) in zip(answers, course["quiz"]) if answer == options[ord(correct) - 65])
            percent = int(score / len(course["quiz"]) * 100)
            st.session_state[score_key] = percent
            if score >= 4:
                st.session_state[quiz_key] = True
                st.success(f"🏆 Assessment passed: {score}/5 ({percent}%). You are eligible for the certificate.")
            else:
                st.session_state[quiz_key] = False
                st.warning(f"Score: {score}/5 ({percent}%). You need at least 4/5. Review the modules and try again.")

    if st.session_state.get(quiz_key, False):
        st.markdown("### 🏆 Course Completed")
        score = st.session_state.get(score_key, 80)
        st.success(f"You completed **{course['title']}** with a final score of **{score}%**.")

        user_name = st.text_input("👤 Name for Certificate", key=f"actual_certificate_name_{selected_key}")
        if not HAS_REPORTLAB:
            st.error("Certificate generation requires reportlab. Add reportlab to requirements.txt.")
        elif st.button("📜 Generate Certificate", key=f"actual_generate_certificate_{selected_key}", use_container_width=True):
            if not user_name.strip():
                st.warning("Please enter your name first.")
            else:
                certificate_id = f"CMAI-{selected_key[:4].upper()}-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
                pdf_file = create_course_certificate(user_name.strip(), course["title"], score, certificate_id)
                if pdf_file:
                    st.success(f"Certificate generated successfully! Certificate ID: {certificate_id}")
                    with open(pdf_file, "rb") as file:
                        st.download_button(
                            "📥 Download / Print Certificate",
                            data=file.read(),
                            file_name=f"{course['title'].replace(' ', '_')}_Certificate.pdf",
                            mime="application/pdf",
                            key=f"actual_download_certificate_{selected_key}",
                            use_container_width=True
                        )


# Show the complete course library independently of Skill Gap.
show_course_completion(
    sorted(selected_row["missing_skills"]) if recommendations is not None and not recommendations.empty else []
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
    AI-Assisted Smart Job Recommendation System
    <br><br>
    Built with Python • Pandas • Streamlit • NLP
</div>
""",
    unsafe_allow_html=True
)
