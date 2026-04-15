"""Command-line entry point for ``como-tag-audit``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from como_tag_audit import __version__
from como_tag_audit.audit import audit_gtm_id, audit_js, audit_url
from como_tag_audit.fetcher import FetchError
from como_tag_audit.models import AuditResult, Verdict

_VERDICT_STYLE = {
    Verdict.OK: "green",
    Verdict.OPTIONAL_CONSENT: "yellow",
    Verdict.MISSING_CONSENT_CONFIG: "red",
}


def _render_rich(result: AuditResult, console: Console) -> None:
    s = result.summary
    header = (
        f"[bold]{result.source_ref}[/bold]\n"
        f"GTM ID: [cyan]{s.gtm_id or 'not found'}[/cyan]  "
        f"CMP: [cyan]{s.cmp_detected or 'none / unknown'}[/cyan]  "
        f"Consent Mode init: "
        f"[{'green' if s.consent_mode_initialized else 'yellow'}]"
        f"{'yes' if s.consent_mode_initialized else 'no'}[/]\n"
        f"Tags: {s.total_tags} "
        f"([cyan]{s.google_tags}[/cyan] Google, [cyan]{s.non_google_tags}[/cyan] non-Google)"
        f"   Violations: [red]{s.violations}[/red]"
    )
    console.print(Panel(header, title="CoMo Tag Audit", border_style="blue"))

    if not result.tags:
        console.print("[yellow]No tags parsed.[/yellow]")
    else:
        table = Table(show_lines=False, header_style="bold")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Tag")
        table.add_column("Type", style="cyan")
        table.add_column("Vendor")
        table.add_column("Google?", justify="center")
        table.add_column("Consent")
        table.add_column("Verdict")
        for t in result.tags:
            consent = ", ".join(t.consent_types) if t.consent_types else "—"
            verdict_style = _VERDICT_STYLE[t.verdict]
            table.add_row(
                str(t.tag_id),
                t.tag_name,
                t.tag_type,
                t.vendor or "—",
                "yes" if t.is_google_tag else "no",
                consent,
                f"[{verdict_style}]{t.verdict.value}[/{verdict_style}]",
            )
        console.print(table)

    for w in result.warnings:
        console.print(f"[yellow]warning:[/yellow] {w}")

    if result.violations:
        console.print(
            Panel(
                f"[bold red]{len(result.violations)} non-Google tag(s) fire regardless "
                f"of user consent.[/bold red]\n\n"
                "Static analysis only shows misconfiguration. To see what actually "
                "fires after a user denies consent — including network requests, "
                "cookies set, and legal exposure — run a live audit at\n"
                "[link]https://consent-api.roseskyconsulting.com[/link]",
                border_style="red",
            )
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="como-tag-audit",
        description=(
            "Static Google Consent Mode audit for GTM containers. Finds every tag "
            "that fires without respecting user consent — from a URL, GTM ID, or "
            "raw gtm.js body."
        ),
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("url", nargs="?", help="URL to audit (fetches page + gtm.js)")
    src.add_argument("--gtm-id", help="Audit a GTM container ID directly")
    src.add_argument("--file", type=Path, help="Audit a local gtm.js file")

    out = p.add_mutually_exclusive_group()
    out.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    out.add_argument("--md", action="store_true", help="Emit a Markdown report")

    p.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout seconds")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console()
    try:
        if args.file:
            result = audit_js(args.file.read_text(encoding="utf-8"))
        elif args.gtm_id:
            result = audit_gtm_id(args.gtm_id, timeout=args.timeout)
        else:
            result = audit_url(args.url, timeout=args.timeout)
    except FetchError as exc:
        console.print(f"[red]error:[/red] {exc}")
        return 2
    except ValueError as exc:
        console.print(f"[red]error:[/red] {exc}")
        return 2

    if args.json:
        print(result.to_json())
    elif args.md:
        print(result.to_markdown())
    else:
        _render_rich(result, console)

    # Exit code reflects violations so CI can gate on it.
    return 1 if result.summary.violations > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
