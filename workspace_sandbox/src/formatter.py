import json

class OutputFormatter:
    def to_json(self, data: dict) -> str:
        return json.dumps(data, indent=2)
