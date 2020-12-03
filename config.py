import json

with open("config.json") as f:
    CONFIG = json.load(f)

print(CONFIG["DEBUG"])
