import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CareerMatch AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# FILE PATHS
# =========================================================

DATA_FILE = "Cleaned_New_Data.csv"
USER_FILE = "user_data.json"


# =========================================================
# PASSWORD FUNCTIONS
# =========================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def load_user_data():
    if not os.path.exists(USER_FILE):
        return {}

    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except Exception:
        return {}


def save_user_data(user_data):
    with open(USER_FILE, "w") as file:
        json.dump(
            user_data,
            file,
            indent=4
        )


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "page" not in st.session_state:
    st.session_state.page = "login"


# =========================================================
# AUTHENTICATION UI
# =========================================================

def authentication_page():

    st.markdown(
        """
        <style>

        .auth-title {
            text-align: center;
            font-size: 38px;
            font-weight: 800;
            margin-top: 20px;
        }

        .auth-subtitle {
            text-align: center;
            color: #666;
            font-size: 17px;
            margin-bottom: 25px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="auth-title">💼 CareerMatch AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="auth-subtitle">'
        'Smart Job Recommendation System'
        '</div>',
        unsafe_allow_html=True
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🔐 Login",
            "📝 Register",
            "🔑 Forgot Password"
        ]
    )

    # =====================================================
    # LOGIN
    # =====================================================

    with tab1:

        st.subheader("Login")

        login_id = st.text_input(
            "Email or Username",
            key="login_id"
        )

        login_password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            users = load_user_data()

            if not users:
                st.error(
                    "No account found. Please register first."
                )

            else:

                found_user = None

                for username, details in users.items():

                    if (
                        details.get("email") == login_id
                        or username == login_id
                    ):
                        found_user = username
                        break

                if found_user is None:

                    st.error(
                        "Invalid email or username."
                    )

                elif (
                    users[found_user].get("password")
                    != hash_password(login_password)
                ):

                    st.error(
                        "Incorrect password."
                    )

                else:

                    st.session_state.logged_in = True
                    st.session_state.username = found_user

                    st.success(
                        "Login successful!"
                    )

                    st.rerun()

    # =====================================================
    # REGISTER
    # =====================================================

    with tab2:

        st.subheader("Create Account")

        register_email = st.text_input(
            "Email",
            key="register_email"
        )

        register_username = st.text_input(
            "Username",
            key="register_username"
        )

        register_password = st.text_input(
            "Password",
            type="password",
            key="register_password"
        )

        register_confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="register_confirm_password"
        )

        if st.button(
            "Register",
            use_container_width=True
        ):

            users = load_user_data()

            email = register_email.strip()
            username = register_username.strip()

            if not email or not username:

                st.warning(
                    "Please enter email and username."
                )

            elif not register_password:

                st.warning(
                    "Please enter a password."
                )

            elif (
                register_password
                != register_confirm_password
            ):

                st.error(
                    "Passwords do not match."
                )

            elif username in users:

                st.error(
                    "Username already exists."
                )

            elif any(
                user.get("email") == email
                for user in users.values()
            ):

                st.error(
                    "Email is already registered."
                )

            else:

                users[username] = {
                    "email": email,
                    "password": hash_password(
                        register_password
                    )
                }

                save_user_data(users)

                st.success(
                    "Registration successful! "
                    "You can now login."
                )

    # =====================================================
    # FORGOT PASSWORD
    # =====================================================

    with tab3:

        st.subheader("Reset Password")

        reset_email = st.text_input(
            "Registered Email",
            key="reset_email"
        )

        new_password = st.text_input(
            "New Password",
            type="password",
            key="new_password"
        )

        confirm_new_password = st.text_input(
            "Confirm New Password",
            type="password",
            key="confirm_new_password"
        )

        if st.button(
            "Reset Password",
            use_container_width=True
        ):

            users = load_user_data()

            found_username = None

            for username, details in users.items():

                if details.get("email") == reset_email.strip():

                    found_username = username
                    break

            if found_username is None:

                st.error(
                    "Email is not registered."
                )

            elif not new_password:

                st.warning(
                    "Please enter a new password."
                )

            elif (
                new_password
                != confirm_new_password
            ):

                st.error(
                    "Passwords do not match."
                )

            else:

                users[found_username]["password"] = (
                    hash_password(new_password)
                )

                save_user_data(users)

                st.success(
                    "Password updated successfully!"
                )


# =========================================================
# SHOW LOGIN IF NOT LOGGED IN
# =========================================================

if not st.session_state.logged_in:

    authentication_page()

    st.stop()


# =========================================================
# LOAD DATASET
# =========================================================

try:

    df = pd.read_csv(DATA_FILE)

except FileNotFoundError:

    st.error(
        f"{DATA_FILE} was not found. "
        "Please keep the CSV file in the same folder "
        "as app.py."
    )

    st.stop()

except Exception as e:

    st.error(
        f"Error loading dataset: {e}"
    )

    st.stop()


# =========================================================
# REQUIRED COLUMNS
# =========================================================

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
        "Missing columns in dataset: "
        + ", ".join(missing_columns)
    )

    st.stop()


# =========================================================
# CLEAN BASIC DATA
# =========================================================

df = df.dropna(
    subset=[
        "category",
        "job_title"
    ]
).copy()

df["category"] = (
    df["category"]
    .astype(str)
    .str.strip()
)

df["job_title"] = (
    df["job_title"]
    .astype(str)
    .str.strip()
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        text-align: center;
        font-size: 44px;
        font-weight: 800;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    .sub-title {
        text-align: center;
        font-size: 19px;
        color: #666;
        margin-bottom: 25px;
    }

    .step-card {
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #dddddd;
        text-align: center;
        min-height: 120px;
    }

    .step-number {
        font-size: 27px;
        font-weight: bold;
    }

    .step-title {
        font-size: 17px;
        font-weight: 700;
        margin-top: 5px;
    }

    .step-text {
        color: #666;
        font-size: 14px;
    }

    .job-card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #dddddd;
        margin-bottom: 18px;
    }

    .job-title {
        font-size: 23px;
        font-weight: 750;
    }

    .job-category {
        color: #666;
        font-size: 14px;
    }

    .match-score {
        font-size: 22px;
        font-weight: 750;
    }

    .skill-box {
        padding: 7px 11px;
        border-radius: 20px;
        border: 1px solid #cccccc;
        display: inline-block;
        margin: 3px;
        font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">💼 CareerMatch AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'Find the right job for your career<br>'
    'Discover • Explore • Find Your Opportunity'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# USER HEADER
# =========================================================

col1, col2 = st.columns(
    [8, 1]
)

with col1:

    st.write(
        f"👋 Welcome, **{st.session_state.username}**"
    )

with col2:

    if st.button(
        "Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.username = ""

        st.rerun()


st.divider()


# =========================================================
# HOW IT WORKS
# =========================================================

st.subheader("🚀 How It Works")

step1, step2, step3 = st.columns(3)

with step1:

    st.markdown(
        """
        <div class="step-card">
            <div class="step-number">1️⃣</div>
            <div class="step-title">Choose Category</div>
            <div class="step-text">
                Select your preferred career category.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with step2:

    st.markdown(
        """
        <div class="step-card">
            <div class="step-number">2️⃣</div>
            <div class="step-title">Choose Position</div>
            <div class="step-text">
                Select the job position you are interested in.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with step3:

    st.markdown(
        """
        <div class="step-card">
            <div class="step-number">3️⃣</div>
            <div class="step-title">Enter Skills</div>
            <div class="step-text">
                Enter up to 8 skills separated by commas.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.divider()


# =========================================================
# SKILL CLEANING
# =========================================================

def clean_skill(skill):

    skill = str(skill).lower().strip()

    skill = skill.replace(
        "_",
        " "
    )

    skill = skill.replace(
        "-",
        " "
    )

    skill = re.sub(
        r"\s+",
        " ",
        skill
    )

    return skill


# =========================================================
# EXTRACT REQUIRED SKILLS
# =========================================================

def extract_required_skills(skill_text):

    if pd.isna(skill_text):

        return set()

    text = str(skill_text).strip()

    if not text:

        return set()

    # Try Python-list format
    try:

        parsed = ast.literal_eval(text)

        if isinstance(
            parsed,
            list
        ):

            return {
                clean_skill(skill)
                for skill in parsed
                if str(skill).strip()
            }

    except (
        ValueError,
        SyntaxError
    ):

        pass

    # Handle different separators
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

    return {
        clean_skill(skill)
        for skill in skills
        if skill.strip()
    }


# =========================================================
# EXTRACT USER SKILLS
# =========================================================

def extract_user_skills(user_text):

    if not user_text.strip():

        return []

    skills = user_text.split(",")

    unique_skills = []

    seen = set()

    for skill in skills:

        cleaned = clean_skill(skill)

        if (
            cleaned
            and cleaned not in seen
        ):

            seen.add(cleaned)

            unique_skills.append(
                cleaned
            )

    # Maximum 8 skills
    return unique_skills[:8]


# =========================================================
# RECOMMENDATION FUNCTION
# =========================================================

def get_recommendations(
    category,
    job_title,
    user_skills
):

    # -----------------------------------------------------
    # All jobs from selected category
    # -----------------------------------------------------

    category_data = df[
        df["category"] == category
    ].copy()

    if category_data.empty:

        return category_data


    # -----------------------------------------------------
    # User skills
    # -----------------------------------------------------

    user_skill_list = extract_user_skills(
        user_skills
    )

    if not user_skill_list:

        return category_data.iloc[0:0]


    user_skill_set = set(
        user_skill_list
    )


    # -----------------------------------------------------
    # Selected position data
    # -----------------------------------------------------

    selected_position_data = df[
        (df["category"] == category)
        &
        (df["job_title"] == job_title)
    ].copy()

    if selected_position_data.empty:

        return category_data.iloc[0:0]


    # -----------------------------------------------------
    # Find all skills available for selected position
    # -----------------------------------------------------

    position_skill_pool = set()

    for skill_text in (
        selected_position_data[
            "job_skill_set"
        ].dropna()
    ):

        position_skill_pool.update(
            extract_required_skills(
                skill_text
            )
        )


    if not position_skill_pool:

        return category_data.iloc[0:0]


    # -----------------------------------------------------
    # Keep only relevant user skills
    # -----------------------------------------------------

    relevant_user_skills = (
        user_skill_set
        .intersection(
            position_skill_pool
        )
    )

    if not relevant_user_skills:

        return category_data.iloc[0:0]


    # Maximum 8 relevant skills
    relevant_user_skills = set(
        list(relevant_user_skills)[:8]
    )


    total_user_skills = len(
        relevant_user_skills
    )


    results = []


    # =====================================================
    # CALCULATE MATCH SCORE FOR EACH JOB
    # =====================================================

    for index, row in category_data.iterrows():

        required_skills = extract_required_skills(
            row["job_skill_set"]
        )

        if not required_skills:

            continue


        # -------------------------------------------------
        # Matching skills
        # -------------------------------------------------

        matched_skills = (
            relevant_user_skills
            .intersection(
                required_skills
            )
        )

        matched_count = len(
            matched_skills
        )


        # No matching skills = no recommendation
        if matched_count == 0:

            continue


        # -------------------------------------------------
        # User Skill Coverage
        # -------------------------------------------------

        user_skill_coverage = (
            matched_count
            /
            total_user_skills
        ) * 100


        # -------------------------------------------------
        # Job Requirement Coverage
        # -------------------------------------------------

        job_requirement_coverage = (
            matched_count
            /
            len(required_skills)
        ) * 100


        # -------------------------------------------------
        # Normal Score
        #
        # 70% User Skill Coverage
        # 30% Job Requirement Coverage
        # -------------------------------------------------

        normal_score = (
            user_skill_coverage * 0.70
            +
            job_requirement_coverage * 0.30
        )


        # =================================================
        # FINAL SCORE RULE
        #
        # 1 or 2 skills  -> below 30%
        # 3+ skills      -> maximum 95%
        # =================================================

        if len(user_skill_list) <= 2:

            final_score = min(
                normal_score,
                29.9
            )

        else:

            final_score = min(
                normal_score,
                95
            )


        # -------------------------------------------------
        # Position priority
        #
        # Used ONLY for sorting.
        # It is NOT added to percentage.
        # -------------------------------------------------

        position_priority = (
            1
            if clean_skill(
                row["job_title"]
            )
            ==
            clean_skill(
                job_title
            )
            else 0
        )


        results.append(
            {
                "index": index,

                "match_percentage":
                    final_score,

                "matched_skills":
                    matched_skills,

                "matched_skill_count":
                    matched_count,

                "user_skill_coverage":
                    user_skill_coverage,

                "job_requirement_coverage":
                    job_requirement_coverage,

                "position_priority":
                    position_priority
            }
        )


    if not results:

        return category_data.iloc[0:0]


    # =====================================================
    # CREATE RESULT DATAFRAME
    # =====================================================

    result_df = pd.DataFrame(
        results
    )


    recommendations = category_data.merge(
        result_df,
        left_index=True,
        right_on="index"
    )


    # =====================================================
    # SORT TOP MATCHES
    # =====================================================

    recommendations = (
        recommendations
        .sort_values(
            by=[
                "match_percentage",
                "matched_skill_count",
                "position_priority"
            ],
            ascending=[
                False,
                False,
                False
            ]
        )
        .head(5)
    )


    return recommendations


# =========================================================
# CATEGORY SELECTION
# =========================================================

st.subheader("🎯 Find Your Job")

categories = sorted(
    df["category"]
    .dropna()
    .unique()
    .tolist()
)

selected_category = st.selectbox(
    "1. Select Category",
    categories
)


# =========================================================
# POSITION SELECTION
# =========================================================

position_data = df[
    df["category"] == selected_category
]

positions = sorted(
    position_data["job_title"]
    .dropna()
    .unique()
    .tolist()
)

selected_position = st.selectbox(
    "2. Select Job Position",
    positions
)


# =========================================================
# SKILLS INPUT
# =========================================================

user_skills = st.text_input(
    "3. Enter Your Skills",
    placeholder=(
        "Example: Python, SQL, Pandas, "
        "Machine Learning, Excel"
    )
)

st.caption(
    "Enter up to 8 unique skills separated by commas."
)


# =========================================================
# SKILL COUNT INFORMATION
# =========================================================

entered_skills = extract_user_skills(
    user_skills
)

if entered_skills:

    st.write(
        f"**Skills entered:** "
        f"{len(entered_skills)}/8"
    )

    if len(entered_skills) > 8:

        st.warning(
            "Only the first 8 skills are considered."
        )


# =========================================================
# RECOMMEND BUTTON
# =========================================================

recommend_button = st.button(
    "🔍 Find Best Job Matches",
    use_container_width=True
)


# =========================================================
# RECOMMENDATIONS
# =========================================================

if recommend_button:

    if not user_skills.strip():

        st.warning(
            "Please enter at least one skill."
        )

    else:

        recommendations = get_recommendations(
            selected_category,
            selected_position,
            user_skills
        )


        if recommendations.empty:

            st.warning(
                "No matching jobs found for the "
                "entered skills and selected position."
            )

        else:

            st.success(
                f"Found {len(recommendations)} "
                "matching job opportunities."
            )


            st.caption(
                "The percentage represents the skill "
                "match between your skills and the "
                "job requirements."
            )


            # =================================================
            # DISPLAY TOP 5
            # =================================================

            for rank, (
                index,
                row
            ) in enumerate(
                recommendations.iterrows(),
                start=1
            ):

                match_percentage = round(
                    row["match_percentage"],
                    1
                )

                matched_skills = sorted(
                    row["matched_skills"]
                )

                required_skills = sorted(
                    extract_required_skills(
                        row["job_skill_set"]
                    )
                )


                st.markdown(
                    f"""
                    <div class="job-card">

                        <div class="job-title">
                            #{rank} {row["job_title"]}
                        </div>

                        <div class="job-category">
                            📂 {row["category"]}
                        </div>

                        <br>

                        <div class="match-score">
                            🎯 Skill Match:
                            {match_percentage}%
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True
                )


                st.progress(
                    min(
                        match_percentage / 100,
                        0.95
                    )
                )


                # -------------------------------------------------
                # MATCHED SKILLS
                # -------------------------------------------------

                st.markdown(
                    "**✅ Matching Skills**"
                )

                if matched_skills:

                    skill_html = ""

                    for skill in matched_skills:

                        skill_html += (
                            f'<span class="skill-box">'
                            f'{skill}'
                            f'</span>'
                        )

                    st.markdown(
                        skill_html,
                        unsafe_allow_html=True
                    )

                else:

                    st.write(
                        "No matching skills."
                    )


                st.markdown("")


                # -------------------------------------------------
                # REQUIRED SKILLS
                # -------------------------------------------------

                st.markdown(
                    "**📋 Required Skills**"
                )

                if required_skills:

                    required_html = ""

                    for skill in required_skills:

                        required_html += (
                            f'<span class="skill-box">'
                            f'{skill}'
                            f'</span>'
                        )

                    st.markdown(
                        required_html,
                        unsafe_allow_html=True
                    )


                st.markdown("")


                # -------------------------------------------------
                # COVERAGE
                # -------------------------------------------------

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "Your Skill Coverage",
                        f"{round(row['user_skill_coverage'], 1)}%"
                    )

                with col2:

                    st.metric(
                        "Job Requirement Coverage",
                        f"{round(row['job_requirement_coverage'], 1)}%"
                    )


                st.divider()


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div style="
        text-align:center;
        color:#777;
        padding:20px;
        font-size:13px;
    ">
        💼 CareerMatch AI |
        Smart Job Recommendation System
    </div>
    """,
    unsafe_allow_html=True
)
