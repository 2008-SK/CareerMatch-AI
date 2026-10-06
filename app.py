import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast
from io import BytesIO
from urllib.parse import quote_plus

# Optional library for Course Completion certificates
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
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
# COURSE COMPLETION & CERTIFICATE
# =====================================================

COURSES = {
    "python": {
        "title": "Python Fundamentals",
        "level": "Beginner",
        "duration": "4 Modules",
        "description": "Learn Python basics, conditions, loops, functions and collections through practical examples.",
        "modules": [
            ("Python Basics", "Learn variables, data types, input/output and basic Python syntax.", "name = 'CareerMatch AI'\nprint(name)", "Create three variables for your name, age and city and print them."),
            ("Conditions & Loops", "Learn if-else conditions and for/while loops for program control.", "for i in range(1, 6):\n    print(i)", "Write a program that prints numbers from 1 to 10 and identifies even numbers."),
            ("Functions & Collections", "Understand functions, lists, tuples and dictionaries.", "def add(a, b):\n    return a + b", "Create a function that receives a list of numbers and returns their sum."),
            ("Mini Project", "Combine Python concepts to build a small practical application.", "marks = [78, 85, 91]\navg = sum(marks) / len(marks)\nprint(avg)", "Build a small student marks calculator that displays total and average marks.")
        ],
        "quiz": [
            ("Which keyword is used to define a function in Python?", ["func", "def", "function", "define"], 1),
            ("Which data type stores key-value pairs?", ["List", "Tuple", "Set", "Dictionary"], 3),
            ("Which symbol starts a Python comment?", ["//", "#", "/*", "--"], 1),
            ("Which function is used to display output?", ["show()", "display()", "print()", "output()"], 2),
            ("Which collection is ordered and changeable?", ["List", "Tuple", "Set", "None"], 0)
        ]
    },
    "sql": {
        "title": "SQL for Data Analysis",
        "level": "Beginner",
        "duration": "4 Modules",
        "description": "Learn how to retrieve, filter, update and analyze data using SQL queries.",
        "modules": [
            ("Database Basics", "Understand databases, tables, rows, columns and primary keys.", "CREATE TABLE students (id INT, name VARCHAR(50));", "Write down the columns you would use for a student information table."),
            ("SELECT & WHERE", "Retrieve and filter records using SELECT and WHERE.", "SELECT name FROM students WHERE marks > 70;", "Write a query to display students whose marks are greater than 80."),
            ("Sorting & Aggregation", "Use ORDER BY, COUNT, SUM, AVG and GROUP BY for analysis.", "SELECT AVG(marks) FROM students;", "Write a query to find the average marks of all students."),
            ("Joins", "Understand how JOIN combines related information from multiple tables.", "SELECT s.name, d.course\nFROM students s\nJOIN departments d ON s.dept_id = d.id;", "Identify two related tables in a college system and the column that can connect them.")
        ],
        "quiz": [
            ("Which command retrieves data?", ["GET", "SELECT", "FETCH", "READ"], 1),
            ("Which clause filters rows?", ["ORDER BY", "GROUP BY", "WHERE", "SORT"], 2),
            ("Which function calculates the average?", ["SUM()", "AVG()", "COUNT()", "MEAN()"], 1),
            ("Which clause sorts query results?", ["SORT", "ORDER BY", "ARRANGE", "GROUP BY"], 1),
            ("Which operation combines rows from related tables?", ["JOIN", "MERGE", "CONNECT", "LINK"], 0)
        ]
    },
    "pandas": {
        "title": "Pandas & Data Analysis",
        "level": "Beginner",
        "duration": "4 Modules",
        "description": "Learn practical Pandas operations for loading, cleaning and analyzing tabular datasets.",
        "modules": [
            ("Series & DataFrame", "Understand the main Pandas data structures.", "df = pd.DataFrame({'Name':['A','B'], 'Marks':[80,90]})", "Create a DataFrame with three students and their marks."),
            ("Reading Data", "Load CSV data and inspect rows, columns and basic statistics.", "df = pd.read_csv('data.csv')\nprint(df.head())", "Load a CSV file and display its first five records."),
            ("Cleaning Data", "Handle missing values, duplicates and inconsistent text.", "df = df.drop_duplicates()\ndf = df.dropna()", "Find and remove duplicate rows from a dataset."),
            ("Analysis", "Filter, sort and summarize data using Pandas.", "top = df[df['Marks'] >= 80]\nprint(top)", "Filter a DataFrame to show records with marks of 80 or above.")
        ],
        "quiz": [
            ("Which function reads a CSV file?", ["pd.load_csv()", "pd.read_csv()", "pd.csv()", "pd.open_csv()"], 1),
            ("Which is Pandas' main 2D structure?", ["Array", "DataFrame", "Tensor", "Matrix"], 1),
            ("Which method removes missing values?", ["dropna()", "remove()", "deleteNA()", "clearna()"], 0),
            ("Which method removes duplicate rows?", ["delete_duplicates()", "drop_duplicates()", "remove_duplicates()", "unique_rows()"], 1),
            ("Which method shows the first rows?", ["head()", "top()", "first()", "start()"], 0)
        ]
    },
    "machine_learning": {
        "title": "Machine Learning Fundamentals",
        "level": "Beginner",
        "duration": "4 Modules",
        "description": "Understand the complete basic ML workflow from data preparation to model evaluation.",
        "modules": [
            ("ML Fundamentals", "Learn supervised and unsupervised learning and common ML tasks.", "from sklearn.model_selection import train_test_split", "Give one real-life example of classification and one of regression."),
            ("Data Preparation", "Understand features, labels, missing values and preprocessing.", "X = df[['age','income']]\ny = df['approved']", "Identify the features and target column in a simple loan dataset."),
            ("Training & Testing", "Learn why data is split into training and testing sets.", "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)", "Explain in your own words why a test set is needed."),
            ("Evaluation", "Understand accuracy and other basic evaluation concepts.", "accuracy = model.score(X_test, y_test)\nprint(accuracy)", "Compare two models using an evaluation metric and choose the better one.")
        ],
        "quiz": [
            ("Which learning type uses labelled data?", ["Supervised", "Unsupervised", "Random", "Manual"], 0),
            ("Why use a test set?", ["Formatting", "Evaluation", "Printing", "Storage"], 1),
            ("Which is a classification task?", ["House price prediction", "Temperature prediction", "Spam detection", "Average calculation"], 2),
            ("What is a feature?", ["An input variable", "The final answer", "A database", "A chart"], 0),
            ("What does a trained model learn?", ["Patterns from data", "Only file names", "Passwords", "Web pages"], 0)
        ]
    },
    "java": {
        "title": "Java Programming Fundamentals",
        "level": "Beginner",
        "duration": "4 Modules",
        "description": "Build a foundation in Java syntax, methods, arrays and object-oriented programming.",
        "modules": [
            ("Java Basics", "Learn classes, objects, variables and basic Java syntax.", "class Student {\n    String name;\n}", "Create a Java class named Student with name and age variables."),
            ("Control Statements", "Use if-else and loops to control program execution.", "for (int i = 1; i <= 5; i++) {\n    System.out.println(i);\n}", "Write a loop that prints numbers from 1 to 10."),
            ("Methods & Arrays", "Work with reusable methods and arrays.", "static int add(int a, int b) {\n    return a + b;\n}", "Create a method that returns the largest value in an integer array."),
            ("OOP Concepts", "Understand encapsulation, inheritance and polymorphism.", "class Child extends Parent {\n}", "Explain one practical example of inheritance.")
        ],
        "quiz": [
            ("Which keyword defines a class?", ["class", "define", "struct", "object"], 0),
            ("Which method is the Java entry point?", ["start()", "run()", "main()", "begin()"], 2),
            ("Java is mainly an ___ language.", ["Object-oriented", "Markup", "Query", "Spreadsheet"], 0),
            ("Which keyword creates inheritance?", ["inherits", "extends", "implements", "superclass"], 1),
            ("Which structure stores multiple values of the same type?", ["Array", "Class", "Method", "Package"], 0)
        ]
    },
    "javascript": {
        "title": "JavaScript Fundamentals",
        "level": "Beginner",
        "duration": "4 Modules",
        "description": "Learn JavaScript basics, functions and DOM concepts used in modern web development.",
        "modules": [
            ("JavaScript Basics", "Learn variables, data types and basic syntax.", "let name = 'CareerMatch AI';\nconsole.log(name);", "Create variables for your name and age and display them in the console."),
            ("Conditions & Loops", "Use conditions and loops for program logic.", "for (let i = 1; i <= 5; i++) {\n  console.log(i);\n}", "Write a loop that prints the first five even numbers."),
            ("Functions", "Create reusable functions with parameters and return values.", "function add(a, b) {\n  return a + b;\n}", "Create a function that returns the square of a number."),
            ("DOM Basics", "Understand how JavaScript interacts with HTML elements.", "document.getElementById('title').textContent = 'Hello';", "Create a button that changes a heading text when clicked.")
        ],
        "quiz": [
            ("Which keyword can declare a block-scoped variable?", ["let", "define", "variable", "dim"], 0),
            ("Which operator checks strict equality?", ["=", "==", "===", "!="], 2),
            ("JavaScript mainly adds ___ to web pages.", ["Structure", "Interactivity", "Database tables", "Operating systems"], 1),
            ("Which keyword defines a function?", ["function", "def", "func", "method"], 0),
            ("Which method selects an element by ID?", ["getElementById()", "selectId()", "findId()", "getId()"], 0)
        ]
    }
}


