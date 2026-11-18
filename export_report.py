"""
export_report.py - Converts PROJECT_REPORT.md to an academic, print-ready HTML file
Can be opened in any web browser and saved to PDF via Ctrl+P.
"""

import re
import html

def convert_md_to_html(md_path="PROJECT_REPORT.md", html_path="PROJECT_REPORT.html"):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    html_parts = []
    in_code_block = False
    in_table = False
    in_list = False

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")

        # Code block handling
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                html_parts.append("<pre><code>")
            else:
                in_code_block = False
                html_parts.append("</code></pre>")
            continue

        if in_code_block:
            html_parts.append(html.escape(line) + "\n")
            continue

        # Table handling
        if line.strip().startswith("|") and line.strip().endswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c).issubset({"-", ":", " "}) for c in cells):
                # separator row, skip
                continue
            if not in_table:
                in_table = True
                html_parts.append("<table>\n<thead>\n<tr>")
                for c in cells:
                    formatted_c = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", c)
                    formatted_c = re.sub(r"\*(.*?)\*", r"<em>\1</em>", formatted_c)
                    formatted_c = re.sub(r"`(.*?)`", r"<code>\1</code>", formatted_c)
                    html_parts.append(f"<th>{formatted_c}</th>")
                html_parts.append("</tr>\n</thead>\n<tbody>")
            else:
                html_parts.append("<tr>")
                for c in cells:
                    formatted_c = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", c)
                    formatted_c = re.sub(r"\*(.*?)\*", r"<em>\1</em>", formatted_c)
                    formatted_c = re.sub(r"`(.*?)`", r"<code>\1</code>", formatted_c)
                    html_parts.append(f"<td>{formatted_c}</td>")
                html_parts.append("</tr>")
            continue
        else:
            if in_table:
                in_table = False
                html_parts.append("</tbody>\n</table>")

        # Unordered list handling
        if line.startswith("- "):
            if not in_list:
                in_list = True
                html_parts.append("<ul>")
            content = line[2:]
            formatted = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
            formatted = re.sub(r"\*(.*?)\*", r"<em>\1</em>", formatted)
            formatted = re.sub(r"`(.*?)`", r"<code>\1</code>", formatted)
            html_parts.append(f"<li>{formatted}</li>")
            continue
        else:
            if in_list:
                in_list = False
                html_parts.append("</ul>")

        # Headings
        if line.startswith("# "):
            html_parts.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_parts.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_parts.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("#### "):
            html_parts.append(f"<h4>{line[5:]}</h4>")
        elif line.strip() == "---":
            html_parts.append("<hr/>")
        elif line.startswith("> "):
            html_parts.append(f"<blockquote>{line[2:]}</blockquote>")
        elif line.strip():
            formatted = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
            formatted = re.sub(r"\*(.*?)\*", r"<em>\1</em>", formatted)
            formatted = re.sub(r"`(.*?)`", r"<code>\1</code>", formatted)
            html_parts.append(f"<p>{formatted}</p>")

    if in_table:
        html_parts.append("</tbody>\n</table>")
    if in_list:
        html_parts.append("</ul>")

    template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI-Based Academic Content Generator - University Project Report</title>
<style>
    body {{
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        line-height: 1.65;
        color: #1e293b;
        max-width: 900px;
        margin: 40px auto;
        padding: 0 40px;
        background-color: #ffffff;
    }}
    h1 {{
        color: #0B2545;
        border-bottom: 3px solid #0B2545;
        padding-bottom: 10px;
        margin-top: 35px;
        font-size: 2rem;
    }}
    h2 {{
        color: #134074;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 6px;
        margin-top: 28px;
        font-size: 1.5rem;
    }}
    h3 {{
        color: #1d2d44;
        margin-top: 22px;
        font-size: 1.2rem;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 22px 0;
        font-size: 0.95rem;
    }}
    th, td {{
        border: 1px solid #cbd5e1;
        padding: 10px 14px;
        text-align: left;
    }}
    th {{
        background-color: #eef4f8;
        color: #0b2545;
        font-weight: 600;
    }}
    tr:nth-child(even) {{
        background-color: #f8fafc;
    }}
    pre {{
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-left: 4px solid #134074;
        padding: 14px;
        border-radius: 6px;
        overflow-x: auto;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 0.88rem;
    }}
    blockquote {{
        border-left: 4px solid #8da9c4;
        background-color: #f0f4f8;
        padding: 12px 18px;
        margin: 18px 0;
        font-style: italic;
        border-radius: 0 6px 6px 0;
    }}
    code {{
        background-color: #f1f5f9;
        color: #0f172a;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Consolas', monospace;
        font-size: 0.9em;
    }}
    hr {{
        border: 0;
        height: 1px;
        background: #cbd5e1;
        margin: 32px 0;
    }}
    ul {{
        padding-left: 24px;
        margin: 12px 0;
    }}
    li {{
        margin-bottom: 6px;
    }}
    @media print {{
        body {{
            margin: 20px;
            padding: 0;
            max-width: 100%;
        }}
        h1, h2, h3 {{
            page-break-after: avoid;
        }}
        table, pre, blockquote {{
            page-break-inside: avoid;
        }}
    }}
</style>
</head>
<body>
{''.join(html_parts)}
</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(template)

    print(f"Report successfully compiled to {html_path}")

if __name__ == "__main__":
    convert_md_to_html()
