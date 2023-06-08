import json

table_paths = {}

def load():
    global table_paths
    with open("tables/table_paths.json", "r") as f:
        table_paths = json.load(f)