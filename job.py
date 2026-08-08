import streamlit as st
import pandas as pd
import numpy as np
import pdfplumber
import plotly.graph_objects as go
import math
import io
from sentence_transformers import SentenceTransformer, util

# ==========================================
# 1. UI THEME & BRANDING (CSS INJECTION)
# ==========================================
st.set_page_config(page_title="UNOJOBS - Enterprise Hiring", layout="wide", page_icon="🔵")

# Custom CSS for "Faint Blue and White" Theme
st.markdown("""
    <style>
    /* 1. Main Background - Faint Blue */
    .stApp {
        background-color: #F4F8FB;
    }
    
    /* 2. Global Text Color - Royal Blue */
    .stApp, p, h1, h2, h3, h4, h5, h6, span, div, label, .stMarkdown {
        color: #2563EB !important; /* Royal Blue */
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* 3. Header Styling for UNOJOBS */
    .uno-header {
        font-size: 60px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 20px;
    }
    .uno-blue { color: #2563EB; }
    .uno-cyan { color: #06B6D4; }
    .uno-sub { font-size: 20px; font-weight: 400; color: #3B82F6; letter-spacing: 1px;}

    /* 4. Button Styling */
    div.stButton > button {
        background-color: #2563EB;
        color: white !important; /* Keep button text white for contrast */
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
    }
    div.stButton > button:hover {
        background-color: #1D4ED8;
        color: white !important;
    }
    
    /* 5. Input Fields Styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        color: #2563EB !important; /* Text inside inputs */
        background-color: #FFFFFF;
        border: 1px solid #93C5FD;
        border-radius: 6px;
    }
    
    /* 6. Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #E0F2FE; /* Very light blue sidebar */
    }
    </style>
    
    <div class="uno-header">
        <span class="uno-blue">uno</span><span class="uno-cyan">jobs</span>
        <div class="uno-sub">Top hires with less effort</div>
    </div>
    """, unsafe_allow_html=True)
# ==========================================
# 2. KEYWORD BANKS (Shared Assets)
# ==========================================
# To hit 50+ keywords per role, we build shared lists and combine them.

COMMON_SOFT_SKILLS = [
    "Communication", "Teamwork", "Problem Solving", "Critical Thinking", "Adaptability", 
    "Time Management", "Leadership", "Collaboration", "Creativity", "Emotional Intelligence",
    "Mentorship", "Ownership", "Accountability", "Presentation", "Negotiation", "Conflict Resolution"
]

COMMON_ENG_TOOLS = [
    "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence", "Slack", "Zoom", "Teams",
    "Agile", "Scrum", "Kanban", "Sprint Planning", "Linear", "Asana", "Trello", "Notion",
    "VS Code", "IntelliJ", "Eclipse", "Sublime Text", "Linux", "Unix", "Bash", "Shell"
]

# ==========================================
# 3. ENTERPRISE ROLE DATABASE (Expanded)
# ==========================================

