def display_files(
    request,
    month1="January",
    month2="February",
    field="Location",
    field2="Meter Name",
    method="Month",
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

        if method == "Month":
            if file_month not in combined_data_dict:
                # If the month is not already in the dictionary, create a new key-value pair
                combined_data_dict[file_month] = df
            else:
                # If the month is already in the dictionary, concatenate the DataFrame with the existing data
                combined_data_dict[file_month] = pd.concat(
                    [combined_data_dict[file_month], df], ignore_index=True
                )
        else:
            if project_name not in combined_data_dict:
                # If the month is not already in the dictionary, create a new key-value pair
                combined_data_dict[project_name] = df
            else:
                # If the month is already in the dictionary, concatenate the DataFrame with the existing data
                combined_data_dict[project_name] = pd.concat(
                    [combined_data_dict[project_name], df], ignore_index=True
                )

    print(combined_data_dict)
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

        print(combined_data_dict)

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
        "upload_file"
    )  # Assuming the URL name for the upload_file view is "upload_file"
    upload_button = f'<a href="{upload_url}" style="background-color: #4CAF50;color: white;padding: 10px 20px;border-radius: 5px;cursor: pointer;text-decoration:None;">Go to Home</a>'
    graph_html = f"{upload_button}<br><br>" + fig.to_html(full_html=False)

    # Create the Django response
    response = HttpResponse(content_type="text/html")

    # Write the graph HTML to the response
    response.write(graph_html)

    return response


def line_graph(request, month1, month2, field2, field1="Resource Group Name"):
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
            subset=[field1, field2]
        )
        combined_data_dict[month] = combined_data_dict[month][
            ["Amount_sum", field1, field2]
        ]

        # Group by field2 and aggregate the amounts
        df_grouped_field2 = df.groupby(field2)["Amount"].sum().reset_index()

        # Update the DataFrame with the aggregated amounts
        combined_data_dict[month] = combined_data_dict[month].merge(
            df_grouped_field2, on=field2, suffixes=("", "_sum")
        )

        # Drop duplicate rows and unnecessary columns
        combined_data_dict[month] = combined_data_dict[month].drop_duplicates(
            subset=[field1, field2]
        )
        combined_data_dict[month] = combined_data_dict[month][
            ["Amount_sum", field1, field2]
        ]

        # Modify the code from here
        if not combined_data.empty:
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
        "upload_file"
    )  # Assuming the URL name for the upload_file view is "upload_file"
    upload_button = f'<a href="{upload_url}" style="background-color: #4CAF50;color: white;padding: 10px 20px;border-radius: 5px;cursor: pointer;text-decoration:None;">Go to Home</a>'
    graph_html = f"{upload_button}<br><br>" + fig.to_html(full_html=False)

    # Create the Django response
    response = HttpResponse(content_type="text/html")

    # Write the graph HTML to the response
    response.write(graph_html)

    return response
