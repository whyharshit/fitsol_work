"""
ESG Dashboard — Plotly Chart Builders
All charts isolated from app logic. Professional dark-themed visuals.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from styles import EMERALD, ROYAL_BLUE, AMBER, TEXT, MUTED, DARK_BG

# ── Shared layout defaults ─────────────────────────────────────────────────────
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=TEXT, size=12),
    margin=dict(t=50, b=30, l=40, r=20),
)


# ══════════════════════════════════════════════════════════════════════════════
#  MARKET VIEW CHARTS
# ══════════════════════════════════════════════════════════════════════════════

def company_treemap(pillar_data: list) -> go.Figure:
    """
    Treemap of companies sized by overall ESG confidence score,
    coloured by a gradient (low → high).
    """
    df = pd.DataFrame(pillar_data)
    if df.empty:
        return go.Figure()

    # Bin into quality tiers for grouping
    df["tier"] = pd.cut(
        df["overall"],
        bins=[0, 30, 60, 80, 100],
        labels=["Low (0-30)", "Medium (30-60)", "Good (60-80)", "Excellent (80-100)"],
        include_lowest=True,
    )

    fig = px.treemap(
        df,
        path=["tier", "company"],
        values="overall",
        color="overall",
        color_continuous_scale=["#EF4444", AMBER, EMERALD],
        range_color=[0, 100],
        title="ESG Reporting Confidence by Company",
    )
    fig.update_layout(**_LAYOUT, coloraxis_colorbar=dict(
        title="Score",
        ticksuffix="%",
        len=0.6,
    ))
    fig.update_traces(
        textinfo="label+value",
        hovertemplate="<b>%{label}</b><br>Confidence: %{value:.1f}%<extra></extra>",
    )
    return fig


def emissions_histogram(scope1: list, scope2: list) -> go.Figure:
    """Overlaid histogram of Scope 1 and Scope 2 emissions."""
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=scope1, name="Scope 1",
        marker_color=EMERALD, opacity=0.7,
        nbinsx=40,
        hovertemplate="Range: %{x}<br>Companies: %{y}<extra>Scope 1</extra>",
    ))
    fig.add_trace(go.Histogram(
        x=scope2, name="Scope 2",
        marker_color=ROYAL_BLUE, opacity=0.7,
        nbinsx=40,
        hovertemplate="Range: %{x}<br>Companies: %{y}<extra>Scope 2</extra>",
    ))
    fig.update_layout(
        **_LAYOUT,
        title="Emissions Distribution (tCO₂e)",
        barmode="overlay",
        xaxis_title="Emissions (tCO₂e)",
        yaxis_title="Number of Companies",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


def disclosure_pie(disclosed: int, not_disclosed: int) -> go.Figure:
    """Donut chart showing reporting maturity."""
    fig = go.Figure(go.Pie(
        labels=["Disclosed", "Not Disclosed"],
        values=[disclosed, not_disclosed],
        hole=0.55,
        marker=dict(colors=[EMERALD, "#334155"]),
        textinfo="percent+label",
        textfont=dict(size=13),
        hovertemplate="<b>%{label}</b><br>Count: %{value:,}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT,
        title="Data Disclosure Maturity",
        showlegend=False,
        annotations=[dict(
            text=f"<b>{disclosed + not_disclosed:,}</b><br><span style='font-size:11px;color:{MUTED}'>data points</span>",
            x=0.5, y=0.5, font_size=18, showarrow=False,
            font_color=TEXT,
        )],
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  COMPANY DEEP-DIVE CHARTS
# ══════════════════════════════════════════════════════════════════════════════

def emissions_gauge(company_val: float, avg_val: float, company_name: str = "") -> go.Figure:
    """Gauge chart showing company's emissions intensity relative to industry avg."""
    max_val = max(company_val, avg_val) * 1.5 if avg_val else company_val * 2
    if max_val == 0:
        max_val = 1

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=company_val,
        number=dict(font=dict(size=36, color=TEXT)),
        delta=dict(reference=avg_val, valueformat=".2f", increasing=dict(color="#EF4444"), decreasing=dict(color=EMERALD)),
        title=dict(text=f"Emissions Intensity", font=dict(size=14, color=MUTED)),
        gauge=dict(
            axis=dict(range=[0, max_val], tickcolor=MUTED),
            bar=dict(color=EMERALD, thickness=0.3),
            bgcolor="rgba(30,41,59,0.5)",
            borderwidth=0,
            steps=[
                dict(range=[0, avg_val * 0.5], color="rgba(16,185,129,0.15)"),
                dict(range=[avg_val * 0.5, avg_val], color="rgba(245,158,11,0.15)"),
                dict(range=[avg_val, max_val], color="rgba(239,68,68,0.15)"),
            ],
            threshold=dict(
                line=dict(color=AMBER, width=3),
                thickness=0.8,
                value=avg_val,
            ),
        ),
    ))
    fig.update_layout(**_LAYOUT, height=320)
    return fig


