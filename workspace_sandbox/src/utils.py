import re
from html import unescape

def parse_markdown(markdown_text):
    headers = re.findall(r'^(#+) (.*)$', markdown_text, re.MULTILINE)
    links = re.findall(r'[(.*?)]((.*?))', markdown_text)
    images = re.findall(r'![(.*?)]((.*?))', markdown_text)
    parsed_text = ''
    for line in markdown_text.split('\n'):
        if line.startswith('#'):
            header_level = line.find(' ') - 1
            header_text = line[header_level + 1:]
            parsed_text += f'<h{header_level}>{header_text}</h{header_level}>\n'
        else:
            parsed_text += line + '\n'
    for link in links:
        parsed_text = parsed_text.replace(f'[{link[0]}]({link[1]})', f'<a href="{link[1]}">{link[0]}</a>')
    for image in images:
        parsed_text = parsed_text.replace(f'![{image[0]}]({image[1]})', f'<img src="{image[1]}" alt="{image[0]}">')
    return unescape(parsed_text)