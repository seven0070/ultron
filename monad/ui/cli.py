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
def update(check_only: bool = typer.Option(False, "--check", help="Only check, don't pull.")) -> None:
    """Level 1 self-improvement — pull latest Monad from git remote."""
    from monad.evolution import SelfUpdater
    updater = SelfUpdater(Path.cwd())
    info = updater.check_for_updates()
    if info.get("error"):
        console.print(f"[red]Update check failed:[/red] {info['error']}")
        raise typer.Exit(1)
    console.print(f"Local:  [cyan]{info.get('local', '?')}[/cyan]")
    console.print(f"Remote: [cyan]{info.get('remote', '?')}[/cyan]")
    if not info["available"]:
        console.print("[green]Already up to date.[/green]")
        return
    console.print(f"[yellow]{info['commits_behind']} commit(s) behind[/yellow]")
    if check_only:
        return
    result = updater.apply_update()
    if result["ok"]:
        console.print(f"[green]✔ Updated to {result['new_version']}[/green]")
    else:
        console.print(f"[red]✘ Update failed:[/red] {result.get('error') or result.get('reason')}")


evolve = typer.Typer(help="Self-improvement (Level 2/3) — propose, apply, rollback changes.")
app.add_typer(evolve, name="evolve")


def _build_evolution_manager(root: Path):
    from monad.evolution import (
        EvolutionLog, PatchProposer, SandboxRunner, RollbackManager, EvolutionManager,
    )
    from monad.policy import PolicyGate
    memory_dir = root / "memory_data"
    memory_dir.mkdir(parents=True, exist_ok=True)
    elog = EvolutionLog(memory_dir / "evolution.db")
    proposer = PatchProposer(root=root)
    sandbox = SandboxRunner(root=root)
    rollback = RollbackManager(root=root, backups_dir=memory_dir / "evolution_backups")
    gate = PolicyGate(require_approval_for=["evolution.apply"])
    return EvolutionManager(root, elog, proposer, sandbox, rollback, policy_gate=gate)


@evolve.command("history")
def evolve_history(limit: int = 20) -> None:
    """Show recent self-improvement history."""
    mgr = _build_evolution_manager(Path.cwd())
    tbl = Table(title="Evolution History", border_style="cyan")
    tbl.add_column("ID", style="bold")
    tbl.add_column("When")
    tbl.add_column("Type")
    tbl.add_column("Target")
    tbl.add_column("Outcome")
    for r in mgr.history(limit=limit):
        tbl.add_row(r.id, r.timestamp[:19], r.change_type.value,
                    r.target_path, r.outcome.value)
    console.print(tbl)


@evolve.command("propose")
def evolve_propose(
    goal: str = typer.Argument(..., help="What you want Monad to change."),
    target: str = typer.Option(..., "--target", "-t", help="File path to modify."),
    zone: str = typer.Option("plugins", "--zone", "-z",
                             help="plugins|tools|prompts|configs"),
) -> None:
    """Propose a self-improvement change (does not apply)."""
    from monad.evolution import EvolutionZone
    mgr = _build_evolution_manager(Path.cwd())
    try:
        zone_enum = EvolutionZone(zone)
    except ValueError:
        console.print(f"[red]Invalid zone:[/red] {zone}")
        raise typer.Exit(1)
    try:
        rec, proposal = mgr.propose(goal=goal, zone=zone_enum, target_path=target)
    except PermissionError as e:
        console.print(f"[red]✘ Refused:[/red] {e}")
        raise typer.Exit(1)
    console.print(Panel(
        f"[bold]ID:[/bold] {rec.id}\n"
        f"[bold]Model:[/bold] {proposal.model_used}\n"
        f"[bold]Rationale:[/bold] {proposal.rationale}\n\n"
        f"[dim]Diff preview (first 40 lines):[/dim]\n" +
        "\n".join(proposal.diff.splitlines()[:40]),
        title="✎ Proposal", border_style="yellow",
    ))
    console.print(f"\nTo apply: [bold]monad evolve apply {rec.id}[/bold]")


