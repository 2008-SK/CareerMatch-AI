"""CareerMatch AI - Smart Job Recommendation System
Updated with sidebar feature navigation and AI career-assistance modules.
"""

import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast
from io import BytesIO
from urllib.parse import quote_plus

# Optional libraries
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

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    genai = None
    types = None
    HAS_GEMINI = False

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    go = None
    HAS_PLOTLY = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    A4 = None
    canvas = None
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

if "active_feature" not in st.session_state:
    st.session_state.active_feature = "Job Recommendations"

if "selected_category" not in st.session_state:
    st.session_state.selected_category = ""

if "combined_skills_text" not in st.session_state:
    st.session_state.combined_skills_text = ""

if "selected_job_title" not in st.session_state:
    st.session_state.selected_job_title = ""

if "interview_questions" not in st.session_state:
    st.session_state.interview_questions = []

if "interview_job_title" not in st.session_state:
    st.session_state.interview_job_title = ""

if "interview_feedback" not in st.session_state:
    st.session_state.interview_feedback = ""

if "resume_ai_result" not in st.session_state:
    st.session_state.resume_ai_result = ""

if "outreach_result" not in st.session_state:
    st.session_state.outreach_result = ""


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


for column in [
    "category",
    "job_title",
    "job_description",
    "job_skill_set"
]:
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

    for skill in sorted(
        dataset_skills,
        key=len,
        reverse=True
    ):
        if not skill:
            continue

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

        (
            skill_score,
            precision_percentage,
            recall_percentage,
            matched_skills
        ) = calculate_skill_score(
            user_skill_set,
            required_skills
        )

        original_final_score = skill_score

        semantic_score = 0.0

        if semantic_enabled:
            semantic_score = calculate_semantic_score(
                user_skills,
                row["job_title"],
                row["job_description"],
                required_skills
            )

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
# AI FEATURE HELPERS
# =====================================================

@st.cache_resource
def load_gemini_client():
    if not HAS_GEMINI:
        return None

    try:
        api_key = st.secrets.get(
            "GEMINI_API_KEY",
            os.getenv("GEMINI_API_KEY", "")
        )
    except Exception:
        api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


gemini_client = load_gemini_client()


def generate_ai_text(prompt):
    if gemini_client is None:
        return ""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return getattr(response, "text", "") or ""
    except Exception:
        return ""


def generate_ai_audio_text(prompt, audio_bytes, mime_type="audio/wav"):
    if gemini_client is None or not audio_bytes:
        return ""

    try:
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type
        )
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, audio_part]
        )
        return getattr(response, "text", "") or ""
    except Exception:
        return ""


def get_recommended_jobs():
    recommendations = st.session_state.get("recommendations")

    if recommendations is None or recommendations.empty:
        return pd.DataFrame()

    return recommendations


def get_selected_job_from_recommendations(key):
    recommendations = get_recommended_jobs()

    if recommendations.empty:
        return None

    titles = recommendations["job_title"].astype(str).tolist()

    selected = st.selectbox(
        "Select a recommended job",
        titles,
        key=key
    )

    rows = recommendations[
        recommendations["job_title"] == selected
    ]

    if rows.empty:
        return None

    return rows.iloc[0]


def fallback_interview_questions(job_title, skills):
    skill_list = [
        s.strip()
        for s in skills.split(",")
        if s.strip()
    ]

    first = skill_list[:3]

    return [
        f"Explain your approach to solving a practical problem as a {job_title}.",
        f"What is your experience with {first[0] if first else 'the key skills required for this role'}?",
        f"How would you debug or improve a project related to {job_title}?",
        "Tell me about a project where you faced a technical challenge and how you solved it.",
        "Why are you a good fit for this role, and what skill are you currently improving?"
    ]


def parse_questions(text):
    if not text:
        return []

    questions = []

    for line in text.splitlines():
        line = re.sub(
            r"^\s*(?:\d+[\).\:-]|[-*])\s*",
            "",
            line
        ).strip()

        if line.endswith("?") and len(line) > 15:
            questions.append(line)

    return questions[:5]


