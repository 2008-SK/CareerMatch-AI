import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast
from io import BytesIO

# Imports for Resume Parsing
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx
except ImportError:
    docx = None

# Imports for NLP Semantic Matching
try:
    from sentence_transformers import SentenceTransformer, util
    HAS_ST = True
except ImportError:
    HAS_ST = False

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
# LOAD NLP MODEL (CACHED FOR PERFORMANCE)
# =====================================================

@st.cache_resource
def load_nlp_model():
    if HAS_ST:
        # Fast, lightweight and accurate sentence transformer model
        return SentenceTransformer('all-MiniLM-L6-v2')
    return None

nlp_model = load_nlp_model()

# =====================================================
# USER DATA FILE & AUTHENTICATION
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
    option = st.radio("Choose an option", ["Login", "Register", "Forgot Password"], horizontal=True)

    if option == "Register":
        st.subheader("Create Account")
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register", use_container_width=True):
            if not email or not username or not password:
                st.warning("Please fill all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must contain at least 6 characters.")
            else:
                user = {
                    "email": email,
                    "username": username,
                    "password": hash_password(password)
                }
                save_user(user)
                st.success("Registration successful! You can now login.")

    elif option == "Login":
        st.subheader("Login")
        login_id = st.text_input("Email or Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            user = load_user()
            if user is None:
                st.warning("No account found. Please register first.")
            elif (login_id == user["email"] or login_id == user["username"]) and (hash_password(password) == user["password"]):
                st.session_state.logged_in = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Incorrect email/username or password.")

    else:
        st.subheader("🔑 Forgot Password")
        email = st.text_input("Enter your registered email")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

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
                st.success("Password reset successfully! You can now login.")

    st.stop()

# =====================================================
# LOGOUT
# =====================================================

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# =====================================================
# LOAD & CLEAN DATA
# =====================================================

@st.cache_data
def load_dataset():
    if not os.path.exists("Cleaned_New_Data.csv"):
        st.error("Dataset 'Cleaned_New_Data.csv' not found.")
        st.stop()
    return pd.read_csv("Cleaned_New_Data.csv")

df = load_dataset()

required_columns = ["job_id", "category", "job_title", "job_description", "job_skill_set"]
missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error("Dataset is missing required columns: " + ", ".join(missing_columns))
    st.stop()

df["category"] = df["category"].fillna("").astype(str).str.strip()
df["job_title"] = df["job_title"].fillna("").astype(str).str.strip()
df["job_description"] = df["job_description"].fillna("").astype(str).str.strip()
df["job_skill_set"] = df["job_skill_set"].fillna("").astype(str).str.strip()

# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
.hero {
    text-align: center;
    padding: 30px;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 25px;
    background: linear-gradient(135deg, rgba(128,128,128,0.08), rgba(128,128,128,0.02));
}
.hero h1 { font-size: 38px; margin-bottom: 8px; }
.hero p { font-size: 16px; opacity: 0.85; }

.step-card {
    padding: 15px;
    border-radius: 14px;
    border: 1px solid rgba(128,128,128,0.2);
    min-height: 130px;
    text-align: center;
    background: rgba(128,128,128,0.03);
}

.job-card {
    padding: 22px;
    border-radius: 16px;
    border: 1px solid rgba(128,128,128,0.25);
    margin-bottom: 20px;
    background: rgba(128,128,128,0.025);
}

.skill-tag {
    display: inline-block;
    padding: 4px 10px;
    margin: 3px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 500;
}
.skill-matched { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.skill-missing { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }

</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPER FUNCTIONS & SKILL EXTRACTION
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
            return {clean_skill(s) for s in parsed if clean_skill(s)}
    except (ValueError, SyntaxError):
        pass

    text = text.replace(",", "|").replace(";", "|").replace("/", "|")
    return {clean_skill(s) for s in text.split("|") if clean_skill(s)}

def extract_user_skills(user_text):
    if not user_text or not user_text.strip():
        return set()
    return {clean_skill(s) for s in user_text.split(",") if clean_skill(s)}

# -----------------------------------------------------
# RESUME PARSER (PDF/DOCX)
# -----------------------------------------------------

def parse_resume(uploaded_file):
    extracted_text = ""
    file_type = uploaded_file.name.split(".")[-1].lower()

    try:
        if file_type == "pdf":
            if pdfplumber is None:
                st.error("`pdfplumber` library unavailable. Please install it using `pip install pdfplumber`.")
                return ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"

        elif file_type in ["docx", "doc"]:
            if docx is None:
                st.error("`python-docx` library unavailable. Please install it using `pip install python-docx`.")
                return ""
            doc = docx.Document(BytesIO(uploaded_file.read()))
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"
    except Exception as e:
        st.error(f"Error reading resume file: {e}")
        return ""

    return extracted_text

def extract_skills_from_text(raw_text, dataset_skills):
    """Matches words in uploaded resume text against known dataset skills."""
    if not raw_text:
        return set()

    clean_raw = raw_text.lower()
    found_skills = set()

    for skill in dataset_skills:
        # Word boundary match to avoid partial substring mismatches
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, clean_raw):
            found_skills.add(skill)

    return found_skills

# =====================================================
# SEMANTIC MATCHING & RECOMMENDATION ENGINE
# =====================================================

def get_recommendations(category, target_position, user_skills_set, user_skills_text, top_n=5):
    category_df = df[df["category"] == category].copy()
    if category_df.empty:
        return pd.DataFrame()

    results = []

    for idx, row in category_df.iterrows():
        job_skills = extract_required_skills(row["job_skill_set"])
        if not job_skills:
            continue

        # 1. Direct Skill Matching (Intersection)
        matched_skills = user_skills_set.intersection(job_skills)
        missing_skills = job_skills - user_skills_set

        overlap_score = (len(matched_skills) / len(job_skills)) * 100 if job_skills else 0

        # 2. NLP Semantic Matching
        semantic_score = 0.0
        if nlp_model and user_skills_text.strip():
            # Combine position + skill details for semantic evaluation
            job_representation = f"{row['job_title']}. Key Skills: {', '.join(job_skills)}. Description: {row['job_description'][:200]}"
            user_representation = f"Target Role: {target_position}. User Skills: {user_skills_text}"

            emb1 = nlp_model.encode(user_representation, convert_to_tensor=True)
            emb2 = nlp_model.encode(job_representation, convert_to_tensor=True)

            cosine_sim = util.cos_sim(emb1, emb2).item()
            semantic_score = max(0.0, cosine_sim) * 100

        # 3. Hybrid Final Match Score (60% Skill Match + 40% NLP Semantic Match)
        if nlp_model:
            final_score = (0.6 * overlap_score) + (0.4 * semantic_score)
        else:
            final_score = overlap_score

        results.append({
            "job_id": row["job_id"],
            "job_title": row["job_title"],
            "category": row["category"],
            "job_description": row["job_description"],
            "job_skill_set": row["job_skill_set"],
            "required_skills": job_skills,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "skill_match_score": round(overlap_score, 1),
            "semantic_score": round(semantic_score, 1),
            "final_score": round(final_score, 1)
        })

    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df = results_df.sort_values(by="final_score", ascending=False).head(top_n)

    return results_df

# =====================================================
# UI HEADER
# =====================================================

st.markdown("""
<div class="hero">
    <h1>💼 CareerMatch AI</h1>
    <p>Smart AI-Assisted Job Recommendation Engine with Semantic Matching & Skill Gap Analysis</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# HOW IT WORKS
# =====================================================

st.subheader("🚀 How It Works")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="step-card"><h3>1️⃣ Category & Title</h3><p>Choose your targeted industry sector and role.</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="step-card"><h3>2️⃣ Resume Extraction</h3><p>Upload PDF/DOCX to automatically parse skills.</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="step-card"><h3>3️⃣ NLP AI Matching</h3><p>Deep semantic matching using SBERT embeddings.</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="step-card"><h3>4️⃣ Skill Gap Analysis</h3><p>Identify missing skills & access learning links.</p></div>', unsafe_allow_html=True)

st.divider()

# =====================================================
# JOB SEARCH FORM
# =====================================================

st.subheader("🔎 Find Your Smart Career Match")

col_cat, col_pos = st.columns(2)

categories = sorted(df["category"].unique())
with col_cat:
    category = st.selectbox("📂 Career Category", categories)

category_jobs = sorted(df[df["category"] == category]["job_title"].unique())
with col_pos:
    job_title = st.selectbox("💼 Target Position", category_jobs)

# -----------------------------------------------------
# RESUME PARSER & SKILLS INPUT SECTION
# -----------------------------------------------------

st.markdown("### 📄 Step 3: Enter Skills or Upload Resume")

# Pre-extract all known dataset skills for resume word matching
all_dataset_skills = set()
for s_str in df["job_skill_set"].dropna():
    all_dataset_skills.update(extract_required_skills(s_str))

tab_manual, tab_resume = st.tabs(["✍️ Manual Skills Entry", "📤 Upload Resume (PDF / DOCX)"])

extracted_skills_set = set()
skills_text_input = ""

with tab_manual:
    skills_text_input = st.text_input(
        "🛠️ Enter your skills (separated by commas)",
        placeholder="Example: Python, SQL, Machine Learning, Pandas, Data Analysis"
    )
    if skills_text_input:
        extracted_skills_set = extract_user_skills(skills_text_input)

with tab_resume:
    uploaded_file = st.file_uploader("Upload your resume file", type=["pdf", "docx", "doc"])
    if uploaded_file is not None:
        resume_text = parse_resume(uploaded_file)
        if resume_text:
            auto_detected = extract_skills_from_text(resume_text, all_dataset_skills)
            if auto_detected:
                st.success(f"🎉 Successfully extracted **{len(auto_detected)} skills** from your resume!")
                st.write("**Extracted Skills:** " + ", ".join([s.title() for s in sorted(auto_detected)]))
                extracted_skills_set = auto_detected
                skills_text_input = ", ".join(auto_detected)
            else:
                st.warning("Could not automatically match specific technical skills from dataset. Please enter manually above.")

# =====================================================
# RECOMMENDATION EXECUTION & DISPLAY
# =====================================================

st.divider()

if st.button("🚀 Find Best Matching Jobs", use_container_width=True, type="primary"):
    if not extracted_skills_set:
        st.warning("⚠️ Please provide skills manually or upload a resume to get recommendations.")
    else:
        with st.spinner("🧠 AI is analyzing skills, computing embeddings & performing Skill Gap Analysis..."):
            rec_df = get_recommendations(
                category=category,
                target_position=job_title,
                user_skills_set=extracted_skills_set,
                user_skills_text=skills_text_input,
                top_n=5
            )

        if rec_df.empty:
            st.error("No matching jobs found for selected criteria.")
        else:
            st.subheader(f"🎯 Top 5 Job Recommendations for '{job_title}'")

            for rank, (_, row) in enumerate(rec_df.iterrows(), 1):
                matched = sorted(list(row["matched_skills"]))
                missing = sorted(list(row["missing_skills"]))

                st.markdown(f"""
                <div class="job-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 22px; font-weight: bold;">#{rank} {row['job_title']}</span>
                        <span style="font-size: 22px; font-weight: bold; color: #28a745;">Match: {row['final_score']}%</span>
                    </div>
                    <p style="margin-top: 5px; opacity: 0.8;"><b>Category:</b> {row['category']} | <b>Job ID:</b> {row['job_id']}</p>
                </div>
                """, unsafe_allow_html=True)

                # Expandable details section
                with st.expander(f"📊 View Skill Gap & Match Breakdown for {row['job_title']}"):
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Overall Match Score", f"{row['final_score']}%")
                    m2.metric("Exact Skill Match", f"{row['skill_match_score']}%")
                    m3.metric("NLP Semantic Score", f"{row['semantic_score']}%")

                    st.markdown("---")

                    c1, c2 = st.columns(2)

                    with c1:
                        st.markdown("##### ✅ Matched Skills You Have:")
                        if matched:
                            tags_html = "".join([f'<span class="skill-tag skill-matched">✓ {s.title()}</span>' for s in matched])
                            st.markdown(tags_html, unsafe_allow_html=True)
                        else:
                            st.info("No exact matching skills found.")

                    with c2:
                        st.markdown("##### ⚠️ Missing Skills (Skill Gap Analysis):")
                        if missing:
                            tags_html = "".join([f'<span class="skill-tag skill-missing">✗ {s.title()}</span>' for s in missing])
                            st.markdown(tags_html, unsafe_allow_html=True)
                        else:
                            st.success("🎉 You have all required skills for this role!")

                    # Learning Resources Recommendations for Missing Skills
                    if missing:
                        st.markdown("<br><b>📚 Recommended Free Upskilling Links:</b>", unsafe_allow_html=True)
                        links = []
                        for missing_skill in missing[:4]: # Limit to top 4 missing skills
                            search_url = f"https://www.youtube.com/results?search_query={missing_skill.replace(' ', '+')}+tutorial"
                            links.append(f"👉 [Learn {missing_skill.title()} on YouTube]({search_url})")
                        st.markdown(" • ".join(links))

                    st.markdown("<br><b>📝 Job Description Preview:</b>", unsafe_allow_html=True)
                    st.write(row['job_description'][:400] + ("..." if len(row['job_description']) > 400 e
