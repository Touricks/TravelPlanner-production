#!/usr/bin/env python3
"""Merge MCP exported POI files into a single JSON."""
import json
import sys
from pathlib import Path

base_dir = Path("/Users/carrick/.claude/projects/-Users-carrick-gatech-Project/4f8e51b6-5647-4b0e-b8fc-d6fed92eca53/tool-results")
output_dir = Path("/Users/carrick/gatech/Project/CRAG-travelplanner/data")
output_dir.mkdir(exist_ok=True)

files = [
    "mcp-postgres-execute_sql-1767649519488.txt",
    "mcp-postgres-execute_sql-1767649607462.txt",
    "mcp-postgres-execute_sql-1767649610269.txt",
    "mcp-postgres-execute_sql-1767649613196.txt",
    "mcp-postgres-execute_sql-1767649615975.txt",
    "mcp-postgres-execute_sql-1767649618741.txt",
]

all_pois = []
for fname in files:
    fpath = base_dir / fname
    if fpath.exists():
        with open(fpath) as f:
            data = json.load(f)
            for item in data:
                if item.get("type") == "text":
                    poi = json.loads(item["text"])
                    all_pois.append(poi)
        print(f"Loaded {fname}: {len(data)} records")

output_file = output_dir / "pois_export.json"
with open(output_file, "w") as f:
    json.dump(all_pois, f)

print(f"\nTotal: {len(all_pois)} POIs exported to {output_file}")