def generate_interview_questions(
    job_title,
    job_description,
    required_skills
):
    prompt = f"""
Create exactly 5 mock interview questions for the job below.

Job title: {job_title}
Required skills: {', '.join(sorted(required_skills))}
Job description: {job_description[:1200]}

Include 3 technical questions and 2 HR/situational questions.
Return only one question per line, numbered 1 to 5.
"""

    generated = parse_questions(
        generate_ai_text(prompt)
    )

    if len(generated) >= 5:
        return generated[:5]

    return fallback_interview_questions(
        job_title,
        ", ".join(sorted(required_skills))
    )


def evaluate_interview_answers(
    job_title,
    skills,
    qa_pairs
):
    prompt = f"""
You are an expert technical and HR interviewer.

Candidate target role: {job_title}
Candidate skills: {skills}

Evaluate these answers:

{qa_pairs}

Return:
1. Overall score out of 10
2. Technical and communication strengths
3. Mistakes or weak points
4. Specific improvement suggestions
5. An ideal answer approach for the weakest answer

Keep the feedback practical and suitable for a diploma/entry-level candidate.
"""

    return generate_ai_text(prompt)


def create_resume_pdf(text):
    if not HAS_REPORTLAB:
        return None

    buffer = BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4
    y = height - 45

    pdf.setFont(
        "Helvetica-Bold",
        15
    )

    pdf.drawString(
        40,
        y,
        "CareerMatch AI - Improved Resume Suggestions"
    )

    y -= 30
    pdf.setFont(
        "Helvetica",
        10
    )

    for paragraph in text.splitlines():

        if y < 45:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 45

        pdf.drawString(
            40,
            y,
            paragraph[:105]
        )

        y -= 15

    pdf.save()
    buffer.seek(0)

    return buffer


def calculate_new_regime_tax(income):
    # AY 2026-27 new-regime slabs.
    if income <= 400000:
        tax = 0
    elif income <= 800000:
        tax = (income - 400000) * 0.05
    elif income <= 1200000:
        tax = 20000 + (income - 800000) * 0.10
    elif income <= 1600000:
        tax = 60000 + (income - 1200000) * 0.15
    elif income <= 2000000:
        tax = 120000 + (income - 1600000) * 0.20
    elif income <= 2400000:
        tax = 200000 + (income - 2000000) * 0.25
    else:
        tax = 300000 + (income - 2400000) * 0.30

    # Section 87A rebate for eligible resident individuals
    # with total income up to ₹12 lakh.
    if income <= 1200000:
        tax = 0

    cess = tax * 0.04

    return tax + cess


def estimate_salary_range(job_title, category):
    text = f"{job_title} {category}".lower()

    if any(
        x in text
        for x in [
            "machine learning",
            "data scientist",
            "artificial intelligence",
            " ai "
        ]
    ):
        return 6.0, 12.0

    if (
        "data analyst" in text
        or "analytics" in text
    ):
        return 4.5, 8.0

    if any(
        x in text
        for x in [
            "python",
            "software",
            "developer",
            "full stack",
            "web"
        ]
    ):
        return 4.0, 9.0

    if any(
        x in text
        for x in [
            "finance",
            "financial"
        ]
    ):
        return 3.5, 7.5

    if any(
        x in text
        for x in [
            "sales",
            "business development"
        ]
    ):
        return 3.0, 7.0

    if (
        "hr" in text
        or "human resource" in text
    ):
        return 3.0, 6.5

    return 3.5, 7.5


# =====================================================
# SIDEBAR NAVIGATION
# =====================================================

if st.sidebar.button(
    "🚪 Logout",
    use_container_width=True
):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.markdown("## 🚀 CareerMatch Features")

features = [
    ("🏠 Job Recommendations", "Job Recommendations"),
    ("📊 Skill Gap & Readiness", "Skill Gap & Readiness"),
    ("🎤 AI Mock Interview", "AI Mock Interview"),
    ("📄 Resume AI", "Resume AI"),
    ("📧 HR Outreach", "HR Outreach"),
    ("💰 Salary & Tax", "Salary & Tax")
]

