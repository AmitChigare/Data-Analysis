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
from dash.dependencies import Input, Output
import io
import base64
import pandas as pd
import plotly.subplots as sp
import plotly.graph_objects as go

import matplotlib.pyplot as plt

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


def home(request):
    if request.method == "POST" and request.FILES.getlist("files"):
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
            parts = filename.split()
            project_name = " ".join(
                parts[
                    3 : next(
                        (i for i, part in enumerate(parts) if part.isdigit()),
                        len(parts),
                    )
                ]
            )
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

    return render(request, 'index.html')

def line_graph_method(request):
    if request.method == "POST":
        month1 = request.POST.get("month1")
        month2 = request.POST.get("month2")
        field2 = request.POST.get("field2")

        return redirect("line_graph", month1=month1, month2=month2, field2=field2)

    return render(request, 'line.html', {'months':months})

def stacked_bar_method(request):
    if request.method == "POST":
        month1 = request.POST.get("month1")
        month2 = request.POST.get("month2")
        field = request.POST.get("field")
        field2 = request.POST.get("field2")
        # method = request.POST.get("method")

        return redirect(
            'display_files',
            month1=month1,
            month2=month2,
            field=field,
            field2=field2,
            # method=method,
        )

    return render(request, 'bar.html', {'months':months})


from django.urls import reverse