def diversity_sunburst(board_pct, total_pct, attrition_emp, attrition_wrk) -> go.Figure:
    """Sunburst: Gender Diversity (board vs total) and Attrition."""
    labels = [
        "Social",
        "Gender Diversity", "Board", "Total Employees",
        "Attrition", "Employees", "Workers"
    ]
    parents = [
        "",
        "Social", "Gender Diversity", "Gender Diversity",
        "Social", "Attrition", "Attrition"
    ]
    values = [
        0,
        0, board_pct or 0, total_pct or 0,
        0, attrition_emp or 0, attrition_wrk or 0,
    ]
    colors = [
        ROYAL_BLUE,
        ROYAL_BLUE, "#60A5FA", "#93C5FD",
        AMBER, "#FBBF24", "#FDE68A",
    ]

    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors),
        textinfo="label+value",
        hovertemplate="<b>%{label}</b><br>Value: %{value}%<extra></extra>",
    ))
    fig.update_layout(**_LAYOUT, title="Diversity & Retention Breakdown", height=400)
    return fig


def energy_breakdown_bar(renewable: float, non_renewable: float) -> go.Figure:
    """Horizontal stacked bar showing energy mix."""
    fig = go.Figure()
    total = (renewable or 0) + (non_renewable or 0)
    if total == 0:
        return go.Figure()

    fig.add_trace(go.Bar(
        y=["Energy Mix"], x=[renewable or 0],
        name="Renewable", orientation="h",
        marker_color=EMERALD,
        text=[f"{(renewable or 0)/total*100:.1f}%"],
        textposition="inside",
        hovertemplate="Renewable: %{x:,.0f} GJ<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=["Energy Mix"], x=[non_renewable or 0],
        name="Non-Renewable", orientation="h",
        marker_color="#334155",
        text=[f"{(non_renewable or 0)/total*100:.1f}%"],
        textposition="inside",
        hovertemplate="Non-Renewable: %{x:,.0f} GJ<extra></extra>",
    ))
    fig.update_layout(
        **_LAYOUT,
        barmode="stack",
        height=120,
        title="Energy Mix (GJ)",
        xaxis_title="",
        yaxis=dict(showticklabels=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=60, b=10, l=10, r=10),
    )
    return fig


def governance_table_data(data_points: list) -> pd.DataFrame:
    """Build a styled DataFrame for Governance metrics."""
    gov_metrics = [
        "Anti-Corruption Policy",
        "Whistleblower Mechanism",
        "ESG Oversight Committee",
        "Board Independence %",
        "ESG Linked Pay",
        "Legal Cases",
    ]
    rows = []
    for dp in data_points:
        if dp.get("data_point") in gov_metrics:
            val = dp.get("value")
            if val is None or val == "null":
                val = "Not Disclosed"
            rows.append({
                "Metric": dp["data_point"],
                "Status": str(val)[:120],
                "Verification": dp.get("verification_level", "—"),
                "Confidence": f"{dp.get('confidence_score', 0) * 100:.0f}%",
            })
    return pd.DataFrame(rows)
