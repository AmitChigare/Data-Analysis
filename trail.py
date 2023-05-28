from django.shortcuts import render, HttpResponse, redirect
from .models import ExcelFile
import re
from django.db.models import Q
from datetime import datetime

import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px

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
            return redirect(display_files, month1=month1, month2=month2)
    return render(request, "upload.html", {"months": months})


def display_files(request, month1="January", month2="February"):
    # Convert month names to datetime objects
    datetime_month1 = datetime.strptime(month1, "%B")
    datetime_month2 = datetime.strptime(month2, "%B")

    query = Q(
        month__month__gte=datetime_month1.month, month__month__lte=datetime_month2.month
    )

    excel_files = ExcelFile.objects.filter(query)
    if not excel_files:
        # No data within the specified month range
        message = f"No data available from {month1} to {month2}"
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

    # Create a list to store the graph HTML for each unique month
    graph_html_list = []

    for month, combined_data in combined_data_dict.items():
        if not combined_data.empty:
            # Group the combined data by 'Meter Name' and calculate the sum of 'Amount'
            grouped_data = (
                combined_data.groupby("Meter Name")["Amount"].sum().reset_index()
            )

            # Find the row with the maximum and minimum amounts
            max_amount_row = grouped_data.loc[grouped_data["Amount"].idxmax()]
            min_amount_row = grouped_data.loc[grouped_data["Amount"].idxmin()]

            # Combine the rows into a new DataFrame and transpose it
            selected_rows = pd.concat([max_amount_row, min_amount_row], axis=1).T

            # Create the Plotly graph for the selected rows
            fig = px.bar(selected_rows, x="Meter Name", y="Amount")

            # Customize the graph layout if needed
            fig.update_layout(
                title=f"Amount by Meter Name ({month})",
                xaxis_title="Meter Name",
                yaxis_title="Amount",
            )

            # Convert the Plotly figure to HTML
            graph_html = fig.to_html(full_html=False)

            # Append the graph HTML to the list
            graph_html_list.append(graph_html)

    # Create the Django response
    response = HttpResponse(content_type="text/html")

    # Write the graph HTML for each unique month to the response
    for graph_html in graph_html_list:
        response.write(graph_html)

    return response
