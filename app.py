import streamlit as st
import pandas as pd
import re
import json
import os
import hashlib
import ast
from io import BytesIO
from urllib.parse import quote_plus

# Optional library for course certificates
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas
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

if "course_progress" not in st.session_state:
    st.session_state.course_progress = {}

if "course_quiz_results" not in st.session_state:
    st.session_state.course_quiz_results = {}

if "course_certificates" not in st.session_state:
    st.session_state.course_certificates = {}


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
# SKILL COURSE COMPLETION SYSTEM
# =====================================================

COURSE_TEMPLATES = {
    "python": {
        "title": "Python Fundamentals",
        "level": "Beginner",
        "duration": "3–4 hours",
        "modules": [
            ("Python Basics", "Learn variables, data types, operators and basic syntax.", "name = 'Alex'\nage = 20\nprint(name, age)", "Create variables for your name, age and city and print them."),
            ("Conditions & Loops", "Learn if/else conditions and for/while loops for decision making and repetition.", "for i in range(1, 6):\n    print(i)", "Print numbers from 1 to 10 and display whether each number is even or odd."),
            ("Functions & Collections", "Learn functions and common Python collections such as lists and dictionaries.", "def add(a, b):\n    return a + b", "Create a function that accepts a list of numbers and returns the largest value."),
            ("Practical Python", "Combine the concepts to build a small useful program and handle basic errors.", "skills = ['Python', 'SQL']\nfor skill in skills:\n    print(skill)", "Build a small skill tracker that stores five skills and displays them."),
        ],
        "quiz": [
            ("Which keyword defines a function in Python?", ["function", "def", "fun", "define"], "B"),
            ("Which collection stores key-value pairs?", ["List", "Tuple", "Dictionary", "Set"], "C"),
            ("What does len() return?", ["The last item", "The number of items", "The data type", "The memory size"], "B"),
            ("Which symbol starts a comment in Python?", ["//", "<!--", "#", "/*"], "C"),
            ("Which loop is commonly used to iterate over a sequence?", ["for", "switch", "case", "goto"], "A"),
        ],
    },
    "sql": {
        "title": "SQL for Data Analysis", "level": "Beginner", "duration": "3–4 hours",
        "modules": [
            ("SQL Basics", "Understand databases, tables, rows, columns and SELECT queries.", "SELECT name, salary\nFROM employees;", "Write a query to display all columns from a students table."),
            ("Filtering & Sorting", "Use WHERE, AND, OR, IN, LIKE and ORDER BY to filter data.", "SELECT * FROM employees\nWHERE salary > 50000\nORDER BY salary DESC;", "Find employees from the IT department with salary above 40000."),
            ("Aggregations", "Use COUNT, SUM, AVG, MIN, MAX and GROUP BY to summarize data.", "SELECT department, AVG(salary)\nFROM employees\nGROUP BY department;", "Calculate the average salary for every department."),
            ("Joins & Practical Queries", "Combine related tables using joins and build useful analytical queries.", "SELECT e.name, d.department_name\nFROM employees e\nJOIN departments d ON e.department_id = d.id;", "Join two sample tables and display a person's name with their department."),
        ],
        "quiz": [
            ("Which command retrieves data?", ["SELECT", "INSERT", "DELETE", "DROP"], "A"),
            ("Which clause filters rows?", ["GROUP BY", "WHERE", "ORDER BY", "JOIN"], "B"),
            ("Which function calculates an average?", ["COUNT", "SUM", "AVG", "MAX"], "C"),
            ("Which clause groups records?", ["GROUP BY", "WHERE", "VALUES", "SET"], "A"),
            ("Which operation combines related tables?", ["JOIN", "SORT", "PRINT", "LOOP"], "A"),
        ],
    },
    "pandas": {
        "title": "Pandas for Data Analysis", "level": "Beginner", "duration": "3–4 hours",
        "modules": [
            ("Series & DataFrames", "Understand the basic Pandas structures used for tabular data.", "import pandas as pd\ndf = pd.DataFrame({'Name':['A','B'], 'Score':[80,90]})", "Create a DataFrame containing five students and their marks."),
            ("Reading & Inspecting Data", "Learn to load CSV data and inspect rows, columns, types and missing values.", "df = pd.read_csv('data.csv')\nprint(df.head())", "Load a CSV and display its first five rows and column names."),
            ("Cleaning Data", "Handle missing values, duplicates and inconsistent text values.", "df = df.drop_duplicates()\ndf['Name'] = df['Name'].str.strip()", "Remove duplicate rows and clean whitespace from a text column."),
            ("Filtering & Analysis", "Filter records, select columns and calculate useful statistics.", "result = df[df['Score'] >= 70]", "Filter students scoring 70 or above and calculate their average score."),
        ],
        "quiz": [
            ("Which library provides DataFrame?", ["NumPy", "Pandas", "Matplotlib", "Flask"], "B"),
            ("Which function reads CSV?", ["read_csv", "load_csv", "open_csv", "csv_read"], "A"),
            ("Which method removes duplicates?", ["drop_duplicates", "remove_rows", "unique_rows", "delete_duplicates"], "A"),
            ("Which attribute gives column names?", ["df.columns", "df.names", "df.fields", "df.headers"], "A"),
            ("Which method shows the first rows?", ["tail", "head", "first", "top"], "B"),
        ],
    },
    "machine learning": {
        "title": "Machine Learning Fundamentals", "level": "Beginner", "duration": "4–5 hours",
        "modules": [
            ("ML Concepts", "Understand supervised, unsupervised and reinforcement learning at a basic level.", "X = [[1], [2], [3]]\ny = [2, 4, 6]", "Classify a simple real-world problem as supervised or unsupervised learning."),
            ("Data Preparation", "Learn features, labels, train-test split and basic preprocessing.", "from sklearn.model_selection import train_test_split\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)", "Identify the features and target variable in a student performance dataset."),
            ("Model Training", "Understand fitting a model and making predictions.", "model.fit(X_train, y_train)\npredictions = model.predict(X_test)", "Train a simple regression or classification model on a small dataset."),
            ("Evaluation", "Learn why accuracy and other evaluation metrics are important.", "accuracy = (predictions == y_test).mean()", "Compare two model results and explain which one performs better and why."),
        ],
        "quiz": [
            ("What is a feature?", ["Input variable", "Final report", "Password", "Output format"], "A"),
            ("Which learning type uses labelled data?", ["Supervised", "Unsupervised", "Random", "Manual"], "A"),
            ("What does fit() generally do?", ["Deletes data", "Trains the model", "Prints data", "Creates a database"], "B"),
            ("Why split train and test data?", ["To test generalization", "To increase file size", "To remove labels", "To rename columns"], "A"),
            ("Accuracy is mainly used for?", ["Measuring predictions", "Sorting files", "Creating folders", "Parsing PDFs"], "A"),
        ],
    },
    "java": {
        "title": "Java Programming Fundamentals", "level": "Beginner", "duration": "4–5 hours",
        "modules": [
            ("Java Basics", "Learn classes, main method, variables and primitive data types.", "public class Main {\n  public static void main(String[] args) {\n    int age = 20;\n  }\n}", "Create a Java program that stores and prints a student's name and marks."),
            ("Conditions & Loops", "Use if/else, switch and loops to control program flow.", "for(int i=1; i<=5; i++){\n    System.out.println(i);\n}", "Print the first ten even numbers using a loop."),
            ("Methods & Arrays", "Create reusable methods and work with arrays.", "static int add(int a, int b){\n    return a+b;\n}", "Write a method that returns the largest value in an integer array."),
            ("OOP Basics", "Understand classes, objects, constructors and encapsulation.", "class Student {\n    String name;\n}", "Create a Student class with two properties and one method."),
        ],
        "quiz": [
            ("Which method is the entry point of a Java program?", ["start()", "main()", "run()", "begin()"], "B"),
            ("Which keyword creates a class?", ["class", "object", "define", "struct"], "A"),
            ("Which concept hides internal data?", ["Encapsulation", "Compilation", "Iteration", "Casting"], "A"),
            ("Which structure repeats code?", ["Loop", "Package", "Import", "Class"], "A"),
            ("An object is an instance of a...", ["Method", "Class", "Loop", "Variable"], "B"),
        ],
    },
    "javascript": {
        "title": "JavaScript Fundamentals", "level": "Beginner", "duration": "3–4 hours",
        "modules": [
            ("JavaScript Basics", "Learn variables, data types and operators.", "const name = 'Alex';\nlet age = 20;", "Create variables for a user's name, age and course."),
            ("Conditions & Functions", "Use conditions and functions to build reusable logic.", "function add(a, b) { return a + b; }", "Create a function that checks whether a number is even."),
            ("Arrays & Objects", "Store structured data using arrays and objects.", "const student = {name:'A', score:85};", "Create an array of three student objects."),
            ("DOM Basics", "Understand how JavaScript can interact with HTML elements.", "document.getElementById('title').textContent = 'Hello';", "Change the text of an HTML element using JavaScript."),
        ],
        "quiz": [
            ("Which keyword declares a constant?", ["const", "fixed", "constant", "let"], "A"),
            ("Which method selects an element by ID?", ["getElementById", "selectId", "findId", "idElement"], "A"),
            ("Which structure stores key-value pairs?", ["Object", "Loop", "Function", "String"], "A"),
            ("Which keyword defines a function traditionally?", ["function", "def", "fun", "method"], "A"),
            ("Which symbol is commonly used for strict equality?", ["=", "==", "===", "=>"], "C"),
        ],
    },
}


