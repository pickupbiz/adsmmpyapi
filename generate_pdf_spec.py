"""
Script to convert Functional Specification Document from Markdown to PDF.
Requires: markdown, weasyprint (or pdfkit with wkhtmltopdf)
"""
import os
import sys
from pathlib import Path

try:
    import markdown
    from weasyprint import HTML, CSS
except ImportError:
    print("Required packages not installed. Installing...")
    os.system(f"{sys.executable} -m pip install markdown weasyprint")
    import markdown
    from weasyprint import HTML, CSS

def markdown_to_pdf(md_file, pdf_file):
    """Convert Markdown file to PDF."""
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'toc']
    )
    
    # Add CSS styling for PDF
    css_style = """
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #1a1a1a;
            border-bottom: 3px solid #0066cc;
            padding-bottom: 10px;
            page-break-after: avoid;
        }
        h2 {
            color: #0066cc;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 5px;
            margin-top: 30px;
            page-break-after: avoid;
        }
        h3 {
            color: #333;
            margin-top: 20px;
            page-break-after: avoid;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            page-break-inside: avoid;
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
        }
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            page-break-inside: avoid;
        }
        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }
        li {
            margin: 5px 0;
        }
        .page-break {
            page-break-before: always;
        }
        hr {
            border: none;
            border-top: 2px solid #ddd;
            margin: 20px 0;
        }
    </style>
    """
    
    # Combine HTML
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Functional Specification Document v1.0.0</title>
        {css_style}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert to PDF
    try:
        HTML(string=full_html).write_pdf(pdf_file)
        print(f"✓ PDF generated successfully: {pdf_file}")
        return True
    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        print("\nAlternative: Open the HTML file in a browser and print to PDF")
        # Save HTML file as fallback
        html_file = pdf_file.replace('.pdf', '.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(full_html)
        print(f"✓ HTML file saved: {html_file}")
        return False

if __name__ == "__main__":
    # File paths
    base_dir = Path(__file__).parent
    md_file = base_dir / "FUNCTIONAL_SPECIFICATION_V1.0.0.md"
    pdf_file = base_dir / "FUNCTIONAL_SPECIFICATION_V1.0.0.pdf"
    
    if not md_file.exists():
        print(f"Error: Markdown file not found: {md_file}")
        sys.exit(1)
    
    print(f"Converting {md_file} to PDF...")
    success = markdown_to_pdf(md_file, pdf_file)
    
    if success:
        print(f"\n✓ Success! PDF file created: {pdf_file}")
    else:
        print(f"\n⚠ PDF generation failed. HTML file created instead.")
        print("You can open the HTML file in a browser and use 'Print to PDF'")
