"""
Build #005 — Typer + Rich CLI.

Commands: start, status, version, config, info, doctor, plugins, services,
env, models, chat, help.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from monad import __codename__, __version__

app = typer.Typer(
    name="monad",
    help=f"Monad-Ultron v{__version__} — Portable local AI orchestration platform",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def _boot(root: Path | None = None):
    """Boot the application (lazy — only when a command needs it)."""
    from monad.core.application import MonadApplication
    apporch = MonadApplication(root=root or Path.cwd())
    apporch.startup(banner=False)
    return apporch


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    """Default: show banner + help if no subcommand given."""
    if ctx.invoked_subcommand is None:
        console.print(Panel.fit(
            f"[bold cyan]Monad-Ultron[/bold cyan] [dim]v{__version__} · codename {__codename__}[/dim]\n"
            "[dim]Portable local AI orchestration platform[/dim]\n\n"
            "Run [bold]monad --help[/bold] to see all commands.\n"
            "Run [bold]monad start[/bold] to boot Monad.\n"
            "Run [bold]monad doctor[/bold] to diagnose your environment.",
            border_style="cyan", title="🧠 Monad",
        ))


@app.command()
def start() -> None:
    """Start the Monad application (boot + wait)."""
    apporch = _boot()
    state = apporch.state
    if state.ready:
        console.print("[bold green]✔[/bold green] Monad is ready.")
    else:
        console.print("[bold red]✘[/bold red] Monad failed to start:")
        for e in state.errors:
            console.print(f"   [red]•[/red] {e}")


@app.command()
def status() -> None:
    """Show application status + health check."""
    apporch = _boot()
    h = apporch.health_check()
    tbl = Table(title="Monad Status", show_header=False, border_style="cyan")
    tbl.add_column("Key", style="bold")
    tbl.add_column("Value")
    tbl.add_row("Ready", "✔ yes" if h["ready"] else "✘ no")
    tbl.add_row("Uptime", f"{h['uptime_s']}s")
    tbl.add_row("Warnings", str(len(h["warnings"])))
    tbl.add_row("Errors", str(len(h["errors"])))
    if h["resources"]:
        tbl.add_row("Root", h["resources"]["root"])
        tbl.add_row("On USB", "✔" if h["resources"]["on_usb"] else "✘")
    console.print(tbl)


@app.command()
def version() -> None:
    """Print Monad version."""
    console.print(f"[bold cyan]Monad-Ultron[/bold cyan] v{__version__} ({__codename__})")


@app.command()
def config() -> None:
    """Print loaded configuration."""
    from monad.config import ConfigManager
    cm = ConfigManager(Path.cwd() / "config.yaml")
    cm.load()
    import yaml
    console.print(Panel(yaml.dump(cm.all(), sort_keys=False, default_flow_style=False),
                        title="config.yaml", border_style="cyan"))


@app.command()
def info() -> None:
    """Show project + build info."""
    tbl = Table(title="Project Info", border_style="cyan")
    tbl.add_column("Field", style="bold")
    tbl.add_column("Value")
    tbl.add_row("Name", "Monad-Ultron")
    tbl.add_row("Version", __version__)
    tbl.add_row("Codename", __codename__)
    tbl.add_row("Repo", "https://github.com/YOUR_USERNAME/Monad-Ultron")
    tbl.add_row("License", "MIT")
    console.print(tbl)


@app.command()
def doctor() -> None:
    """Diagnose environment + report issues."""
    apporch = _boot()
    env = apporch.state.env_report
    if env is None:
        console.print("[red]No environment report available.[/red]")
        raise typer.Exit(1)

    tbl = Table(title="🩺 Monad Doctor", border_style="cyan")
    tbl.add_column("Check", style="bold")
    tbl.add_column("Value")
    tbl.add_column("Status")

    def row(k, v, ok):
        tbl.add_row(k, str(v), "[green]✔[/green]" if ok else "[yellow]![/yellow]")

    row("Python", env.python_version, env.python_ok)
    row("OS", f"{env.os_name} {env.os_release}", True)
    row("CPU", f"{env.cpu} ({env.cpu_cores_logical} cores)", True)
    row("RAM", f"{env.ram_available_gb} / {env.ram_total_gb} GB", env.ram_total_gb >= 8)
    row("Disk free", f"{env.disk_free_gb} GB", env.disk_free_gb >= 10)
    row("GPU", env.gpu_name, env.gpu_detected)
    row("CUDA", env.cuda_version, env.cuda_available)

    console.print(tbl)

    if env.warnings:
        console.print(Panel("\n".join(f"• {w}" for w in env.warnings),
                            title="⚠ Warnings", border_style="yellow"))
    if env.errors:
        console.print(Panel("\n".join(f"• {e}" for e in env.errors),
                            title="✘ Errors", border_style="red"))
    if not env.errors and not env.warnings:
        console.print("[bold green]All checks passed![/bold green]")


@app.command()
def env() -> None:
    """Show detailed environment report."""
    apporch = _boot()
    import json
    if apporch.state.env_report:
        console.print_json(json.dumps(apporch.state.env_report.to_dict()))


@app.command()
def plugins() -> None:
    """List available plugins."""
    apporch = _boot()
    try:
        pm = apporch.container.resolve("plugin_manager")
    except Exception as e:
        console.print(f"[red]Plugin manager not available: {e}[/red]")
        return
    tbl = Table(title="Plugins", border_style="cyan")
    tbl.add_column("ID", style="bold")
    tbl.add_column("Name")
    tbl.add_column("Version")
    tbl.add_column("Enabled")
    for p in pm.list_plugins():
        tbl.add_row(p["id"], p["name"], p["version"],
                    "[green]✔[/green]" if p["enabled"] else "[dim]✘[/dim]")
    console.print(tbl)


@app.command("plugin-enable")
def plugin_enable(plugin_id: str) -> None:
    """Enable a plugin by ID."""
    apporch = _boot()
    pm = apporch.container.resolve("plugin_manager")
    pm.enable(plugin_id)
    console.print(f"[green]✔[/green] Plugin '{plugin_id}' enabled.")


@app.command("plugin-disable")
def plugin_disable(plugin_id: str) -> None:
    """Disable a plugin by ID."""
    apporch = _boot()
    pm = apporch.container.resolve("plugin_manager")
    pm.disable(plugin_id)
    console.print(f"[yellow]✘[/yellow] Plugin '{plugin_id}' disabled.")


@app.command()
def services() -> None:
    """List DI-registered services."""
    apporch = _boot()
    tbl = Table(title="DI Services", border_style="cyan")
    tbl.add_column("Key", style="bold")
    tbl.add_column("Lifetime")
    for k, lt in apporch.container.list_services():
        tbl.add_row(k, lt)
    console.print(tbl)


@app.command()
def models() -> None:
    """List registered models (from models.yaml)."""
    from monad.models import ModelManager
    mm = ModelManager()
    mm.load_registry(Path.cwd() / "models.yaml")
    tbl = Table(title="Models", border_style="cyan")
    tbl.add_column("ID", style="bold")
    tbl.add_column("Role")
    tbl.add_column("Format")
    tbl.add_column("Size (GB)")
    tbl.add_column("Status")
    for m in mm.list_models():
        tbl.add_row(m.id, m.role, m.format, str(m.size_gb), m.status.value)
    console.print(tbl)


@app.command()
def chat() -> None:
    """Enter interactive chat mode (single model)."""
    from monad.chat import ChatEngine
    apporch = _boot()
    console.print(Panel(
        "[bold cyan]Monad Chat[/bold cyan] — commands: /help /clear /status /model /exit",
        border_style="cyan",
    ))
    engine = ChatEngine(app=apporch)
    engine.run_cli(console)
