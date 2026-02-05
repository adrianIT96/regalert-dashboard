# app.py
import os
import datetime
import pandas as pd
import sqlite3

import dash
from dash import html, dcc, Input, Output, callback_context
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import plotly.express as px

from components.sidebar import get_sidebar
from components.navbar import get_navbar

# --- CONFIG ---
DB_FILE = "regalert_data.sqlite"
TABLE_NAME = "pubmed_articles"
ACCENT_COLOR = '#00CC99'
PLOTLY_TEMPLATE = 'plotly_dark'

# --- Load Data (defensive) ---
def load_data():
    """Load data from SQLite; return DataFrame with stable Publication_Date and Publication_Year."""
    if not os.path.exists(DB_FILE):
        # Return minimal placeholder
        today = pd.to_datetime(datetime.datetime.now().date())
        return pd.DataFrame([{
            'PMID':'N/A','Title':'No data loaded','Source':'No Source','Publication_Year':datetime.datetime.now().year,
            'Publication_Date': today, 'Categories':'General', 'Source_URL':'', 'Abstract':''
        }])
    try:
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
        conn.close()
    except Exception as e:
        print("ERROR loading DB:", e)
        return pd.DataFrame()

    # Defensive columns
    for col in ['Publication_Year','Publication_Date','Source','Categories','Title','PMID','Source_URL','Abstract']:
        if col not in df.columns:
            df[col] = pd.NA

    df['Publication_Year'] = pd.to_numeric(df['Publication_Year'], errors='coerce').fillna(datetime.datetime.now().year).astype(int)
    df['Publication_Date'] = pd.to_datetime(df['Publication_Date'], errors='coerce')
    na_mask = df['Publication_Date'].isna()
    if na_mask.any():
        df.loc[na_mask, 'Publication_Date'] = pd.to_datetime(df.loc[na_mask, 'Publication_Year'].astype(str) + '-07-01', errors='coerce')
    df['Source'] = df['Source'].fillna('Unknown')
    df['Categories'] = df['Categories'].fillna('General')
    df['Title'] = df['Title'].fillna('')
    df['PMID'] = df['PMID'].fillna('N/A')
    df['Source_URL'] = df['Source_URL'].fillna('')
    return df

df_full = load_data()

# --- Plotly helpers (stable ranges, no autorange jitter) ---
def source_fig(df):
    counts = df['Source'].value_counts().reset_index()
    counts.columns = ['Source','Count']
    if counts.empty:
        return px.pie(names=['No Data'], values=[1], template=PLOTLY_TEMPLATE, title='Data Source Contribution')
    fig = px.pie(counts, names='Source', values='Count', hole=.45, title='Data Source Contribution', template=PLOTLY_TEMPLATE)
    fig.update_layout(margin=dict(l=10,r=10,t=35,b=10), uirevision='source_pie', transition={'duration':0})
    return fig

def category_fig(df):
    all_cats = df['Categories'].astype(str).str.split(', ').explode().dropna()
    counts = all_cats.value_counts().reset_index()
    counts.columns = ['Category','Count']
    if counts.empty:
        return px.bar(title='Top Areas of Interest', template=PLOTLY_TEMPLATE)
    fig = px.bar(counts.sort_values('Count', ascending=True), x='Count', y='Category', orientation='h',
                 title='Top Areas of Interest (AI in MedTech)', template=PLOTLY_TEMPLATE)
    fig.update_layout(margin=dict(l=10,r=10,t=35,b=10), uirevision='category_bar', transition={'duration':0})
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig

