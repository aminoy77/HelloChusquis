import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()


def generate_plan(user_input: str, pool) -> list[str]:
    try:
        response = pool.chat_with_retry([
            {
                "role": "system",
                "content": (
                    "You are a task planner. "
                    "Given a task, respond ONLY with a JSON array of steps. "
                    "Each step is a short, concrete action string. Maximum 6 steps. "
                    "Example: [\"Search temperature in Barcelona\", \"Write report to file\"] "
                    "Respond ONLY with the JSON array, nothing else."
                )
            },
            {"role": "user", "content": user_input}
        ])
        content = response["choices"][0]["message"]["content"].strip()
        content = content.replace("```json", "").replace("```", "").strip()
        steps = json.loads(content)
        return steps if isinstance(steps, list) else []
    except Exception:
        return []


def show_plan(steps: list[str]) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    for i, step in enumerate(steps, 1):
        table.add_row(f"[#f5a623]{i}.[/#f5a623]", step)
    console.print(Panel(table, title="[bold]Execution Plan[/bold]", expand=False))


def confirm_plan(steps: list[str], pool, user_input: str) -> list[str] | None:
    while True:
        show_plan(steps)
        console.print("\n[dim]s = execute · n = cancel · e = edit[/dim]")
        choice = Prompt.ask("Proceed?", choices=["s", "n", "e"], default="s")

        if choice == "s":
            return steps
        elif choice == "n":
            console.print("[dim]Cancelled.[/dim]")
            return None
        elif choice == "e":
            feedback = Prompt.ask("What should I change?")
            steps = generate_plan(f"{user_input}. Changes: {feedback}", pool)
            if not steps:
                console.print("[red]Could not regenerate plan.[/red]")
                return None


def execute_plan(steps: list[str], agent) -> None:
    console.print(f"\n[dim]Executing {len(steps)} steps...[/dim]\n")
    for i, step in enumerate(steps, 1):
        console.print(f"[bold #f5a623]Step {i}/{len(steps)}:[/bold #f5a623] {step}")
        try:
            result = agent.run(step)
            from ui.terminal import print_assistant
            print_assistant(result)
        except RuntimeError as e:
            console.print(f"[yellow]⚠ Step {i} failed. Attempting to re-plan...[/yellow]")
            try:
                new_plan = generate_plan(f"The step '{step}' failed. The original goal was: {agent.history.get_user_inputs()[-1]}. Please generate a new plan to achieve the goal, avoiding the previous error.", agent.pool)
                if new_plan:
                    console.print("[bold green]New plan generated. Continuing execution.[/bold green]")
                    execute_plan(new_plan, agent)
                    return # Exit the current execution loop
                else:
                    console.print("[red]Could not generate a new plan. Skipping step.[/red]")
                    continue
            except Exception as e2:
                console.print(f"[red]Failed to generate a new plan: {e2}. Skipping step.[/red]")
                continue
    console.print("\n[#5eb97e]✓ Plan completed.[/#5eb97e]")"))
