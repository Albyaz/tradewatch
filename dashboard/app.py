"""
app.py — TradeWatch Platform dashboard
Live global trade corridor risk intelligence
"""
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="TradeWatch — Global Trade Risk Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; background:#0A0B0F; color:#E8E6DF; }
  .block-container { padding: 1.4rem 2rem 2rem; max-width:1400px; }
  [data-testid="stSidebar"] { background:#0F1015; border-right:1px solid #1E2028; }
  .wordmark { font-family:'Space Grotesk',sans-serif; font-size:24px; font-weight:700; color:#00D4AA; letter-spacing:-0.5px; }
  .wordmark span { color:#E8E6DF; }
  .section-label { font-size:11px; font-weight:500; letter-spacing:.12em; text-transform:uppercase; color:#444650; margin:1.4rem 0 .7rem; }
  .risk-card { background:#0F1015; border:1px solid #1E2028; border-radius:12px; padding:16px 18px; position:relative; overflow:hidden; }
  .risk-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; }
  .risk-critical::before { background:#FF4444; }
  .risk-high::before    { background:#FF8C00; }
  .risk-medium::before  { background:#F5C242; }
  .risk-low::before     { background:#00D4AA; }
  .risk-corridor { font-size:11px; font-weight:500; letter-spacing:.08em; text-transform:uppercase; color:#444650; margin-bottom:4px; }
  .risk-score { font-family:'Space Grotesk',sans-serif; font-size:40px; font-weight:700; line-height:1; letter-spacing:-2px; }
  .score-critical { color:#FF4444; }
  .score-high      { color:#FF8C00; }
  .score-medium    { color:#F5C242; }
  .score-low       { color:#00D4AA; }
  .risk-badge { display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:500; margin-top:4px; }
  .badge-critical { background:#2D1515; color:#FF4444; }
  .badge-high      { background:#2D1F0A; color:#FF8C00; }
  .badge-medium    { background:#2D260A; color:#F5C242; }
  .badge-low       { background:#0A2D25; color:#00D4AA; }
  .metric-row { display:flex; gap:8px; margin-top:8px; }
  .metric-chip { background:#1A1B22; border-radius:6px; padding:6px 10px; font-size:11px; color:#6B7080; }
  .metric-chip span { color:#C2C0B6; font-weight:500; }
  #MainMenu, footer, header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_engine():
    return create_engine(os.getenv("DATABASE_URL"))

@st.cache_data(ttl=300)
def load_risk_scores():
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT
                cr.corridor,
                cr.metric_date,
                cr.risk_score,
                cr.risk_level,
                cr.avg_wind_speed,
                cr.avg_wave_height,
                cr.avg_sentiment,
                cr.vessel_count,
                cr.any_storm,
                mrs.predicted_risk
            FROM staging.corridor_risk cr
            LEFT JOIN marts.corridor_risk_scores mrs
                ON cr.corridor = mrs.corridor
                AND cr.metric_date = mrs.score_date
            ORDER BY cr.metric_date DESC, cr.risk_score DESC
        """), conn)
    return df

@st.cache_data(ttl=300)
def load_news(corridor=None):
    engine = get_engine()
    query = """
        SELECT corridor, title, source, sentiment_score, published_at
        FROM raw.news_articles
        WHERE title IS NOT NULL
    """
    if corridor:
        query += f" AND corridor = '{corridor}'"
    query += " ORDER BY published_at DESC LIMIT 30"
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df

RISK_COLORS = {
    "CRITICAL": "#FF4444",
    "HIGH":     "#FF8C00",
    "MEDIUM":   "#F5C242",
    "LOW":      "#00D4AA",
}

CORRIDOR_COORDS = {
    "Suez Canal":          (30.5852,  32.2654),
    "Panama Canal":        ( 9.0820, -79.6813),
    "Strait of Malacca":   ( 2.5000, 101.5000),
    "Gulf of Aden":        (12.5000,  47.5000),
    "Strait of Hormuz":    (26.5667,  56.2500),
    "English Channel":     (50.2000,   0.5000),
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="wordmark">Trade<span>Watch</span></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#444650;margin-bottom:1.4rem;">Global Trade Risk Intelligence</div>', unsafe_allow_html=True)
    st.markdown("**Select corridor**")
    all_corridors = list(CORRIDOR_COORDS.keys())
    selected = st.selectbox("", ["All corridors"] + all_corridors, label_visibility="collapsed")
    st.markdown("---")
    st.markdown('<div style="font-size:11px;color:#444650;">Data refreshes every 6 hours<br>Pipeline: GitHub Actions<br>DB: Neon PostgreSQL</div>', unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    df = load_risk_scores()
    latest = df.groupby("corridor").first().reset_index()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="wordmark" style="font-size:28px">Trade<span>Watch</span></div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:13px;color:#444650;margin-bottom:1rem;">Global trade corridor risk intelligence · Updated {datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC</div>', unsafe_allow_html=True)

# ── Risk score cards ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Live corridor risk scores</div>', unsafe_allow_html=True)

display_df = latest if selected == "All corridors" else latest[latest["corridor"] == selected]
cols = st.columns(len(display_df))

for i, (_, row) in enumerate(display_df.iterrows()):
    level = row["risk_level"] or "LOW"
    score = float(row["risk_score"] or 0)
    with cols[i]:
        st.markdown(f"""
        <div class="risk-card risk-{level.lower()}">
          <div class="risk-corridor">{row['corridor']}</div>
          <div class="risk-score score-{level.lower()}">{score:.0f}</div>
          <div><span class="risk-badge badge-{level.lower()}">{level}</span></div>
          <div class="metric-row">
            <div class="metric-chip">💨 <span>{float(row['avg_wind_speed'] or 0):.0f} km/h</span></div>
            <div class="metric-chip">🚢 <span>{int(row['vessel_count'] or 0)}</span></div>
          </div>
          <div class="metric-row">
            <div class="metric-chip">📰 <span>{float(row['avg_sentiment'] or 0):+.2f}</span></div>
            <div class="metric-chip">⛈ <span>{'Yes' if row['any_storm'] else 'No'}</span></div>
          </div>
          <div class="metric-row">
            <div class="metric-chip">🤖 ML: <span>{float(row['predicted_risk'] or 0):.0f}</span></div>
          </div>
        </div>""", unsafe_allow_html=True)

# ── World map ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Corridor risk map</div>', unsafe_allow_html=True)

map_data = []
for _, row in latest.iterrows():
    coords = CORRIDOR_COORDS.get(row["corridor"])
    if coords:
        map_data.append({
            "corridor":   row["corridor"],
            "lat":        coords[0],
            "lon":        coords[1],
            "risk_score": float(row["risk_score"] or 0),
            "risk_level": row["risk_level"] or "LOW",
            "color":      RISK_COLORS.get(row["risk_level"], "#00D4AA"),
        })

map_df = pd.DataFrame(map_data)
fig_map = px.scatter_geo(
    map_df,
    lat="lat", lon="lon",
    size="risk_score",
    color="risk_level",
    hover_name="corridor",
    hover_data={"risk_score": True, "lat": False, "lon": False},
    color_discrete_map=RISK_COLORS,
    size_max=40,
    projection="natural earth",
)
fig_map.update_layout(
    paper_bgcolor="#0A0B0F",
    plot_bgcolor="#0A0B0F",
    geo=dict(
        bgcolor="#0A0B0F",
        landcolor="#1A1B22",
        oceancolor="#0F1015",
        showocean=True,
        showland=True,
        showcountries=True,
        countrycolor="#2A2B35",
        showframe=False,
    ),
    margin=dict(l=0, r=0, t=0, b=0),
    height=420,
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9B9890")),
)
st.plotly_chart(fig_map, use_container_width=True)

# ── Risk trend chart ──────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Risk score trends</div>', unsafe_allow_html=True)

trend_df = df if selected == "All corridors" else df[df["corridor"] == selected]
fig_trend = go.Figure()
for corridor in trend_df["corridor"].unique():
    c_data = trend_df[trend_df["corridor"] == corridor].sort_values("metric_date")
    fig_trend.add_trace(go.Scatter(
        x=c_data["metric_date"],
        y=c_data["risk_score"],
        name=corridor,
        mode="lines+markers",
        line=dict(width=2),
        marker=dict(size=6),
    ))

fig_trend.update_layout(
    paper_bgcolor="#0A0B0F",
    plot_bgcolor="#0A0B0F",
    font=dict(color="#9B9890", family="Inter"),
    xaxis=dict(showgrid=False, color="#444650"),
    yaxis=dict(gridcolor="#1E2028", color="#444650", range=[0, 100]),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=0, r=0, t=10, b=0),
    height=280,
    hovermode="x unified",
)
st.plotly_chart(fig_trend, use_container_width=True)

# ── News feed ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Latest corridor news</div>', unsafe_allow_html=True)

corridor_filter = None if selected == "All corridors" else selected
news_df = load_news(corridor_filter)

if not news_df.empty:
    for _, row in news_df.head(8).iterrows():
        sentiment = float(row["sentiment_score"] or 0)
        s_color = "#FF4444" if sentiment < -0.3 else ("#F5C242" if sentiment < 0 else "#00D4AA")
        s_label = "negative" if sentiment < -0.3 else ("neutral" if sentiment < 0.1 else "positive")
        st.markdown(f"""
        <div style="background:#0F1015;border:1px solid #1E2028;border-left:3px solid {s_color};
                    border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:8px;">
          <div style="font-size:11px;color:#444650;margin-bottom:4px;">
            {row['corridor']} · {row['source']} · <span style="color:{s_color}">{s_label} ({sentiment:+.2f})</span>
          </div>
          <div style="font-size:13px;color:#C2C0B6;">{row['title']}</div>
        </div>""", unsafe_allow_html=True)
else:
    st.info("No news articles found.")

st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)