ROLES_DB = {
    # --- ENGINEERING ---
    "Backend Engineer (General)": {
        "weights": {"S": 0.20, "E": 0.15, "P": 0.15, "A": 0.10, "D": 0.10, "T": 0.10, "C": 0.05, "J": 0.05, "L": 0.05, "SAL": 0.05},
        "y_ref": 5,
        "definitions": {
            "S": ["Python", "Java", "Node.js", "Golang", "C++", "C#", ".NET", "Rust", "Scala", "PHP", "Ruby", 
                  "Rest API", "GraphQL", "gRPC", "WebSockets", "SOAP", "Microservices", "Serverless", "Lambda",
                  "Django", "Flask", "FastAPI", "Spring Boot", "Spring MVC", "Hibernate", "Express.js", "NestJS",
                  "Ruby on Rails", "Laravel", "Symfony", "ASP.NET Core", "Entity Framework"] + COMMON_SOFT_SKILLS,
            "A": ["System Design", "Distributed Systems", "Event Driven", "CAP Theorem", "Load Balancing", "Caching", 
                  "CDN", "Scalability", "High Availability", "Fault Tolerance", "Sharding", "Replication", 
                  "Message Queues", "Kafka", "RabbitMQ", "ActiveMQ", "SQS", "Pub/Sub", "Design Patterns", "Solid Principles"],
            "D": ["SQL", "NoSQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra", "Elasticsearch", "DynamoDB",
                  "MariaDB", "Oracle", "SQL Server", "CockroachDB", "Neo4j", "Database Design", "Normalization", "Indexing"],
            "T": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "Ansible", "Jenkins", "CircleCI", 
                  "TravisCI", "GitHub Actions", "Prometheus", "Grafana", "New Relic", "Datadog", "Splunk"] + COMMON_ENG_TOOLS,
            "C": ["Unit Testing", "Integration Testing", "TDD", "BDD", "Clean Code", "Code Review", "Documentation", 
                  "PyTest", "JUnit", "Mocha", "Chai", "Jest", "SonarQube", "OWASP"]
        }
    },
    
    "Frontend Engineer (React/Web)": {
        "weights": {"S": 0.25, "E": 0.15, "P": 0.15, "A": 0.10, "D": 0.05, "T": 0.10, "C": 0.05, "J": 0.05, "L": 0.05, "SAL": 0.05},
        "y_ref": 4,
        "definitions": {
            "S": ["React.js", "Angular", "Vue.js", "Svelte", "Next.js", "Nuxt.js", "Gatsby", "Remix", 
                  "TypeScript", "JavaScript", "ES6+", "HTML5", "CSS3", "Sass", "Less", "Tailwind CSS", 
                  "Bootstrap", "Material UI", "Chakra UI", "Ant Design", "Styled Components", "Emotion",
                  "Redux", "MobX", "Recoil", "Zustand", "Context API", "React Query", "Apollo Client"] + COMMON_SOFT_SKILLS,
            "A": ["Component Design", "State Management", "Micro Frontends", "Server Side Rendering (SSR)", 
                  "Static Site Generation (SSG)", "Client Side Rendering (CSR)", "Progressive Web Apps (PWA)", 
                  "Web Performance", "Core Web Vitals", "SEO", "Security", "XSS", "CSRF"],
            "D": ["JSON", "XML", "REST Integration", "GraphQL", "Axios", "Fetch API", "WebSockets", "Local Storage", 
                  "Session Storage", "Cookies", "IndexedDB", "Service Workers"],
            "T": ["Webpack", "Vite", "Rollup", "Parcel", "Babel", "NPM", "Yarn", "PNPM", "Figma", "Adobe XD", 
                  "Zeplin", "Storybook", "Chrome DevTools", "Lighthouse"] + COMMON_ENG_TOOLS,
            "C": ["Accessibility", "WCAG", "Responsive Design", "Cross-Browser Compatibility", "Mobile First", 
                  "Jest", "React Testing Library", "Cypress", "Playwright", "End-to-End Testing", "Linting", "Prettier"]
        }
    },

    "Data Scientist": {
        "weights": {"S": 0.20, "E": 0.15, "P": 0.15, "A": 0.05, "D": 0.20, "T": 0.05, "C": 0.05, "J": 0.05, "L": 0.05, "SAL": 0.05},
        "y_ref": 4,
        "definitions": {
            "S": ["Python", "R", "SQL", "Julia", "Scala", "Java", "MATLAB", "SAS",
                  "Machine Learning", "Deep Learning", "Natural Language Processing (NLP)", "Computer Vision", 
                  "Reinforcement Learning", "Generative AI", "LLMs", "Transformers", "BERT", "GPT",
                  "Regression", "Classification", "Clustering", "Dimensionality Reduction", "Ensemble Methods",
                  "Random Forest", "Gradient Boosting", "XGBoost", "LightGBM", "CatBoost", "Scikit-learn"] + COMMON_SOFT_SKILLS,
            "A": ["Model Deployment", "MLOps", "Model Serving", "Inference Pipelines", "Scalable Training", 
                  "Data Pipelines", "Feature Store", "Experiment Tracking", "Model Monitoring", "Drift Detection"],
            "D": ["Pandas", "NumPy", "SciPy", "Statsmodels", "Data Wrangling", "Feature Engineering", 
                  "EDA", "Data Cleaning", "Data Mining", "Big Data", "Spark", "Hadoop", "Hive", "Dask", "Ray"],
            "T": ["Jupyter", "Colab", "TensorFlow", "PyTorch", "Keras", "Fastai", "Hugging Face", "OpenCV", 
                  "Spacy", "NLTK", "Gensim", "AWS SageMaker", "Azure ML", "Google AI Platform", "Databricks", 
                  "Tableau", "Power BI", "Matplotlib", "Seaborn", "Plotly", "Streamlit"] + COMMON_ENG_TOOLS,
            "C": ["Model Evaluation", "Cross-Validation", "A/B Testing", "Hypothesis Testing", "Statistical Significance",
                  "Bias and Fairness", "Explainability", "SHAP", "LIME", "Reproducibility"]
        }
    },

    # --- MANAGEMENT ---
    "Product Manager (Tech)": {
        "weights": {"S": 0.15, "E": 0.20, "P": 0.20, "A": 0.15, "D": 0.10, "T": 0.05, "C": 0.05, "J": 0.05, "L": 0.05, "SAL": 0.00},
        "y_ref": 6,
        "definitions": {
            "S": ["Product Strategy", "Product Roadmap", "Feature Prioritization", "User Stories", "Acceptance Criteria",
                  "Agile", "Scrum", "Kanban", "Sprint Planning", "Backlog Grooming", "Retrospectives",
                  "Market Research", "Competitor Analysis", "User Research", "Customer Interviews", "Personas",
                  "Go-to-Market Strategy", "Product Launch", "Pricing Strategy", "Growth Hacking"] + COMMON_SOFT_SKILLS,
            "A": ["Platform Thinking", "Tech Stack Understanding", "API Economy", "Scalability", "Technical Debt",
                  "System Architecture Basics", "Mobile App Lifecycle", "SaaS Metrics", "Cloud Concepts"],
            "D": ["SQL", "Data Analytics", "Funnel Analysis", "Cohort Analysis", "Retention Analysis", "Churn Rate",
                  "A/B Testing", "Experimentation", "KPIs", "OKRs", "North Star Metric", "Google Analytics", 
                  "Mixpanel", "Amplitude", "Heap", "Looker", "Tableau"],
            "T": ["Jira", "Confluence", "Linear", "Asana", "Monday.com", "Trello", "Notion", "Airtable",
                  "Figma", "Sketch", "InVision", "Miro", "Mural", "Lucidchart", "Slack", "Zoom", "Teams"],
            "C": ["PRD Writing", "Requirement Gathering", "Stakeholder Management", "Cross-functional Collaboration",
                  "Public Speaking", "Storytelling", "Influence without Authority", "Documentation"]
        }
    }
}