for label, key in features:
    if st.sidebar.button(
        label,
        key=f"nav_{key}",
        use_container_width=True
    ):
        st.session_state.active_feature = key
        st.rerun()

st.sidebar.markdown("---")

if gemini_client:
    st.sidebar.success("🤖 Gemini AI: Connected")
else:
    st.sidebar.info(
        "🤖 Gemini AI: Not connected\n\n"
        "AI features use safe fallback content until "
        "GEMINI_API_KEY is configured."
    )


# =====================================================
# SEPARATE FEATURE: SKILL GAP
# =====================================================

if st.session_state.active_feature == "Skill Gap & Readiness":

    st.title("📊 Skill Gap & Readiness")

    st.write(
        "Compare your current skills with the requirements "
        "of a recommended job."
    )

    selected_row = get_selected_job_from_recommendations(
        "skill_gap_feature_job"
    )

    if selected_row is None:
        st.info(
            "First go to **🏠 Job Recommendations**, "
            "generate your Top 5 jobs, and then open this feature."
        )
        st.stop()

    required = (
        set(selected_row["missing_skills"])
        | set(selected_row["matched_skills"])
    )

    matched = set(selected_row["matched_skills"])
    missing = set(selected_row["missing_skills"])

    readiness = (
        len(matched) / len(required) * 100
        if required
        else 0
    )

    st.markdown(
        f"### 🎯 {selected_row['job_title']}"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Readiness Score",
        f"{readiness:.1f}%"
    )

    c2.metric(
        "Skills You Have",
        len(matched)
    )

    c3.metric(
        "Skills to Learn",
        len(missing)
    )

    if HAS_PLOTLY and required:

        labels = sorted(required)

        current_values = [
            100 if skill in matched else 0
            for skill in labels
        ]

        required_values = [
            100
            for _ in labels
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=required_values,
                theta=labels,
                fill="toself",
                name="Job Required Skills"
            )
        )

        fig.add_trace(
            go.Scatterpolar(
                r=current_values,
                theta=labels,
                fill="toself",
                name="Your Current Skills"
            )
        )

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=520
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    left, right = st.columns(2)

    with left:
        st.markdown("### ✅ Skills You Have")

        if matched:
            for skill in sorted(matched):
                st.success(skill.title())
        else:
            st.info("No direct skill matches.")

    with right:
        st.markdown("### ❌ Skills You Need")

        if missing:
            for skill in sorted(missing):
                st.warning(skill.title())
        else:
            st.success(
                "You already match all direct required skills!"
            )

    st.markdown("### ▶️ Learning Recommendations")

    if missing:
        for skill in sorted(missing)[:8]:
            st.markdown(
                f"**{skill.title()}** — "
                f"[Learn on YouTube]({youtube_search_url(skill)})"
            )
    else:
        st.success(
            "No missing skills found. Keep improving your current skills!"
        )

    st.stop()


# =====================================================
# SEPARATE FEATURE: AI MOCK INTERVIEW
# =====================================================

