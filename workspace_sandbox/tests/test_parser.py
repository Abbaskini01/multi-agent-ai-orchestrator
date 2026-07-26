import unittest
import sys
sys.path.append('src')
from parser import ContentParser

class TestParser(unittest.TestCase):
    def test_parse(self):
        p = ContentParser()
        res = p.parse('a\nb')
        self.assertEqual(res['line_count'], 2)

if __name__ == '__main__':
    unittest.main()
