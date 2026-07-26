import re

def parse_markdown(markdown_content):
    # Parse headers
    headers = re.findall(r'^(#+) (.*)$', markdown_content, re.MULTILINE)
    for header in headers:
        level = len(header[0])
        text = header[1]
        print(f'H{level}: {text}')
    # Parse bold and italic text
    bold_text = re.findall(r'\*\*(.*?)\*\*', markdown_content)
    italic_text = re.findall(r'\*(.*?)\*', markdown_content)
    for text in bold_text:
        print(f'Bold: {text}')
    for text in italic_text:
        print(f'Italic: {text}')
    return markdown_content