if st.session_state.active_feature == "AI Mock Interview":

    st.title("🎤 AI Mock Interview Simulator")

    st.write(
        "Practice technical and HR questions based on "
        "your selected job recommendation."
    )

    selected_row = get_selected_job_from_recommendations(
        "interview_feature_job"
    )

    if selected_row is None:
        st.info(
            "Generate Top 5 job recommendations first."
        )
        st.stop()

    job_title = str(
        selected_row["job_title"]
    )

    required_skills = extract_required_skills(
        selected_row["job_skill_set"]
    )

    skills_text = st.session_state.get(
        "combined_skills_text",
        ""
    )

    if (
        st.session_state.interview_job_title
        != job_title
    ):
        st.session_state.interview_questions = []
        st.session_state.interview_feedback = ""
        st.session_state.interview_job_title = job_title

    if st.button(
        "✨ Generate 5 Interview Questions",
        use_container_width=True
    ):

        with st.spinner(
            "Preparing your mock interview..."
        ):
            st.session_state.interview_questions = (
                generate_interview_questions(
                    job_title,
                    str(
                        selected_row["job_description"]
                    ),
                    required_skills
                )
            )

        st.session_state.interview_feedback = ""

    if not st.session_state.interview_questions:

        st.info(
            "Click the button above to generate "
            "your interview questions."
        )

    else:

        answers = []

        for i, question in enumerate(
            st.session_state.interview_questions,
            1
        ):

            st.markdown(
                f"### Q{i}. {question}"
            )

            answer = st.text_area(
                f"✍️ Text Answer {i}",
                key=f"interview_answer_{job_title}_{i}",
                height=120
            )

            audio = st.audio_input(
                f"🎙️ Or record your answer {i}",
                key=f"interview_audio_{job_title}_{i}"
            )

            answers.append(
                (
                    question,
                    answer,
                    audio
                )
            )

        if st.button(
            "🧠 Evaluate My Answers",
            type="primary",
            use_container_width=True
        ):

            text_answers = []

            for question, answer, audio in answers:

                if answer.strip():

                    text_answers.append(
                        f"Question: {question}\n"
                        f"Answer: {answer}"
                    )

                elif audio is not None and gemini_client:

                    with st.spinner(
                        "Transcribing and evaluating recorded answers..."
                    ):
                        audio_feedback = (
                            generate_ai_audio_text(
                                f"""
You are evaluating an interview answer.

Question:
{question}

Listen to the candidate's audio and:
1. Transcribe the answer.
2. Score it out of 10.
3. State strengths.
4. State mistakes or missing points.
5. Give a better answer approach.
""",
                                audio.getvalue(),
                                audio.type or "audio/wav"
                            )
                        )

                    text_answers.append(
                        f"Question: {question}\n"
                        f"Recorded Answer Evaluation:\n"
                        f"{audio_feedback or 'Audio could not be evaluated.'}"
                    )

                else:

                    text_answers.append(
                        f"Question: {question}\n"
                        f"Answer: [No text answer provided]"
                    )

            qa_text = "\n\n".join(
                text_answers
            )

            with st.spinner(
                "AI is evaluating your interview..."
            ):
                feedback = evaluate_interview_answers(
                    job_title,
                    skills_text,
                    qa_text
                )

            if feedback:

                st.session_state.interview_feedback = (
                    feedback
                )

            else:

                answered = sum(
                    bool(
                        answer.strip()
                    )
                    for _, answer, _ in answers
                )

                score = min(
                    10,
                    answered * 2
                )

                st.session_state.interview_feedback = (
                    f"### Overall Score: {score}/10\n\n"
                    f"You answered {answered} out of 5 questions. "
                    "Add specific examples, explain your approach "
                    "clearly, and connect your answers to the "
                    "required job skills."
                )

        if st.session_state.interview_feedback:

            st.divider()

            st.markdown(
                "### 📋 AI Interview Feedback"
            )

            st.markdown(
                st.session_state.interview_feedback
            )

    st.stop()


# =====================================================
# SEPARATE FEATURE: RESUME AI
# =====================================================