def display_files(
    request,
    month1="January",
    month2="February",
    field="Location",
    field2="Meter Name",
    # method="Month",
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

        # Get the project_name
        project_name = excel_file.project_name

        # if method == "Month":
        if file_month not in combined_data_dict:
            # If the month is not already in the dictionary, create a new key-value pair
            combined_data_dict[file_month] = df
        else:
            # If the month is already in the dictionary, concatenate the DataFrame with the existing data
            combined_data_dict[file_month] = pd.concat(
                [combined_data_dict[file_month], df], ignore_index=True
            )
        # else:
        #     if project_name not in combined_data_dict:
        #         # If the month is not already in the dictionary, create a new key-value pair
        #         combined_data_dict[project_name] = df
        #     else:
        #         # If the month is already in the dictionary, concatenate the DataFrame with the existing data
        #         combined_data_dict[project_name] = pd.concat(
        #             [combined_data_dict[project_name], df], ignore_index=True
        #         )

    # Create the Plotly subplots for the combined data
    fig = sp.make_subplots(
        rows=1,
        cols=len(combined_data_dict),
        subplot_titles=list(combined_data_dict.keys()),
    )

    col_num = 1

    for month, combined_data in combined_data_dict.items():
        combined_data_dict[month] = df[["Amount", field, field2]]

        # Group by field1 and aggregate the amounts
        df_grouped_field1 = df.groupby(field)["Amount"].sum().reset_index()

        # Update the DataFrame with the aggregated amounts
        combined_data_dict[month] = combined_data_dict[month].merge(
            df_grouped_field1, on=field, suffixes=("", "_sum")
        )

        # Drop duplicate rows and unnecessary columns
        combined_data_dict[month] = combined_data_dict[month].drop_duplicates(
            subset=field
        )
        combined_data_dict[month] = combined_data_dict[month][
            ["Amount_sum", field, field2]
        ]

        # Group by field2 and aggregate the amounts
        df_grouped_field2 = df.groupby(field2)["Amount"].sum().reset_index()

        # Update the DataFrame with the aggregated amounts
        combined_data_dict[month] = combined_data_dict[month].merge(
            df_grouped_field2, on=field2, suffixes=("", "_sum")
        )

        # Drop duplicate rows and unnecessary columns
        combined_data_dict[month] = combined_data_dict[month].drop_duplicates(
            subset=field2
        )
        combined_data_dict[month] = combined_data_dict[month][
            ["Amount_sum", field, field2]
        ]

        if not combined_data.empty:
            # Group the combined data by 'field' and 'field2' and calculate the sum of 'Amount'
            grouped_data = (
                combined_data.groupby([field, field2])["Amount"].sum().reset_index()
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

            # Sort the data by 'Amount' in descending order
            sorted_data = sorted_data.sort_values("Amount", ascending=False)

            sorted_data = sorted_data.head(2)

            # Calculate the total amount for each field
            total_amount = sorted_data["Amount"].sum()

            # Calculate the percentage taken for each row
            sorted_data["Percentage Taken"] = (
                sorted_data["Amount"] / total_amount
            ) * 100

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
                        text=f"Amount: {row['Amount']:.2f}<br>{row['Percentage Taken']:.2f}%",
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
        "home"
    )  # Assuming the URL name for the upload_file view is "upload_file"
    upload_button = f'<a href="{upload_url}" style="background-color: #4CAF50;color: white;padding: 10px 20px;border-radius: 5px;cursor: pointer;text-decoration:None;">Go to Home</a>'
    graph_html = f"{upload_button}<br><br>" + fig.to_html(full_html=False)

    # Create the Django response
    response = HttpResponse(content_type="text/html")

    # Write the graph HTML to the response
    response.write(graph_html)

    return response

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def line_graph(request, month1, month2, field2, field1="Resource Group Name"):
    # Convert month names to datetime objects
    datetime_month1 = datetime.strptime(month1, "%B")
    datetime_month2 = datetime.strptime(month2, "%B")

    query = Q(
        month__month__gt=datetime_month1.month, month__month__lte=datetime_month2.month
    )

    excel_files = ExcelFile.objects.filter(query).order_by('month')
    if not excel_files:
        # No data within the specified month range
        message = f"<h1>No data available from {month1} to {month2}</h1>"
        return HttpResponse(message)

    # Create a dictionary to store the combined data for each month
    combined_data_dict = {}
    combined_data_dict1 = {}

    for excel_file in excel_files:
        excel_file_path = excel_file.file.path

        # Read Excel file into a DataFrame using pandas, skipping the first 10 rows and last row
        df = pd.read_excel(excel_file_path, skiprows=10, skipfooter=1)

        # Get the month of the current file
        file_month = excel_file.month.strftime("%B")

        if file_month not in combined_data_dict:
            # If the month is not already in the dictionary, create a new key-value pair
            combined_data_dict[file_month] = df
            combined_data_dict1[file_month] = df
        else:
            # If the month is already in the dictionary, concatenate the DataFrame with the existing data
            combined_data_dict[file_month] = pd.concat(
                [combined_data_dict[file_month], df], ignore_index=True
            )
            combined_data_dict1[file_month] = pd.concat(
                [combined_data_dict1[file_month], df], ignore_index=True
            )

    # Keep only 'Amount', field1, and field2 columns in each DataFrame
    for month, df in combined_data_dict.items():
        combined_data_dict[month] = df[["Amount", field1, field2]]

        # Group by field1 and aggregate the amounts
        df_grouped_field1 = df.groupby(field1)["Amount"].sum().reset_index()

        # Update the DataFrame with the aggregated amounts
        combined_data_dict[month] = combined_data_dict[month].merge(
            df_grouped_field1, on=field1, suffixes=("", "_sum")
        )

        # Drop duplicate rows and unnecessary columns
        combined_data_dict[month] = combined_data_dict[month].drop_duplicates(
            subset=field1
        )
        combined_data_dict[month] = combined_data_dict[month][
            ["Amount", field1, field2]
        ]

    for month, df in combined_data_dict1.items():
        combined_data_dict1[month] = df[["Amount", field1, field2]]

        # Group by field1 and aggregate the amounts
        df_grouped_field1 = df.groupby(field1)["Amount"].sum().reset_index()

        # Update the DataFrame with the aggregated amounts
        combined_data_dict1[month] = combined_data_dict1[month].merge(
            df_grouped_field1, on=field1, suffixes=("", "_sum")
        )

        # Drop duplicate rows and unnecessary columns
        combined_data_dict1[month] = combined_data_dict1[month].drop_duplicates(
            subset=field1
        )
        combined_data_dict1[month] = combined_data_dict1[month][
            ["Amount", field1, field2]
        ]

        # Group by field2 and aggregate the amounts
        df_grouped_field2 = df.groupby(field2)["Amount"].sum().reset_index()

        # Update the DataFrame with the aggregated amounts
        combined_data_dict1[month] = combined_data_dict1[month].merge(
            df_grouped_field2, on=field2, suffixes=("", "_sum")
        )

        # Drop duplicate rows and unnecessary columns
        combined_data_dict1[month] = combined_data_dict1[month].drop_duplicates(
            subset=field2
        )
        combined_data_dict1[month] = combined_data_dict1[month][
            ["Amount", field1, field2]
        ]

    # Combine unique values of field1
    combined_field1_values = sorted(list(set(item for sublist in [df[field1].tolist() for df in combined_data_dict.values()] for item in sublist)))
    combined_field2_values = sorted(list(set(item for sublist in [df[field2].tolist() for df in combined_data_dict1.values()] for item in sublist)))

    context = {
        'combined_field1_values': combined_field1_values,
        'combined_field2_values': combined_field2_values,
        'field2': field2,
    }

    if request.method == 'POST':
        field1value = request.POST.get('field1value')
        field2value = request.POST.get('field2value')

        if field2value is not None:
            # Combine unique values of field1 and field2
            combined_field2_values = sorted(list(set(item for sublist in [df[field2].tolist() for df in combined_data_dict.values()] for item in sublist)))
            context['combined_field2_values'] = combined_field2_values

        if field2value == 'All':
            amounts_dict = {}  # Dictionary to store amounts for each field2 value

            for field2_val in combined_field2_values:
                amounts = []  # List to store the amounts

                for month, df in combined_data_dict1.items():
                    # Search for the row in the column field2 matching the field2_val
                    row = df[df[field2] == field2_val]

                    if len(row) > 0:
                        # If the row is present, get the corresponding amount
                        amount = row['Amount'].iloc[0]
                    else:
                        # If the row is not present, consider the amount as zero
                        amount = 0

                    amounts.append(amount)

                amounts_dict[field2_val] = amounts

            # Plotting the line graph
            months = list(combined_data_dict1.keys())

            fig = go.Figure()

            for field2_val, amounts in amounts_dict.items():
                fig.add_trace(go.Scatter(x=months, y=amounts, mode='lines+markers', name=field2_val))

            fig.update_layout(title=f'Amount for "{field1value}" in each month', xaxis_title='Month', yaxis_title='Amount')

            fig.show()
    
        else:
            amounts = []  # List to store the amounts

            for month, df in combined_data_dict1.items():
                # Search for the row in the column field2 matching the field2value value
                row = df[df[field2] == field2value]

                if len(row) > 0:
                    # If the row is present, get the corresponding amount
                    amount = row['Amount'].iloc[0]
                else:
                    # If the row is not present, consider the amount as zero
                    amount = 0

                amounts.append(amount)

            # Plotting the line graph and pie chart
            months = list(combined_data_dict1.keys())

            fig = sp.make_subplots(rows=1, cols=1, subplot_titles=[
                f'Amount for "{field2value}" in "{field1value}" in each month'
                ])

            # Line graph
            fig.add_trace(go.Scatter(x=months, y=amounts, mode='markers+lines+text', fillcolor='red'), row=1, col=1)
            fig.update_xaxes(title='Month', row=1, col=1)
            fig.update_yaxes(title='Amount', row=1, col=1)

            # Pie chart (using a separate figure)
            # pie_fig = go.Figure(data=[go.Pie(labels=months, values=amounts, hoverinfo='label+percent')])
            # pie_fig.update_layout(title=f'Proportions of Amount for "{field2value} in "{field1value}"')

            fig.show()
            # pie_fig.show()
    
    return render(request, 'choose.html', context)

     