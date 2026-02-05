import sqlite3
import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Input, Output, dash_table, State, ctx
import plotly.express as px
import plotly.graph_objects as go 
from datetime import datetime

# ======================
# 1. CONFIGURATION & GLOBAL VARIABLES
# ======================
DB_PATH = "data/regalert_data.sqlite"
CATEGORY_COL = "Category_V2"

REG_GLOSSARY = {
    "SaMD": "Software as a Medical Device - Software intended for medical purposes without being part of a hardware medical device.",
    "MDR / IVDR": "Medical Device Regulation / In Vitro Diagnostic Regulation - Core regulatory frameworks in the European Union.",
    "AI Act": "The EU's regulatory framework for AI, categorizing most medical AI as high-risk.",
    "510(k)": "FDA marketing submission to demonstrate that a device is 'substantially equivalent' to a legally marketed device.",
    "PMA": "Pre-Market Approval - The most stringent type of FDA device marketing application.",
    "Class I/II/III": "Device classification based on risk; Class III represents the highest risk.",
    "PMS": "Post-Market Surveillance - Monitoring the safety of a medical device after its release on the market."
}

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM master_data", conn)
    conn.close()
    
    df["Publication_Date"] = pd.to_datetime(df["Publication_Date"], errors="coerce")
    
    # Standardizing dates for FDA sources for demo consistency
    fda_mask = df["Source"] == "FDA"
    if fda_mask.any():
        fda_indices = df[fda_mask].index
        half = len(fda_indices) // 2
        df.loc[fda_indices[:half], "Publication_Date"] = pd.Timestamp('2024-07-01')
        df.loc[fda_indices[half:], "Publication_Date"] = pd.Timestamp('2025-07-01')

    df["Year"] = df["Publication_Date"].dt.year
    df[CATEGORY_COL] = df[CATEGORY_COL].fillna("Uncategorized").replace(["", "Other"], "Uncategorized")
    
    # Domain Mapping for better UI labels
    category_map = {
        "Post_Market_Surveillance": "PMS",
        "Regulatory_Compliance": "Reg. Compliance",
        "Imaging_Devices": "Imaging",
        "Medical_Devices": "Med. Devices",
        "Clinical_Trials": "Clin. Trials",
        "Digital_Health": "DigiHealth"
    }
    df[CATEGORY_COL] = df[CATEGORY_COL].replace(category_map)
    
    # Alert logic (Recalls and Risks)
    alert_keywords = 'Recall|Warning|Safety Notice|Alert|Adverse|Risk|Hazard|Action'
    df['is_alert'] = df['Title'].str.contains(alert_keywords, case=False, na=False)
    
    # AI and SaMD focused filtering logic
    ai_regex = 'AI|Artificial Intelligence|Machine Learning|Deep Learning|Neural|Algorithm|SaMD|Software as a Medical Device'
    df['is_ai'] = df['Title'].str.contains(ai_regex, case=False, na=False) | \
                  df[CATEGORY_COL].str.contains('AI|DigiHealth|SaMD', case=False, na=False)
    
    today = pd.Timestamp.now()
    df = df[df["Publication_Date"] <= today]

    return df[df["Year"] >= 2024]

df = load_data()

# ======================
# 2. UI BRANDING & STYLES
# ======================
BG, CARD, CARD_INNER = "#0B0F14", "#111827", "#0B1220"
TEXT, MUTED, ACCENT = "#E5E7EB", "#9CA3AF", "#00E5C0"
BORDER = "#1f2933"
GREEN, AMBER, RED, BLUE = "#22c55e", "#f59e0b", "#ef4444", "#38bdf8"

SOURCE_COLOR_MAP = {"FDA": "#00E5C0", "EMA": "#7DD3FC", "PubMed": "#0694A2", "MHRA": "#FFFFFF"}
TITLE_STYLE = {"fontWeight": "600", "marginBottom": "10px", "color": TEXT, "fontSize": "13px", "letterSpacing": "0.5px"}

def card(children, style=None):
    base = {"background": CARD, "borderRadius": "12px", "padding": "18px", "border": f"1px solid {BORDER}", "marginBottom": "14px"}
    if style: base.update(style)
    return html.Div(children, style=base)

