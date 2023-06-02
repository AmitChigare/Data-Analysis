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