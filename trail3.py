def line_graph(
    request,
    month1="January",
    month2="December",
    field2="Category",
    field1="Resource Group Name",
):
    if request.method == "POST":
        # Some code here

        month1 = request.POST.get("month1")
        month2 = request.POST.get("month2")
        field2 = request.POST.get("field2")
        field1value = request.POST.get("field1value")

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
        htmlresponse=pio.to_html(fig, full_html=False)
        return render(request, 'show.html',{'graph':htmlresponse})
    
    # Some code here
    return render(request, "choose.html", context)

choose.html form:
<form method="post" id="my-form"
        action="{% url 'line_graph' 'January' 'December' 'Category' 'Resource Group Name'  %}">
        {% csrf_token %}
        <p>Select the Usage Start Date:</p>
        <select name="month1" class="custom-select">
            {% for month in months %}
            <option value="{{ month }}"><span>{{ month }}</span></option>
            {% endfor %}
        </select>

        <p>Select the Usage End Date:</p>
        <select name="month2" class="custom-select">
            <option value="" disabled selected>None</option>
            {% for month in months %}
            <option value="{{ month }}"><span>{{ month }}</span></option>
            {% endfor %}
        </select>

        <p>Select the Field 2:</p>
        <select name="field2" class="custom-select">
            <option value="Meter Name">Meter Name</option>
            <!-- <option value="Resource Group Name">Resource Group Name</option> -->
            <option value="Category">Category</option>
            <option value="Subcategory">Subcategory</option>
            <option value="Location">Location</option>
        </select>

        <p>Select the Resource group name:</p>
        <select name="field1value">
            {% for combined_field1_value in combined_field1_values %}
            <option value="{{ combined_field1_value }}">{{ combined_field1_value }}</option>
            {% endfor %}
        </select>

        <!-- <p>Select the {{field2}} value:</p>
        <select name="field2value">
            <option value="All" selected>All</option>
            {% for combined_field2_value in combined_field2_values %}
            <option value="{{ combined_field2_value }}">{{ combined_field2_value }}</option>
            {% endfor %}
        </select> -->
        <button type="submit">Submit</button>
        <br>
        <div class="button-container">
            <button>
                <a style="font-size: 13px;" href="{% url 'home' %}">Go to Upload >> </a>
            </button>
        </div>
    </form>

url patters:
path("home/", views.home, name="home"),
    path(
        "lines/<str:month1>/<str:month2>/<str:field2>/<str:field1>/",
        views.line_graph,
        name="line_graph",
    ),

The response is not returned, everything is fine above the post request return but the response is not showing.
If any confusion or any file code you want ill send 