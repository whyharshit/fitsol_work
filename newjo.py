import streamlit as st
import pandas as pd
import numpy as np
import pdfplumber
import plotly.graph_objects as go
import plotly.express as px
import math
import time
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer, util

# ==========================================
# 0. CONFIG & PAGE SETUP
# ==========================================
st.set_page_config(page_title="UNOJOBS - Enterprise Edition", layout="wide", page_icon="💎")

# College Database
TIER_1_COLLEGES = [
    "IIT", "Indian Institute of Technology", "BITS Pilani", "NIT", "National Institute of Technology", 
    "IIIT", "Indian Institute of Information Technology", "IIM", "Indian Institute of Management",
    "Delhi Technological University", "DTU", "NSIT", "Anna University", "Jadavpur University"
]

TIER_2_COLLEGES = [
    "VIT", "Vellore Institute of Technology", "SRM", "Manipal", "MIT Manipal", "Thapar", 
    "RV College", "PES University", "BMS College", "Ramaiah", "Symbiosis", "Amity", "Lovely Professional University"
]

# ==========================================
# 1. PREMIUM UI THEME (ENHANCED CSS)
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ===== BASE THEME ===== */
.stApp {
    background: linear-gradient(145deg, #0a0f1a 0%, #111827 50%, #1a1f2e 100%);
    font-family: 'Inter', sans-serif;
}

/* ===== TYPOGRAPHY ===== */
h1, h2, h3, h4, h5, h6, p, div, span, label {
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ===== ANIMATED GRADIENT HEADER ===== */
.hero-container {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 50%, rgba(236, 72, 153, 0.1) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 40px;
    margin-bottom: 30px;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(20px);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.hero-container::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 50%);
    animation: pulse 8s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.8; }
}

.brand-title {
    font-size: 56px;
    font-weight: 800;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -2px;
    position: relative;
    z-index: 1;
    text-align: center;
    margin-bottom: 8px;
}

.brand-subtitle {
    color: #94a3b8 !important;
    font-size: 18px;
    font-weight: 400;
    text-align: center;
    position: relative;
    z-index: 1;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.badge-row {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-top: 20px;
    position: relative;
    z-index: 1;
}

.tech-badge {
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.3);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    color: #a5b4fc !important;
    font-weight: 500;
}

/* ===== GLASSMORPHISM CARDS ===== */
.glass-card {
    background: rgba(30, 41, 59, 0.5);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.glass-card:hover {
    transform: translateY(-4px);
    border-color: rgba(99, 102, 241, 0.5);
    box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
}

.glass-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
}

/* ===== METRIC CARDS ===== */
.metric-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    padding: 28px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4);
}

.metric-card.score-high {
    border-color: rgba(52, 211, 153, 0.4);
    box-shadow: 0 0 40px rgba(52, 211, 153, 0.15);
}

.metric-card.score-medium {
    border-color: rgba(251, 191, 36, 0.4);
    box-shadow: 0 0 40px rgba(251, 191, 36, 0.15);
}

.metric-card.score-low {
    border-color: rgba(248, 113, 113, 0.4);
    box-shadow: 0 0 40px rgba(248, 113, 113, 0.15);
}

.metric-value {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 4px;
}

.metric-label {
    color: #64748b !important;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
}

.metric-icon {
    font-size: 24px;
    margin-bottom: 12px;
    display: block;
}

/* ===== SECTION HEADERS ===== */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.section-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}

.section-title {
    font-size: 18px;
    font-weight: 700;
    color: #f1f5f9 !important;
    margin: 0;
}

/* ===== BUTTONS ===== */
div.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
    color: white !important;
    border: none;
    padding: 16px 32px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 15px;
    letter-spacing: 0.5px;
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
}

div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px rgba(139, 92, 246, 0.5);
}

div.stButton > button:active {
    transform: translateY(0);
}

/* ===== INPUTS ===== */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div,
.stMultiSelect > div > div > div {
    background: rgba(15, 23, 42, 0.8) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    transition: all 0.2s ease;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

section[data-testid="stSidebar"] .stRadio > label {
    color: #e2e8f0 !important;
}

/* ===== CONSTRAINT BOX ===== */
.constraint-violation {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(185, 28, 28, 0.1));
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-left: 4px solid #ef4444;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 24px;
}

.constraint-violation h4 {
    color: #fca5a5 !important;
    margin: 0 0 8px 0;
    font-weight: 600;
}

.constraint-violation p {
    color: #fecaca !important;
    margin: 0;
    font-size: 14px;
}