@evolve.command("apply")
def evolve_apply(
    record_id: str,
    skip_tests: bool = typer.Option(False, "--skip-tests"),
) -> None:
    """Apply a previously-proposed change (runs tests + asks approval)."""
    from monad.evolution import EvolutionZone
    mgr = _build_evolution_manager(Path.cwd())
    rec = mgr.log.get(record_id)
    if not rec:
        console.print(f"[red]No such record:[/red] {record_id}")
        raise typer.Exit(1)
    # Re-draft the proposal from the recorded goal (safer than pickling a diff)
    console.print("[dim]Re-drafting proposal from record…[/dim]")
    # Map recorded change_type back to a zone (best-effort)
    zone_map = {
        "new_plugin": EvolutionZone.PLUGINS, "patch_plugin": EvolutionZone.PLUGINS,
        "new_tool": EvolutionZone.TOOLS,     "patch_tool": EvolutionZone.TOOLS,
        "patch_prompt": EvolutionZone.PROMPTS,
        "patch_config": EvolutionZone.CONFIGS,
    }
    zone = zone_map.get(rec.change_type.value, EvolutionZone.PLUGINS)
    _, proposal = mgr.propose(goal=rec.goal, zone=zone, target_path=rec.target_path)
    result = mgr.apply(rec, proposal, skip_tests=skip_tests)
    console.print(f"Outcome: [bold]{result.outcome.value}[/bold]")


@evolve.command("rollback")
def evolve_rollback(record_id: str) -> None:
    """Undo a previously-applied change."""
    mgr = _build_evolution_manager(Path.cwd())
    if mgr.rollback_change(record_id):
        console.print(f"[green]✔ Rolled back {record_id}[/green]")
    else:
        console.print(f"[red]✘ Rollback failed[/red]")


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


@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Your question or request."),
    strategy: str = typer.Option("", "--strategy", "-s",
        help="Force strategy: auto|domain_routing|cascade|mixture_of_agents|verification|ensemble"),
    trace: bool = typer.Option(False, "--trace", help="Show orchestration trace."),
    cognition: bool = typer.Option(False, "--cognition", "-c",
        help="Run cognition pre-pass (memory + organs) before LLM."),
) -> None:
    """Multi-model orchestrated ask (Build #017) — routes to the right model(s)."""
    from monad.inference import InferenceManager, LlamaCppProvider
    from monad.models import ModelManager
    from monad.orchestration import MultiModelOrchestrator

    apporch = _boot()
    root = Path.cwd()

    # Ensure model registry is loaded
    mm = ModelManager()
    if len(mm.list_models()) == 0:
        mm.load_registry(root / "models.yaml", root / "models")

    im = InferenceManager()
    if "llama_cpp" not in im.list():
        im.register(LlamaCppProvider(), default=True)

    cfg = apporch.config
    pool = cfg.get("orchestration.model_pool", {}) if cfg else {}
    default_strategy = cfg.get("orchestration.default_strategy", "auto") if cfg else "auto"

    orch = MultiModelOrchestrator(
        inference_manager=im,
        model_manager=mm,
        model_pool=pool,
        default_strategy=default_strategy,
        max_workers=cfg.get("orchestration.max_workers", 3) if cfg else 3,
    )

    if cognition:
        try:
            from monad.cognition import Monad, MonadConfig
            cog = Monad(MonadConfig(max_organs_per_cycle=4))
            orch.attach_cognition(cog)
            console.print("[dim]🧠 cognition pre-pass attached[/dim]")
        except Exception as e:
            console.print(f"[yellow]cognition pre-pass unavailable: {e}[/yellow]")

    try:
        response, tr = orch.handle_text(prompt, strategy_override=strategy)
    except Exception as e:
        console.print(f"[red]Orchestration failed:[/red] {e}")
        raise typer.Exit(1)

    console.print(Panel(response.text or "[dim](empty)[/dim]",
                        title=f"🧠 Monad ({tr.final_model or 'no-model'})",
                        border_style="magenta"))

    if trace:
        tbl = Table(title="Orchestration Trace", border_style="cyan")
        tbl.add_column("Field", style="bold")
        tbl.add_column("Value")
        tbl.add_row("Intent", tr.intent)
        tbl.add_row("Strategy", tr.strategy)
        tbl.add_row("Models invoked", ", ".join(tr.models_invoked))
        tbl.add_row("Synthesis", tr.synthesis_mode)
        tbl.add_row("Final model", tr.final_model)
        tbl.add_row("Escalated?", "yes" if tr.escalated else "no")
        tbl.add_row("Total latency", f"{tr.total_latency_ms} ms")
        console.print(tbl)
        for i, pr in enumerate(tr.proposer_results, 1):
            console.print(f"  [{i}] {pr['model']:12} conf={pr['confidence']} "
                          f"lat={pr['latency_ms']}ms ok={pr['ok']}")


