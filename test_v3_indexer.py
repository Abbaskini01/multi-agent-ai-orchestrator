from orchestrator.code_indexer import MultilingualCodeIndexer

indexer = MultilingualCodeIndexer()

# 1. Test Python Code
python_code = """
import math

class Calculator:
    def add(self, a, b):
        return a + b

def main():
    calc = Calculator()
    print(calc.add(5, 3))
"""

# 2. Test JavaScript Code
js_code = """
import React from 'react';

class UserProfile extends React.Component {
    render() {
        return <div>User Profile</div>;
    }
}

function calculateTotal(items) {
    return items.reduce((acc, item) => acc + item.price, 0);
}
"""

print("=== Testing Python Indexing ===")
py_res = indexer.parse_file("app.py", python_code)
print(py_res)

print("\n=== Testing JavaScript Indexing ===")
js_res = indexer.parse_file("component.jsx", js_code)
print(js_res)