# ==========================================
# 4. SCORING ENGINE (Updated with Salary)
# ==========================================

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

class EnterpriseScorer:
    
    @staticmethod
    def calculate(resume_text, role_config, cand_data):
        W = role_config["weights"]
        D = role_config["definitions"]
        
        # 1. Experience (Mapped from Dropdown)
        y_actual = cand_data.get('years_exp', 0)
        y_ref = role_config['y_ref']
        score_e = min(math.log(1 + y_actual) / math.log(1 + y_ref), 1.0) if y_actual > 0 else 0.0
        
        # 2. Salary Feasibility (New)
        prev_salary = cand_data.get('prev_salary', 0)
        max_budget = cand_data.get('max_budget', 0)
        
        if max_budget == 0:
            score_sal = 1.0 # No budget constraint set
        elif prev_salary <= max_budget:
            score_sal = 1.0 # Within budget
        elif prev_salary <= (max_budget * 1.15):
            score_sal = 0.7 # Slightly over (Negotiable)
        elif prev_salary <= (max_budget * 1.30):
            score_sal = 0.4 # Over budget
        else:
            score_sal = 0.0 # Too expensive
            
        # 3. Joining
        days = cand_data.get('notice_days', 90)
        if days <= 15: score_j = 1.0
        elif days <= 30: score_j = 0.8
        elif days <= 60: score_j = 0.5
        elif days <= 90: score_j = 0.2
        else: score_j = 0.0
        
        # 4. Location
        job_loc = cand_data.get('job_loc', '').lower()
        cand_loc = cand_data.get('cand_loc', '').lower()
        mode = cand_data.get('work_mode', 'Hybrid')
        relocate = cand_data.get('relocate', False)
        
        if mode == "Remote": score_l = 1.0
        elif job_loc in cand_loc: score_l = 1.0
        elif relocate: score_l = 0.5
        else: score_l = 0.0
            
        # 5. Semantic Components
        sem_scores = {}
        for comp in ['S', 'A', 'D', 'T', 'C']:
            keywords = D.get(comp, [])
            if not keywords:
                sem_scores[comp] = 0.0
                continue
                
            resume_emb = model.encode(resume_text)
            kw_text = ", ".join(keywords)
            kw_emb = model.encode(kw_text)
            cos_sim = util.cos_sim(resume_emb, kw_emb).item()
            
            hits = sum(1 for k in keywords if k.lower() in resume_text.lower())
            density = min(hits / (len(keywords) * 0.1), 1.0) # Adjusted density threshold for 50+ keywords
            
            sem_scores[comp] = (cos_sim * 0.6) + (density * 0.4)
            sem_scores[comp] = max(0.0, min(sem_scores[comp], 1.0))

        # 6. Project Depth (Heuristic)
        p_keywords = ["developed", "deployed", "managed", "created", "built", "reduced", "increased", "revenue", "users", "optimization", "lead", "architected"]
        p_hits = sum(1 for k in p_keywords if k in resume_text.lower())
        score_p = min(p_hits / 6, 1.0)
        
        # FINAL SUM
        final_score = (
            (W['S'] * sem_scores['S']) +
            (W['E'] * score_e) +
            (W['P'] * score_p) +
            (W['A'] * sem_scores['A']) +
            (W['D'] * sem_scores['D']) +
            (W['T'] * sem_scores['T']) +
            (W['C'] * sem_scores['C']) +
            (W['J'] * score_j) +
            (W['L'] * score_l) +
            (W.get('SAL', 0) * score_sal)
        )
        
        # Normalize in case weights don't sum to exactly 1
        total_weight = sum(W.values())
        final_score = final_score / total_weight if total_weight > 0 else 0
        
        return round(final_score, 3), {
            "Skills": sem_scores['S'], "Exp": score_e, "Projects": score_p, 
            "Arch": sem_scores['A'], "Data": sem_scores['D'], "Tools": sem_scores['T'], 
            "Quality": sem_scores['C'], "Notice": score_j, "Loc": score_l, "Salary": score_sal
        }