if st.session_state.active_feature == "Resume AI":

    st.title("📄 AI Smart Resume Analyzer")

    st.write(
        "Analyze your resume and improve job-specific "
        "bullet points without inventing experience."
    )

    resume_file_feature = st.file_uploader(
        "Upload Resume for AI Analysis",
        type=["pdf", "docx", "txt"],
        key="resume_ai_uploader"
    )

    if resume_file_feature is not None:

        resume_text_feature = parse_resume(
            resume_file_feature
        )

        if resume_text_feature:

            st.session_state.resume_text = (
                resume_text_feature
            )

            st.success(
                "Resume text extracted successfully."
            )

    resume_text_feature = st.session_state.get(
        "resume_text",
        ""
    )

    if not resume_text_feature:

        st.info(
            "Upload a PDF, DOCX or TXT resume to continue."
        )

        st.stop()

    selected_row = get_selected_job_from_recommendations(
        "resume_ai_feature_job"
    )

    if selected_row is None:

        st.warning(
            "Generate Top 5 jobs first so the resume "
            "can be tailored to a target job."
        )

        st.stop()

    job_title = str(
        selected_row["job_title"]
    )

    required_skills = extract_required_skills(
        selected_row["job_skill_set"]
    )

    st.markdown(
        f"### 🎯 Target Job: {job_title}"
    )

    st.write(
        "Required skills: "
        + ", ".join(
            sorted(required_skills)
        )
    )

    if st.button(
        "✨ Analyze & Improve My Resume",
        type="primary",
        use_container_width=True
    ):

        prompt = f"""
You are a professional resume improvement assistant.

Target job: {job_title}

Required skills:
{', '.join(sorted(required_skills))}

Resume:
{resume_text_feature[:8000]}

Do the following:
1. Identify weak or generic resume bullet points.
2. Rewrite up to 8 bullet points using strong action verbs.
3. Naturally include relevant job skills where appropriate.
4. Do not invent experience, projects, achievements, or numbers.
5. List important missing keywords separately.

Return clear sections:
WEAK/ORIGINAL AREAS
IMPROVED BULLET POINTS
MISSING KEYWORDS
"""

        with st.spinner(
            "Analyzing your resume with AI..."
        ):

            result = generate_ai_text(
                prompt
            )

        if result:

            st.session_state.resume_ai_result = (
                result
            )

        else:

            missing = sorted(
                required_skills
                - st.session_state.get(
                    "resume_skills",
                    set()
                )
            )

            st.session_state.resume_ai_result = (
                "Gemini AI is not configured.\n\n"
                "Detected missing job keywords:\n\n"
                + "\n".join(
                    f"- {skill}"
                    for skill in missing
                )
                + "\n\n"
                "Add only skills and achievements "
                "that you genuinely possess."
            )

    if st.session_state.resume_ai_result:

        st.divider()

        st.markdown(
            "### ✨ Resume Improvement Suggestions"
        )

        st.markdown(
            st.session_state.resume_ai_result
        )

        pdf_data = create_resume_pdf(
            st.session_state.resume_ai_result
        )

        if pdf_data:

            st.download_button(
                "⬇️ Download Suggestions as PDF",
                data=pdf_data,
                file_name=(
                    "CareerMatch_AI_Resume_Suggestions.pdf"
                ),
                mime="application/pdf",
                use_container_width=True
            )

    st.stop()


# =====================================================
# SEPARATE FEATURE: HR OUTREACH
# =====================================================

if st.session_state.active_feature == "HR Outreach":

    st.title("📧 HR Outreach Generator")

    st.write(
        "Create a professional HR email and LinkedIn "
        "outreach message from your job match."
    )

    selected_row = get_selected_job_from_recommendations(
        "outreach_feature_job"
    )

    if selected_row is None:

        st.info(
            "Generate Top 5 recommendations first."
        )

        st.stop()

    user_name = st.text_input(
        "Your Name",
        placeholder="e.g. Priya Sharma"
    )

    company_name = st.text_input(
        "Company Name",
        placeholder="e.g. ABC Technologies"
    )

    contact_role = st.text_input(
        "HR/Recruiter Name (optional)"
    )

    skills_text = st.session_state.get(
        "combined_skills_text",
        ""
    )

    if st.button(
        "✉️ Generate Outreach",
        type="primary",
        use_container_width=True
    ):

        prompt = f"""
Create two professional job outreach messages.

Candidate name: {user_name or 'Candidate'}
Company: {company_name or 'the company'}
Recruiter: {contact_role or 'Hiring Team'}
Target role: {selected_row['job_title']}
Candidate skills: {skills_text}

1. A concise HR email with subject line.
2. A concise LinkedIn message.

Do not invent experience or achievements.
"""

        with st.spinner(
            "Creating your outreach messages..."
        ):

            generated = generate_ai_text(
                prompt
            )

        if generated:

            st.session_state.outreach_result = (
                generated
            )

        else:

            st.session_state.outreach_result = f"""
### HR Email

**Subject:** Application for {selected_row['job_title']}

Dear {contact_role or 'Hiring Team'},

I am {user_name or 'a candidate'} interested in the
{selected_row['job_title']} opportunity at
{company_name or 'your organization'}.

My relevant skills include:
{skills_text or 'the skills listed in my resume'}.

I would appreciate the opportunity to discuss how my
skills can contribute to your team.

Regards,
{user_name or 'Candidate'}

### LinkedIn Message

Hello {contact_role or 'Hiring Team'},

I am interested in the {selected_row['job_title']}
role at {company_name or 'your organization'}.
My skills include {skills_text or 'relevant technical skills'}.

I would be glad to connect and discuss the opportunity.
"""

    if st.session_state.outreach_result:

        st.divider()

        st.markdown(
            st.session_state.outreach_result
        )

    st.stop()