def time_series_fig(df):
    if df.empty:
        return px.area(title='Time Trend', template=PLOTLY_TEMPLATE)
    monthly = df.groupby(df['Publication_Date'].dt.to_period('M')).size().reset_index(name='Count')
    monthly['Publication_Date'] = monthly['Publication_Date'].dt.to_timestamp()
    monthly = monthly.sort_values('Publication_Date')
    monthly['Cumulative'] = monthly['Count'].cumsum()
    if monthly.empty:
        return px.area(title='Time Trend', template=PLOTLY_TEMPLATE)
    fig = px.line(monthly, x='Publication_Date', y='Cumulative', title='Total Cumulative Output', template=PLOTLY_TEMPLATE)
    fig.add_traces(px.area(monthly, x='Publication_Date', y='Cumulative', template=PLOTLY_TEMPLATE).data)
    # fix ranges to global
    try:
        x_min = df_full['Publication_Date'].min()
        x_max = df_full['Publication_Date'].max()
        fig.update_xaxes(range=[x_min, x_max], fixedrange=True)
    except Exception:
        pass
    fig.update_yaxes(range=[0, max(df_full.shape[0], int(monthly['Cumulative'].max())) + 5], fixedrange=True)
    fig.update_layout(margin=dict(l=10,r=10,t=35,b=10), uirevision='time_series', transition={'duration':0})
    return fig

def keywords_fig(df, top_n=5):
    pubmed = df[df['Source']=='PubMed']
    if pubmed.empty:
        return px.bar(title='Top Keywords', template=PLOTLY_TEMPLATE)
    text = ' '.join(pubmed['Title'].astype(str).str.lower().tolist())
    words = [w for w in __import__('re').findall(r'\b[a-z]{4,}\b', text) if w not in {'medical','device','study','model','clinical','patients','analysis'}]
    from collections import Counter
    top = Counter(words).most_common(top_n)
    if not top:
        return px.bar(title='Top Keywords', template=PLOTLY_TEMPLATE)
    dfk = pd.DataFrame(top, columns=['Keyword','Frequency'])
    fig = px.bar(dfk.sort_values('Frequency', ascending=True), x='Frequency', y='Keyword', orientation='h', title=f'Top {top_n} Trending Keywords', template=PLOTLY_TEMPLATE)
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(margin=dict(l=10,r=10,t=35,b=10), uirevision='keywords', transition={'duration':0})
    return fig

