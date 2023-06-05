import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import base64, io
import plotly.graph_objs as go


# Initialize the Dash application
app = dash.Dash(__name__)

# Define the layout of the application
app.layout = html.Div(
    [
        html.H1("Bar, Tree and Tabular Representation"),
        html.Hr(),
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
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
        dcc.Dropdown(
            id="column-dropdown",
            options=[],
            placeholder="Select column",
            multi=False,
            style={"width": "60%", "margin": "20px 0"},
        ),
        html.Div(
            [
                html.H3("Tabular Columns"),
                dcc.Dropdown(
                    id="row-dropdown",
                    options=[],
                    placeholder="Select row",
                    multi=True,
                    style={"width": "60%", "margin": "20px 0"},
                ),
                html.Link(rel="stylesheet", href="/assets/styles.css"),
                html.Div(id="selected-rows", className="styled-table"),
            ]
        ),
        html.Div(
            [
                html.Div([dcc.Graph(id="bar-chart")], className="six columns"),
                html.Div([dcc.Graph(id="alternative-chart")], className="six columns"),
            ],
            className="row",
        ),
    ]
)


# Store the DataFrame in app UserData
def store_dataframe(contents):
    if contents is not None:
        content_type, content_string = contents.split(",")

        # Decode the file contents
        decoded = base64.b64decode(content_string)

        # Read the Excel file into a DataFrame
        df = pd.read_excel(io.BytesIO(decoded))

        app.userData["dataframe"] = df


# Callback function to handle file upload and populate the dropdown options
@app.callback(Output("column-dropdown", "options"), Input("upload-data", "contents"))
def update_dropdown(contents):
    if contents is not None:
        store_dataframe(contents)

        # Retrieve the stored DataFrame
        df = app.userData.get("dataframe")

        # Create dropdown options from column names
        options = [{"label": col, "value": col} for col in df.columns]

        return options

    return []


# Callback function to display the bar chart
@app.callback(Output("bar-chart", "figure"), Input("column-dropdown", "value"))
def display_bar_chart(selected_column):
    if selected_column:
        # Retrieve the stored DataFrame
        df = app.userData.get("dataframe")

        # Group by the selected column and sum the Amount
        grouped_df = df.groupby(selected_column)["Amount"].sum().reset_index()

        # Calculate the percentages
        grouped_df["percentage"] = (
            grouped_df["Amount"] / grouped_df["Amount"].sum() * 100
        )

        grouped_df=grouped_df.sort_values('Amount', ascending=False)

        # Create the bar chart
        data = [
            go.Bar(
                x=grouped_df[selected_column],
                y=grouped_df["Amount"],
                marker=dict(color="rgb(65,105,225)"),
                text=grouped_df["percentage"].round(2).astype(str) + "%",
                textposition="auto",
            )
        ]

        layout = go.Layout(
            title=f"Bar Chart: {selected_column}",
            xaxis=dict(title=selected_column),
            yaxis=dict(title="Amount"),
        )

        return go.Figure(data=data, layout=layout)

    return {}


# Callback function to display the alternative chart
@app.callback(Output("alternative-chart", "figure"), Input("column-dropdown", "value"))
def display_alternative_chart(selected_column):
    if selected_column:
        # Retrieve the stored DataFrame
        df = app.userData.get("dataframe")

        # Group by the selected column and sum the Amount
        grouped_df = df.groupby(selected_column)["Amount"].sum().reset_index()

        # Calculate the percentages
        grouped_df["percentage"] = (
            grouped_df["Amount"] / grouped_df["Amount"].sum() * 100
        )

        # Create the alternative chart using a treemap
        data = [
            go.Treemap(
                labels=grouped_df[selected_column],
                parents=[""]
                * len(
                    grouped_df
                ),  # Set all parents to empty string to create a single-level treemap
                values=grouped_df["Amount"],
                text=grouped_df["percentage"].round(2).astype(str) + "%",
                hovertemplate="Label: %{label}<br>Value: %{value}<br>Percentage: %{text}",
                textinfo="label+value+text",
                branchvalues="total",
                marker_colors=grouped_df["Amount"],  # Color based on Amount values
                # hovertemplate="%{label}<br>Amount: %{color:.2f}",
            )
        ]

        layout = go.Layout(
            title=f"Treemap: {selected_column}",
        )

        return go.Figure(data=data, layout=layout)

    return {}


# Callback function to populate the row dropdown options based on the selected column
@app.callback(Output("row-dropdown", "options"), Input("column-dropdown", "value"))
def update_row_dropdown(selected_column):
    if selected_column:
        # Retrieve the stored DataFrame
        df = app.userData.get("dataframe")

        # Get unique values from the selected column
        unique_values = df[selected_column].unique()

        # Create dropdown options from unique values
        options = [{"label": str(value), "value": value} for value in unique_values]

        return options

    return []


# Callback function to display the selected rows
@app.callback(
    Output("selected-rows", "children"),
    Input("row-dropdown", "value"),
    State("column-dropdown", "value"),
)
def display_selected_rows(selected_rows, selected_column):
    if selected_rows and selected_column:
        # Retrieve the stored DataFrame
        df = app.userData.get("dataframe")

        # Filter the DataFrame based on selected rows and column
        filtered_df = df[df[selected_column].isin(selected_rows)]

        # Convert the filtered DataFrame to an HTML table
        table = html.Table(
            [
                html.Thead(html.Tr([html.Th(col) for col in filtered_df.columns])),
                html.Tbody(
                    [
                        html.Tr([html.Td(str(value)) for value in row])
                        for row in filtered_df.values
                    ]
                ),
            ],
            className="styled-table",
        )

        return table

    return ""


# Add CSS styles for the table
app.css.append_css(
    {
        "external_url": "https://cdn.jsdelivr.net/npm/semantic-ui@2.0.8/dist/semantic.min.css"
    }
)

# Run the Dash application
if __name__ == "__main__":
    app.userData = {}  # Initialize app UserData
    app.run_server(debug=True)
