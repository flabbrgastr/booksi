"""HTML rendering — DataFrame to sortable HTML table."""

import pandas as pd
from datetime import datetime


def convert_dataframe_to_html(df):
    """Convert DataFrame to complete HTML page with sortable table."""
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
    day_of_week = current_datetime.strftime("%A")

    stringif = lambda column, ifstring, ifempty: column.apply(
        lambda x: ifstring if isinstance(x, str) and x.strip() != "" else ifempty
    )
    stringappend = lambda column, ifstring, ifempty: column.apply(
        lambda x: x + ifstring
        if isinstance(x, str) and x.strip() != ""
        else x + ifempty
    )

    df = df.sort_index()
    df = df.fillna("")

    # Add image column
    df.insert(
        0,
        "Img",
        df["Purl"].apply(
            lambda x: f'<img src="{x}" style="max-width: 140px; max-height: 140px;">'
        ),
    )
    # Make Girl name a link
    df["Girl"] = df.apply(
        lambda row: f'<a href="{row["Gurl"]}" target="_blank" class="no-underline">{row["Girl"]}</a>',
        axis=1,
    )

    condition = ((df["a1"].str.len() > 0) | (df["a0"].str.len() > 0)) & (
        df["Strasse"].str.len() > 0
    )
    ahomecount = df[condition].shape[0]
    asscount = len(df[(df["a1"] == "✓") | (df["a0"] == "✓")])

    # Add tags
    df.loc[
        (df["t"].apply(lambda x: isinstance(x, str) and x.strip() != "")), "Girl"
    ] += '<span style="color: red;"><sup><b>' + df["t"] + "</b></sup></span>"
    df["Loc"] = stringif(df["Strasse"], "🛌", "🚗")
    df["a0"] = stringif(df["a0"], "🍑", "·")
    df["a1"] = stringif(df["a1"], "🍑", "·")
    df["cim"] = stringif(df["cim"], "💦", "·")
    df["cof"] = stringif(df["cof"], "💦", "·")

    # Combine location columns
    df["Bezirk"] = df["Bezirk"].apply(lambda x: f"{x}<br>")
    df["Strasse"] = df["Strasse"].apply(lambda x: f"{x}<br>")
    df["Location"] = df["Bezirk"] + df["Strasse"]
    df = df.drop(columns=["Stadt", "Bezirk", "Strasse"])

    # Column order
    new_column_order = [
        "Img", "Girl", "Loc", "Score", "Fans", "a1", "a0", "cof", "cim",
        "Short", "Location", "Tel", "t",
    ]
    df = df[new_column_order]

    table_html = df.to_html(escape=False, index=False, classes="sortable")

    html = f"""
    <html>
    <head>
	<meta charset="UTF-8">
        <style>
            table {{
                font-family: Arial, sans-serif;
                border-collapse: collapse;
                width: 100%;
                border: none;
            }}
            th, td {{
                text-align: left;
                padding: 8px;
                border: none;
            }}
            th.sortable {{
                background-color: #007bff;
                color: white;
                cursor: pointer;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            tr:hover {{
                background-color: #e6e6ff;
            }}
            img {{
                max-width: 140px;
                max-height: 140px;
                border: none;
            }}
            thead th {{
                position: sticky;
                top: 0;
                background-color: #f1f1f1;
            }}
            .no-underline {{
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <p>Date: {formatted_datetime}, Time: {day_of_week}, Day: {day_of_week}, Gals: {len(df)}, As{asscount}, Ah{ahomecount}</p>
        {table_html}
        <script src="https://cdn.jsdelivr.net/gh/tofsjonas/sortable@latest/sortable.min.js"></script>
    </body>
    </html>
    """
    return html