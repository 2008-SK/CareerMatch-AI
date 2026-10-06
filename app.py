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
