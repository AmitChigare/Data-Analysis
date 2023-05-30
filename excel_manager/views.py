from django.shortcuts import render, HttpResponse, redirect
from .models import ExcelFile
import re
from django.db.models import Q
from datetime import datetime
import os

import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px

import io
import base64
import pandas as pd
import plotly.subplots as sp
import plotly.graph_objects as go

# Mapping of keywords to months
keyword_to_month = {
    "JAN": "January",
    "FEB": "February",
    "MAR": "March",
    "APR": "April",
    "MAY": "May",
    "JUN": "June",
    "JUL": "July",
    "AUG": "August",
    "SEP": "September",
    "OCT": "October",
    "NOV": "November",
    "DEC": "December",
}
months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def upload_file(request):
    if request.method == "POST":
        month1 = request.POST.get("month1")
        month2 = request.POST.get("month2")
        field = request.POST.get("field")
        field2 = request.POST.get("field2")

        if request.FILES.getlist("files"):
            files = request.FILES.getlist("files")

            for file in files:
                keyword = file.name

                match = re.search(
                    r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b",
                    keyword.upper(),
                )

                if match:
                    keyword = match.group(0)
                    month = datetime.strptime(keyword_to_month[keyword], "%B").date()
                else:
                    month = None

                filename = file.name
                project_name = "random"
                excel_file = ExcelFile.objects.filter(filename=filename).first()

                if excel_file:
                    # Update the file field of the existing object
                    excel_file.file = file
                    excel_file.save()
                else:
                    # Create a new ExcelFile object
                    ExcelFile.objects.create(
                        file=file,
                        month=month,
                        filename=filename,
                        project_name=project_name,
                    )
        else:
            return redirect(
                display_files, month1=month1, month2=month2, field=field, field2=field2
            )
    return render(request, "upload.html", {"months": months})


from django.urls import reverse


def display_files(
    request, month1="January", month2="February", field="Location", field2="Meter Name"
):
    # Convert month names to datetime objects
    datetime_month1 = datetime.strptime(month1, "%B")
    datetime_month2 = datetime.strptime(month2, "%B")

    query = Q(
        month__month__gt=datetime_month1.month, month__month__lte=datetime_month2.month
    )

    excel_files = ExcelFile.objects.filter(query)
    if not excel_files:
        # No data within the specified month range
        message = f"<h1>No data available from {month1} to {month2}</h1>"
        return HttpResponse(message)

    # Create a dictionary to store the combined data for each month
    combined_data_dict = {}

    for excel_file in excel_files:
        excel_file_path = excel_file.file.path

        # Read Excel file into a DataFrame using pandas, skipping the first 10 rows and last row
        df = pd.read_excel(excel_file_path, skiprows=10, skipfooter=1)

        # Get the month of the current file
        file_month = excel_file.month.strftime("%B")

        if file_month not in combined_data_dict:
            # If the month is not already in the dictionary, create a new key-value pair
            combined_data_dict[file_month] = df
        else:
            # If the month is already in the dictionary, concatenate the DataFrame with the existing data
            combined_data_dict[file_month] = pd.concat(
                [combined_data_dict[file_month], df], ignore_index=True
            )

    # Create the Plotly subplots for the combined data
    fig = sp.make_subplots(
        rows=1,
        cols=len(combined_data_dict),
        subplot_titles=list(combined_data_dict.keys()),
    )

    col_num = 1

    for month, combined_data in combined_data_dict.items():
        if not combined_data.empty:
            # Group the combined data by 'field' and 'field2' and calculate the sum of 'Amount'
            grouped_data = (
                combined_data.groupby([field, field2])["Amount"].sum().reset_index()
            )

            # Find the row with the maximum and minimum amounts for each 'field'
            max_amount_row = (
                grouped_data.groupby(field)["Amount"]
                .idxmax()
                .apply(lambda x: grouped_data.loc[x])
            )
            min_amount_row = (
                grouped_data.groupby(field)["Amount"]
                .idxmin()
                .apply(lambda x: grouped_data.loc[x])
            )

            # Sort the data by 'Amount' in descending order for each 'field'
            sorted_data = (
                grouped_data.groupby(field)
                .apply(lambda x: x.sort_values("Amount", ascending=False))
                .reset_index(drop=True)
            )

            # Calculate the cumulative sum of 'Amount' for each 'field'
            sorted_data["Cumulative Amount"] = sorted_data.groupby(field)[
                "Amount"
            ].cumsum()

            # Add the stacked bar traces to the subplot
            for i, row in sorted_data.iterrows():
                # Get the color for the current field2 value
                color = px.colors.qualitative.Alphabet[
                    i % len(px.colors.qualitative.Alphabet)
                ]

                fig.add_trace(
                    go.Bar(
                        x=[row[field]],
                        y=[row["Amount"]],
                        name=row[field2],
                        marker_color=color,
                        text=f"Amount: {row['Amount']:.2f}<br>Cumulative Amount: {row['Cumulative Amount']:.2f}",
                        textposition="auto",
                    ),
                    row=1,
                    col=col_num,
                )

            col_num += 1

    # Update the subplot layout
    fig.update_layout(
        title="Stacked Bar Graph by Month",
        showlegend=False,
        xaxis=dict(title=field),
        yaxis=dict(title="Amount"),
        barmode="stack",
    )

    # Add a button linking to the /upload URL
    upload_url = reverse(
        "upload_file"
    )  # Assuming the URL name for the upload_file view is "upload_file"
    upload_button = f'<a href="{upload_url}" style="background-color: #4CAF50;color: white;padding: 10px 20px;border-radius: 5px;cursor: pointer;text-decoration:None;">Go to Home</a>'
    graph_html = f"{upload_button}<br><br>" + fig.to_html(full_html=False)

    # Create the Django response
    response = HttpResponse(content_type="text/html")

    # Write the graph HTML to the response
    response.write(graph_html)

    return response
