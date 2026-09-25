import streamlit as st
import pandas as pd
import sqlite3
import re
import ast

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

conn.commit()


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""


# =========================================================
# LOGIN / REGISTER / FORGOT PASSWORD
# =========================================================

if not st.session_state.logged_in:

    st.title("🔐 CareerMatch AI")

    option = st.radio(
        "Select Option",
        ["Login", "Create Account", "Forgot Password"],
        horizontal=True
    )


    # =====================================================
    # LOGIN
    # =====================================================

    if option == "Login":

        st.subheader("Login")

        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Login", use_container_width=True):

            if username == "" or password == "":
                st.warning("Please enter username and password.")

            else:
                hashed_password = hash_password(password)

                cursor.execute(
                    """
                    SELECT * FROM users
                    WHERE username = ? AND password = ?
                    """,
                    (username, hashed_password)
                )

                user = cursor.fetchone()

                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username

                    st.success("Login successful!")
                    st.rerun()

                else:
                    st.error("Invalid username or password.")


    # =====================================================
    # CREATE ACCOUNT
    # =====================================================

    elif option == "Create Account":

        st.subheader("Create New Account")

        name = st.text_input("Full Name")
        email = st.text_input("Email")
        username = st.text_input("Create Username")
        password = st.text_input(
            "Create Password",
            type="password"
        )
        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button("Register", use_container_width=True):

            if not name or not email or not username or not password:
                st.warning("Please fill all fields.")

            elif not re.match(
                r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
                email
            ):
                st.error("Please enter a valid email address.")

            elif len(password) < 6:
                st.error("Password must contain at least 6 characters.")

            elif password != confirm_password:
                st.error("Passwords do not match.")

            else:

                try:
                    hashed_password = hash_password(password)

                    cursor.execute(
                        """
                        INSERT INTO users
                        (name, email, username, password)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            name,
                            email,
                            username,
                            hashed_password
                        )
                    )

                    conn.commit()

                    st.success(
                        "Account created successfully! "
                        "You can now login."
                    )

                except sqlite3.IntegrityError:

                    st.error(
                        "Username or email already exists."
                    )


    # =====================================================
    # FORGOT PASSWORD
    # =====================================================

    elif option == "Forgot Password":

        st.subheader("🔑 Forgot Password")

        email = st.text_input("Enter Registered Email")

        new_password = st.text_input(
            "New Password",
            type="password"
        )

        confirm_new_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

        if st.button(
            "Reset Password",
            use_container_width=True
        ):

            if not email or not new_password:
                st.warning("Please fill all fields.")

            elif len(new_password) < 6:
                st.error(
                    "Password must contain at least 6 characters."
                )

            elif new_password != confirm_new_password:
                st.error("Passwords do not match.")

            else:

                cursor.execute(
                    "SELECT * FROM users WHERE email = ?",
                    (email,)
                )

                user = cursor.fetchone()

                if user:

                    hashed_password = hash_password(
                        new_password
                    )

                    cursor.execute(
                        """
                        UPDATE users
                        SET password = ?
                        WHERE email = ?
                        """,
                        (hashed_password, email)
                    )

                    conn.commit()

                    st.success(
                        "Password reset successfully! "
                        "You can now login."
                    )

                else:
                    st.error(
                        "No account found with this email."
                    )


    # IMPORTANT:
    # Stop here until user logs in
    st.stop()


# =========================================================
# LOGOUT
# =========================================================

st.sidebar.success(
    f"Welcome, {st.session_state.username}!"
)

if st.sidebar.button("Logout"):

    st.session_state.logged_in = False
    st.session_state.username = ""

    st.rerun()


# =========================================================
# YOUR EXISTING CAREERMATCH AI CODE
# =========================================================

st.title("🤖 CareerMatch AI")

st.write(
    "Find the right job for your career"
)

# ---------------------------------------------------------
# PUT YOUR EXISTING CAREERMATCH AI CODE BELOW THIS LINE
# ---------------------------------------------------------
    
# =========================================================
# 1. LOAD DATA
# =========================================================

df = pd.read_csv("Cleaned_New_Data.csv")


# =========================================================
# 2. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="CareerMatch AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 3. CUSTOM CSS
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
# 4. HEADER
# =========================================================

st.markdown("""
<div class="hero">

<h1>💼 CareerMatch AI</h1>

<p>Find the right job for your career</p>

<p>Discover • Explore • Find Your Opportunity</p>

</div>
""", unsafe_allow_html=True)


# =========================================================
# 5. HOW IT WORKS
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
# 6. JOB SEARCH
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

category = st.selectbox(
    "📂 Career Category",
    sorted(
        df["category"]
        .dropna()
        .astype(str)
        .unique()
    )
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
    "Enter your skills separated by commas."
)

user_skills = st.text_input(
    "🛠️ Your Skills",
    placeholder="Example: Python, SQL, Pandas, Machine Learning"
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
# 7. POSITION PREVIEW
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
# 8. SKILL PROCESSING
# =========================================================

def clean_skill(skill):

    skill = str(skill).lower().strip()

    skill = skill.replace("_", " ")
    skill = skill.replace("-", " ")

    skill = re.sub(
        r"\s+",
        " ",
        skill
    )

    return skill


def extract_required_skills(skill_text):

    if pd.isna(skill_text):
        return set()

    text = str(skill_text).strip()

    # Dataset list format
    try:

        parsed = ast.literal_eval(text)

        if isinstance(parsed, list):

            return {
                clean_skill(skill)
                for skill in parsed
                if str(skill).strip()
            }

    except:

        pass

    # Normal text format
    text = text.replace(",", "|")
    text = text.replace(";", "|")
    text = text.replace("/", "|")

    skills = text.split("|")

    return {
        clean_skill(skill)
        for skill in skills
        if skill.strip()
    }


def extract_user_skills(user_text):

    if not user_text.strip():
        return set()

    skills = user_text.split(",")

    return {
        clean_skill(skill)
        for skill in skills
        if skill.strip()
    }


# =========================================================
# 9. POSITION SIMILARITY
# =========================================================

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

    # Exact position
    if user_position == job_position:
        return 100

    user_words = set(
        user_position.split()
    )

    job_words = set(
        job_position.split()
    )

    if not user_words or not job_words:
        return 0

    common_words = (
        user_words.intersection(
            job_words
        )
    )

    # Similarity based on common position words
    similarity = (
        len(common_words)
        /
        max(
            len(user_words),
            len(job_words)
        )
    ) * 100

    return similarity


# =========================================================
# 10. JOB RECOMMENDATION FUNCTION
# =========================================================

def get_recommendations(
    category,
    job_title,
    user_skills
):

    # -----------------------------------------------------
    # Category filtering
    # -----------------------------------------------------

    category_data = df[
        df["category"] == category
    ].copy()

    if category_data.empty:
        return category_data


    # -----------------------------------------------------
    # User skills
    # -----------------------------------------------------

    user_skill_set = extract_user_skills(
        user_skills
    )

    if not user_skill_set:
        return category_data.iloc[0:0]


    results = []


    # -----------------------------------------------------
    # Compare jobs
    # -----------------------------------------------------

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
            user_skill_set
            .intersection(
                required_skills
            )
        )


        # -------------------------------------------------
        # USER SKILL COVERAGE
        #
        # How many of user's skills are useful
        # -------------------------------------------------

        user_skill_coverage = (
            len(matched_skills)
            /
            len(user_skill_set)
        ) * 100


        # -------------------------------------------------
        # JOB REQUIREMENT COVERAGE
        #
        # How many required skills user has
        # -------------------------------------------------

        job_skill_coverage = (
            len(matched_skills)
            /
            len(required_skills)
        ) * 100


        # -------------------------------------------------
        # SKILL RELEVANCE
        #
        # Average of both sides
        # -------------------------------------------------

        skill_relevance = (
            user_skill_coverage
            +
            job_skill_coverage
        ) / 2


        # -------------------------------------------------
        # POSITION RELEVANCE
        # -------------------------------------------------

        position_relevance = (
            calculate_position_similarity(
                job_title,
                row["job_title"]
            )
        )


        # -------------------------------------------------
        # FINAL RECOMMENDATION SCORE
        #
        # Skills = 80%
        # Position = 20%
        # -------------------------------------------------

        final_score = (
            skill_relevance * 0.80
            +
            position_relevance * 0.20
        )


        results.append(
            {
                "index": index,

                "match_percentage":
                    final_score,

                "matched_skills":
                    matched_skills,

                "skill_relevance":
                    skill_relevance,

                "position_relevance":
                    position_relevance
            }
        )


    # -----------------------------------------------------
    # Result DataFrame
    # -----------------------------------------------------

    result_df = pd.DataFrame(
        results
    )

    if result_df.empty:
        return category_data.iloc[0:0]


    # -----------------------------------------------------
    # Merge with original data
    # -----------------------------------------------------

    recommendations = category_data.merge(
        result_df,
        left_index=True,
        right_on="index"
    )


    # -----------------------------------------------------
    # Sort by best match
    # -----------------------------------------------------

    recommendations = (
        recommendations
        .sort_values(
            by="match_percentage",
            ascending=False
        )
        .head(5)
    )


    return recommendations


# =========================================================
# 11. FIND JOBS
# =========================================================

st.subheader("🎯 Find Your Jobs")

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
                "😔 No suitable jobs found."
            )

            st.info(
                "💡 Try entering more relevant skills."
            )


        else:

            # -------------------------------------------------
            # RESULT HEADER
            # -------------------------------------------------

            st.success(
                "🎉 Top 5 matching jobs generated!"
            )

            st.subheader(
                "🏆 Your Best Job Recommendations"
            )

            st.caption(
                "The percentage represents how well each "
                "job matches your selected position and skills."
            )


            # =================================================
            # DISPLAY TOP 5
            # =================================================

            for number, (_, row) in enumerate(
                recommendations.iterrows(),
                start=1
            ):

                match_percentage = round(
                    row["match_percentage"],
                    1
                )


                matched_skills = row[
                    "matched_skills"
                ]


                # -------------------------------------------------
                # Convert matched skills
                # -------------------------------------------------

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
                    min(
                        int(match_percentage),
                        100
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
                        "### 🎯 Recommendation"
                    )

                    st.write(
                        f"This job is a "
                        f"**{match_percentage}% match** "
                        f"for your selected position and skills."
                    )

                    st.write(
                        f"**Matching Skills:** "
                        f"{matched_skills_text}"
                    )


# =========================================================
# 12. FOOTER
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
