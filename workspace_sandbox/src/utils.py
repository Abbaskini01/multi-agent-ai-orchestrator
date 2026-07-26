import re

def extract_headers(markdown_text):
    headers = re.findall(r'^(#+) (.*)$', markdown_text, re.MULTILINE)
    return headers