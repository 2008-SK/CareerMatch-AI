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
    initial_sidebar_state="expanded"
)


# =========================================================
# USER DATA FILE
# =========================================================

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
    return hashlib.sha256(password.encode()).hexdigest()


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# =========================================================
# LOGIN SYSTEM
# =========================================================

if not st.session_state.logged_in:

    st.title("🔐 CareerMatch AI")

    option = st.radio(
        "Choose an option",
        ["Login", "Register", "Forgot Password"],
        horizontal=True
    )

    # =====================================================
    # REGISTER
    # =====================================================

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

                existing_user = load_user()

                if existing_user is not None:

                    st.error(
                        "An account is already registered. "
                        "Please use Login or Forgot Password."
                    )

                else:

                    user = {
                        "email": email.strip(),
                        "username": username.strip(),
                        "password": hash_password(password)
                    }

                    save_user(user)

                    st.success(
                        "Registration successful! "
                        "Please select Login and login with your credentials."
                    )


    # =====================================================
    # LOGIN
    # =====================================================

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
                login_id.strip() == user["email"]
                or login_id.strip() == user["username"]
            ) and hash_password(password) == user["password"]:

                st.session_state.logged_in = True

                st.success(
                    "Login successful!"
                )

                st.rerun()

            else:

                st.error(
                    "Incorrect email/username or password."
                )


    # =====================================================
    # FORGOT PASSWORD
    # =====================================================

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

            elif email.strip() != user["email"]:

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
                    "Please select Login and login again."
                )

    st.stop()


# =========================================================
# LOGOUT
# =========================================================

if st.sidebar.button("Logout"):

    st.session_state.logged_in = False

    st.rerun()


# =========================================================
# LOAD DATA
# =========================================================

try:

    df = pd.read_csv(
        "Cleaned_New_Data.csv"
    )

except FileNotFoundError:

    st.error(
        "Cleaned_New_Data.csv file was not found."
    )

    st.stop()


# =========================================================
# CHECK REQUIRED COLUMNS
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
        "Missing required columns: "
        + ", ".join(missing_columns)
    )

    st.stop()


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
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
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="hero">

<h1>💼 CareerMatch AI</h1>

<p>Find the right job for your career</p>

<p>Discover • Explore • Find Your Opportunity</p>

