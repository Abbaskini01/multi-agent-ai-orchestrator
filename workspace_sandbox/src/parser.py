class ContentParser:
    def parse(self, raw_text: str) -> dict:
        lines = raw_text.split('\n')
        return {'line_count': len(lines), 'raw': raw_text}