def normalize_course_key(skill):
    s = clean_skill(skill)
    aliases = {
        "python 3": "python", "python programming": "python",
        "sql server": "sql", "mysql": "sql", "mysql workbench": "sql",
        "pandas library": "pandas", "pandas dataframe": "pandas",
        "ml": "machine learning", "machinelearning": "machine learning",
        "java programming": "java", "javascript programming": "javascript",
        "js": "javascript",
    }
    if s in COURSE_TEMPLATES:
        return s
    if s in aliases:
        return aliases[s]
    for key in COURSE_TEMPLATES:
        if key in s or s in key:
            return key
    return "generic"


def build_generic_course(skill):
    title = skill.title()
    return {
        "title": f"{title} Skill Development",
        "level": "Beginner",
        "duration": "2–3 hours",
        "modules": [
            (f"Introduction to {title}", f"Understand the purpose, terminology and common uses of {title}.", f"Skill: {title}\nGoal: understand the fundamentals", f"Write five important concepts or uses of {title}."),
            (f"Core Concepts of {title}", f"Study the fundamental concepts and workflow used when working with {title}.", f"{title} workflow → Input → Process → Output", f"Describe the basic workflow of {title} in your own words."),
            (f"Practical {title}", f"Apply the skill to a small practical task related to your career goal.", f"Practice task: Build a small example using {title}.", f"Create one small practical example using {title}."),
            (f"Job-Oriented Practice", f"Connect {title} with a real job requirement and identify what you need to practise further.", f"Job Skill: {title}\nPractice → Test → Improve", f"Find one job-related task where {title} would be useful and explain it."),
        ],
        "quiz": [
            (f"What is the main goal of learning {title}?", ["Build practical skill", "Avoid practice", "Delete data", "Only memorize terms"], "A"),
            (f"Which approach is best for improving {title}?", ["Practice regularly", "Never practise", "Skip examples", "Only read titles"], "A"),
            (f"Where can {title} be useful?", ["Real projects", "Only games", "Only passwords", "Nowhere"], "A"),
            ("What should you do after learning a concept?", ["Apply it", "Forget it", "Delete it", "Avoid examples"], "A"),
            ("What helps confirm your understanding?", ["Practice and assessment", "Skipping all tasks", "Only opening the page", "No activity"], "A"),
        ],
    }


