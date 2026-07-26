import sys
from parser import ContentParser
from formatter import OutputFormatter

def main():
    sample_text = '# Hello World\nThis is parsed content.'
    parser = ContentParser()
    parsed_data = parser.parse(sample_text)
    formatter = OutputFormatter()
    result = formatter.to_json(parsed_data)
    print('[OK] Parse Output Result:')
    print(result)

if __name__ == '__main__':
    main()
