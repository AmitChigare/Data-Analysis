def line_graph(
    request,
    month1="January",
    month2="December",
    field2="Category",
    field1="Resource Group Name",
):
    if request.method == "POST":
        month1 = request.POST.get("month1")
        month2 = request.POST.get("month2")
        field2 = request.POST.get("field2")
        field1value = request.POST.get("field1value")
        # field2value = request.POST.get("field2value")

        # Convert month names to datetime objects
        datetime_month1 = datetime.strptime(month1, "%B")
        datetime_month2 = datetime.strptime(month2, "%B")

        query = Q(
            month__month__gte=datetime_month1.month,
            month__month__lte=datetime_month2.month,
        )

        excel_files = ExcelFile.objects.filter(query).order_by("month")

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
        combined_field1_values = sorted(
            list(
                set(
                    item
                    for sublist in [
                        df[field1].tolist() for df in combined_data_dict.values()
                    ]
                    for item in sublist
                )
            )
        )
        combined_field2_values = sorted(
            list(
                set(
                    item
                    for sublist in [
                        df[field2].tolist() for df in combined_data_dict1.values()
                    ]
                    for item in sublist
                )
            )
        )

        # if field2value == "All":
        amounts_dict = {}  # Dictionary to store amounts for each field2 value

        for field2_val in combined_field2_values:
            amounts = []  # List to store the amounts

            for month, df in combined_data_dict1.items():
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
        months = list(combined_data_dict1.keys())

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

        # Customize x-axis labels to display month and year
        month_years = [
            f"{month} {excel_file.month.year}"
            for month, excel_file in zip(months, excel_files)
        ]
        fig.update_layout(
            xaxis=dict(
                tickmode="array",
                tickvals=months,
                ticktext=month_years,
                title="Month",
            ),
            yaxis=dict(title="Amount"),
            title=f'Amount for "{field1value}" in "{field2}" from {month1} to {month2}',
        )

        # fig.show()
        # return render(request, 'index.html')
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
        div = pio.to_html(fig, full_html=False)
        print(month1, month2, field1, field2, field1value)
        context2 = {
            "combined_field1_values": combined_field1_values,
            "combined_field2_values": combined_field2_values,
            "months": months,
            "graph": div,
        }
        print("Hey")
        return render(request, "show.html", context2)

    ###################################################################################################################
    print("HIIII")
    # Convert month names to datetime objects
    datetime_month1 = datetime.strptime(month1, "%B")
    datetime_month2 = datetime.strptime(month2, "%B")

    query = Q(
        month__month__gte=datetime_month1.month, month__month__lte=datetime_month2.month
    )

    excel_files = ExcelFile.objects.filter(query).order_by("month")

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
    combined_field1_values = sorted(
        list(
            set(
                item
                for sublist in [
                    df[field1].tolist() for df in combined_data_dict.values()
                ]
                for item in sublist
            )
        )
    )
    combined_field2_values = sorted(
        list(
            set(
                item
                for sublist in [
                    df[field2].tolist() for df in combined_data_dict1.values()
                ]
                for item in sublist
            )
        )
    )
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

    context = {
        "combined_field1_values": combined_field1_values,
        "combined_field2_values": combined_field2_values,
        # "field2": field2,
        "months": months,
    }

    return render(request, "show.html", context)
    # return HttpResponse('Hey')