def get_course_for_skill(skill):
    key = normalize_course_key(skill)
    if key == "generic":
        return f"generic::{clean_skill(skill)}", build_generic_course(skill)
    return key, COURSE_TEMPLATES[key]


def certificate_pdf_bytes(user_name, course_title, skill, score):
    if not HAS_REPORTLAB:
        return None
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    certificate_id = f"CMAI-{hashlib.sha256((user_name + course_title + skill).encode()).hexdigest()[:10].upper()}"
    c.setStrokeColor(colors.HexColor("#2E5AAC"))
    c.setLineWidth(4)
    c.rect(28, 28, width - 56, height - 56)
    c.setLineWidth(1)
    c.rect(40, 40, width - 80, height - 80)
    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height - 105, "CERTIFICATE OF COMPLETION")
    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2, height - 135, "CareerMatch AI • Skill Development Program")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 195, "This certificate is proudly presented to")
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 25)
    c.drawCentredString(width / 2, height - 235, user_name)
    c.setFillColor(colors.HexColor("#374151"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 275, "for successfully completing the course")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 310, course_title)
    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2, height - 340, f"Skill: {skill.title()}   •   Final Assessment: {score}%")
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, 85, f"Certificate ID: {certificate_id}   •   Completion Date: {pd.Timestamp.now().strftime('%d %B %Y')}")
    c.save()
    buffer.seek(0)
    return buffer.getvalue(), certificate_id


