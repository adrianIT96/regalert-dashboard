# components/sidebar.py
import dash_mantine_components as dmc
from dash import html, dcc
import datetime

def get_sidebar(source_options, accent='#00CC99'):
    """
    Returns a Mantine-style sidebar component with filters:
    - multi-select source filter
    - date range slider (uses timestamps)
    """
    # convert sources to options
    opts = [{'label': s, 'value': s} for s in source_options]

    # date defaults
    now = datetime.datetime.now()
    min_ts = int((now.replace(year=now.year-2)).timestamp())
    max_ts = int(now.timestamp())

    sidebar = dmc.Paper(
        children=[
            dmc.Group([
                dmc.Image(src="", width=40),  # placeholder for vertical logo
                dmc.Text("RegAlert", weight=700)
            ], position="left"),
            dmc.Space(h=8),
            dmc.Text("Filters", size="sm", color="dimmed"),
            dmc.MultiSelect(id='source-filter', data=opts, value=[o['value'] for o in opts], placeholder="Select sources", maxSelectedValues=10, style={'width':'100%'}),
            dmc.Space(h=12),
            dmc.Text("Date range", size="sm", color="dimmed"),
            dcc.RangeSlider(id='date-range', min=min_ts, max=max_ts, value=[min_ts, max_ts],
                            tooltip={'placement':'bottom', 'always_visible':False}),
            dmc.Space(h=12),
            dmc.Button("Reload Data", id='reload-btn', variant="outline", color="teal", fullWidth=True),
            dmc.Space(h=8),
            dmc.Text("RegAlert • MedTech monitoring", size="xs", color="dimmed")
        ],
        p="md",
        radius="md",
        style={'height':'100vh','background':'#0b0d0e'}
    )
    return sidebar
