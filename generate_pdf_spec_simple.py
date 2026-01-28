"""
Simple script to convert Functional Specification Document from Markdown to HTML.
The HTML file can be opened in any browser and printed to PDF.
"""
import re
import sys
from pathlib import Path

def markdown_to_html(md_file, html_file):
    """Convert Markdown file to HTML with styling."""
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Simple markdown to HTML conversion
    html = md_content
    
    # Headers
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Code blocks
    html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
    
    # Links
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
    
    # Horizontal rules
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
    
    # Lists (simple)
    lines = html.split('\n')
    in_list = False
    result = []
    for line in lines:
        if re.match(r'^[-*]\s', line):
            if not in_list:
                result.append('<ul>')
                in_list = True
            content = re.sub(r'^[-*]\s(.+)$', r'<li>\1</li>', line)
            result.append(content)
        elif re.match(r'^\d+\.\s', line):
            if not in_list:
                result.append('<ol>')
                in_list = True
            content = re.sub(r'^\d+\.\s(.+)$', r'<li>\1</li>', line)
            result.append(content)
        else:
            if in_list:
                result.append('</ul>' if '<ul>' in '\n'.join(result[-10:]) else '</ol>')
                in_list = False
            result.append(line)
    if in_list:
        result.append('</ul>')
    html = '\n'.join(result)
    
    # Tables (basic)
    table_pattern = r'\|(.+)\|'
    in_table = False
    lines = html.split('\n')
    result = []
    for i, line in enumerate(lines):
        if '|' in line and not line.strip().startswith('<'):
            if not in_table:
                result.append('<table>')
                in_table = True
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if all(cell.replace('-', '').replace(':', '').strip() == '' for cell in cells):
                continue  # Skip separator row
            result.append('<tr>')
            for cell in cells:
                tag = 'th' if i > 0 and '|' in lines[i-1] and '---' in lines[i-1] else 'td'
                result.append(f'<{tag}>{cell}</{tag}>')
            result.append('</tr>')
        else:
            if in_table:
                result.append('</table>')
                in_table = False
            result.append(line)
    if in_table:
        result.append('</table>')
    html = '\n'.join(result)
    
    # Paragraphs (lines not in other tags)
    lines = html.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not any(line.startswith(f'<{tag}') for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'pre', 'code', 'hr', 'a', 'strong', 'em']):
            result.append(f'<p>{line}</p>')
        else:
            result.append(line)
    html = '\n'.join(result)
    
    # CSS styling for PDF printing
    css_style = """
    <style>
        @media print {
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-size: 11pt;
            }
            h1 {
                page-break-after: avoid;
            }
            h2 {
                page-break-after: avoid;
            }
            table {
                page-break-inside: avoid;
            }
        }
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #1a1a1a;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
            margin-top: 0;
        }
        h2 {
            color: #0066cc;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 5px;
            margin-top: 30px;
        }
        h3 {
            color: #333;
            margin-top: 20px;
        }
        h4 {
            color: #555;
            margin-top: 15px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #0066cc;
            color: white;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        pre code {
            background-color: transparent;
            padding: 0;
        }
        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }
        li {
            margin: 5px 0;
        }
        hr {
            border: none;
            border-top: 2px solid #ddd;
            margin: 20px 0;
        }
        p {
            margin: 10px 0;
        }
        a {
            color: #0066cc;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
    """
    
    # Full HTML document
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Functional Specification Document v1.0.0 - ADS Innotech</title>
    {css_style}
</head>
<body>
    {html}
</body>
</html>"""
    
    # Write HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    return html_file

if __name__ == "__main__":
    base_dir = Path(__file__).parent
    md_file = base_dir / "FUNCTIONAL_SPECIFICATION_V1.0.0.md"
    html_file = base_dir / "FUNCTIONAL_SPECIFICATION_V1.0.0.html"
    
    if not md_file.exists():
        print(f"Error: Markdown file not found: {md_file}")
        sys.exit(1)
    
    print(f"Converting {md_file.name} to HTML...")
    output_file = markdown_to_html(md_file, html_file)
    
    print(f"\n[SUCCESS] HTML file created: {output_file}")
    print("\nTo generate PDF:")
    print("1. Open the HTML file in your web browser")
    print("2. Press Ctrl+P (or Cmd+P on Mac)")
    print("3. Select 'Save as PDF' or 'Microsoft Print to PDF'")
    print("4. Save the file as FUNCTIONAL_SPECIFICATION_V1.0.0.pdf")
    print(f"\nOr use an online converter: https://www.markdowntopdf.com/")
