import argparse
import os
from markdown import Markdown

def parse_markdown(file_path):
    with open(file_path, 'r') as file:
        markdown_text = file.read()
    md = Markdown()
    return md.convert(markdown_text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Markdown File Parser CLI')
    parser.add_argument('file_path', type=str, help='Path to markdown file')
    args = parser.parse_args()
    print(parse_markdown(args.file_path))