def pill(text, color, border_only=False):
    style = {
        "border": f"1px solid {color}40", "color": color, "padding": "2px 10px", "borderRadius": "999px",
        "fontSize": "11px", "margin": "3px", "display": "inline-block", "fontWeight": "600", "background": f"{color}08"
    }
    if not border_only:
        style["background"] = f"{color}15"
        style["border"] = f"1px solid {color}"
    return html.Span(text, style=style)

# ======================
# 3. LAYOUT
# ======================
app = Dash(__name__)
server = app.server

app.layout = html.Div([
    # Top Header
    html.Div([
        html.Div("RegAlert — MedTech Regulatory & Research Monitor", 
                 style={"fontSize": "26px", "fontWeight": "600", "color": ACCENT}),
        html.Div(id="alert-indicator")
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "20px"}),

    html.Div([
        # LEFT COLUMN (Control Panel)
        html.Div([
            card([
                html.Div("Control Panel", style={"fontSize": "18px", "fontWeight": "600", "marginBottom": "15px"}),
                
                # AI Focus Toggle
                html.Div([
                    html.Label("AI & SaMD FOCUS MODE", style={"color": ACCENT, "fontSize": "11px", "fontWeight": "700"}),
                    dcc.Checklist(id="ai-toggle", options=[{"label": " Enabled", "value": "AI"}], 
                                  style={"color": TEXT, "marginTop": "5px"}),
                ], style={"padding": "10px", "background": f"{ACCENT}10", "borderRadius": "8px", "border": f"1px solid {ACCENT}30", "marginBottom": "15px"}),

                # Show All Recalls Button
                html.Button("⚠️ SHOW ALL RECALLS", id="btn-show-alerts", n_clicks=0,
                            style={"width": "100%", "backgroundColor": f"{RED}20", "color": RED, 
                                   "border": f"1px solid {RED}", "borderRadius": "8px", 
                                   "padding": "10px", "fontWeight": "bold", "cursor": "pointer", "marginBottom": "20px"}),
                
                # Filtering Options
                html.Details([
                    html.Summary("🔍 Advanced Filters", style={"color": ACCENT, "cursor": "pointer", "fontWeight": "600", "outline": "none"}),
                    html.Div([
                        html.Br(),
                        html.Div("Search Keywords", style={"color": ACCENT, "fontSize": "12px", "marginBottom": "5px"}),
                        dcc.Input(id="search-input", type="text", placeholder="Search (Siemens, AI...)",
                                style={"width": "100%", "backgroundColor": CARD_INNER, "color": TEXT, "border": f"1px solid {BORDER}", "borderRadius": "8px", "padding": "10px", "boxSizing": "border-box"}),
                        html.Br(), html.Br(),
                        html.Div("Source", style={"color": ACCENT, "fontSize": "12px", "marginBottom": "5px"}),
                        dcc.Dropdown(id="filter-source", options=[{"label": s, "value": s} for s in sorted(df["Source"].unique())], value=sorted(df["Source"].unique()), multi=True),
                        html.Br(),
                        html.Div("Category", style={"color": ACCENT, "fontSize": "12px", "marginBottom": "5px"}),
                        dcc.Dropdown(id="filter-category", options=[{"label": c, "value": c} for c in sorted(df[CATEGORY_COL].unique())], value=sorted(df[CATEGORY_COL].unique()), multi=True),
                        html.Br(),
                        html.Div("Year Range", style={"color": ACCENT, "fontSize": "12px", "marginBottom": "5px"}),
                        dcc.RangeSlider(id="filter-year", min=int(df["Year"].min()), max=int(df["Year"].max()), step=1, value=[int(df["Year"].min()), int(df["Year"].max())], marks={int(y): {"label": str(int(y)), "style": {"color": MUTED, "fontSize": "10px"}} for y in sorted(df["Year"].unique())}),
                    ])
                ]),
                
                # Regulatory Glossary
                html.Div("Regulatory Glossary", style={"color": ACCENT, "fontSize": "14px", "fontWeight": "bold", "marginTop": "25px", "marginBottom": "12px"}),
                html.Div([
                    html.Details([
                        html.Summary(k, style={"color": TEXT, "cursor": "pointer", "fontSize": "12px", "fontWeight": "600", "outline": "none"}),
                        html.P(v, style={"color": MUTED, "fontSize": "11px", "padding": "8px 5px", "lineHeight": "1.4"})
                    ], style={"marginBottom": "8px", "borderBottom": f"1px solid {BORDER}"})
                    for k, v in REG_GLOSSARY.items()
                ])
            ])
        ], style={"width": "280px", "flexShrink": 0}),

        # RIGHT COLUMN (Visuals)
        html.Div([
            # KPI Indicators
            html.Div([
                card([html.Div("TOTAL RECORDS", style={"color": MUTED, "fontSize": "11px"}), html.Div(id="kpi-total", style={"fontSize": "26px", "color": ACCENT, "fontWeight": "700"})]),
                card([html.Div("SCIENTIFIC", style={"color": MUTED, "fontSize": "11px"}), html.Div(id="kpi-scientific", style={"fontSize": "26px", "color": ACCENT, "fontWeight": "700"})]),
                card([html.Div("REGULATORY", style={"color": MUTED, "fontSize": "11px"}), html.Div(id="kpi-regulatory", style={"fontSize": "26px", "color": ACCENT, "fontWeight": "700"})]),
                card([html.Div("LATEST DATA", style={"color": MUTED, "fontSize": "11px"}), html.Div(id="kpi-latest-year", style={"fontSize": "26px", "color": ACCENT, "fontWeight": "700"})]),
            ], style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "14px"}),
            
            # Watchlist & Trends Panel
            html.Div([
                card([
                    html.Div("Strategic Watchlist & Alerts", style=TITLE_STYLE),
                    html.Div(id="panel-watchlist", style={"display": "flex", "flexWrap": "wrap", "gap": "2px"})
                ], style={"gridColumn": "span 2", "marginBottom": "14px"}),
                
                card([
                    html.Div("Emerging Topics", style=TITLE_STYLE),
                    html.Div(id="panel-emerging", style={"display": "flex", "flexWrap": "wrap", "gap": "2px"})
                ], style={"gridColumn": "span 1", "marginBottom": "14px"}),
            ], style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "14px"}),

            # Time Activity Chart
            card([html.Div("Cumulative Activity Over Time", style=TITLE_STYLE), dcc.Graph(id="chart-time", style={"height": "300px"})]),
            
            # Evidence Gap Analysis
            card([
                html.Div("Evidence Gap Analysis", style=TITLE_STYLE),
                dcc.Graph(id="chart-gap", className="gap-chart-rounded", style={"height": "350px"})
            ]),

            # Quarterly Domain Trends
            card([html.Div("Domain Trends (Quarterly)", style=TITLE_STYLE), dcc.Graph(id="chart-trends", style={"height": "350px"})]),

            # Source & Recall Radar
            html.Div([
                card([html.Div("Activity by Source", style=TITLE_STYLE), dcc.Graph(id="chart-source", style={"height": "350px"})]),
                card([html.Div("Recall Radar", style=TITLE_STYLE), dcc.Graph(id="chart-recall-causes", style={"height": "350px"})]),
            ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "14px"}),
            
            # Concentration Bar Chart
            card([
                html.Div("Top Domains Concentration", style=TITLE_STYLE),
                dcc.Graph(id="chart-top-domains", className="domains-chart-rounded", style={"height": "400px"})
            ]),
            
            # Main Data Table
            card([
                html.Div("Records Explorer", style=TITLE_STYLE), 
                dash_table.DataTable(
                    id="records-table",
                    page_size=12,
                    page_action='native',
                    sort_action="native",
                    filter_action="native",
                    active_cell=None,
                    style_table={"overflowX": "auto", "borderRadius": "8px", "border": "none"},
                    style_cell={
                        "backgroundColor": CARD,
                        "color": TEXT,
                        "fontSize": "13px",
                        "textAlign": "left",
                        "padding": "12px 15px",
                        "fontFamily": "Inter, sans-serif",
                        "borderBottom": f"1px solid {BORDER}",
                        "borderTop": "none", "borderLeft": "none", "borderRight": "none",
                    },
                    style_header={
                        "backgroundColor": CARD_INNER,
                        "fontWeight": "700",
                        "color": ACCENT,
                        "borderBottom": f"2px solid {ACCENT}",
                        "textTransform": "uppercase",
                        "fontSize": "11px",
                        "letterSpacing": "1px"
                    },
                    style_data_conditional=[
                        {
                            'if': {'column_id': CATEGORY_COL},
                            'color': ACCENT,
                            'fontWeight': 'bold'
                        }
                    ],
                    css=[{
                        'selector': '.dash-spreadsheet-container .dash-spreadsheet-inner td',
                        'rule': 'border: none !important;'
                    }, {
                        'selector': 'tr',
                        'rule': f'border-bottom: 1px solid {BORDER} !important;'
                    }]
                )
            ])
        ], style={"flex": 1, "marginLeft": "20px", "minWidth": "0"})
    ], style={"display": "flex", "maxWidth": "1600px", "margin": "0 auto"})
], style={"padding": "25px", "backgroundColor": BG})

