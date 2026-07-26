#!/usr/bin/env python3
import argparse
import os
from markdown_parser import parse_markdown

def main():
    parser = argparse.ArgumentParser(description='Markdown File Parser CLI')
    parser.add_argument('file', help='Path to markdown file')
    args = parser.parse_args()
    with open(args.file, 'r') as f:
        markdown_text = f.read()
    parsed_text = parse_markdown(markdown_text)
    print(parsed_text)

if __name__ == '__main__':
    main()