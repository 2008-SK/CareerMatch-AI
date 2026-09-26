import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast


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

        recommendations = (
            get_recommendations(
                category,
                job_title,
                user_skills
            )
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


                match_percentage = round(
                    float(
                        row["match_percentage"]
                    ),
                    1
                )


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

                    🎯 Best Match: {match_percentage}%

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