# ==========================================
# 5. UI INTERFACE (Updated)
# ==========================================

st.sidebar.header("🔧 Configuration")
app_mode = st.sidebar.radio("Mode", ["Single Audit", "Batch Screening"])

# Mappings for Experience Dropdown
EXP_MAP = {
    "Fresher (0 Years)": 0.0,
    "Internship Only": 0.5,
    "1 Year": 1.0,
    "2 Years": 2.0,
    "3 Years": 3.0,
    "4 Years": 4.0,
    "5 Years": 5.0,
    "6-8 Years": 7.0,
    "9-12 Years": 10.0,
    "12+ Years": 15.0
}

if app_mode == "Single Audit":
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 1. Job Details")
        role_select = st.selectbox("Job Role", list(ROLES_DB.keys()))
        config = ROLES_DB[role_select]
        
        st.markdown("---")
        st.markdown("### 2. Constraints")
        job_loc = st.text_input("Job Location", "Bangalore")
        max_budget = st.number_input("Max Budget (LPA)", 0, 100, 12, help="Max Salary you can offer")
        work_mode = st.selectbox("Work Mode", ["Hybrid", "Onsite", "Remote"])
        
    with col2:
        st.markdown("### 3. Candidate Data")
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")
        
        c1, c2, c3 = st.columns(3)
        # Dropdown for Experience
        c_exp_str = c1.selectbox("Experience Level", list(EXP_MAP.keys()), index=2)
        c_exp = EXP_MAP[c_exp_str]
        
        c_notice = c2.number_input("Notice Period (Days)", 0, 90, 30)
        c_prev_sal = c3.number_input("Prev Salary (LPA)", 0, 100, 8)
        
        c4, c5 = st.columns(2)
        c_city = c4.text_input("Current City", "Pune")
        c_reloc = c5.checkbox("Willing to Relocate?", value=True)

    if st.button("🚀 Analyze Candidate"):
        if uploaded_file:
            with st.spinner("Analyzing against 50+ parameters..."):
                with pdfplumber.open(uploaded_file) as pdf:
                    text = "".join([p.extract_text() or "" for p in pdf.pages])
                
                cand_data = {
                    "years_exp": c_exp, "notice_days": c_notice, 
                    "job_loc": job_loc, "cand_loc": c_city, 
                    "work_mode": work_mode, "relocate": c_reloc,
                    "prev_salary": c_prev_sal, "max_budget": max_budget
                }
                
                score, details = EnterpriseScorer.calculate(text, config, cand_data)
                
                # Header Result
                st.markdown(f"""
                <div style="background-color: white; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #e0e0e0;">
                    <h2 style='color: #475569; margin:0;'>Match Score</h2>
                    <h1 style='color: #2563EB; font-size: 4em; margin:0;'>{score*100:.1f}%</h1>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("")
                
                # Radar Chart
                fig = go.Figure(data=go.Scatterpolar(
                    r=list(details.values()),
                    theta=list(details.keys()),
                    fill='toself',
                    fillcolor='rgba(37, 99, 235, 0.2)',
                    line=dict(color='#2563EB')
                ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed Breakdown
                st.subheader("📊 Factor Analysis")
                audit_data = []
                for k, v in details.items():
                    status = "✅ Strong" if v > 0.7 else "⚠️ Average" if v > 0.4 else "❌ Weak"
                    audit_data.append({"Factor": k, "Score": f"{v:.2f}", "Status": status})
                
                st.table(pd.DataFrame(audit_data))
                
        else:
            st.warning("Please upload a resume.")

elif app_mode == "Batch Screening":
    st.title("Batch Processor")
    # Batch logic remains similar, can be expanded if needed
    st.info("Batch mode uses the same underlying logic as Single Audit.")