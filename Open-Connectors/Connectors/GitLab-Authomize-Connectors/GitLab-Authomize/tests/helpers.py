import json


def read_json(json_file: str) -> dict:
    with open(json_file) as handle:
        data = json.load(handle)
    return data


class Fixture:
    _fixture_path = "tests/fixtures/{0}/{1}.json"

    def __init__(self, name: str) -> None:
        self.name = name

    def read_json(self, file_name: str) -> dict:
        path = self._fixture_path.format(self.name, file_name)
        return read_json(path)

    def read_json_str(self, file_name: str) -> dict:
        return json.dumps(self.read_json(file_name))
