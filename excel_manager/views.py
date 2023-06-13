from django.shortcuts import render
from django.http import HttpResponse
from .models import ExcelFile
import re
from django.db.models import Q
from datetime import datetime

import calendar

import pandas as pd
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

months_years = [
    f"{month}-{year}" for year in range(2022, 2024) for month in calendar.month_name[1:]
]

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


def home(request):
    if request.method == "POST" and request.FILES.getlist("files"):
        files = request.FILES.getlist("files")

        for file in files:
            filename = file.name
            parts = filename.split()
            project_name = " ".join(
                parts[
                    3 : next(
                        (i for i, part in enumerate(parts) if part.isdigit()),
                        len(parts),
                    )
                ]
            )

            # Extract month and year from the filename
            match = re.search(
                r"\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b",
                filename.upper(),
            )
            month = None
            year = None
            if match:
                keyword = match.group(0)
                month_str = keyword_to_month.get(keyword)
                year_match = re.search(r"\b(\d{4})\b", filename)
                if year_match:
                    year = int(year_match.group(0))
                if month_str:
                    month = datetime.strptime(month_str, "%B").date()
                    if year:
                        month = month.replace(year=year)
                    else:
                        # If no year is found, default to the current year
                        current_year = datetime.now().year
                        month = month.replace(year=current_year)

            excel_file = ExcelFile.objects.filter(filename=filename).first()

            if excel_file:
                # Update the file field and month of the existing object
                excel_file.file = file
                excel_file.month = month
                excel_file.save()
            else:
                # Create a new ExcelFile object
                ExcelFile.objects.create(
                    file=file,
                    month=month,
                    filename=filename,
                    project_name=project_name,
                )

    return render(request, "index.html")

field1='Resource Group Name'
excel_files = ExcelFile.objects.all().order_by("month")

# if not excel_files:
#     # No data within the specified month range
#     message = f"<h1>No files in the database. Please upload</h1>"
#     return HttpResponse(message)

# Create a dictionary to store the combined data for each month
combined_data_dict = {}
for excel_file in excel_files:
    excel_file_path = excel_file.file.path

    # Read Excel file into a DataFrame using pandas, skipping the first 10 rows and last row
    df = pd.read_excel(excel_file_path, skiprows=10, skipfooter=1, usecols=[field1])

    # Keep only the desired columns: field1, field2, and 'Amount'
    # df = df[[field1]]

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

# Combine unique values of field1 for every month
combined_field1_values = []
for df in combined_data_dict.values():
    unique_values = df[field1].unique().tolist()
    combined_field1_values.extend(unique_values)

# Get unique values from the combined list
combined_field1_values = sorted(
    [str(value) for value in set(combined_field1_values)]
)

def line_graph(
    request,
    month1="January",
    month2="December",
    field2="Category",
    field1="Resource Group Name",
):
    if request.method == "POST":
        month_year1 = request.POST.get("month_year1")
        month_year2 = request.POST.get("month_year2")
        field2 = request.POST.get("field2")
        field1value = request.POST.get("field1value")

        # Convert month and year to datetime objects
        datetime_month_year1 = datetime.strptime(month_year1, "%B-%Y")
        datetime_month_year2 = datetime.strptime(month_year2, "%B-%Y")

        query = Q(month__gte=datetime_month_year1, month__lte=datetime_month_year2)

        excel_files = ExcelFile.objects.filter(query).order_by("month")
        print(1)

        if not excel_files:
            # No data within the specified month range
            message = f"<h1>No data available from {month_year1} to {month_year2}</h1>"
            return HttpResponse(message)

        # Create a dictionary to store the combined data for each month
        combined_data_dict = {}

        for excel_file in excel_files:
            excel_file_path = excel_file.file.path

            # Read the Excel file into a dictionary of DataFrames using pandas
            excel_data_dict = pd.read_excel(
                excel_file_path,
                sheet_name=None,  # Read all sheets
                usecols=[field1, field2, 'Amount'],
                skiprows=10,
                skipfooter=1,
            )

            for sheet_name, df in excel_data_dict.items():
                # Filter the DataFrame based on field1value
                df = df[df[field1] == field1value]

                # Groupby field2 
                df = df.groupby(field2, as_index=False)['Amount'].sum()
                
                # Get the month and year of the current sheet
                sheet_month = excel_file.month.strftime("%B")
                sheet_year = excel_file.month.strftime("%Y")

                # Create a unique key combining month and year
                sheet_key = f"{sheet_month}-{sheet_year}"

                if sheet_key not in combined_data_dict:
                    # If the month-year key is not already in the dictionary, create a new key-value pair
                    combined_data_dict[sheet_key] = df
                else:
                    # If the month-year key is already in the dictionary, concatenate the DataFrame with the existing data
                    combined_data_dict[sheet_key] = pd.concat(
                        [combined_data_dict[sheet_key], df],
                        ignore_index=True,
                    )
        # print(combined_data_dict)
        print(2)

        # Combine unique values of field2 for every month
        combined_field2_values = []
        for df in combined_data_dict.values():
            unique_values = df[field2].unique().tolist()
            combined_field2_values.extend(unique_values)

        # Get unique values from the combined list
        combined_field2_values = list(set(combined_field2_values))

        # Forming Graphs
        # if field2value == "All":
        amounts_dict = {}  # Dictionary to store amounts for each field2 value

        for field2_val in combined_field2_values:
            amounts = []  # List to store the amounts

            for month, df in combined_data_dict.items():
                # Search for the row in the column field2 matching the field2_val
                row = df[df[field2] == field2_val]

                if len(row) > 0:
                    # If the row is present, get the corresponding amount
                    amount = row["Amount"].iloc[0]
                else:
                    # If the row is not present, consider the amount as zero
                    amount = 0

                amounts.append(amount)

            amounts_dict[field2_val] = amounts

        # Plotting the line graph
        months = list(combined_data_dict.keys())

        fig = go.Figure()

        # Create traces
        for index, (field2_val, amounts) in enumerate(amounts_dict.items()):
            trace = go.Scatter(
                x=months, y=amounts, mode="lines+markers", name=field2_val
            )

            # Set visibility property for the first three traces to "True", "legendonly" for the rest
            if index < 3:
                trace.visible = True
            else:
                trace.visible = "legendonly"

            fig.add_trace(trace)

        # Add button to toggle visibility of all traces
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    buttons=[
                        dict(
                            label="Toggle All",
                            method="update",
                            args=[
                                {"visible": [True] * len(fig.data)}
                            ],  # Show all traces
                        ),
                        dict(
                            label="Reset",
                            method="update",
                            args=[
                                {
                                    "visible": [True]
                                    + ["legendonly"] * (len(fig.data) - 1)
                                }
                            ],  # Reset visibility to initial state
                        ),
                    ],
                )
            ]
        )

        fig.update_layout(
            xaxis=dict(
                tickmode="array",
                tickvals=months,
                # ticktext=month_years,
                title="Month",
            ),
            yaxis=dict(title="Amount"),
            title=f'Amount for "{field1value}" in "{field2}" from {month_year1} to {month_year2}',
        )
        print(3)
        # fig.show()
        div = pio.to_html(fig, full_html=False)

        context = {
            "months_years": months_years,
            "combined_field1_values": combined_field1_values,
            "graph": div,
        }
        return render(request, "show.html", context)
    fig = go.Figure()
    div = pio.to_html(fig, full_html=False)
    context = {
        "months_years": months_years,
        "graph": div,
        "combined_field1_values": combined_field1_values,
    }

    return render(request, "show.html", context)
