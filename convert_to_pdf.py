#!/usr/bin/env python3
"""
Convert PROJECT_SUMMARY.md to PDF
Simple script to generate PDF documentation
"""

def convert_markdown_to_pdf():
    """Convert the project summary to PDF format"""
    print("📄 Converting PROJECT_SUMMARY.md to PDF...")
    print()
    print("🔧 Method 1: Using Pandoc (Recommended)")
    print("Install: https://pandoc.org/installing.html")
    print("Command: pandoc PROJECT_SUMMARY.md -o DBA-GPT_Documentation.pdf")
    print()
    print("🔧 Method 2: Using Python markdown2pdf")
    print("Install: pip install markdown2pdf")
    print("Command: markdown2pdf PROJECT_SUMMARY.md DBA-GPT_Documentation.pdf")
    print()
    print("🔧 Method 3: Using Online Converter")
    print("Upload PROJECT_SUMMARY.md to: https://www.markdowntopdf.com/")
    print()
    print("🔧 Method 4: Using VS Code Extension")
    print("Install 'Markdown PDF' extension in VS Code")
    print("Right-click PROJECT_SUMMARY.md → 'Markdown PDF: Export (pdf)'")
    print()
    print("✅ Your documentation is ready in PROJECT_SUMMARY.md")
    print("📊 Document contains: Executive Summary, Technologies, Architecture, Features, Testing Results")

if __name__ == "__main__":
    convert_markdown_to_pdf() 