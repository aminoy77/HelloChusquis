from tools.base import BaseTool, ToolResult


PLUGIN_NAME = "visualize"
PLUGIN_DESCRIPTION = "Generate data visualizations and charts"

VISUALIZE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "visualize",
        "description": "Create charts and visualizations",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["bar", "line", "pie", "scatter", "histogram"]},
                "data": {"type": "string", "description": "Data as JSON or CSV"},
                "title": {"type": "string", "description": "Chart title"},
                "output": {"type": "string", "description": "Output file path"},
            },
            "required": ["type", "data"]
        }
    }
}


def run(chart_type: str, data: str, title: str = "", output: str = "") -> str:
    """Generate visualizations."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import json
        
        # Parse data
        if data.startswith("["):
            data_list = json.loads(data)
        else:
            # Try CSV format
            lines = data.strip().split("\n")
            labels = []
            values = []
            for line in lines:
                parts = line.split(",")
                if len(parts) >= 2:
                    labels.append(parts[0].strip())
                    values.append(float(parts[1].strip()))
            data_list = {"labels": labels, "values": values}
        
        if "bar" in chart_type or "pie" in chart_type:
            # Check if it's labeled data
            if isinstance(data_list, dict) and "labels" in data_list:
                plt.figure(figsize=(10, 6))
                if "bar" in chart_type:
                    plt.bar(range(len(data_list["labels"])), data_list["values"])
                elif "pie" in chart_type:
                    plt.pie(data_list["values"], labels=data_list["labels"], autopct='%1.1f%%')
                plt.xticks(range(len(data_list["labels"])), data_list["labels"], rotation=45)
            else:
                plt.bar(range(len(data_list)), [v for v in data_list.values()])
        
        elif "line" in chart_type:
            if isinstance(data_list, dict) and "labels" in data_list:
                plt.plot(data_list["labels"], data_list["values"])
            else:
                plt.plot(list(data_list.values()))
        
        if title:
            plt.title(title)
        
        if output:
            plt.savefig(output)
            return f"✓ Saved chart to: {output}"
        else:
            default_output = "/tmp/chart.png"
            plt.savefig(default_output)
            return f"✓ Chart saved to: {default_output}"
        
        plt.close()
    
    except ImportError:
        return "Error: matplotlib not installed. Run: pip install matplotlib"
    except Exception as e:
        return f"Error: {str(e)}"


# dbt integration
def dbt(action: str = "", model: str = "") -> str:
    """dbt (data build tool) integration."""
    import os
    import subprocess
    
    if not os.path.exists("dbt_project"):
        return "Error: No dbt project found. Initialize with 'dbt init'"
    
    if action == "run":
        cmd = ["dbt", "run", "--select", model] if model else ["dbt", "run"]
    elif action == "test":
        cmd = ["dbt", "test"]
    elif action == "docs":
        cmd = ["dbt", "docs", "generate"]
    else:
        return f"Unknown dbt action: {action}"
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout + result.stderr


if __name__ == "__main__":
    print("Visualization and dbt plugins loaded.")