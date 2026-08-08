"""
ESG Dashboard — Custom CSS & Theming
Dark professional theme with glassmorphism, Inter font, and ESG pillar colours.
"""

# Pillar colours
EMERALD = "#10B981"    # Environmental
ROYAL_BLUE = "#3B82F6" # Social
AMBER = "#F59E0B"      # Governance
DARK_BG = "#0F172A"
CARD_BG = "rgba(30, 41, 59, 0.7)"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Inter, sans-serif", "color": TEXT},
        "margin": {"t": 40, "b": 30, "l": 40, "r": 20},
    }
}


def inject_css():
    """Returns the full CSS string to inject via st.markdown."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Global ──────────────────────────────────────────────────────── */
html, body, .stApp {{
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(135deg, {DARK_BG} 0%, #1E293B 50%, #0F172A 100%) !important;
    color: {TEXT};
}}

/* Remove default Streamlit padding */
.block-container {{
    padding-top: 1.5rem !important;
    max-width: 1400px;
}}

/* ── Sidebar ─────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
    border-right: 1px solid rgba(59, 130, 246, 0.15);
}}

section[data-testid="stSidebar"] .stTextInput input {{
    background: rgba(30, 41, 59, 0.8) !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    border-radius: 10px !important;
    color: {TEXT} !important;
    padding: 0.6rem 1rem !important;
}}

section[data-testid="stSidebar"] .stTextInput input::placeholder {{
    color: {MUTED} !important;
}}

section[data-testid="stSidebar"] .stSelectbox > div > div {{
    background: rgba(30, 41, 59, 0.8) !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    border-radius: 10px !important;
    color: {TEXT} !important;
}}

/* ── Hero / Glass Cards ──────────────────────────────────────────── */
.hero-card {{
    background: {CARD_BG};
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    animation: fadeIn 0.5s ease-out;
}}

.hero-title {{
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, {EMERALD}, {ROYAL_BLUE}, {AMBER});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.25rem;
}}

.hero-subtitle {{
    font-size: 1rem;
    color: {MUTED};
    font-weight: 400;
}}

/* ── KPI Metric Cards ────────────────────────────────────────────── */
.kpi-card {{
    background: {CARD_BG};
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.5rem;
    text-align: center;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    position: relative;
    overflow: hidden;
}}

.kpi-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.3);
}}

.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 14px 14px 0 0;
}}

.kpi-card.env::before {{ background: linear-gradient(90deg, {EMERALD}, #34D399); }}
.kpi-card.soc::before {{ background: linear-gradient(90deg, {ROYAL_BLUE}, #60A5FA); }}
.kpi-card.gov::before {{ background: linear-gradient(90deg, {AMBER}, #FBBF24); }}

.kpi-label {{
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: {MUTED};
    margin-bottom: 0.5rem;
    font-weight: 600;
}}

.kpi-value {{
    font-size: 2rem;
    font-weight: 700;
    color: {TEXT};
}}

.kpi-unit {{
    font-size: 0.8rem;
    color: {MUTED};
    margin-top: 0.25rem;
}}

/* ── Stat Pills (Market View header) ─────────────────────────────── */
.stat-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 999px;
    padding: 0.5rem 1.2rem;
    font-size: 0.85rem;
    color: {TEXT};
}}

.stat-pill .num {{
    font-weight: 700;
    font-size: 1.1rem;
}}

/* ── Tabs override ───────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background: rgba(30, 41, 59, 0.5);
    border-radius: 12px;
    padding: 4px;
}}

.stTabs [data-baseweb="tab"] {{
    border-radius: 10px;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    color: {MUTED};
}}

.stTabs [aria-selected="true"] {{
    background: rgba(59, 130, 246, 0.2) !important;
    color: {TEXT} !important;
}}

/* ── DataFrames / Tables ─────────────────────────────────────────── */
.stDataFrame {{
    border-radius: 12px;
    overflow: hidden;
}}

/* ── Expander ────────────────────────────────────────────────────── */
.streamlit-expanderHeader {{
    background: rgba(30, 41, 59, 0.5) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}

/* ── Buttons ─────────────────────────────────────────────────────── */
.stButton > button {{
    background: linear-gradient(135deg, {ROYAL_BLUE}, #2563EB) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.25s ease !important;
}}

.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3) !important;
}}

/* ── Back button ─────────────────────────────────────────────────── */
.back-btn {{
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: {ROYAL_BLUE};
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 1rem;
    transition: color 0.2s;
}}
.back-btn:hover {{ color: #60A5FA; }}

/* ── Animation ───────────────────────────────────────────────────── */
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

.fade-in {{ animation: fadeIn 0.4s ease-out; }}

/* ── Evidence Badge ──────────────────────────────────────────────── */
.evidence-badge {{
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.evidence-badge.high {{ background: rgba(16,185,129,0.2); color: {EMERALD}; }}
.evidence-badge.med  {{ background: rgba(245,158,11,0.2); color: {AMBER}; }}
.evidence-badge.low  {{ background: rgba(239,68,68,0.2);  color: #EF4444; }}
</style>
"""
