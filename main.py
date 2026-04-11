from core.setup import ensure_config
from ui.terminal import print_assistant, print_banner, get_input, print_status
from core.agent import Agent
from core.planner import detect_complexity, generate_plan, confirm_plan, execute_plan
from core.learning import add_feedback
from rich.console import Console

console = Console()


def main():
    config = ensure_config()
    agent = Agent(config)
    retention_days = config["settings"].get("memory_retention_days", 30)

    print_banner()
    try:
        user_input = get_input()
        while user_input not in ["exit", "quit"]:

            # Feedback
            if user_input in ["👍", "+", "good", "bien"]:
                msgs = agent.history.get()
                context = msgs[-2]["content"] if len(msgs) >= 2 else ""
                add_feedback("positive", context)
                console.print("[green]✓ Feedback saved[/green]")
                user_input = get_input()
                continue

            if user_input in ["👎", "-", "bad", "mal"]:
                msgs = agent.history.get()
                context = msgs[-2]["content"] if len(msgs) >= 2 else ""
                add_feedback("negative", context)
                console.print("[red]✓ Feedback saved[/red]")
                user_input = get_input()
                continue

            if user_input == "/help":
                console.print("""
[bold cyan]HelloChusquis Commands[/bold cyan]

[bold]Chat commands:[/bold]
  /help      — Show this help
  /status    — Show provider status
  /clear     — Clear conversation history
  /plan      — Force planning mode: /plan <task>
  👍 / +     — Positive feedback on last response
  👎 / -     — Negative feedback on last response
  exit       — Exit and save memory

[bold]Terminal commands:[/bold]
  hellochusquis install <plugin>    — Install a plugin
  hellochusquis uninstall <plugin>  — Remove a plugin
  hellochusquis plugins             — List installed plugins
  hellochusquis build               — Build a new plugin
  hellochusquis learn               — Show learned patterns
""")

            elif user_input == "/status":
                print_status(agent.pool.status())

            elif user_input == "/clear":
                agent.history.clear()
                console.print("  [dim]Historial limpiado.[/dim]")

            elif user_input.startswith("/plan "):
                task = user_input[6:].strip()
                console.print("[dim]Generating plan...[/dim]")
                steps = generate_plan(task, agent.pool)
                if steps:
                    final = confirm_plan(steps, agent.pool, task)
                    if final:
                        execute_plan(final, agent)
                else:
                    console.print("[red]Could not generate a plan.[/red]")

            elif user_input.strip() == "":
                pass

            else:
                try:
                    console.print("[dim]...[/dim]", end="\r")
                    is_complex = detect_complexity(user_input, agent.pool)

                    if is_complex:
                        console.print("[dim]Complex task detected. Generating plan...[/dim]")
                        steps = generate_plan(user_input, agent.pool)
                        if steps:
                            final = confirm_plan(steps, agent.pool, user_input)
                            if final:
                                execute_plan(final, agent)
                        else:
                            respuesta = agent.run(user_input)
                            print_assistant(respuesta)
                    else:
                        respuesta = agent.run(user_input)
                        print_assistant(respuesta)
                        console.print("[dim]  👍 / 👎 to give feedback[/dim]")

                except RuntimeError as e:
                    console.print(f"\n[red]✗ {e}[/red]")
                    console.print("[dim]Tip: Run 'rm config.yaml && hellochusquis' to add more providers.[/dim]")

            user_input = get_input()

    except KeyboardInterrupt:
        console.print("\n")

    console.print("[dim]Guardando memoria...[/dim]")
    agent.summarize_and_save(retention_days)
    console.print("[dim]Hasta luego.[/dim]")


if __name__ == "__main__":
    main()