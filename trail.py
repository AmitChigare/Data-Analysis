from django.shortcuts import render, HttpResponse, redirect
from .models import ExcelFile
import re
from django.db.models import Q
from datetime import datetime

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

                ExcelFile.objects.create(file=file, month=month)
        else:
            return redirect(display_files, month1=month1, month2=month2, field=field)
    return render(request, "upload.html", {"months": months})


def display_files(request, month1="January", month2="February", field="Location"):
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
            # Group the combined data by 'Meter Name' and calculate the sum of 'Amount'
            grouped_data = combined_data.groupby(field)["Amount"].sum().reset_index()

            # Find the row with the maximum and minimum amounts
            max_amount_row = grouped_data.loc[grouped_data["Amount"].idxmax()]
            min_amount_row = grouped_data.loc[grouped_data["Amount"].idxmin()]

            # Find the row with the second maximum amount
            sorted_data = grouped_data.sort_values("Amount", ascending=False)
            second_max_amount_row = sorted_data.iloc[1]

            # Calculate the percentage of the amount for each bar
            max_amount_percentage = (
                max_amount_row["Amount"] / grouped_data["Amount"].sum()
            ) * 100
            min_amount_percentage = (
                min_amount_row["Amount"] / grouped_data["Amount"].sum()
            ) * 100
            second_max_amount_percentage = (
                second_max_amount_row["Amount"] / grouped_data["Amount"].sum()
            ) * 100

            # Add the maximum, second maximum, and minimum traces to the subplot
            fig.add_trace(
                go.Bar(
                    x=[
                        max_amount_row[field],
                        second_max_amount_row[field],
                        min_amount_row[field],
                    ],
                    y=[
                        max_amount_row["Amount"],
                        second_max_amount_row["Amount"],
                        min_amount_row["Amount"],
                    ],
                    name=f"{month}",
                    marker_color=["green", "blue", "red"],
                    text=[
                        f"Max: {max_amount_row['Amount']:.2f} ({max_amount_percentage:.2f}%)",
                        f"Second Max: {second_max_amount_row['Amount']:.2f} ({second_max_amount_percentage:.2f}%)",
                        f"Min: {min_amount_row['Amount']:.2f} ({min_amount_percentage:.2f}%)",
                    ],
                    textposition="auto",
                ),
                row=1,
                col=col_num,
            )

            col_num += 1

    # Update the subplot layout
    fig.update_layout(
        title="Max, Second Max, and Min Amounts by Month", showlegend=False
    )

    # Convert the plotly figure to HTML
    graph_html = fig.to_html(full_html=False)

    # Create the Django response
    response = HttpResponse(content_type="text/html")

    # Write the graph HTML to the response
    response.write(graph_html)

    return response