/* ===== INSIGHT CARDS ===== */
.insight-card {
    background: rgba(30, 41, 59, 0.6);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border-left: 3px solid;
    transition: all 0.2s ease;
}

.insight-card:hover {
    background: rgba(30, 41, 59, 0.8);
    transform: translateX(4px);
}

.insight-card.positive { border-color: #34d399; }
.insight-card.warning { border-color: #fbbf24; }
.insight-card.negative { border-color: #f87171; }
.insight-card.info { border-color: #60a5fa; }

/* ===== PROGRESS RING (for scores) ===== */
.score-ring {
    position: relative;
    width: 120px;
    height: 120px;
    margin: 0 auto 16px;
}

/* ===== PERSONALIZATION INDICATOR ===== */
.personalization-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.2));
    border: 1px solid rgba(139, 92, 246, 0.3);
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 13px;
    color: #c4b5fd !important;
    font-weight: 500;
}

/* ===== FILE UPLOADER ===== */
.stFileUploader > div {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 2px dashed rgba(99, 102, 241, 0.3) !important;
    border-radius: 16px !important;
    padding: 32px !important;
    transition: all 0.3s ease;
}

.stFileUploader > div:hover {
    border-color: rgba(99, 102, 241, 0.6) !important;
    background: rgba(99, 102, 241, 0.05) !important;
}

/* ===== HIDE STREAMLIT BRANDING ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ===== CUSTOM SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.5);
}

::-webkit-scrollbar-thumb {
    background: rgba(99, 102, 241, 0.5);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(99, 102, 241, 0.7);
}

/* ===== ANIMATIONS ===== */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-in {
    animation: fadeInUp 0.5s ease-out forwards;
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.loading-shimmer {
    background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
}
</style>

<div class="hero-container">
    <div class="brand-title">UNOJOBS 💎</div>
    <div class="brand-subtitle">AI-Powered Strategic Hiring Engine</div>
    <div class="badge-row">
        <span class="tech-badge">🧠 GLMix Personalization</span>
        <span class="tech-badge">🎯 Thompson Sampling</span>
        <span class="tech-badge">⚡ Real-time Scoring</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 2. ROLES DATABASE
# ==========================================
ROLES_DB = {
    "Backend Engineer": {
        "weights": {"S": 0.40, "E": 0.12, "P": 0.10, "A": 0.10, "D": 0.10, "T": 0.06, "C": 0.05, "J": 0.03, "L": 0.02, "TIER": 0.02}, 
        "y_ref": 4,
        "definitions": {
            "S": ["Python", "Java", "Node.js", "Golang", "C++", "C#", "Rest API", "GraphQL", "Microservices", "Django", "Spring Boot", "Express.js", "System Design"],
            "A": ["Distributed Systems", "Load Balancing", "Caching", "Scalability", "High Availability", "Message Queues", "Kafka", "RabbitMQ", "Design Patterns"],
            "D": ["SQL", "NoSQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Database Design", "Indexing", "ORM"],
            "T": ["Docker", "Kubernetes", "AWS", "Azure", "Terraform", "Jenkins", "Git", "CI/CD", "Linux"],
            "C": ["Unit Testing", "Integration Testing", "TDD", "Clean Code", "Code Review", "Documentation"]
        }
    },
    "Frontend Engineer": {
        "weights": {"S": 0.45, "E": 0.10, "P": 0.10, "A": 0.06, "D": 0.06, "T": 0.10, "C": 0.06, "J": 0.03, "L": 0.02, "TIER": 0.02},
        "y_ref": 3,
        "definitions": {
            "S": ["React.js", "Angular", "Vue.js", "Next.js", "TypeScript", "JavaScript", "HTML5", "CSS3", "Redux", "Tailwind CSS", "Bootstrap"],
            "A": ["State Management", "SSR", "CSR", "Web Performance", "SEO", "Security", "Responsive Design", "PWA"],
            "D": ["JSON", "REST API Integration", "GraphQL", "Axios", "Fetch API", "Local Storage", "Cookies"],
            "T": ["Webpack", "Vite", "NPM", "Yarn", "Figma", "Adobe XD", "Chrome DevTools", "Git"],
            "C": ["Accessibility", "WCAG", "Cross-Browser Compatibility", "Jest", "Cypress", "Testing Library"]
        }
    },
    "Data Scientist": {
        "weights": {"S": 0.40, "E": 0.10, "P": 0.10, "A": 0.08, "D": 0.15, "T": 0.06, "C": 0.05, "J": 0.03, "L": 0.01, "TIER": 0.02},
        "y_ref": 4,
        "definitions": {
            "S": ["Python", "R", "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Statistics", "Regression", "Classification", "Clustering"],
            "A": ["Model Deployment", "MLOps", "Inference Pipelines", "Scalable Training", "Feature Store"],
            "D": ["Pandas", "NumPy", "SQL", "Spark", "Hadoop", "Data Wrangling", "EDA", "Feature Engineering", "Big Data"],
            "T": ["Jupyter", "TensorFlow", "PyTorch", "Scikit-learn", "AWS SageMaker", "Tableau", "Power BI", "Matplotlib"],
            "C": ["Model Evaluation", "A/B Testing", "Hypothesis Testing", "Bias and Fairness", "Explainability"]
        }
    },
    "Full Stack Developer": {
        "weights": {"S": 0.42, "E": 0.10, "P": 0.12, "A": 0.08, "D": 0.10, "T": 0.08, "C": 0.04, "J": 0.03, "L": 0.01, "TIER": 0.02},
        "y_ref": 3,
        "definitions": {
            "S": ["JavaScript", "TypeScript", "Python", "React", "Node.js", "Express", "MongoDB", "PostgreSQL", "REST API", "GraphQL"],
            "A": ["System Design", "Microservices", "API Design", "Authentication", "Cloud Architecture"],
            "D": ["SQL", "NoSQL", "MongoDB", "PostgreSQL", "Redis", "Data Modeling"],
            "T": ["Git", "Docker", "AWS", "CI/CD", "Webpack", "Vite"],
            "C": ["Testing", "Code Review", "Documentation", "Agile"]
        }
    }
}

# ==========================================
# 3. LOAD MODEL
# ==========================================
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# ==========================================
# 4. PERSONALIZATION LAYER (GLMix-inspired)
# ==========================================
@dataclass
class PersonalizationFeatures:
    """Company hiring preferences learned from history"""
    location_preferences: Dict[str, float]
    skill_affinities: Dict[str, float]
    experience_range: Tuple[float, float]
    college_tier_preference: Dict[str, float]
    industry_affinities: Dict[str, float]

class ThompsonSamplingBandit:
    """Multi-Armed Bandit for exploration-exploitation"""
    def __init__(self, n_arms: int = 5):
        self.alpha = np.ones(n_arms)  # Success counts
        self.beta = np.ones(n_arms)   # Failure counts
        
    def select_arm(self) -> int:
        samples = [np.random.beta(self.alpha[i], self.beta[i]) for i in range(len(self.alpha))]
        return int(np.argmax(samples))
    
    def update(self, arm: int, reward: float):
        if reward > 0.5:
            self.alpha[arm] += 1
        else:
            self.beta[arm] += 1

class GLMixPersonalizer:
    """GLMix-inspired personalization layer"""
    
    def __init__(self):
        self.global_weights = None
        self.company_weights = {}
        self.bandit = ThompsonSamplingBandit(n_arms=5)
        
    def compute_personalization_boost(self, base_score: float, candidate_features: dict, 
                                       company_history: dict) -> Tuple[float, dict]:
        """Apply personalization layer on top of base score"""
        
        boost = 0.0
        explanations = []
        
        # Location affinity
        if company_history.get('preferred_locations'):
            cand_loc = candidate_features.get('location', '').lower()
            for loc, weight in company_history['preferred_locations'].items():
                if loc.lower() in cand_loc:
                    boost += 0.05 * weight
                    explanations.append(f"Location match: {loc}")
                    
        # College tier preference
        tier = candidate_features.get('college_tier', 'Tier 3')
        tier_prefs = company_history.get('tier_preference', {})
        if tier in tier_prefs:
            boost += 0.03 * tier_prefs[tier]
            if tier_prefs[tier] > 0.7:
                explanations.append(f"Strong preference for {tier} candidates")
                
        # Skill affinity (beyond JD requirements)
        skill_affinities = company_history.get('skill_affinities', {})
        candidate_skills = candidate_features.get('skills', [])
        for skill in candidate_skills:
            if skill in skill_affinities:
                boost += 0.02 * skill_affinities[skill]
                
        # Experience pattern match
        exp_pref = company_history.get('experience_preference', (2, 8))
        cand_exp = candidate_features.get('years_exp', 0)
        if exp_pref[0] <= cand_exp <= exp_pref[1]:
            boost += 0.03
            explanations.append(f"Experience ({cand_exp}y) matches hiring pattern")
            
        # Apply exploration bonus (Thompson Sampling)
        exploration_bonus = 0.02 * (1 - base_score)  # Explore more for uncertain candidates
        
        final_score = min(base_score + boost + exploration_bonus, 1.0)
        
        return final_score, {
            'boost': boost,
            'exploration_bonus': exploration_bonus,
            'explanations': explanations
        }

# ==========================================
# 5. GENERALIZED SCORER (Improved Model)
# ==========================================
class EnterpriseScorer:
    """
    Improved scoring model with:
    - Soft constraints instead of harsh penalties
    - Generalized semantic matching (not overfitting to keywords)
    - Balanced weighting with floor scores
    - Multi-signal fusion approach
    """
    
    def __init__(self):
        self.personalizer = GLMixPersonalizer()
    
    @staticmethod
    def detect_tier(text):
        text_lower = text.lower()
        for college in TIER_1_COLLEGES:
            if college.lower() in text_lower:
                return "Tier 1"
        for college in TIER_2_COLLEGES:
            if college.lower() in text_lower:
                return "Tier 2"
        return "Tier 3"

    @staticmethod
    def calculate_tier_score(detected_tier, hiring_stats):
        t1_count = hiring_stats.get('tier1', 0)
        t2_count = hiring_stats.get('tier2', 0)
        total_hires = t1_count + t2_count
        
        if total_hires == 0:
            return 0.7  # Neutral-positive default
            
        t1_ratio = t1_count / total_hires
        t2_ratio = t2_count / total_hires
        
        if detected_tier == "Tier 1":
            return 1.0
        elif detected_tier == "Tier 2":
            return 0.95 if t2_ratio > t1_ratio else 0.85
        else:
            return 0.7  # Don't penalize unknown tiers heavily

    @staticmethod
    def compute_semantic_similarity(resume_text: str, skill_categories: Dict[str, List[str]]) -> Dict[str, float]:
        """
        Generalized semantic matching using:
        1. Full resume embedding vs skill domain embedding
        2. Soft TF-IDF style keyword presence (not exact match)
        3. Category-level semantic similarity
        """
        scores = {}
        
        # Get resume embedding once
        resume_emb = model.encode(resume_text, normalize_embeddings=True)
        resume_lower = resume_text.lower()
        
        for category, keywords in skill_categories.items():
            if not keywords:
                scores[category] = 0.5  # Neutral score for empty categories
                continue
            
            # 1. Semantic similarity (generalized - not keyword specific)
            # Create a rich context from keywords
            skill_context = f"Professional experience with {', '.join(keywords[:8])}. " \
                           f"Expertise in {' and '.join(keywords[:5])}."
            skill_emb = model.encode(skill_context, normalize_embeddings=True)
            semantic_sim = float(util.cos_sim(resume_emb, skill_emb).item())
            
            # 2. Soft keyword presence (fuzzy matching approach)
            # Count partial matches and synonyms
            keyword_score = 0
            for kw in keywords:
                kw_lower = kw.lower()
                # Exact match
                if kw_lower in resume_lower:
                    keyword_score += 1.0
                # Partial match (for compound terms like "React.js" matching "React")
                elif any(part in resume_lower for part in kw_lower.split()):
                    keyword_score += 0.6
                # Semantic proximity check for missed keywords
                else:
                    # Give partial credit based on semantic similarity
                    kw_emb = model.encode(kw, normalize_embeddings=True)
                    kw_sim = float(util.cos_sim(resume_emb, kw_emb).item())
                    if kw_sim > 0.4:  # Threshold for semantic match
                        keyword_score += kw_sim * 0.5
            
            # Normalize keyword score with diminishing returns
            max_keywords = len(keywords)
            normalized_kw_score = min(keyword_score / (max_keywords * 0.4), 1.0)
            
            # 3. Combined score with semantic emphasis
            # Weight: 60% semantic, 40% keyword (avoiding keyword overfitting)
            combined = (semantic_sim * 0.6) + (normalized_kw_score * 0.4)
            
            # Apply floor to avoid very low scores
            scores[category] = max(combined, 0.25)
        
        return scores

    @staticmethod  
    def compute_experience_score(years_actual: float, years_required: float, years_ref: float) -> float:
        """Smooth experience scoring with soft requirements"""
        if years_actual <= 0:
            return 0.3  # Fresher gets base score
        
        # Score based on how well experience matches
        if years_actual >= years_required:
            # Met or exceeded requirement
            ratio = min(years_actual / years_ref, 1.5)
            return min(0.7 + (ratio * 0.3), 1.0)
        else:
            # Below requirement - soft penalty
            gap_ratio = years_actual / max(years_required, 1)
            return 0.4 + (gap_ratio * 0.4)  # Range: 0.4 to 0.8

    @staticmethod
    def compute_soft_constraint_adjustment(cand_data: dict, constraints: dict, resume_text: str) -> Tuple[float, List[str], List[str]]:
        """
        Soft constraints - adjustments instead of harsh penalties
        Returns: (adjustment_factor, missing_skills, warnings)
        """
        adjustment = 1.0
        missing_skills = []
        warnings = []
        
        # 1. Experience gap (soft penalty)
        min_exp = constraints.get('min_exp', 0)
        y_actual = cand_data.get('years_exp', 0)
        if y_actual < min_exp:
            gap = min_exp - y_actual
            # Soft penalty: max 15% reduction for experience gap
            exp_penalty = min(gap * 0.05, 0.15)
            adjustment -= exp_penalty
            warnings.append(f"Experience gap: {y_actual}Y vs {min_exp}Y required")
        
        # 2. Mandatory skills (soft penalty with semantic fallback)
        mandatory_skills = constraints.get('mandatory_skills', [])
        resume_lower = resume_text.lower()
        resume_emb = model.encode(resume_text, normalize_embeddings=True) if mandatory_skills else None
        
        for skill in mandatory_skills:
            skill_lower = skill.lower()
            if skill_lower in resume_lower:
                continue  # Found exact match
            
            # Check for semantic match
            skill_emb = model.encode(skill, normalize_embeddings=True)
            similarity = float(util.cos_sim(resume_emb, skill_emb).item())
            
            if similarity > 0.5:
                # Semantic match found - minor penalty
                adjustment -= 0.03
                warnings.append(f"Partial match for {skill}")
            else:
                # Missing skill - moderate penalty (max 8% per skill)
                adjustment -= 0.08
                missing_skills.append(skill)
        
        # Floor adjustment at 0.7 (never penalize more than 30%)
        adjustment = max(adjustment, 0.7)
        
        return adjustment, missing_skills, warnings

    def calculate(self, resume_text: str, role_config: dict, cand_data: dict, constraints: dict):
        """Main scoring function with improved generalization"""
        
        D = role_config.get("definitions", {})
        y_ref = role_config.get('y_ref', 3)
        min_exp = constraints.get('min_exp', 0)
        y_actual = cand_data.get('years_exp', 0)
        
        # 1. Compute semantic skill scores (generalized)
        sem_scores = self.compute_semantic_similarity(resume_text, D)
        
        # 2. Experience score (soft)
        score_e = self.compute_experience_score(y_actual, min_exp, y_ref)
        
        # 3. Project depth score
        action_verbs = ["developed", "deployed", "managed", "created", "built", 
                       "reduced", "increased", "led", "architected", "designed", 
                       "implemented", "optimized", "delivered", "launched", "scaled"]
        resume_lower = resume_text.lower()
        action_hits = sum(1 for v in action_verbs if v in resume_lower)
        score_p = min((action_hits / 6) + 0.2, 1.0)  # Base of 0.2, need 6 hits for max
        
        # 4. Notice period score (softer)
        days = cand_data.get('notice_days', 90)
        strict_notice = constraints.get('strict_notice', False)
        
        if days <= 15: score_j = 1.0
        elif days <= 30: score_j = 0.9
        elif days <= 45: score_j = 0.8
        elif days <= 60: score_j = 0.7
        elif days <= 90: score_j = 0.5 if strict_notice else 0.6
        else: score_j = 0.3 if strict_notice else 0.5
        
        # 5. Location score (more generous)
        job_loc = constraints.get('job_loc', '').lower()
        cand_loc = cand_data.get('cand_loc', '').lower()
        mode = cand_data.get('work_mode', 'Hybrid')
        relocate = cand_data.get('relocate', False)
        
        if mode == "Remote": 
            score_l = 1.0
        elif job_loc and job_loc in cand_loc: 
            score_l = 1.0
        elif relocate: 
            score_l = 0.85
        elif mode == "Hybrid":
            score_l = 0.7
        else: 
            score_l = 0.5

        # 6. College tier score
        detected_tier = self.detect_tier(resume_text)
        score_tier = self.calculate_tier_score(detected_tier, constraints.get('hiring_stats', {}))
        
        # 7. Salary compatibility
        prev_salary = cand_data.get('prev_salary', 0)
        max_budget = constraints.get('max_budget', 0)
        if max_budget == 0 or prev_salary <= max_budget: 
            score_sal = 1.0 
        elif prev_salary <= (max_budget * 1.2): 
            score_sal = 0.8
        elif prev_salary <= (max_budget * 1.4):
            score_sal = 0.6
        else: 
            score_sal = 0.4
        
        # 8. Compute soft constraint adjustments
        adjustment, missing_skills, warnings = self.compute_soft_constraint_adjustment(
            cand_data, constraints, resume_text
        )
        
        # ===== SCORING MODEL (Balanced Weights) =====
        # Primary signals (70%)
        skill_score = (
            sem_scores.get('S', 0.5) * 0.50 +  # Core skills
            sem_scores.get('A', 0.5) * 0.20 +  # Architecture
            sem_scores.get('D', 0.5) * 0.15 +  # Data skills
            sem_scores.get('T', 0.5) * 0.10 +  # Tools
            sem_scores.get('C', 0.5) * 0.05    # Code quality
        )
        
        # Secondary signals (30%)
        fit_score = (
            score_e * 0.35 +      # Experience
            score_p * 0.25 +      # Projects
            score_tier * 0.15 +   # College tier
            score_j * 0.10 +      # Notice period
            score_l * 0.10 +      # Location
            score_sal * 0.05      # Salary
        )
        
        # Combined raw score
        raw_score = (skill_score * 0.70) + (fit_score * 0.30)
        
        # Apply soft adjustment (not harsh penalty)
        adjusted_score = raw_score * adjustment
        
        # Apply floor to ensure reasonable scores
        adjusted_score = max(adjusted_score, 0.35)
        
        # Apply personalization boost
        company_history = {
            'tier_preference': {
                'Tier 1': 0.9, 
                'Tier 2': constraints.get('hiring_stats', {}).get('tier2', 0) / max(1, constraints.get('hiring_stats', {}).get('tier1', 1) + constraints.get('hiring_stats', {}).get('tier2', 1)),
                'Tier 3': 0.5
            },
            'experience_preference': (min_exp, min_exp + 6)
        }
        
        final_score, personalization_details = self.personalizer.compute_personalization_boost(
            adjusted_score, 
            {'college_tier': detected_tier, 'years_exp': y_actual, 'location': cand_loc},
            company_history
        )
        
        # Ensure final score is in valid range
        final_score = min(max(final_score, 0.35), 1.0)
        
        return round(final_score, 3), {
            "Skills": sem_scores.get('S', 0.5), 
            "Experience": score_e, 
            "Projects": score_p,
            "Architecture": sem_scores.get('A', 0.5),
            "Data Skills": sem_scores.get('D', 0.5),
            "Tools": sem_scores.get('T', 0.5),
            "College Tier": score_tier,
            "Notice Period": score_j,
            "Detected Tier": detected_tier,
            "Missing Skills": missing_skills,
            "Penalty Factor": adjustment,
            "Warnings": warnings,
            "Personalization": personalization_details
        }

# ==========================================
# 6. UI COMPONENTS
# ==========================================
def render_metric_card(icon, value, label, score_class=""):
    st.markdown(f"""
    <div class="metric-card {score_class}">
        <span class="metric-icon">{icon}</span>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def render_insight_card(icon, text, card_type="info"):
    st.markdown(f"""
    <div class="insight-card {card_type}">
        <span style="font-size: 16px;">{icon}</span> {text}
    </div>
    """, unsafe_allow_html=True)

def render_section_header(icon, title):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-icon">{icon}</div>
        <h3 class="section-title">{title}</h3>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 7. MAIN APPLICATION
# ==========================================
st.sidebar.markdown("""
<div style="padding: 20px 0;">
    <h2 style="color: #a5b4fc !important; font-size: 18px; margin-bottom: 20px;">⚙️ Control Panel</h2>
</div>
""", unsafe_allow_html=True)

app_mode = st.sidebar.radio("Mode", ["🎯 Single Audit", "📊 Batch Screening"], label_visibility="collapsed")

EXP_MAP = {"Fresher": 0.0, "1-2 Years": 1.5, "3-5 Years": 4.0, "6-9 Years": 7.5, "10+ Years": 12.0}

scorer = EnterpriseScorer()

if app_mode == "🎯 Single Audit":
    col1, col2 = st.columns([1.2, 2], gap="large")
    
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_section_header("🛡️", "Job Requirements")
        
        role_select = st.selectbox("Job Role", list(ROLES_DB.keys()), key="role")
        config = ROLES_DB[role_select]
        
        job_loc = st.text_input("📍 Location", "Bangalore")
        max_budget = st.number_input("💰 Max Budget (LPA)", 0, 100, 15)
        
        st.markdown("---")
        render_section_header("🔒", "Hard Constraints")
        
        min_exp_req = st.number_input("Min Experience (Years)", 0, 20, 2)
        
        all_role_skills = []
        for cat in config['definitions'].values():
            all_role_skills.extend(cat)
        all_role_skills = sorted(list(set(all_role_skills)))
        
        mandatory_skills = st.multiselect("Mandatory Skills", all_role_skills)
        strict_notice = st.checkbox("⏱️ Strict Notice Period (<60 days)", value=True)
        
        st.markdown("---")
        render_section_header("📈", "Company Hiring History")
        
        h_tier1 = st.number_input("Past Tier 1 Hires", 0, 1000, 10)
        h_tier2 = st.number_input("Past Tier 2 Hires", 0, 1000, 45)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_section_header("👤", "Candidate Profile")
        
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf", key="resume")
        
        c1, c2, c3 = st.columns(3)
        c_exp_str = c1.selectbox("Experience", list(EXP_MAP.keys()), index=2)
        c_notice = c2.number_input("Notice (Days)", 0, 90, 30)
        c_prev_sal = c3.number_input("Current CTC", 0, 100, 10)
        
        c4, c5 = st.columns(2)
        c_city = c4.text_input("Current City", "Pune")
        c_reloc = c5.checkbox("Willing to Relocate", value=True)
        c_mode = st.selectbox("Preferred Work Mode", ["Hybrid", "Onsite", "Remote"])
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Run Analysis Engine", use_container_width=True):
            if uploaded_file:
                with st.spinner(""):
                    # Loading animation
                    progress_placeholder = st.empty()
                    progress_placeholder.markdown("""
                    <div style="text-align: center; padding: 40px;">
                        <div class="loading-shimmer" style="width: 100%; height: 4px; border-radius: 2px; margin-bottom: 20px;"></div>
                        <p style="color: #94a3b8;">Analyzing resume with AI models...</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with pdfplumber.open(uploaded_file) as pdf:
                        text = "".join([p.extract_text() or "" for p in pdf.pages])
                    
                    cand_data = {
                        "years_exp": EXP_MAP[c_exp_str], 
                        "notice_days": c_notice, 
                        "cand_loc": c_city, 
                        "work_mode": c_mode, 
                        "relocate": c_reloc, 
                        "prev_salary": c_prev_sal
                    }
                    
                    constraints = {
                        "min_exp": min_exp_req,
                        "mandatory_skills": mandatory_skills,
                        "strict_notice": strict_notice,
                        "max_budget": max_budget,
                        "job_loc": job_loc,
                        "hiring_stats": {"tier1": h_tier1, "tier2": h_tier2}
                    }
                    
                    score, details = scorer.calculate(text, config, cand_data, constraints)
                    
                    progress_placeholder.empty()
                    
                    detected_tier = details.pop("Detected Tier")
                    missing = details.pop("Missing Skills")
                    adjustment = details.pop("Penalty Factor")
                    warnings = details.pop("Warnings", [])
                    personalization = details.pop("Personalization")
                    
                    # Results
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Soft adjustment notice (not harsh penalty warning)
                    if adjustment < 0.95 and (missing or warnings):
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(251, 191, 36, 0.12), rgba(245, 158, 11, 0.08)); border: 1px solid rgba(251, 191, 36, 0.3); border-left: 4px solid #fbbf24; padding: 16px 20px; border-radius: 12px; margin-bottom: 20px;">
                            <h4 style="color: #fcd34d !important; margin: 0 0 6px 0; font-weight: 600; font-size: 15px;">📋 Areas for Consideration</h4>
                            <p style="color: #fde68a !important; margin: 0; font-size: 13px;">Some criteria may benefit from further review. Score adjusted by <strong>{(1-adjustment)*100:.0f}%</strong>.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Personalization badge
                    if personalization['boost'] > 0:
                        st.markdown(f"""
                        <div style="text-align: center; margin-bottom: 20px;">
                            <span class="personalization-badge">
                                ✨ Personalization Active (+{personalization['boost']*100:.1f}% boost)
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Score metrics
                    score_class = "score-high" if score > 0.7 else "score-medium" if score > 0.5 else "score-low"
                    score_color = "#34d399" if score > 0.7 else "#fbbf24" if score > 0.5 else "#f87171"
                    
                    k1, k2, k3, k4 = st.columns(4)
                    
                    with k1:
                        st.markdown(f"""
                        <div class="metric-card {score_class}">
                            <span class="metric-icon">🎯</span>
                            <div class="metric-value" style="color: {score_color} !important;">{score*100:.1f}%</div>
                            <div class="metric-label">Match Score</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with k2:
                        tier_icon = "🏆" if detected_tier == "Tier 1" else "🥈" if detected_tier == "Tier 2" else "📚"
                        st.markdown(f"""
                        <div class="metric-card">
                            <span class="metric-icon">{tier_icon}</span>
                            <div class="metric-value" style="font-size: 28px;">{detected_tier}</div>
                            <div class="metric-label">College Tier</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with k3:
                        skill_pct = details['Skills']*100
                        st.markdown(f"""
                        <div class="metric-card">
                            <span class="metric-icon">💻</span>
                            <div class="metric-value">{skill_pct:.0f}%</div>
                            <div class="metric-label">Tech Skill Fit</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with k4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <span class="metric-icon">⏳</span>
                            <div class="metric-value">{cand_data['years_exp']:.1f}Y</div>
                            <div class="metric-label">Experience</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Radar Chart & Insights
                    st.markdown("<br>", unsafe_allow_html=True)
                    r1, r2 = st.columns([1.2, 1])
                    
                    with r1:
                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        render_section_header("🕸️", "360° Assessment")
                        
                        radar_data = {k: v for k, v in details.items() if isinstance(v, (int, float))}
                        
                        fig = go.Figure(data=go.Scatterpolar(
                            r=list(radar_data.values()),
                            theta=list(radar_data.keys()),
                            fill='toself',
                            fillcolor='rgba(99, 102, 241, 0.25)',
                            line=dict(color='#818cf8', width=2),
                            marker=dict(size=8, color='#a5b4fc')
                        ))
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True, 
                                    range=[0, 1], 
                                    gridcolor='rgba(255,255,255,0.08)',
                                    tickfont=dict(color='#64748b', size=10)
                                ),
                                angularaxis=dict(
                                    gridcolor='rgba(255,255,255,0.08)',
                                    tickfont=dict(color='#94a3b8', size=11)
                                ),
                                bgcolor='rgba(0,0,0,0)'
                            ),
                            showlegend=False,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            margin=dict(t=30, b=30, l=60, r=60),
                            height=350
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with r2:
                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        render_section_header("💡", "AI Insights")
                        
                        # Show warnings first (softer messaging)
                        for warn in warnings[:2]:
                            render_insight_card("ℹ️", warn, "warning")
                        
                        if missing:
                            render_insight_card("�", f"Skills to verify: {', '.join(missing)}", "warning")
                        
                        # Positive signals
                        if detected_tier == "Tier 1":
                            render_insight_card("🌟", "Premium Talent: Tier 1 Institution", "positive")
                        elif detected_tier == "Tier 2" and h_tier2 > h_tier1:
                            render_insight_card("💎", f"Strategic Fit: {detected_tier} aligns with hiring preference", "positive")
                        
                        if cand_data['years_exp'] >= min_exp_req:
                            render_insight_card("✅", f"Experience requirement met ({cand_data['years_exp']}Y)", "positive")
                            
                        if details['Skills'] > 0.6:
                            render_insight_card("🔥", "Strong technical skill alignment", "positive")
                        elif details['Skills'] > 0.45:
                            render_insight_card("💡", "Good skill foundation, room for growth", "info")
                        
                        if details['Projects'] > 0.6:
                            render_insight_card("�", "Strong project experience demonstrated", "positive")
                            
                        if details['Notice Period'] < 0.5 and c_notice > 60:
                            render_insight_card("⏱️", f"Notice Period: {c_notice} days - consider negotiation", "info")
                            
                        if personalization['explanations']:
                            for exp in personalization['explanations'][:2]:
                                render_insight_card("🎯", exp, "info")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("👈 Upload a resume to begin audit.")

elif app_mode == "📊 Batch Screening":
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_section_header("🏭", "Bulk Intelligence Processing")
    
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 64px; margin-bottom: 20px;">🚧</div>
        <h3 style="color: #f1f5f9 !important; margin-bottom: 12px;">Coming Soon</h3>
        <p style="color: #64748b !important;">Batch processing with GLMix personalization is under development.</p>
        <p style="color: #64748b !important;">Features: Multi-resume upload, parallel scoring, export to CSV/Excel</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)