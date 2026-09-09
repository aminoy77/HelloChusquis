"""Generate charts and run bounded dbt helper commands."""

import json
import os
import subprocess
import tempfile


PLUGIN_NAME = "visualize"
PLUGIN_DESCRIPTION = "Generate data visualizations and charts"
DBT_TIMEOUT_SECONDS = 120
DBT_OUTPUT_MAX_CHARS = 8_192
CHART_DATA_MAX_CHARS = 1_000_000

VISUALIZE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "visualize",
        "description": "Create charts and visualizations",
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter", "histogram"]},
                "data": {"type": "string", "description": "Data as JSON or CSV"},
                "title": {"type": "string", "description": "Chart title"},
                "output": {"type": "string", "description": "Output file path"},
            },
            "required": ["chart_type", "data"],
        },
    },
}


def _parse_chart_data(data: str) -> object:
    if data.lstrip().startswith("[") or data.lstrip().startswith("{"):
        return json.loads(data)
    labels: list[str] = []
    values: list[float] = []
    for line in data.strip().splitlines():
        parts = line.split(",", 1)
        if len(parts) >= 2:
            labels.append(parts[0].strip())
            values.append(float(parts[1].strip()))
    return {"labels": labels, "values": values}


def _default_chart_path() -> str:
    descriptor, path = tempfile.mkstemp(prefix="hellochusquis-chart-", suffix=".png")
    os.fchmod(descriptor, 0o600)
    os.close(descriptor)
    return path


def _values(data: object) -> list[float]:
    if isinstance(data, dict) and "values" in data:
        return [float(value) for value in data["values"]]
    if isinstance(data, dict):
        return [float(value) for value in data.values()]
    if isinstance(data, list):
        return [float(value) for value in data]
    raise ValueError("data must be a JSON list, JSON object, or two-column CSV")


def run(chart_type: str = "", data: str = "", title: str = "", output: str = "", **kwargs: str) -> str:
    """Generate a chart from JSON or CSV data and always release the figure."""
    chart_type = chart_type or kwargs.get("type", "")
    if chart_type not in {"bar", "line", "pie", "scatter", "histogram"}:
        return "Error: chart_type must be bar, line, pie, scatter, or histogram."
    if not data:
        return "Error: data is required."
    if len(data) > CHART_DATA_MAX_CHARS:
        return f"Error: data exceeds {CHART_DATA_MAX_CHARS} characters."

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        parsed = _parse_chart_data(data)
        labels = parsed.get("labels", []) if isinstance(parsed, dict) else []
        values = _values(parsed)
        if not values:
            return "Error: data contains no values."

        figure, axes = plt.subplots(figsize=(10, 6))
        try:
            if chart_type == "bar":
                positions = range(len(values))
                axes.bar(positions, values)
                if labels:
                    axes.set_xticks(list(positions), labels, rotation=45, ha="right")
            elif chart_type == "pie":
                axes.pie(values, labels=labels or None, autopct="%1.1f%%")
            elif chart_type == "line":
                axes.plot(labels if labels else range(len(values)), values)
            elif chart_type == "scatter":
                axes.scatter(range(len(values)), values)
            else:
                axes.hist(values)
            if title:
                axes.set_title(title)
            figure.tight_layout()
            destination = output or _default_chart_path()
            figure.savefig(destination)
        finally:
            plt.close(figure)
        return f"✓ Saved chart to: {destination}"
    except ImportError:
        return "Error: matplotlib not installed. Run: pip install matplotlib"
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return f"Error: unable to generate chart: {exc}"


def dbt(action: str = "", model: str = "") -> str:
    """Run a dbt operation from a local project with bounded output and time."""
    if not os.path.exists("dbt_project"):
        return "Error: No dbt project found. Initialize with 'dbt init'"
    if action == "run":
        command = ["dbt", "run", "--select", model] if model else ["dbt", "run"]
    elif action == "test":
        command = ["dbt", "test"]
    elif action == "docs":
        command = ["dbt", "docs", "generate"]
    else:
        return f"Unknown dbt action: {action}"

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=DBT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return f"dbt timed out after {DBT_TIMEOUT_SECONDS} seconds"
    except FileNotFoundError:
        return "Error: dbt is not installed."
    return (result.stdout + result.stderr)[:DBT_OUTPUT_MAX_CHARS]


if __name__ == "__main__":
    print("Visualization and dbt plugins loaded.")
