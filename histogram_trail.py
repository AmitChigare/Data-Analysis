import dash
from dash import html, dcc
import dash_mantine_components as dmc
import pandas as pd
import base64
import io
import plotly.express as px

style = {
    "border": f"1px solid {dmc.theme.DEFAULT_COLORS['indigo'][4]}",
    "textAlign": "center",
}


# Create the app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div(
    [
        html.H1("Histogram Dashboard"),
        html.Hr(),
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Drag and Drop or ", html.A("Select Excel File")]),
            style={
                "width": "50%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px 0",
            },
            multiple=False,
        ),
        html.Div(
            [
                dcc.Dropdown(
                    id="x-axis",
                    options=[],
                    placeholder="Select X-Axis",
                    style={"width": "100%"},
                ),
                dcc.Dropdown(
                    id="color",
                    options=[],
                    placeholder="Select Color",
                    style={"width": "100%"},
                ),
            ],
            style={"display": "flex", "margin": "20px 0", "gap": "100px"},
        ),
        dcc.Graph(id="histogram"),
    ]
)


# Callback to handle the file upload and populate dropdowns
@app.callback(
    [
        dash.dependencies.Output("x-axis", "options"),
        dash.dependencies.Output("color", "options"),
        dash.dependencies.Output("color", "value"),
    ],
    [
        dash.dependencies.Input("upload-data", "contents"),
        dash.dependencies.Input("x-axis", "value"),
    ],
)
def update_dropdowns(contents, selected_x_axis):
    if contents is not None:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))

        # Populate the x-axis dropdown options
        x_options = [{"label": col, "value": col} for col in df.columns]

        # Exclude selected_x_axis from the color dropdown options
        color_options = [
            {"label": col, "value": col} for col in df.columns if col != selected_x_axis
        ]

        # Set default color value to the first option in color_options
        # color_value = color_options[0]["value"] if color_options else None
        color_value = None

        return x_options, color_options, color_value

    return [], [], None


# Callback to update the histogram graph
@app.callback(
    dash.dependencies.Output("histogram", "figure"),
    [
        dash.dependencies.Input("x-axis", "value"),
        dash.dependencies.Input("color", "value"),
    ],
    [dash.dependencies.State("upload-data", "contents")],
)
def update_histogram(x_axis, color, contents):
    if contents is not None and x_axis is not None:
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))

        fig = px.histogram(
            df, x=x_axis, y="Amount", color=color, histfunc="avg", barmode="group"
        )
        fig.update_xaxes(categoryorder="total descending")
        return fig

    return {}


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
