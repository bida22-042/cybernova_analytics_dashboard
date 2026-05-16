# dashboard.py
# CyberNova Analytics Dashboard
# Student Name: Amantle Magotho
# Module: CET333 Product Development

import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import time

st.set_page_config(
    page_title="CyberNova Analytics",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
# CONSTANTS & CONFIGURATION
# ================================================================

SRC_SPEND = {
    "google_ads": 12000,
    "linkedin": 9500,
    "webinar": 3000,
    "email_campaign": 2200,
    "direct": 0,
    "referral": 800,
}

API_BASE = "http://localhost:8000"
PALETTE = ["#345EEB", "#059669", "#7C3AED", "#D97706", "#DC2626", "#0891B2"]

EMPLOYEES = [
    {"n": "T. Mokobi", "dept": "Sales"}, {"n": "K. Sithole", "dept": "Sales"},
    {"n": "B. Kefilwe", "dept": "Sales"}, {"n": "L. Dlamini", "dept": "Marketing"},
    {"n": "R. Molefe", "dept": "Marketing"}, {"n": "P. Osei", "dept": "Advertising"},
    {"n": "C. Banda", "dept": "Advertising"}, {"n": "A. Nkosi", "dept": "Support"},
    {"n": "M. Juma", "dept": "Support"},
]
EMP_NAMES = [e["n"] for e in EMPLOYEES]

# ================================================================
# CSS STYLES
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif !important; }
#MainMenu, header, footer, .stDeployButton { visibility: hidden; }
.stApp { background: #F8F9FA; }

[data-testid="stSidebar"] { background: #FFFFFF !important; border-right: 1px solid #E9ECEF; }

.kpi-card {
    background: #FFFFFF; border: 1px solid #E9ECEF; border-radius: 12px;
    padding: 16px 20px; position: relative; overflow: hidden;
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: var(--kpi-color, #345EEB);
}
.kpi-lbl { font-size: 11px; font-weight: 600; text-transform: uppercase; color: #6C757D; margin-bottom: 8px; }
.kpi-val { font-size: 28px; font-weight: 700; color: #212529; }
.kpi-delta { font-size: 12px; margin-top: 6px; }
.kpi-up { color: #28A745; }
.kpi-down { color: #DC3545; }
.kpi-hint { font-size: 11px; color: #ADB5BD; margin-top: 4px; }

.chart-panel {
    background: #FFFFFF; border: 1px solid #E9ECEF;
    border-radius: 12px; padding: 20px; margin-bottom: 20px;
}
.chart-panel-title { font-size: 15px; font-weight: 600; color: #212529; margin-bottom: 4px; }
.chart-panel-sub { font-size: 12px; color: #6C757D; margin-bottom: 16px; }

.story-hl { font-size: 20px; font-weight: 700; color: #212529; margin-bottom: 4px; }
.story-sub { font-size: 13px; color: #6C757D; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ================================================================
# SESSION STATE
# ================================================================
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()

# ================================================================
# API FUNCTIONS
# ================================================================
def fetch_all():
    try:
        r = requests.get(f"{API_BASE}/stream", timeout=5)
        if r.status_code == 200 and r.json():
            df = pd.DataFrame(r.json())
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
    except:
        pass
    return pd.DataFrame()

def fetch_latest():
    try:
        r = requests.get(f"{API_BASE}/latest", timeout=2)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def get_buf():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=2)
        if r.status_code == 200:
            return r.json().get("buffer_size", 0)
    except:
        pass
    return len(st.session_state.df)

# ================================================================
# LOAD DATA
# ================================================================
if st.session_state.df.empty:
    with st.spinner("Connecting to data stream..."):
        st.session_state.df = fetch_all()

df_all = st.session_state.df
if df_all.empty:
    st.warning("No data. Start api.py in a separate terminal.")
    st.code("python api.py")
    st.stop()

np.random.seed(42)
if "revenue" not in df_all.columns:
    df_all["revenue"] = 0
if "emp" not in df_all.columns:
    df_all["emp"] = np.random.choice(EMP_NAMES, size=len(df_all))
    emp_dept = {e["n"]: e["dept"] for e in EMPLOYEES}
    df_all["dept"] = df_all["emp"].map(emp_dept)

# ================================================================
# HELPER FUNCTIONS
# ================================================================
def fmt(n): return f"${n:,.0f}"
def fmtK(n): return f"${n/1000:.1f}k" if n >= 1000 else f"${n:.0f}"
def pct(a, b): return (a - b) / b * 100 if b else 0.0

def kpi_card(col, label, value, delta=None, hint="", color="#345EEB"):
    d = ""
    if delta is not None:
        cls = "kpi-up" if delta >= 0 else "kpi-down"
        arrow = "▲" if delta >= 0 else "▼"
        d = f'<div class="kpi-delta"><span class="{cls}">{arrow} {abs(delta):.1f}%</span> vs prev</div>'
    h = f'<div class="kpi-hint">{hint}</div>' if hint else ""
    col.markdown(
        f'<div class="kpi-card" style="--kpi-color:{color}">'
        f'<div class="kpi-lbl">{label}</div>'
        f'<div class="kpi-val">{value}</div>{d}{h}</div>',
        unsafe_allow_html=True)

def story(headline, sub):
    st.markdown(f'<div class="story-hl">{headline}</div><div class="story-sub">{sub}</div>', unsafe_allow_html=True)

def ctheme(fig, h=400):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#6C757D", size=11),
        xaxis=dict(gridcolor="#E9ECEF", linecolor="#E9ECEF"),
        yaxis=dict(gridcolor="#E9ECEF", linecolor="#E9ECEF"),
        height=h,
        margin=dict(l=40, r=40, t=40, b=80)
    )
    return fig

# ================================================================
# FILTERS (Applied to all tabs)
# ================================================================
with st.sidebar:
    st.markdown('<div style="padding:16px; border-bottom:1px solid #E9ECEF;"><strong>CyberNova</strong><br><span style="font-size:10px;color:#6C757D">Analytics Platform</span></div>', unsafe_allow_html=True)
    
    st.markdown('<div style="font-size:11px; font-weight:600; padding:14px 16px 6px;">FILTERS</div>', unsafe_allow_html=True)
    
    min_d = df_all["timestamp"].min().date()
    max_d = df_all["timestamp"].max().date()
    today = date.today()
    default_start = max(date(2024, 1, 1), min_d)
    default_end = max_d
    
    start_date = st.date_input("From", value=default_start, min_value=min_d, max_value=max_d)
    end_date = st.date_input("To", value=default_end, min_value=min_d, max_value=max_d)
    
    countries = ["All"] + sorted(df_all["country"].unique().tolist())
    sel_c = st.selectbox("Country", countries)
    
    raw_svcs = sorted(df_all["request"].unique().tolist())
    svc_labels = ["All"] + [s.replace("/", "").replace(".php", "").title() for s in raw_svcs]
    sel_sl = st.selectbox("Service", svc_labels)
    sel_s = "All" if sel_sl == "All" else raw_svcs[svc_labels.index(sel_sl) - 1]
    
    st.markdown('<div style="font-size:11px; font-weight:600; padding:14px 16px 6px;">EXPORT</div>', unsafe_allow_html=True)
    csv_bytes = df_all.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv_bytes, file_name=f"cybernova_{datetime.now():%Y%m%d}.csv", mime="text/csv", use_container_width=True)

# Apply filters
mask = (df_all["timestamp"].dt.date >= start_date) & (df_all["timestamp"].dt.date <= end_date)
dff = df_all[mask].copy()
if sel_c != "All":
    dff = dff[dff["country"] == sel_c]
if sel_s != "All":
    dff = dff[dff["request"] == sel_s]

# Previous period for comparison
delta_d = (end_date - start_date).days + 1
prev_s = start_date - timedelta(days=delta_d)
prev_e = start_date - timedelta(days=1)
dfp = df_all[(df_all["timestamp"].dt.date >= prev_s) & (df_all["timestamp"].dt.date <= prev_e)].copy()

st.caption(f"Showing data from {start_date} to {end_date} · {len(dff):,} records")
st.markdown("---")

# ================================================================
# CHART FUNCTIONS
# ================================================================

def requests_by_region_chart(data, key_suffix):
    if data.empty:
        return
    by_region = data.groupby("country").size().reset_index(name="requests").sort_values("requests", ascending=False).head(8)
    fig = px.bar(by_region, x="country", y="requests", color_discrete_sequence=["#345EEB"], text=by_region["requests"].apply(lambda x: f"{x:,}"))
    fig.update_traces(textposition="outside", textfont=dict(size=10))
    fig.update_layout(yaxis_title="Number of Service Requests", xaxis_title="", yaxis=dict(range=[0, by_region["requests"].max() * 1.15]))
    st.plotly_chart(ctheme(fig, 400), use_container_width=True, key=f"req_region_{key_suffix}")

def revenue_by_region_chart(data, key_suffix):
    if data.empty:
        return
    by_region = data.groupby("country")["revenue"].sum().reset_index().sort_values("revenue", ascending=False).head(8)
    fig = px.bar(by_region, x="country", y="revenue", color_discrete_sequence=["#345EEB"], text=by_region["revenue"].apply(fmtK))
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="Revenue ($)", xaxis_title="")
    st.plotly_chart(ctheme(fig, 400), use_container_width=True, key=f"rev_region_{key_suffix}")

def revenue_by_industry_chart(data, key_suffix):
    if data.empty:
        return
    by_industry = data.groupby("industry_sector")["revenue"].sum().reset_index()
    fig = px.pie(by_industry, names="industry_sector", values="revenue", hole=0.5, color_discrete_sequence=PALETTE)
    fig.update_traces(textinfo="percent+label", textfont_size=11)
    fig.update_layout(legend=dict(orientation="v", font=dict(size=10)))
    st.plotly_chart(ctheme(fig, 350), use_container_width=True, key=f"industry_pie_{key_suffix}")

def revenue_by_service_chart(data, key_suffix):
    if data.empty:
        return
    svc_rev = data.groupby("request").agg(revenue=("revenue", "sum"), deals=("converted_to_contract", "sum")).reset_index().sort_values("revenue", ascending=False)
    svc_rev["service_name"] = svc_rev["request"].str.replace("/", "").str.replace(".php", "").str.title()
    svc_rev["service_name"] = svc_rev["service_name"].replace({
        "Aicyberassistant": "AI Cyber Assistant",
        "Networksecurityaudit": "Network Security Audit", 
        "Penetrationtesting": "Penetration Testing",
        "Scheduleconsultation": "Schedule Consultation"
    })
    fig = px.bar(svc_rev, x="service_name", y="revenue", color="revenue", color_continuous_scale="Blues", text=svc_rev["revenue"].apply(fmtK))
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_title="", yaxis_title="Revenue ($)")
    st.plotly_chart(ctheme(fig, 400), use_container_width=True, key=f"service_rev_{key_suffix}")

def roi_by_channel_chart(data, key_suffix):
    ch_data = []
    for src, spend in SRC_SPEND.items():
        if spend == 0:
            continue
        src_df = data[data["marketing_source"] == src]
        src_rev = src_df["revenue"].sum()
        roi = (src_rev - spend) / spend * 100 if spend > 0 else 0
        ch_data.append({"channel": src.replace("_", " ").title(), "roi": roi})
    df_roi = pd.DataFrame(ch_data).sort_values("roi", ascending=False)
    fig = px.bar(df_roi, x="channel", y="roi", color="roi", color_continuous_scale="RdYlGn", text=df_roi["roi"].apply(lambda x: f"{x:.0f}%"))
    fig.add_hline(y=0, line_dash="dot", line_color="#DC3545", annotation_text="Breakeven")
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="ROI (%)", xaxis_title="")
    st.plotly_chart(ctheme(fig, 400), use_container_width=True, key=f"roi_channel_{key_suffix}")

def cost_per_lead_chart(data, key_suffix):
    """Requirement #8: Cost per lead analysis by advertising channel"""
    ch_data = []
    for src, spend in SRC_SPEND.items():
        if spend == 0:
            continue
        src_df = data[data["marketing_source"] == src]
        leads = len(src_df)
        if leads > 0:
            cpl = spend / leads
        else:
            cpl = 0
        ch_data.append({"channel": src.replace("_", " ").title(), "cpl": cpl, "leads": leads})
    df_cpl = pd.DataFrame(ch_data).sort_values("cpl", ascending=True)
    fig = px.bar(df_cpl, x="channel", y="cpl", color="cpl", color_continuous_scale="Blues", text=df_cpl["cpl"].apply(lambda x: f"${x:.0f}"))
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="Cost Per Lead ($)", xaxis_title="")
    st.plotly_chart(ctheme(fig, 400), use_container_width=True, key=f"cpl_{key_suffix}")

def roi_trend_chart(data, key_suffix):
    """Requirement #9: ROI trend analysis over time"""
    if data.empty or len(data) < 10:
        st.info("Not enough data for ROI trend analysis")
        return
    
    data["_m"] = data["timestamp"].dt.to_period("M").astype(str)
    
    monthly_roi_data = []
    for src, spend in SRC_SPEND.items():
        if spend == 0:
            continue
        src_df = data[data["marketing_source"] == src]
        monthly = src_df.groupby("_m").agg(
            revenue=("revenue", "sum"),
            leads=("request", "count")
        ).reset_index()
        
        for _, row in monthly.iterrows():
            month = row["_m"]
            revenue = row["revenue"]
            leads = row["leads"]
            invest = leads * 50
            if invest > 0:
                roi = (revenue - invest) / invest * 100
            else:
                roi = 0
            monthly_roi_data.append({
                "month": month,
                "channel": src.replace("_", " ").title(),
                "roi": round(roi, 1)
            })
    
    if not monthly_roi_data:
        st.info("No ROI trend data available")
        return
    
    df_trend = pd.DataFrame(monthly_roi_data)
    
    fig = px.line(df_trend, x="month", y="roi", color="channel", 
                  markers=True, title="ROI Trend Over Time by Channel")
    fig.add_hline(y=0, line_dash="dot", line_color="#DC3545", annotation_text="Breakeven")
    fig.update_layout(
        yaxis_title="ROI (%)",
        xaxis_title="Month",
        legend_title="Channel"
    )
    st.plotly_chart(ctheme(fig, 400), use_container_width=True, key=f"roi_trend_{key_suffix}")

def revenue_by_channel_chart(data, key_suffix):
    by_src = data.groupby("marketing_source").agg(revenue=("revenue", "sum"), leads=("request", "count")).reset_index().sort_values("revenue", ascending=False)
    fig = px.bar(by_src, x="marketing_source", y="revenue", color="revenue", color_continuous_scale="Blues", text=by_src["revenue"].apply(fmtK))
    fig.update_traces(textposition='outside')
    fig.update_layout(xaxis_title="", yaxis_title="Revenue ($)")
    st.plotly_chart(ctheme(fig, 400), use_container_width=True, key=f"rev_channel_{key_suffix}")

def satisfaction_trend_chart(data, key_suffix):
    if data.empty:
        return
    data["_d"] = data["timestamp"].dt.date
    trend = data.groupby("_d")["satisfaction_rating"].mean().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["_d"].astype(str), y=trend["satisfaction_rating"], mode="lines+markers", line=dict(color="#D97706", width=2)))
    fig.add_hline(y=3.5, line_dash="dot", line_color="#DC3545", annotation_text="Target 3.5")
    fig.update_layout(yaxis=dict(range=[1, 5]), yaxis_title="Satisfaction Rating", xaxis_title="Date")
    st.plotly_chart(ctheme(fig, 350), use_container_width=True, key=f"satisfaction_trend_{key_suffix}")

def revenue_trend_chart(data, key_suffix):
    if data.empty:
        return
    data["_m"] = data["timestamp"].dt.to_period("M").astype(str)
    mrev = data.groupby("_m")["revenue"].sum().reset_index().sort_values("_m")
    fig = go.Figure(go.Scatter(x=mrev["_m"], y=mrev["revenue"], mode="lines+markers", line=dict(color="#345EEB", width=2.5), fill="tozeroy", fillcolor="rgba(52,94,235,0.05)"))
    fig.update_layout(yaxis_title="Revenue ($)", xaxis_title="Month")
    st.plotly_chart(ctheme(fig, 350), use_container_width=True, key=f"rev_trend_{key_suffix}")

def forecast_chart(data, key_suffix):
    if len(data) < 10:
        st.info("Not enough data for forecasting. Need at least 10 records.")
        return
    
    data["date_only"] = data["timestamp"].dt.date
    daily = data.groupby("date_only")["revenue"].sum().reset_index().sort_values("date_only")
    
    if len(daily) < 5:
        st.info("Need at least 5 days of data for forecast.")
        return
    
    last_7_avg = daily.tail(7)["revenue"].mean()
    last_date = daily["date_only"].iloc[-1]
    last_revenue = daily["revenue"].iloc[-1]
    
    forecast_dates = []
    forecast_values = []
    for i in range(1, 8):
        forecast_dates.append((last_date + timedelta(days=i)).strftime("%b %d"))
        forecast_values.append(last_7_avg * (1 + (i * 0.01)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date_only"].tail(30).astype(str), y=daily["revenue"].tail(30), name="Historical", mode="lines+markers", line=dict(color="#345EEB", width=2.5)))
    fig.add_trace(go.Scatter(x=forecast_dates, y=forecast_values, name="Forecast", mode="lines+markers", line=dict(color="#28A745", width=2.5, dash="dot"), marker=dict(symbol="diamond", size=8)))
    fig.update_layout(yaxis_title="Revenue ($)", xaxis_title="Date")
    st.plotly_chart(ctheme(fig, 400), use_container_width=True, key=f"forecast_{key_suffix}")
    
    total_forecast = sum(forecast_values)
    growth = ((forecast_values[0] - last_revenue) / last_revenue) * 100 if last_revenue > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("7-Day Total", fmtK(total_forecast))
    with col2:
        st.metric("Daily Average", fmtK(total_forecast / 7))
    with col3:
        st.metric("Growth Forecast", f"{growth:+.1f}%")
    
    if growth > 5:
        st.success(f"Revenue expected to increase by {growth:.1f}% over the next 7 days.")
    elif growth < -5:
        st.warning(f"Revenue expected to decrease by {abs(growth):.1f}% over the next 7 days.")
    else:
        st.info(f"Revenue expected to remain stable ({growth:+.1f}%).")

def growth_rate_chart(data, key_suffix):
    if len(data) < 10:
        st.info("Need more data for growth analysis")
        return
    country_growth = []
    for country in data["country"].unique():
        country_df = data[data["country"] == country].sort_values("timestamp")
        if len(country_df) >= 4:
            first_half = country_df.iloc[:len(country_df)//2]["revenue"].sum()
            second_half = country_df.iloc[len(country_df)//2:]["revenue"].sum()
            if first_half > 0:
                growth = ((second_half - first_half) / first_half) * 100
                country_growth.append({"country": country, "growth_rate": round(growth, 1)})
    if not country_growth:
        st.info("No growth data available")
        return
    growth_df = pd.DataFrame(country_growth).sort_values("growth_rate", ascending=False).head(8)
    fig = px.bar(growth_df, x="country", y="growth_rate", color="growth_rate", color_continuous_scale="RdYlGn", text=growth_df["growth_rate"].apply(lambda x: f"{x:.1f}%"))
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis_title="Growth Rate (%)", xaxis_title="")
    st.plotly_chart(ctheme(fig, 400), use_container_width=True, key=f"growth_rate_{key_suffix}")

def world_map_chart(data, key_suffix):
    crev = data.groupby("country")["revenue"].sum().reset_index().rename(columns={"revenue": "Revenue"})
    fig = px.choropleth(crev, locations="country", locationmode="country names", color="Revenue", hover_name="country",
                        color_continuous_scale=[[0, "#E8F4F8"], [0.5, "#90CAF9"], [1, "#345EEB"]])
    fig.update_layout(height=400, geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, key=f"world_map_{key_suffix}")

# ================================================================
# TAB FUNCTIONS (Each tab has its own complete content)
# ================================================================

def overview_tab():
    rev = dff["revenue"].sum()
    prev_rev = dfp["revenue"].sum() if not dfp.empty else rev
    conv = int(dff["converted_to_contract"].sum())
    sat = dff["satisfaction_rating"].mean() if len(dff) else 0
    top_c = dff.groupby("country")["revenue"].sum().idxmax() if len(dff) else "--"
    
    story(f"CyberNova generated {fmt(rev)} across {conv} contracts this period",
          f"{'Up' if rev >= prev_rev else 'Down'} {abs(pct(rev, prev_rev)):.1f}% from previous period · {start_date} to {end_date} · {len(dff):,} records")
    
    cols = st.columns(5)
    kpi_card(cols[0], "Total Revenue", fmt(rev), pct(rev, prev_rev), "All closed contracts", "#345EEB")
    kpi_card(cols[1], "Contracts Closed", f"{conv:,}", None, "Confirmed deals", "#28A745")
    kpi_card(cols[2], "Avg Deal Value", fmt(rev / conv) if conv else "$0", None, "Revenue divided by contracts", "#7C3AED")
    kpi_card(cols[3], "Avg Satisfaction", f"{sat:.1f}/5", None, "CSAT score", "#FD7E14")
    kpi_card(cols[4], "Top Market", top_c, None, "Highest revenue country", "#0891B2")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">Global Revenue Distribution</div><div class="chart-panel-sub">Hover over countries for details</div>', unsafe_allow_html=True)
    world_map_chart(dff, "overview")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.markdown('<div class="chart-panel-title">Service Request Volume by Region</div><div class="chart-panel-sub">Number of service requests per country</div>', unsafe_allow_html=True)
        requests_by_region_chart(dff, "overview")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.markdown('<div class="chart-panel-title">Revenue by Industry</div><div class="chart-panel-sub">Which sectors generate the most value</div>', unsafe_allow_html=True)
        revenue_by_industry_chart(dff, "overview")
        st.markdown('</div>', unsafe_allow_html=True)

def sales_tab():
    rev = dff["revenue"].sum()
    prev_rev = dfp["revenue"].sum() if not dfp.empty else rev
    conv = int(dff["converted_to_contract"].sum())
    prev_c = int(dfp["converted_to_contract"].sum()) if not dfp.empty else conv
    cr = conv / len(dff) * 100 if len(dff) else 0
    sat = dff["satisfaction_rating"].mean() if len(dff) else 0
    avg_deal = rev / conv if conv else 0

    story(f"Sales closed {conv} contracts worth {fmt(rev)} this period",
          f"{'Up' if rev >= prev_rev else 'Down'} {abs(pct(rev, prev_rev)):.1f}% · Conv. rate {cr:.1f}% · Avg deal {fmt(avg_deal)}")

    cols = st.columns(4)
    kpi_card(cols[0], "Revenue Generated", fmt(rev), pct(rev, prev_rev), "From closed contracts", "#345EEB")
    kpi_card(cols[1], "Contracts Closed", f"{conv:,}", pct(conv, prev_c), "Confirmed deals", "#28A745")
    kpi_card(cols[2], "Avg Deal Size", fmt(avg_deal), None, "Target: $3,500+", "#7C3AED")
    kpi_card(cols[3], "Avg Satisfaction", f"{sat:.1f}/5", None, "Post-sale CSAT", "#FD7E14")

    if cr < 8:
        st.warning(f"Conversion rate {cr:.1f}% is below 10% target")

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">Revenue by Region</div><div class="chart-panel-sub">Where revenue is coming from</div>', unsafe_allow_html=True)
    revenue_by_region_chart(dff, "sales")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">Revenue by Service Type</div><div class="chart-panel-sub">Which services generate the most revenue</div>', unsafe_allow_html=True)
    revenue_by_service_chart(dff, "sales")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">Revenue Trend</div><div class="chart-panel-sub">Monthly revenue from closed deals</div>', unsafe_allow_html=True)
    revenue_trend_chart(dff, "sales")
    st.markdown('</div>', unsafe_allow_html=True)

def marketing_tab():
    rev = dff["revenue"].sum()
    prev_rev = dfp["revenue"].sum() if not dfp.empty else rev
    leads = len(dff)
    webinar = int(dff["webinar_registration"].sum())
    wpaper = int(dff["whitepaper_download"].sum())
    sat = dff["satisfaction_rating"].mean() if len(dff) else 0

    story(f"Marketing influenced {fmt(rev)} in revenue across {leads:,} leads",
          f"{'Up' if rev >= prev_rev else 'Down'} {abs(pct(rev, prev_rev)):.1f}%")

    cols = st.columns(5)
    kpi_card(cols[0], "Revenue Influenced", fmt(rev), pct(rev, prev_rev), "From all channels", "#345EEB")
    kpi_card(cols[1], "Leads Generated", f"{leads:,}", None, "Across all sources", "#28A745")
    kpi_card(cols[2], "Webinar Sign-ups", f"{webinar:,}", None, "High-intent leads", "#7C3AED")
    kpi_card(cols[3], "Whitepaper Downloads", f"{wpaper:,}", None, "Security guides downloaded", "#0891B2")
    kpi_card(cols[4], "Avg Satisfaction", f"{sat:.1f}/5", None, "Target at least 4.0", "#FD7E14")

    if rev < prev_rev * 0.9:
        st.error("Revenue down significantly. Activate emergency demand-gen campaigns.")

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">Revenue by Channel</div><div class="chart-panel-sub">Which acquisition source is closing the most value</div>', unsafe_allow_html=True)
    revenue_by_channel_chart(dff, "marketing")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">Satisfaction Trend</div><div class="chart-panel-sub">Daily average CSAT</div>', unsafe_allow_html=True)
    satisfaction_trend_chart(dff, "marketing")
    st.markdown('</div>', unsafe_allow_html=True)

def advertising_tab():
    rev = dff["revenue"].sum()
    total_invest = sum(SRC_SPEND.values())
    net_roi = (rev - total_invest) / total_invest * 100 if total_invest else 0

    story(f"Invested {fmt(total_invest)} — returned {fmt(rev)} in revenue", f"Net ROI {net_roi:.1f}%")

    cols = st.columns(4)
    kpi_card(cols[0], "Total Invested", fmt(total_invest), None, "Across all channels", "#DC3545")
    kpi_card(cols[1], "Revenue Returned", fmt(rev), None, "Total revenue", "#28A745")
    kpi_card(cols[2], "Overall ROI", f"{net_roi:.1f}%", None, "Target above 50%", "#345EEB")

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">ROI by Channel</div><div class="chart-panel-sub">Which channels deliver the best return</div>', unsafe_allow_html=True)
    roi_by_channel_chart(dff, "advertising")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">Cost Per Lead by Channel</div><div class="chart-panel-sub">How much each lead costs per channel</div>', unsafe_allow_html=True)
    cost_per_lead_chart(dff, "advertising")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">ROI Trend Over Time</div><div class="chart-panel-sub">How channel ROI has changed over months</div>', unsafe_allow_html=True)
    roi_trend_chart(dff, "advertising")
    st.markdown('</div>', unsafe_allow_html=True)

def executive_tab():
    rev = dff["revenue"].sum()
    prev_rev = dfp["revenue"].sum() if not dfp.empty else rev
    conv = int(dff["converted_to_contract"].sum())
    total_invest = sum(SRC_SPEND.values())
    net_roi = (rev - total_invest) / total_invest * 100 if total_invest else 0
    sat = dff["satisfaction_rating"].mean() if len(dff) else 0
    cr = conv / len(dff) * 100 if len(dff) else 0

    story(f"CyberNova generated {fmt(rev)} · Net ROI {net_roi:.1f}%",
          f"{'Up' if rev >= prev_rev else 'Down'} {abs(pct(rev, prev_rev)):.1f}% from previous period")

    cols = st.columns(4)
    kpi_card(cols[0], "Total Revenue", fmt(rev), pct(rev, prev_rev), "From all contracts", "#345EEB")
    kpi_card(cols[1], "Net ROI", f"{net_roi:.1f}%", None, f"After {fmt(total_invest)} invested", "#28A745")
    kpi_card(cols[2], "Avg Satisfaction", f"{sat:.1f}/5", None, "Company-wide CSAT", "#FD7E14")
    kpi_card(cols[3], "Conversion Rate", f"{cr:.1f}%", None, "Lead to contract", "#7C3AED")

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">Revenue by Region</div><div class="chart-panel-sub">Geographic revenue breakdown</div>', unsafe_allow_html=True)
    revenue_by_region_chart(dff, "executive")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">7-Day Revenue Forecast</div><div class="chart-panel-sub">Predictive analytics based on historical trends</div>', unsafe_allow_html=True)
    forecast_chart(dff, "executive")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.markdown('<div class="chart-panel-title">Growth Rate by Region</div><div class="chart-panel-sub">Revenue growth rate per country</div>', unsafe_allow_html=True)
    growth_rate_chart(dff, "executive")
    st.markdown('</div>', unsafe_allow_html=True)

# ================================================================
# TABS 
# ================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Sales", "Marketing", "Advertising", "Executive"])

with tab1:
    overview_tab()

with tab2:
    sales_tab()

with tab3:
    marketing_tab()

with tab4:
    advertising_tab()

with tab5:
    executive_tab()

# ================================================================
# REAL-TIME UPDATE
# ================================================================
time.sleep(10)
rec = fetch_latest()
if rec:
    new_row = pd.DataFrame([rec])
    new_row["timestamp"] = pd.to_datetime(new_row["timestamp"])
    if "revenue" not in new_row.columns:
        new_row["revenue"] = 0
    np.random.seed(None)
    new_row["emp"] = np.random.choice(EMP_NAMES)
    emp_dept = {e["n"]: e["dept"] for e in EMPLOYEES}
    new_row["dept"] = new_row["emp"].map(emp_dept)
    st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True).tail(500)
    st.session_state.last_update = datetime.now()
st.rerun()