def show_skill_course_center(resource_items):
    if not resource_items:
        return

    st.divider()
    st.subheader("🎓 Skill Courses & Certification")
    st.write(
        "Every missing skill identified for your Top 5 job recommendations has a related "
        "course. Complete the modules, pass the assessment, and download your certificate."
    )

    # Unique job-skill pairs keep the course tied to the exact recommendation and gap.
    unique_items = []
    seen = set()
    for job_title, skill in resource_items:
        pair = (job_title, clean_skill(skill))
        if pair not in seen:
            seen.add(pair)
            unique_items.append(pair)

    labels = [f"{job} → {skill.title()}" for job, skill in unique_items]
    selected_label = st.selectbox(
        "📚 Select a required skill to start its course",
        labels,
        key="skill_course_selector"
    )
    selected_index = labels.index(selected_label)
    job_title, skill = unique_items[selected_index]
    course_key, course = get_course_for_skill(skill)
    state_key = f"{job_title}::{skill}::{course_key}"

    st.markdown(f"### 🎯 {course['title']}")
    st.caption(f"Recommended for: {job_title}  •  Required skill: {skill.title()}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Level", course["level"])
    c2.metric("Modules", len(course["modules"]))
    c3.metric("Duration", course["duration"])

    if state_key not in st.session_state.course_progress:
        st.session_state.course_progress[state_key] = set()
    completed = st.session_state.course_progress[state_key]

    progress = len(completed) / len(course["modules"])
    st.progress(progress)
    st.caption(f"Course Progress: {len(completed)}/{len(course['modules'])} modules completed")

    for i, (title, lesson, example, practice) in enumerate(course["modules"]):
        done = i in completed
        with st.expander(f"{'✅' if done else '📘'} Module {i+1}: {title}", expanded=(i == 0 and not done)):
            st.markdown("**Lesson**")
            st.write(lesson)
            st.markdown("**Example**")
            st.code(example, language="text")
            st.markdown("**Practice Task**")
            st.write(practice)
            if done:
                st.success("Module completed.")
            else:
                if st.button("✅ Mark Module Complete", key=f"complete_{hashlib.md5((state_key+str(i)).encode()).hexdigest()}", use_container_width=True):
                    completed.add(i)
                    st.session_state.course_progress[state_key] = completed
                    st.rerun()

    if len(completed) == len(course["modules"]):
        st.success("🎉 All modules completed. You can now take the final assessment.")
        quiz_state_key = state_key + "::quiz"
        score_state_key = state_key + "::score"

        st.markdown("### 📝 Final Skill Assessment")
        answers = []
        for i, (question, options, correct) in enumerate(course["quiz"]):
            answers.append(st.radio(question, options, index=None, key=f"quiz_{hashlib.md5((state_key+str(i)).encode()).hexdigest()}"))

        if st.button("🎯 Submit Assessment", key=f"submit_{hashlib.md5(state_key.encode()).hexdigest()}", type="primary", use_container_width=True):
            if any(answer is None for answer in answers):
                st.warning("Please answer all questions before submitting.")
            else:
                score = sum(1 for answer, (_, options, correct) in zip(answers, course["quiz"]) if answer == options[ord(correct)-65])
                percent = int(score / len(course["quiz"]) * 100)
                st.session_state.course_quiz_results[quiz_state_key] = score >= 4
                st.session_state.course_quiz_results[score_state_key] = percent
                if score >= 4:
                    st.success(f"🏆 Passed: {score}/5 ({percent}%). Certificate unlocked!")
                else:
                    st.warning(f"Score: {score}/5 ({percent}%). You need at least 4/5. Review the modules and try again.")

        if st.session_state.course_quiz_results.get(quiz_state_key, False):
            score = st.session_state.course_quiz_results.get(score_state_key, 80)
            st.markdown("### 🏆 Skill Course Completed")
            st.success(f"You completed **{course['title']}** for **{skill.title()}** with **{score}%**.")
            certificate_name = st.text_input("👤 Name for Certificate", key=f"certificate_name_{hashlib.md5(state_key.encode()).hexdigest()}")
            if not HAS_REPORTLAB:
                st.error("Certificate generation requires reportlab. Add `reportlab` to requirements.txt.")
            elif st.button("📜 Generate Certificate", key=f"certificate_{hashlib.md5(state_key.encode()).hexdigest()}", use_container_width=True):
                if not certificate_name.strip():
                    st.warning("Please enter your name first.")
                else:
                    pdf_data, certificate_id = certificate_pdf_bytes(certificate_name.strip(), course["title"], skill, score)
                    st.session_state.course_certificates[state_key] = (pdf_data, certificate_id)
                    st.success(f"Certificate generated successfully. ID: {certificate_id}")

            certificate = st.session_state.course_certificates.get(state_key)
            if certificate:
                pdf_data, certificate_id = certificate
                st.download_button(
                    "📥 Download / Print Certificate",
                    data=pdf_data,
                    file_name=f"CareerMatch_{clean_skill(skill).replace(' ', '_')}_Certificate.pdf",
                    mime="application/pdf",
                    key=f"download_{hashlib.md5((state_key+'download').encode()).hexdigest()}",
                    use_container_width=True
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
# LEARNING RESOURCES — YOUTUBE + COURSE FOR EVERY GAP
# =====================================================

if recommendations is not None and not recommendations.empty:

    st.divider()
    st.subheader("📚 Skill Improvement Resources")
    st.write(
        "For every missing skill in your Top 5 recommendations, CareerMatch AI provides "
        "a YouTube learning link and an in-app skill course with assessment and certification."
    )

    course_resource_items = []

    for job_number, (_, resource_row) in enumerate(
        recommendations.iterrows(),
        start=1
    ):
        required = extract_required_skills(resource_row["job_skill_set"])
        candidate = set(combined_skill_set)
        resource_missing = sorted(required.difference(candidate))

        with st.expander(
            f"💼 Job {job_number}: {resource_row['job_title']} — Skill Resources",
            expanded=False
        ):
            if resource_missing:
                st.caption(
                    f"{len(resource_missing)} skill(s) to improve for this job"
                )

                for missing_skill in resource_missing:
                    course_resource_items.append(
                        (resource_row["job_title"], missing_skill)
                    )

                    youtube_url = youtube_search_url(missing_skill)
                    course_key, course_info = get_course_for_skill(missing_skill)

                    st.markdown(f"### 🛠️ {missing_skill.title()}")
                    st.write(
                        f"🎓 **Related Course:** {course_info['title']} "
                        f"• {course_info['duration']}"
                    )
                    r1, r2 = st.columns(2)
                    with r1:
                        st.link_button(
                            f"▶️ Learn {missing_skill.title()} on YouTube",
                            youtube_url,
                            use_container_width=True
                        )
                    with r2:
                        st.info(
                            "🎓 Select this skill in the Course Completion Center below "
                            "to start the course and earn a certificate."
                        )
                    st.markdown("---")
            else:
                st.success("🎉 No missing skills for this job. You are ready for this skill set!")

    if course_resource_items:
        show_skill_course_center(course_resource_items)
    else:
        st.success(
            "🎉 You currently have all directly required skills for the Top 5 recommendations, "
            "so there are no skill courses to complete."
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
