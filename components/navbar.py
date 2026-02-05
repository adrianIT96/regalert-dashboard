# components/navbar.py
from dash import html
import dash_mantine_components as dmc

def get_navbar(accent='#00CC99'):
    # Simple navbar with inline svg logo and title + theme toggle placeholder
    svg_logo = html.Div([
        html.Span([
            html.Span(style={'display':'inline-block','width':'28px','height':'28px','background':accent,'borderRadius':'6px','marginRight':'8px'}),
            html.Strong("RegAlert", style={'verticalAlign':'middle','color':'#fff','marginLeft':'6px'})
        ])
    ], style={'display':'flex','alignItems':'center'})

    nav = dmc.Header(
        height=60,
        children=dmc.Container(
            dmc.Group([
                svg_logo,
                dmc.Space(),
                dmc.Text("Global MedTech Regulatory Dashboard", size="sm", color="dimmed")
            ], position="apart", align="center"),
            fluid=True
        )
    )
    return nav
