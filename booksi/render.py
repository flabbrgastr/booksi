"""HTML rendering — DataFrame to sortable HTML table with modern UI."""

import pandas as pd
from datetime import datetime


def convert_dataframe_to_html(df):
    """Convert DataFrame to complete HTML page with modern styling."""
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    df = df.sort_index()
    df = df.fillna("")

    # Add image column with rounded thumbnails
    df.insert(
        0,
        "Img",
        df["Purl"].apply(
            lambda x: f'<img src="{x}" loading="lazy">'
        ),
    )

    # Make Girl name a link with tag badges
    def girl_cell(row):
        name = f'<a href="{row["Gurl"]}" target="_blank">{row["Girl"]}</a>'
        tag = row.get("t", "")
        if tag and str(tag).strip():
            name += f' <span class="tag tag-new">{tag}</span>'
        return name

    df["Girl"] = df.apply(girl_cell, axis=1)

    condition = ((df["a1"].str.len() > 0) | (df["a0"].str.len() > 0)) & (
        df["Strasse"].str.len() > 0
    )
    ahomecount = df[condition].shape[0]
    asscount = len(df[(df["a1"] == "✓") | (df["a0"] == "✓")])

    # Pill badges for flags
    pill = lambda val, cls: f'<span class="pill pill-{cls}">{val}</span>' if val else '<span class="pill pill-empty">·</span>'
    df["a0"] = df["a0"].apply(lambda x: pill(x, "peach"))
    df["a1"] = df["a1"].apply(lambda x: pill(x, "peach"))
    df["cim"] = df["cim"].apply(lambda x: pill(x, "water"))
    df["cof"] = df["cof"].apply(lambda x: pill(x, "water"))
    df["Loc"] = df["Strasse"].apply(lambda x: "🛌" if x else "🚗")

    # Combine location columns
    df["Location"] = df["Bezirk"].apply(lambda x: f'<span class="loc-bezirk">{x}</span>') + \
                     df["Strasse"].apply(lambda x: f'<span class="loc-strasse">{x}</span>')
    df = df.drop(columns=["Stadt", "Bezirk", "Strasse"])

    # Column order
    new_column_order = [
        "Img", "Girl", "Loc", "Score", "Preis", "Fans",
        "a1", "a0", "cof", "cim",
        "Short", "Location", "Tel",
    ]
    df = df[new_column_order]

    table_html = df.to_html(escape=False, index=False, classes="sortable")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Booksi — {len(df)} Gals</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #fafafa;
    --surface: #fff;
    --border: #e5e7eb;
    --text: #1f2937;
    --text-muted: #6b7280;
    --accent: #6366f1;
    --accent-hover: #4f46e5;
    --peach: #f97316;
    --peach-bg: #fff7ed;
    --water: #3b82f6;
    --water-bg: #eff6ff;
    --new: #ef4444;
    --new-bg: #fef2f2;
    --row-hover: #f5f3ff;
    --row-stripe: #f9fafb;
    --shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
    --radius: 8px;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #111827;
      --surface: #1f2937;
      --border: #374151;
      --text: #f9fafb;
      --text-muted: #9ca3af;
      --accent: #818cf8;
      --accent-hover: #6366f1;
      --peach-bg: #431407;
      --water-bg: #1e3a5f;
      --new-bg: #450a0a;
      --row-hover: #1e1b4b;
      --row-stripe: #1a2332;
      --shadow: 0 1px 3px rgba(0,0,0,.3);
    }}
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }}
  .header {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: var(--shadow);
  }}
  .header-inner {{
    max-width: 1600px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
  }}
  .header h1 {{
    font-size: 18px;
    font-weight: 600;
    color: var(--accent);
    letter-spacing: -0.02em;
  }}
  .stats {{
    display: flex;
    gap: 16px;
    font-size: 13px;
    color: var(--text-muted);
  }}
  .stat {{ display: flex; align-items: center; gap: 4px; }}
  .stat-val {{ font-weight: 600; color: var(--text); }}
  #search {{
    flex: 1;
    min-width: 200px;
    max-width: 360px;
    padding: 8px 14px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 14px;
    background: var(--bg);
    color: var(--text);
    outline: none;
    transition: border-color .15s;
  }}
  #search:focus {{ border-color: var(--accent); }}
  #search::placeholder {{ color: var(--text-muted); }}
  .container {{
    max-width: 1600px;
    margin: 0 auto;
    padding: 16px;
  }}
  table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    background: var(--surface);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
  }}
  thead th {{
    position: sticky;
    top: 57px;
    background: var(--surface);
    border-bottom: 2px solid var(--border);
    padding: 10px 12px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
    z-index: 10;
  }}
  thead th:hover {{ color: var(--accent); }}
  thead th.sortth::after {{ content: ' ↕'; font-size: 10px; opacity: .4; }}
  thead th.sortth.asc::after {{ content: ' ↑'; opacity: 1; }}
  thead th.sortth.desc::after {{ content: ' ↓'; opacity: 1; }}
  tbody tr {{ transition: background .1s; }}
  tbody tr:nth-child(even) {{ background: var(--row-stripe); }}
  tbody tr:hover {{ background: var(--row-hover); }}
  td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    font-size: 14px;
    vertical-align: middle;
  }}
  td a {{
    color: var(--accent);
    text-decoration: none;
    font-weight: 500;
  }}
  td a:hover {{ text-decoration: underline; }}
  img {{
    width: 64px;
    height: 64px;
    object-fit: cover;
    border-radius: 50%;
    border: 2px solid var(--border);
  }}
  .pill {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 500;
    line-height: 1.4;
  }}
  .pill-peach {{ background: var(--peach-bg); color: var(--peach); }}
  .pill-water {{ background: var(--water-bg); color: var(--water); }}
  .pill-empty {{ color: var(--text-muted); opacity: .4; }}
  .tag {{
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    vertical-align: super;
  }}
  .tag-new {{ background: var(--new-bg); color: var(--new); }}
  .loc-bezirk {{
    display: block;
    font-weight: 500;
    font-size: 13px;
  }}
  .loc-strasse {{
    display: block;
    font-size: 12px;
    color: var(--text-muted);
  }}
  .fans {{ font-variant-numeric: tabular-nums; }}
  .score {{ font-weight: 600; }}
  .short {{ font-size: 12px; color: var(--text-muted); max-width: 240px; }}
  @media (max-width: 768px) {{
    .header-inner {{ flex-direction: column; align-items: stretch; }}
    #search {{ max-width: none; }}
    td, th {{ padding: 8px 6px; font-size: 12px; }}
    img {{ width: 48px; height: 48px; }}
  }}
</style>
</head>
<body>
<div class="header">
  <div class="header-inner">
    <h1>Booksi</h1>
    <div class="stats">
      <span class="stat"><span class="stat-val">{len(df)}</span> gals</span>
      <span class="stat">🍑 <span class="stat-val">{asscount}</span></span>
      <span class="stat">🛌 <span class="stat-val">{ahomecount}</span></span>
      <span class="stat">{formatted_datetime}</span>
    </div>
    <input type="text" id="search" placeholder="Search name, location..." autocomplete="off">
  </div>
</div>
<div class="container">
  {table_html}
</div>
<script src="https://cdn.jsdelivr.net/gh/tofsjonas/sortable@latest/sortable.min.js"></script>
<script>
document.getElementById('search').addEventListener('input', e => {{
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('tbody tr').forEach(tr => {{
    tr.style.display = tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}});
</script>
</body>
</html>"""
    return html
