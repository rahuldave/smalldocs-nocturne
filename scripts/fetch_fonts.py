"""Restore pinned font files; normal builds never use the network."""
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
for font in json.loads((ROOT / "src/font-sources.json").read_text()):
    with urlopen(font["url"]) as response:
        (ROOT / "vendor/fonts" / font["file"]).write_bytes(response.read())
    print(font["file"])