@app.command()
def tools() -> None:
    """List available tools (Build #036)."""
    from monad.tools import default_registry
    reg = default_registry(workspace_dir=Path.cwd() / "workspace")
    tbl = Table(title="Tools", border_style="cyan")
    tbl.add_column("ID", style="bold")
    tbl.add_column("Name")
    tbl.add_column("Action")
    tbl.add_column("Needs approval")
    for t in reg.list():
        tbl.add_row(t.id, t.name, t.action, "✔" if t.requires_approval else "✘")
    console.print(tbl)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
) -> None:
    """Start the FastAPI dashboard + REST API (Build #059)."""
    try:
        from monad.api import serve as api_serve
    except Exception as e:
        console.print(f"[red]cannot start server: {e}[/red]")
        raise typer.Exit(1)
    console.print(f"[bold cyan]🧠 Monad API + dashboard[/bold cyan] "
                  f"→ [green]http://{host}:{port}[/green]")
    console.print("[dim]press ctrl-c to stop[/dim]")
    api_serve(host=host, port=port, root=Path.cwd())


@app.command()
def memory(
    op: str = typer.Argument(..., help="remember | recall | forget | size"),
    text: str = typer.Argument("", help="Text to remember / query / forget."),
    top_k: int = typer.Option(5, "--top-k", "-k"),
) -> None:
    """SQLite + vector memory operations (Build #026)."""
    from monad.memory import Memory
    apporch = _boot()
    m = Memory(memory_dir=apporch.resources.memory_dir if apporch.resources
               else Path.cwd() / "memory_data")
    if op == "remember":
        if not text:
            console.print("[red]need text to remember[/red]")
            raise typer.Exit(1)
        eid = m.remember(text, kind="note", tag="cli")
        console.print(f"[green]✔ remembered as event-{eid}[/green]")
    elif op == "recall":
        if not text:
            console.print("[red]need query text[/red]")
            raise typer.Exit(1)
        hits = m.recall(text, top_k=top_k)
        if not hits:
            console.print("[dim]no results[/dim]")
        for h in hits:
            console.print(f"  [{h.score:.3f}] [dim]{h.source:8}[/dim] {h.text[:200]}")
    elif op == "forget":
        if not text:
            console.print("[red]need needle to forget[/red]")
            raise typer.Exit(1)
        n = m.forget(text)
        console.print(f"[yellow]forgot {n} event(s)[/yellow]")
    elif op == "size":
        import json as _json
        console.print(_json.dumps(m.size(), indent=2))
    else:
        console.print(f"[red]unknown op:[/red] {op}")
        raise typer.Exit(1)


@app.command()
def strategies() -> None:
    """List available orchestration strategies (Build #017)."""
    from monad.orchestration import STRATEGY_REGISTRY
    tbl = Table(title="Orchestration Strategies", border_style="cyan")
    tbl.add_column("Name", style="bold")
    tbl.add_column("Description")
    docs = {
        "domain_routing": "Route to specialist by intent (fastest, cheapest)",
        "cascade": "Try cheap model, escalate on low confidence",
        "mixture_of_agents": "N proposers in parallel + aggregator merges",
        "verification": "Proposer + independent verifier (best for code)",
        "ensemble": "Parallel + majority vote (best for factual QA)",
    }
    for name in STRATEGY_REGISTRY:
        tbl.add_row(name, docs.get(name, ""))
    console.print(tbl)


# ---------------------------------------------------------------------------
# Cognitive architecture commands (Phase 5)
# ---------------------------------------------------------------------------