# =====================================================
# SEPARATE FEATURE: SALARY & TAX
# =====================================================

if st.session_state.active_feature == "Salary & Tax":

    st.title("💰 Salary Expectation & Tax Calculator")

    st.write(
        "Estimate role-based CTC range, income tax "
        "and monthly in-hand salary."
    )

    selected_row = get_selected_job_from_recommendations(
        "salary_feature_job"
    )

    if selected_row is not None:

        default_role = str(
            selected_row["job_title"]
        )

        default_category = str(
            selected_row["category"]
        )

    else:

        default_role = "Software Developer"
        default_category = "Information Technology"

    role = st.text_input(
        "Job Role",
        value=default_role
    )

    category_for_salary = st.text_input(
        "Category",
        value=default_category
    )

    low, high = estimate_salary_range(
        role,
        category_for_salary
    )

    st.info(
        f"Estimated entry-level CTC range: "
        f"**₹{low:.1f} LPA – ₹{high:.1f} LPA**"
    )

    c1, c2 = st.columns(2)

    with c1:

        expected_ctc = st.number_input(
            "Expected CTC (₹ LPA)",
            min_value=1.0,
            max_value=100.0,
            value=float(
                (low + high) / 2
            ),
            step=0.5
        )

    with c2:

        pf_percent = st.number_input(
            "Estimated PF / other deductions (%)",
            min_value=0.0,
            max_value=20.0,
            value=12.0,
            step=0.5
        )

    annual_salary = (
        expected_ctc * 100000
    )

    annual_tax = calculate_new_regime_tax(
        annual_salary
    )

    annual_pf = (
        annual_salary
        * pf_percent
        / 100
    )

    annual_deductions = (
        annual_tax
        + annual_pf
    )

    monthly_in_hand = max(
        0,
        (
            annual_salary
            - annual_deductions
        ) / 12
    )

    m1, m2, m3 = st.columns(3)

    m1.metric(
        "Annual CTC",
        f"₹{annual_salary:,.0f}"
    )

    m2.metric(
        "Estimated Annual Tax",
        f"₹{annual_tax:,.0f}"
    )

    m3.metric(
        "Estimated Monthly In-Hand",
        f"₹{monthly_in_hand:,.0f}"
    )

    st.caption(
        "Tax estimate uses AY 2026-27 new-regime slabs "
        "and 4% cess. Actual in-hand salary can differ "
        "because of salary structure, employer PF, "
        "professional tax and other deductions."
    )

    st.stop()


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
# MAIN JOB SEARCH
# POSITION INPUT REMOVED
# =====================================================

st.subheader("🔎 Find Your Job")

st.info(
    "Select a category, enter your skills, "
    "and click **FIND MY TOP 5 JOBS**."
)


# STEP 1
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


# STEP 2
st.markdown(
    "### 2️⃣ Enter Your Skills"
)

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
# RESUME FEATURE
# =====================================================

st.divider()

st.subheader(
    "📄 Resume Skill Extraction"
)

st.write(
    "Upload your resume to automatically identify "
    "skills and use them for job matching."
)