# --- Dash app / layout (Mantine + simple navbar + sidebar) ---
external_stylesheets = [dbc.themes.DARKLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server

navbar = get_navbar(ACCENT_COLOR)
sidebar = get_sidebar(df_full['Source'].unique().tolist(), ACCENT_COLOR)

# main content for Layout B: more analytic view
def build_main_layout():
    # KPI cards top (compact)
    total = df_full.shape[0]
    pubmed_count = df_full[df_full['Source']=='PubMed'].shape[0]
    regulatory = total - pubmed_count
    latest_year = int(df_full['Publication_Year'].max())

    kpi_cards = dmc.Group(
        children=[
            dmc.Paper([dmc.Text(str(total), weight=700, size=28), dmc.Text("Total Records")], radius="md", p="md", style={'background':'#111216','borderLeft':f'4px solid {ACCENT_COLOR}'}),
            dmc.Paper([dmc.Text(str(regulatory), weight=700, size=28), dmc.Text("Regulatory Records")], radius="md", p="md"),
            dmc.Paper([dmc.Text(str(latest_year), weight=700, size=28), dmc.Text("Latest Year")], radius="md", p="md"),
            dmc.Paper([dmc.Text(str(pubmed_count), weight=700, size=28), dmc.Text("PubMed")], radius="md", p="md")
        ],
        spacing="md",
        position="apart"
    )

    # Layout: left column (bigger) for graphs, right column for controls + small charts + table visible
    left_col = dmc.Stack(
        children=[
            dmc.Paper(dmc.Group([dmc.Title("Time Trend: Total Cumulative Output"),], position="apart"), radius="md", p="sm", style={'background':'#0f1416'}),
            dcc.Graph(id='time-series', figure=time_series_fig(df_full), config={'displayModeBar': False}),
            dmc.Space(h=10),
            dmc.Paper(dmc.Group([dmc.Title("Top Areas of Interest"),], position="apart"), radius="md", p="sm", style={'background':'#0f1416'}),
            dcc.Graph(id='category-chart', figure=category_fig(df_full), config={'displayModeBar': False}),
        ],
        spacing="md"
    )

    right_col = dmc.Stack(
        children=[
            dmc.Paper(dmc.Title("Data Source Contribution"), radius="md", p="sm", style={'background':'#0f1416'}),
            dcc.Graph(id='source-pie', figure=source_fig(df_full), config={'displayModeBar': False}),
            dmc.Space(h=8),
            dmc.Paper(dmc.Title("Top 5 Trending Keywords"), radius="md", p="sm", style={'background':'#0f1416'}),
            dcc.Graph(id='keywords', figure=keywords_fig(df_full), config={'displayModeBar': False}),
            dmc.Space(h=8),
            dmc.Paper(dmc.Title("Data Details / Raw Output"), radius="md", p="sm", style={'background':'#0f1416'}),
            # Data table area (scrollable)
            html.Div(id='data-table-div', children=[
                dbc.Table.from_dataframe(df_full[['PMID','Title','Source','Publication_Year','Categories']].head(20), striped=True, bordered=False, hover=True, className="table-dark table-sm")
            ], style={'maxHeight':'360px','overflowY':'auto','padding':'8px'})
        ],
        spacing="md",
        style={'width':'380px'}
    )

    # Compose full grid
    main_grid = dmc.Grid(
        children=[
            dmc.Col(left_col, span=8),
            dmc.Col(right_col, span=4)
        ],
        gutter="lg"
    )

    page = dmc.Container(
        children=[
            dmc.Space(h=10),
            kpi_cards,
            dmc.Space(h=16),
            main_grid
        ],
        size=1200
    )
    return page

app.layout = dmc.MantineProvider(
    withGlobalStyles=True,
    theme={'colorScheme':'dark'},
    children=[
        dmc.Container([
            navbar,
            dmc.Grid([
                dmc.Col(sidebar, span=2),
                dmc.Col(build_main_layout(), span=10)
            ], gutter="md")
        ], fluid=True)
    ]
)

# --- Callbacks: hook filters (sidebar) -> update graphs & table ---
@app.callback(
    Output('time-series', 'figure'),
    Output('category-chart', 'figure'),
    Output('source-pie', 'figure'),
    Output('keywords', 'figure'),
    Output('data-table-div', 'children'),
    Input('source-filter', 'value'),
    Input('date-range', 'value')
)
def update_all(selected_sources, date_range):
    # Parse date range (timestamp integers)
    try:
        start = datetime.datetime.fromtimestamp(int(date_range[0]))
        end = datetime.datetime.fromtimestamp(int(date_range[1]))
    except Exception:
        start = df_full['Publication_Date'].min()
        end = df_full['Publication_Date'].max()

    # Filter
    filtered = df_full[df_full['Source'].isin(selected_sources)]
    filtered = filtered[(filtered['Publication_Date'] >= pd.to_datetime(start)) & (filtered['Publication_Date'] <= pd.to_datetime(end))]

    # Build updated figures
    t = time_series_fig(filtered)
    c = category_fig(filtered)
    s = source_fig(filtered)
    k = keywords_fig(filtered)

    # Data table (first 200 rows or less)
    display = filtered[['PMID','Title','Source','Publication_Year','Categories']].head(200).copy()
    display['Title'] = display['Title'].apply(lambda x: x if len(str(x))<=150 else str(x)[:147]+'...')
    table = dbc.Table.from_dataframe(display, striped=True, bordered=False, hover=True, className="table-dark table-sm")
    table_wrapped = html.Div(table, style={'maxHeight':'360px','overflowY':'auto','padding':'8px'})

    return t, c, s, k, table_wrapped

if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=8050)