# ======================
# 4. CALLBACKS
# ======================
@app.callback(
    [Output("kpi-total", "children"), Output("kpi-scientific", "children"), Output("kpi-regulatory", "children"), Output("kpi-latest-year", "children"),
     Output("panel-watchlist", "children"), Output("panel-emerging", "children"), Output("chart-time", "figure"), 
     Output("chart-trends", "figure"), Output("chart-source", "figure"),
     Output("chart-top-domains", "figure"), Output("chart-recall-causes", "figure"), 
     Output("chart-gap", "figure"),
     Output("records-table", "data"), Output("records-table", "columns"), Output("alert-indicator", "children")],
    [Input("filter-source", "value"), Input("filter-category", "value"), Input("filter-year", "value"),
     Input("btn-show-alerts", "n_clicks"), Input("search-input", "value"),
     Input("ai-toggle", "value")]
)
def update_dashboard(sources, categories, years, n_clicks, search_text, ai_mode):
    triggered_id = ctx.triggered_id
    dff = df.copy()
    
    # AI Filtering Mode
    if ai_mode and "AI" in ai_mode:
        dff = dff[dff['is_ai'] == True]

    # Alert Filtering Logic
    if triggered_id == "btn-show-alerts" and n_clicks > 0:
        dff = dff[dff['is_alert'] == True]
    else:
        dff = dff[(dff["Source"].isin(sources)) & (dff[CATEGORY_COL].isin(categories)) & 
                  (dff["Year"] >= int(years[0])) & (dff["Year"] <= int(years[1]))]

    # Keyword Search
    if search_text:
        dff = dff[dff['Title'].str.contains(search_text, case=False, na=False)]

    # Handle empty states
    if dff.empty:
        empty_fig = px.scatter().update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        return "0", "0", "0", "N/A", "No Data", "No Trends", empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, [], [], ""

    # Emerging Topics Mapping
    recent_date = dff["Publication_Date"].max() - pd.Timedelta(days=180)
    recent_df = dff[dff["Publication_Date"] >= recent_date]
    trends_map = {"Cyber": "Cyber|Security", "GenAI": "Generative|LLM", "DigiHealth": "App|Software", "Sustainability": "Green|Circular"}
    
    emerging_pills = [pill(f"{label} ({recent_df[recent_df['Title'].str.contains(regex, case=False, na=False)].shape[0]})", ACCENT, border_only=True) 
                      for label, regex in trends_map.items() if recent_df[recent_df['Title'].str.contains(regex, case=False, na=False)].shape[0] > 0]

    # Global Alert Indicator badge
    alert_badge = pill(f"🚨 {len(dff[dff['is_alert'] == True])} SAFETY ALERTS", RED) if len(dff[dff['is_alert'] == True]) > 0 else pill("✅ SYSTEM STABLE", GREEN)

    # Time Area Chart
    ts = dff.groupby(pd.Grouper(key="Publication_Date", freq="ME")).size().reset_index(name="count")
    ts["cum"] = ts["count"].cumsum()
    fig_time = px.area(ts, x="Publication_Date", y="cum", color_discrete_sequence=[ACCENT])
    fig_time.update_traces(line_shape='spline')

    # Domain Trends
    top_cats = dff[CATEGORY_COL].value_counts().head(7).index.tolist()
    q_df = dff[dff[CATEGORY_COL].isin(top_cats)].copy()
    q_df = q_df.assign(Q=lambda x: x["Publication_Date"].dt.to_period("Q").dt.to_timestamp())\
              .groupby(["Q", CATEGORY_COL]).size().reset_index(name="Count")
    fig_trends = px.area(q_df, x="Q", y="Count", color=CATEGORY_COL, color_discrete_sequence=px.colors.qualitative.Bold)
    fig_trends.update_traces(line_shape='spline', fill='tonexty')

    # Source Donut Chart
    fig_source = px.pie(dff, names="Source", hole=0.7, color="Source", color_discrete_map=SOURCE_COLOR_MAP)
    fig_source.update_traces(
        marker=dict(line=dict(color=CARD, width=2)), 
        opacity=0.65, 
        textinfo='percent', 
        textposition='outside'
    )

    # Horizontal Bar Chart (Concentration)
    dom_df = dff[CATEGORY_COL].value_counts().reset_index(name="Count").head(10).sort_values("Count")
    fig_top = px.bar(dom_df, x="Count", y=CATEGORY_COL, orientation="h")
    fig_top.update_traces(
        marker_color=ACCENT,
        marker_opacity=0.6,
        marker_line_color=ACCENT,
        marker_line_width=1.5
    )
    # Applying bar corner radius for modern look
    try: fig_top.update_layout(barcornerradius=8) 
    except: pass

    # Recall Causes Radar Chart
    alert_only_df = dff[dff['is_alert'] == True]
    causes = {"Software/AI": "Software|Algorithm", "Labeling": "Labeling|Manual", "Physical": "Break|Hardware", "Sterility": "Sterile|Infection", "Battery": "Battery|Power"}
    radar_data = [{"r": alert_only_df[alert_only_df['Title'].str.contains(reg, case=False, na=False)].shape[0] if not alert_only_df.empty else 0, "theta": lab} for lab, reg in causes.items()]
    fig_causes = px.line_polar(pd.DataFrame(radar_data), r='r', theta='theta', line_close=True)
    fig_causes.update_traces(fill='toself', line_color=ACCENT, fillcolor='rgba(0, 229, 192, 0.2)', line_shape='spline')

    # Evidence Gap Analysis Chart
    gap_data = dff.groupby([pd.Grouper(key="Publication_Date", freq="QE"), "Source"]).size().unstack(fill_value=0)
    fig_gap = go.Figure()
    if "PubMed" in gap_data.columns:
        fig_gap.add_trace(go.Scatter(x=gap_data.index, y=gap_data["PubMed"], name="Research (PubMed)",
                                     line=dict(color="#a855f7", width=3, shape='spline'), fill='tozeroy'))
    if "FDA" in gap_data.columns:
        fig_gap.add_trace(go.Bar(x=gap_data.index, y=gap_data["FDA"], name="Regulatory (FDA)",
                                 marker_color=ACCENT, yaxis="y2", opacity=0.6, width=1500000000))
    
    try: fig_gap.update_layout(barcornerradius=8)
    except: pass
    fig_gap.update_layout(yaxis=dict(title="Research Volume"), yaxis2=dict(title="Regulatory Volume", overlaying="y", side="right"))

    # Applying Global Dark Theming
    for f in [fig_time, fig_trends, fig_source, fig_top, fig_causes, fig_gap]:
        f.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                        margin=dict(l=40, r=40, t=30, b=40), showlegend=True if f in [fig_trends, fig_gap] else False)

    # Watchlist items
    watchlist = [pill(f"ALERT: {row['Title'][:35]}...", RED, border_only=True) for _, row in dff[dff['is_alert']].head(3).iterrows()]
    
    # Table Data Formatting
    t_data = dff.sort_values("Publication_Date", ascending=False).to_dict("records")
    for row in t_data:
        if isinstance(row["Publication_Date"], pd.Timestamp):
            row["Publication_Date"] = row["Publication_Date"].strftime('%Y-%m-%d')

    t_cols = [
        {"name": "Date", "id": "Publication_Date"},
        {"name": "Source", "id": "Source"},
        {"name": "Category", "id": CATEGORY_COL},
        {"name": "Title", "id": "Title"}
    ]

    latest_str = dff["Publication_Date"].max().strftime('%d %b %Y')

    return (f"{len(dff):,}", f"{len(dff[dff['Source']=='PubMed']):,}", f"{len(dff[dff['Source']=='FDA']):,}", latest_str, 
            watchlist, emerging_pills, fig_time, fig_trends, fig_source, fig_top, fig_causes, fig_gap, t_data, t_cols, alert_badge)

if __name__ == "__main__":
    app.run(debug=True)