resume_file = st.file_uploader(
    "Upload Resume",
    type=["pdf", "docx", "txt"],
    help="Supported formats: PDF, DOCX and TXT"
)

all_dataset_skills = set()

for skill_text in df["job_skill_set"].dropna():

    all_dataset_skills.update(
        extract_required_skills(
            skill_text
        )
    )

if resume_file is not None:

    resume_text = parse_resume(
        resume_file
    )

    if resume_text:

        resume_skills = extract_skills_from_resume(
            resume_text,
            all_dataset_skills
        )

        st.session_state.resume_text = (
            resume_text
        )

        st.session_state.resume_skills = (
            resume_skills
        )

        if resume_skills:

            st.success(
                f"✅ {len(resume_skills)} skills "
                "identified from your resume."
            )

            skill_html = "".join(
                [
                    f'<span class="skill-tag skill-matched">'
                    f'✓ {skill.title()}</span>'
                    for skill in sorted(
                        resume_skills
                    )
                ]
            )

            st.markdown(
                skill_html,
                unsafe_allow_html=True
            )

            st.caption(
                "These skills can be combined with "
                "manually entered skills."
            )

        else:

            st.warning(
                "No matching dataset skills were "
                "identified from this resume. "
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

st.subheader(
    "🧠 NLP Semantic Matching"
)

if nlp_model:

    semantic_enabled = st.checkbox(
        "Enable AI/NLP Semantic Matching",
        value=True,
        help=(
            "Compares the user's skill profile with "
            "job information using a Sentence Transformer model."
        )
    )

    st.caption(
        "NLP model: all-MiniLM-L6-v2"
    )

else:

    semantic_enabled = False

    st.warning(
        "NLP model is unavailable. The original "
        "skill-based recommendation system will continue to work."
    )


# =====================================================
# FIND TOP 5
# =====================================================

st.divider()

st.subheader(
    "🎯 Find Your Jobs"
)

st.write(
    "Your manual skills and extracted resume "
    "skills can be used together."
)

manual_set = extract_user_skills(
    user_skills
)

combined_skill_set = manual_set.union(
    st.session_state.resume_skills
)

combined_skills_text = ", ".join(
    sorted(combined_skill_set)
)

if combined_skill_set:

    st.success(
        "✅ Skills ready for matching: "
        + ", ".join(
            sorted(combined_skill_set)
        )
    )

if st.button(
    "🚀 FIND MY TOP 5 JOBS",
    use_container_width=True,
    type="primary"
):

    if not combined_skill_set:

        st.warning(
            "⚠️ Please enter your skills or "
            "upload a resume first."
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

        st.session_state.recommendations = (
            recommendations
        )

        st.session_state.recommendation_source = (
            "Manual + Resume Skills"
            if (
                st.session_state.resume_skills
                and manual_set
            )
            else "Resume Skills"
            if st.session_state.resume_skills
            else "Manual Skills"
        )

        st.session_state.selected_category = (
            category
        )

        st.session_state.combined_skills_text = (
            combined_skills_text
        )


# =====================================================
# RECOMMENDATION OUTPUT
# =====================================================

recommendations = (
    st.session_state.recommendations
)

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
            f"Based on: "
            f"{st.session_state.recommendation_source} | "
            f"Category: {st.session_state.selected_category}"
        )

        for number, (_, row) in enumerate(
            recommendations.iterrows(),
            start=1
        ):

            match_percentage = round(
                float(row["match_percentage"]),
                1
            )

            matched_skills = (
                row["matched_skills"]
            )

            if isinstance(
                matched_skills,
                set
            ):

                matched_skills_text = (
                    ", ".join(
                        sorted(
                            matched_skills
                        )
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
                        max(
                            match_percentage,
                            0
                        ),
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

        st.divider()

        st.info(
            "💡 Use the sidebar to open **Skill Gap**, "
            "**AI Mock Interview**, **Resume AI**, "
            "**HR Outreach**, or **Salary & Tax** "
            "for the recommended jobs."
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
