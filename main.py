from core.setup import ensure_config
from ui.terminal import print_assistant, print_banner, get_input, print_status
from core.agent import Agent
from core.planner import detect_complexity, generate_plan, confirm_plan, execute_plan
from rich.console import Console
from rich.prompt import Prompt

console = Console()


def main():
    config = ensure_config()
    agent = Agent(config)
    retention_days = config["settings"].get("memory_retention_days", 30)

    print_banner()
    try:
        user_input = get_input()
        while user_input not in ["exit", "quit"]:

            if user_input == "/status":
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
                    # Detecta si es tarea compleja
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
                            # Si falla el plan, ejecuta normal
                            respuesta = agent.run(user_input)
                            print_assistant(respuesta)
                    else:
                        respuesta = agent.run(user_input)
                        print_assistant(respuesta)

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
