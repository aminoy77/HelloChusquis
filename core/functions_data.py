# DEPRECATED: This module is not used. Consider removing.
"""Data processing functions for HelloChusquis."""

import json
import csv
import re
from typing import Any, List


def json_to_csv(json_str: str, output_path: str = None, delimiter: str = ",") -> dict:
    """Convert JSON to CSV."""
    try:
        data = json.loads(json_str)
        if isinstance(data, list) and data:
            first_item = data[0] if data else {}
            headers = list(first_item.keys()) if first_item else []
            lines = [delimiter.join(headers)]
            for row in data:
                lines.append(delimiter.join(str(row.get(h, "")) for h in headers))
            result = "\n".join(lines)
            if output_path:
                with open(output_path, "w") as f:
                    f.write(result)
                return {"saved": output_path, "rows": len(data)}
            return {"csv": result, "rows": len(data)}
        return {"error": "JSON must be an array of objects"}
    except Exception as e:
        return {"error": str(e)}


def csv_to_json_simple(csv_path: str, delimiter: str = ",") -> dict:
    """Simple CSV to JSON."""
    try:
        with open(csv_path) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            data = list(reader)
            return {"json": json.dumps(data, indent=2), "rows": len(data)}
    except Exception as e:
        return {"error": str(e)}


def csv_to_json_array(csv_path: str, has_header: bool = True, delimiter: str = ",") -> dict:
    """CSV to JSON array."""
    try:
        with open(csv_path) as f:
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)
            if has_header and rows:
                headers = rows[0] if rows else []
                data = [{headers[i]: row[i] for i in range(len(row))} for row in rows[1:] if row]
            else:
                data = rows
            return {"json": json.dumps(data, indent=2), "rows": len(data)}
    except Exception as e:
        return {"error": str(e)}


def merge_csv(files: List[str], output_path: str, delimiter: str = ",") -> dict:
    """Merge CSV files."""
    try:
        all_rows = []
        for f in files:
            with open(f) as file:
                reader = csv.reader(file, delimiter=delimiter)
                all_rows.extend(list(reader))
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerows(all_rows)
        return {"saved": output_path, "rows": len(all_rows)}
    except Exception as e:
        return {"error": str(e)}


def filter_json(json_str: str, key: str, value: Any) -> dict:
    """Filter JSON by key value."""
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            filtered = [d for d in data if d.get(key) == value]
            return {"json": json.dumps(filtered, indent=2), "filtered": len(filtered)}
        return {"error": "JSON must be array"}
    except Exception as e:
        return {"error": str(e)}


def group_by(data: list, key: str) -> dict:
    """Group JSON array by key."""
    groups = {}
    for item in data:
        k = item.get(key)
        if k not in groups:
            groups[k] = []
        groups[k].append(item)
    return {"groups": {k: len(v) for k, v in groups.items()}, "total_keys": len(groups)}


def sort_json(json_str: str, key: str, reverse: bool = False) -> dict:
    """Sort JSON array."""
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            data.sort(key=lambda x: x.get(key, ""), reverse=reverse)
            return {"json": json.dumps(data, indent=2), "sorted": len(data)}
        return {"error": "JSON must be array"}
    except Exception as e:
        return {"error": str(e)}


def uniq_json(json_str: str, key: str = None) -> dict:
    """Get unique values from JSON array."""
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            if key:
                seen = set()
                unique = [d for d in data if (k := d.get(key)) not in seen and not seen.add(k)]
            else:
                unique = list(set(json.dumps(d) for d in data))
                unique = [json.loads(u) for u in unique]
            return {"json": json.dumps(unique, indent=2), "unique": len(unique)}
        return {"error": "JSON must be array"}
    except Exception as e:
        return {"error": str(e)}


def count_by(data: list, key: str) -> dict:
    """Count occurrences by key."""
    counts = {}
    for item in data:
        k = item.get(key)
        counts[k] = counts.get(k, 0) + 1
    return {"counts": counts, "unique": len(counts)}


def sum_by(data: list, key: str) -> dict:
    """Sum numeric values by key."""
    import numbers
    sums = {}
    for item in data:
        k = item.get(key)
        v = item.get(key)
        if isinstance(v, numbers.Number):
            sums[k] = sums.get(k, 0) + v
    return {"sums": sums, "keys": len(sums)}


def avg_by(data: list, key: str) -> dict:
    """Average numeric values by key."""
    counted = {}
    summed = sum_by(data, key)
    for k, v in summed["sums"].items():
        count = summed.get("counts", {}).get(k, 1)
        counted[k] = round(v / count, 2)
    return {"averages": counted}