cognition = typer.Typer(help="Cognitive architecture — 83 organs, Cognee memory, Reflexion.")
app.add_typer(cognition, name="cognition")


@cognition.command("info")
def cognition_info() -> None:
    """Show cognitive architecture status."""
    from monad.cognition import Monad, MonadConfig
    m = Monad(MonadConfig())
    info = m.info()
    tbl = Table(title="🧠 Monad Cognitive Architecture", border_style="magenta")
    tbl.add_column("Layer", style="bold")
    tbl.add_column("Value")
    tbl.add_row("Version", info["version"])
    tbl.add_row("Organs (total)", str(info["organs"]["total"]))
    tbl.add_row("  Human geniuses", str(info["organs"]["human_genius"]))
    tbl.add_row("  Animal extremes", str(info["organs"]["animal_extreme"]))
    tbl.add_row("  Microbial", str(info["organs"]["microbial"]))
    tbl.add_row("  Conceptual", str(info["organs"]["conceptual"]))
    tbl.add_row("Memory backend", info["memory"]["backend"])
    tbl.add_row("Memory triplets", str(info["memory"]["triplets"]))
    tbl.add_row("Self-model nodes", str(info["self_model"]["total_nodes"]))
    tbl.add_row("MCP tools exported", str(info["mcp_tools"]))
    tbl.add_row("Executive strategy", info["config"]["strategy"])
    console.print(tbl)


@cognition.command("organs")
def cognition_organs(
    category: str = typer.Option("", "--category", "-c",
                                 help="human_genius | animal_extreme | microbial | conceptual"),
) -> None:
    """List cognitive organs, optionally filtered by category."""
    from monad.cognition import register_all
    from monad.cognition.organs.base import OrganCategory
    reg = register_all()
    if category:
        try:
            cat_enum = OrganCategory(category)
        except ValueError:
            console.print(f"[red]Unknown category:[/red] {category}")
            raise typer.Exit(1)
        organs = reg.list_by_category(cat_enum)
    else:
        organs = reg.all()
    tbl = Table(title=f"Organs ({len(organs)})", border_style="magenta")
    tbl.add_column("Name", style="bold")
    tbl.add_column("Inspiration")
    tbl.add_column("Category")
    tbl.add_column("Search")
    for o in organs:
        tbl.add_row(o.name, o.inspiration, o.category.value, o.search_strategy)
    console.print(tbl)


@cognition.command("think")
def cognition_think(
    prompt: str = typer.Argument(..., help="Prompt for the cognitive pipeline."),
    max_organs: int = typer.Option(6, "--max-organs", "-n"),
    strategy: str = typer.Option("weighted_vote", "--strategy", "-s",
                                 help="weighted_vote | highest_confidence"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show organ trace."),
) -> None:
    """Run the full 9-layer cognitive pipeline on a prompt."""
    from monad.cognition import Monad, MonadConfig
    m = Monad(MonadConfig(strategy=strategy, max_organs_per_cycle=max_organs))
    cycle = m.think(prompt)

    console.print(Panel(cycle.output or "[dim](no output)[/dim]",
                        title="🧠 Monad thought", border_style="magenta"))

    if verbose:
        tbl = Table(title="Cognition Trace", border_style="cyan")
        tbl.add_column("Layer", style="bold")
        tbl.add_column("Value")
        tbl.add_row("Query mode", cycle.query_mode)
        tbl.add_row("Model tier", cycle.routing["tier"] if cycle.routing else "-")
        tbl.add_row("Model reason", cycle.routing["reason"] if cycle.routing else "-")
        tbl.add_row("Organs activated", str(len(cycle.activated_organs)))
        tbl.add_row("Executive strategy", cycle.decision["strategy"] if cycle.decision else "-")
        tbl.add_row("Confidence", f"{cycle.decision['confidence']:.2f}" if cycle.decision else "-")
        tbl.add_row("Reflexion triggered",
                    "yes" if (cycle.decision and cycle.decision["reflexion_triggered"]) else "no")
        console.print(tbl)
        for o in cycle.organ_results[:6]:
            console.print(f"  • [dim]{o['organ']:32}[/dim] conf={o['confidence']:.2f} "
                          f"{o['output'][:80]}")