def course_certificate_pdf(student_name, course_title, score):
    """Create a printable PDF certificate and return its bytes."""
    if not HAS_REPORTLAB:
        return None

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Border and title
    pdf.setStrokeColor(colors.HexColor("#1f4e79"))
    pdf.setLineWidth(3)
    pdf.rect(18 * mm, 18 * mm, width - 36 * mm, height - 36 * mm)
    pdf.setLineWidth(1)
    pdf.rect(23 * mm, 23 * mm, width - 46 * mm, height - 46 * mm)

    pdf.setFillColor(colors.HexColor("#1f4e79"))
    pdf.setFont("Helvetica-Bold", 25)
    pdf.drawCentredString(width / 2, height - 65 * mm, "CERTIFICATE OF COMPLETION")

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 82 * mm, "CareerMatch AI Learning Platform")

    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, height - 105 * mm, "This certificate is proudly presented to")

    pdf.setFillColor(colors.HexColor("#1f4e79"))
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 122 * mm, student_name)

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(width / 2, height - 143 * mm, "for successfully completing the course")

    pdf.setFillColor(colors.HexColor("#1f4e79"))
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 157 * mm, course_title)

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 178 * mm, f"Final Assessment Score: {score}%")
    pdf.drawCentredString(width / 2, height - 190 * mm, f"Completion Date: {pd.Timestamp.now().strftime('%d %B %Y')}")

    certificate_id = "CMAI-" + hashlib.sha256(
        f"{student_name}|{course_title}|{pd.Timestamp.now().strftime('%Y%m%d%H%M%S%f')}".encode()
    ).hexdigest()[:10].upper()

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(width / 2, 42 * mm, f"Certificate ID: {certificate_id}")
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, 34 * mm, "CareerMatch AI • AI-Assisted Career Development Platform")

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def show_course_completion():
    st.divider()
    st.subheader("🎓 Course Completion & Certificates")
    st.write(
        "Learn practical skills through guided modules, complete the final assessment, "
        "and unlock a downloadable certificate after passing."
    )

    course_keys = list(COURSES.keys())
    course_titles = [COURSES[key]["title"] for key in course_keys]

    selected_title = st.selectbox(
        "📚 Select a Course",
        course_titles,
        key="course_completion_selector"
    )
    selected_key = course_keys[course_titles.index(selected_title)]
    course = COURSES[selected_key]

    c1, c2, c3 = st.columns(3)
    c1.metric("Level", course["level"])
    c2.metric("Modules", len(course["modules"]))
    c3.metric("Course Format", course["duration"])
    st.info(course["description"])

    progress_key = f"course_progress_{selected_key}"
    quiz_passed_key = f"course_quiz_passed_{selected_key}"
    quiz_score_key = f"course_quiz_score_{selected_key}"

    if progress_key not in st.session_state:
        st.session_state[progress_key] = []
    if quiz_passed_key not in st.session_state:
        st.session_state[quiz_passed_key] = False
    if quiz_score_key not in st.session_state:
        st.session_state[quiz_score_key] = 0

    completed = st.session_state[progress_key]
    total_modules = len(course["modules"])
    progress = len(completed) / total_modules if total_modules else 0

    st.progress(progress)
    st.caption(f"Course Progress: {len(completed)}/{total_modules} modules completed")

    for module_index, (module_title, lesson, example, practice) in enumerate(course["modules"]):
        done = module_index in completed
        with st.expander(
            f"{'✅' if done else '📘'} Module {module_index + 1}: {module_title}",
            expanded=(module_index == 0 and not done)
        ):
            st.markdown("**📖 Lesson**")
            st.write(lesson)
            st.markdown("**💻 Example**")
            st.code(example, language="python" if selected_key in ["python", "pandas", "machine_learning"] else "text")
            st.markdown("**🎯 Practice Task**")
            st.write(practice)

            if done:
                st.success("Module completed.")
            else:
                if st.button(
                    "✅ Mark Module Complete",
                    key=f"complete_module_{selected_key}_{module_index}",
                    use_container_width=True
                ):
                    completed.append(module_index)
                    st.session_state[progress_key] = completed
                    st.rerun()

    if len(completed) == total_modules:
        st.success("🎉 All modules completed. You can now take the final assessment.")
        st.markdown("### 📝 Final Assessment")
        st.caption("5 questions • Passing score: 4/5 (80%)")

        answers = []
        for question_index, (question, options, correct_index) in enumerate(course["quiz"]):
            answer = st.radio(
                f"{question_index + 1}. {question}",
                options,
                index=None,
                key=f"course_quiz_{selected_key}_{question_index}"
            )
            answers.append((answer, options, correct_index))

        if st.button(
            "🎯 Submit Final Assessment",
            key=f"submit_course_quiz_{selected_key}",
            type="primary",
            use_container_width=True
        ):
            unanswered = sum(1 for answer, _, _ in answers if answer is None)
            if unanswered:
                st.warning(f"Please answer all 5 questions. {unanswered} question(s) are unanswered.")
            else:
                score = sum(
                    1 for answer, options, correct_index in answers
                    if answer == options[correct_index]
                )
                percentage = int(score / len(course["quiz"]) * 100)
                st.session_state[quiz_score_key] = percentage
                st.session_state[quiz_passed_key] = score >= 4

                if score >= 4:
                    st.success(f"🏆 Assessment passed: {score}/5 ({percentage}%). Certificate unlocked!")
                else:
                    st.warning(f"Score: {score}/5 ({percentage}%). You need at least 4/5. Review the lessons and try again.")

    if st.session_state[quiz_passed_key]:
        score = st.session_state[quiz_score_key]
        st.markdown("### 🏆 Course Completed")
        st.success(f"You completed **{course['title']}** with a final score of **{score}%**.")

        certificate_name = st.text_input(
            "👤 Name for Certificate",
            key=f"certificate_name_{selected_key}",
            placeholder="Enter your full name"
        )

        if not HAS_REPORTLAB:
            st.error("Certificate generation requires ReportLab. Add `reportlab` to requirements.txt.")
        else:
            if st.button(
                "📜 Generate Certificate",
                key=f"generate_certificate_{selected_key}",
                use_container_width=True,
                type="primary"
            ):
                if not certificate_name.strip():
                    st.warning("Please enter your name first.")
                else:
                    pdf_data = course_certificate_pdf(
                        certificate_name.strip(),
                        course["title"],
                        score
                    )
                    st.session_state[f"certificate_pdf_{selected_key}"] = pdf_data
                    st.success("Certificate generated successfully!")

            pdf_data = st.session_state.get(f"certificate_pdf_{selected_key}")
            if pdf_data:
                st.download_button(
                    "📥 Download / Print Certificate",
                    data=pdf_data,
                    file_name=f"CareerMatch_AI_{selected_key}_Certificate.pdf",
                    mime="application/pdf",
                    key=f"download_certificate_{selected_key}",
                    use_container_width=True
                )


# Show the course library independently of Skill Gap Analysis.
# This means the user can learn any available course even when no job recommendation exists.
show_course_completion()


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