</div>
""", unsafe_allow_html=True)


# =========================================================
# HOW IT WORKS
# =========================================================

st.subheader("🚀 How It Works")

st.write(
    "Choose your category, position and skills "
    "to find the most suitable job opportunities."
)

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown("""
    <div class="step-card">
    <div class="step-icon">1️⃣</div>
    <h3>Choose Category</h3>
    <p>Select your preferred career field.</p>
    </div>
    """, unsafe_allow_html=True)


with col2:

    st.markdown("""
    <div class="step-card">
    <div class="step-icon">2️⃣</div>
    <h3>Choose Position</h3>
    <p>Select your preferred job position.</p>
    </div>
    """, unsafe_allow_html=True)


with col3:

    st.markdown("""
    <div class="step-card">
    <div class="step-icon">3️⃣</div>
    <h3>Enter Skills</h3>
    <p>Enter your skills to get job matches.</p>
    </div>
    """, unsafe_allow_html=True)


st.divider()


# =========================================================
# JOB SEARCH
# =========================================================

st.subheader("🔎 Find Your Job")

st.info(
    "👋 Select a **Category**, choose a **Position**, "
    "and enter your **Skills** to get the top 5 recommendations."
)


# =========================================================
# STEP 1 — CATEGORY
# =========================================================

st.markdown("### 1️⃣ Select Your Career Category")

categories = sorted(
    df["category"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

category = st.selectbox(
    "📂 Career Category",
    categories
)


# =========================================================
# STEP 2 — POSITION
# =========================================================

category_jobs = sorted(
    df[
        df["category"] == category
    ]["job_title"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

st.markdown("### 2️⃣ Select Your Job Position")

job_title = st.selectbox(
    "💼 Available Positions",
    category_jobs
)


# =========================================================
# STEP 3 — USER SKILLS
# =========================================================

st.markdown("### 3️⃣ Enter Your Skills")

st.caption(
    "Enter all your skills separated by commas. "
    "You can enter more than 5 skills."
)

user_skills = st.text_input(
    "🛠️ Your Skills",
    placeholder="Example: Python, SQL, Pandas, Machine Learning, Git, Django"
)


# =========================================================
# PROGRESS
# =========================================================

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


# =========================================================
# POSITION PREVIEW
# =========================================================

st.subheader("👀 Position Preview")

selected_job = df[
    (df["category"] == category) &
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


# =========================================================
# SKILL PROCESSING
# =========================================================

def clean_skill(skill):

    if skill is None:
        return ""

    skill = str(skill).strip().lower()

    # Make different separators consistent
    skill = skill.replace("_", " ")
    skill = skill.replace("-", " ")

    # Remove extra spaces
    skill = re.sub(
        r"\s+",
        " ",
        skill
    )

    return skill.strip()


def extract_required_skills(skill_text):

    """
    Convert dataset job_skill_set into a unique
    normalized set of skills.
    """

    if pd.isna(skill_text):

        return set()

    text = str(skill_text).strip()

    if not text:

        return set()

    # -----------------------------------------------------
    # Try Python-list format
    # Example:
    # ['Python', 'SQL', 'Pandas']
    # -----------------------------------------------------

    try:

        parsed = ast.literal_eval(text)

        if isinstance(
            parsed,
            (list, tuple, set)
        ):

            return {
                clean_skill(skill)
                for skill in parsed
                if clean_skill(skill)
            }

    except (
        ValueError,
        SyntaxError,
        TypeError
    ):

        pass


    # -----------------------------------------------------
    # Normal text format
    # -----------------------------------------------------

    text = text.replace(",", "|")
    text = text.replace(";", "|")
    text = text.replace("/", "|")

    skills = text.split("|")

    return {
        clean_skill(skill)
        for skill in skills
        if clean_skill(skill)
    }


def extract_user_skills(user_text):

    """
    Convert user's comma-separated skills into
    a unique normalized set.

    No 5-skill limit is applied.
    """

    if not user_text or not user_text.strip():

        return set()

    skills = user_text.split(",")

    return {
        clean_skill(skill)
        for skill in skills
        if clean_skill(skill)
    }


# =========================================================
# JOB RECOMMENDATION FUNCTION
# =========================================================

def get_recommendations(
    category,
    job_title,
    user_skills
):

    # -----------------------------------------------------
    # 1. FILTER EXACT CATEGORY + POSITION
    # -----------------------------------------------------

    selected_data = df[
        (df["category"] == category) &
        (df["job_title"] == job_title)
    ].copy()

    if selected_data.empty:

        return selected_data


    # -----------------------------------------------------
    # 2. GET USER SKILLS
    # -----------------------------------------------------

    user_skill_set = extract_user_skills(
        user_skills
    )

    if not user_skill_set:

        return selected_data.iloc[0:0]


    # -----------------------------------------------------
    # 3. GET ALL UNIQUE AVAILABLE SKILLS
    #
    # IMPORTANT:
    # These skills come ONLY from the selected
    # Category + Position.
    # -----------------------------------------------------

    all_available_skills = set()

    for skill_data in selected_data["job_skill_set"]:

        job_skills = extract_required_skills(
            skill_data
        )

        all_available_skills.update(
            job_skills
        )


    # -----------------------------------------------------
    # 4. CHECK AVAILABLE SKILLS
    # -----------------------------------------------------

    if not all_available_skills:

        return selected_data.iloc[0:0]


    # -----------------------------------------------------
    # 5. CALCULATE MATCHING SKILLS FOR EACH JOB
    # -----------------------------------------------------

    results = []

    for index, row in selected_data.iterrows():

        required_skills = extract_required_skills(
            row["job_skill_set"]
        )

        if not required_skills:

            continue


        # -------------------------------------------------
        # USER SKILLS ∩ JOB SKILLS
        # -------------------------------------------------

        matched_skills = (
            user_skill_set
            .intersection(required_skills)
        )


        # -------------------------------------------------
        # EXACT REQUIRED FORMULA
        #
        # Match % =
        # Matched User Skills
        # -------------------------- × 100
        # Total Available Unique Skills
        #
        # Denominator is calculated from ALL jobs
        # having the selected Category + Position.
        # -------------------------------------------------

        match_percentage = (
            len(matched_skills)
            /
            len(all_available_skills)
        ) * 100


        # -------------------------------------------------
        # ONLY KEEP JOBS WITH AT LEAST ONE MATCH
        # -------------------------------------------------

        if len(matched_skills) == 0:

            continue


        results.append(
            {
                "index": index,

                "match_percentage":
                    round(
                        match_percentage,
                        2
                    ),

                "matched_skills":
                    matched_skills,

                "matched_skill_count":
                    len(matched_skills),

                "total_available_skills":
                    len(all_available_skills)
            }
        )


    # -----------------------------------------------------
    # 6. CREATE RESULT DATAFRAME
    # -----------------------------------------------------

    result_df = pd.DataFrame(
        results
    )

    if result_df.empty:

        return selected_data.iloc[0:0]


    # -----------------------------------------------------
    # 7. MERGE WITH ORIGINAL JOB DATA
    # -----------------------------------------------------

    recommendations = selected_data.merge(
        result_df,
        left_index=True,
        right_on="index"
    )


    # -----------------------------------------------------
    # 8. SORT BY MATCH PERCENTAGE
    #
    # Higher percentage first.
    # If percentage is same, more matched skills first.
    # -----------------------------------------------------

    recommendations = (
        recommendations
        .sort_values(
            by=[
                "match_percentage",
                "matched_skill_count"
            ],
            ascending=[
                False,
                False
            ]
        )
        .head(5)
    )


    return recommendations


# =========================================================
# FIND JOBS
# =========================================================

st.subheader("🎯 Find Your Jobs")

st.write(
    "Get the top 5 jobs that best match your "
    "selected category, position and skills."
)

st.info(
    f"🔎 **Category:** {category}  |  "
    f"**Position:** {job_title}"
)


if st.button(
    "🚀 FIND MY TOP 5 JOBS",
    use_container_width=True
):

    # -----------------------------------------------------
    # CHECK SKILLS
    # -----------------------------------------------------

    if not user_skills.strip():

        st.warning(
            "⚠️ Please enter your skills first."
        )

    else:

        recommendations = get_recommendations(
            category,
            job_title,
            user_skills
        )


        # -------------------------------------------------
        # NO RESULTS
        # -------------------------------------------------

        if recommendations.empty:

            st.warning(
                "😔 No matching jobs found."
            )

            st.info(
                "💡 Try entering skills relevant to "
                "the selected position."
            )


        else:

            # ---------------------------------------------
            # RESULT HEADER
            # ---------------------------------------------

            st.success(
                "🎉 Top matching jobs generated!"
            )

            st.subheader(
                "🏆 Your Best Job Recommendations"
            )

            st.caption(
                "Match percentage = "
                "Matched user skills ÷ Total unique available "
                "skills for the selected Category + Position × 100."
            )


            # ---------------------------------------------
            # AVAILABLE SKILLS INFORMATION
            # ---------------------------------------------

            total_available_skills = int(
                recommendations.iloc[0][
                    "total_available_skills"
                ]
            )

            st.info(
                f"📊 **Total unique available skills "
                f"for this Category + Position:** "
                f"{total_available_skills}"
            )


            # ---------------------------------------------
            # DISPLAY TOP 5
            # ---------------------------------------------

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


                matched_skills = row[
                    "matched_skills"
                ]


                # -----------------------------------------
                # CONVERT MATCHED SKILLS TO TEXT
                # -----------------------------------------

                if isinstance(
                    matched_skills,
                    set
                ):

                    if matched_skills:

                        matched_skills_text = ", ".join(
                            sorted(
                                matched_skills
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


                matched_skill_count = int(
                    row["matched_skill_count"]
                )


                # -----------------------------------------
                # JOB CARD
                # -----------------------------------------

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

                    🔢 <b>Matched Skills:</b>
                    {matched_skill_count}

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


                # -----------------------------------------
                # MATCH PROGRESS
                # -----------------------------------------

                st.progress(
                    min(
                        max(
                            int(
                                round(
                                    match_percentage
                                )
                            ),
                            0
                        ),
                        100
                    )
                )


                # -----------------------------------------
                # FULL DETAILS
                # -----------------------------------------

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
                        "### 🎯 Recommendation"
                    )

                    st.write(
                        f"This job has a "
                        f"**{match_percentage}% skill match** "
                        f"based on the total unique skills "
                        f"available for the selected "
                        f"category and position."
                    )


                    st.write(
                        f"**Matching Skills:** "
                        f"{matched_skills_text}"
                    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown("""
<div class="footer">

<b>💼 CareerMatch AI</b>

<br>

Smart Job Recommendation System

<br><br>

Built with Python • Pandas • Streamlit

</div>
""", unsafe_allow_html=True)
