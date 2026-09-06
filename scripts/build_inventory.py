"""M5: generate the concrete file inventory and public Python interfaces from this checkout."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNERS = {
    "schemas": "M1",
    "config": "M1",
    "allocator": "M1",
    "validator": "M1",
    "reservations": "M1",
    "authority_store": "M1",
    "coordinator": "M1",
    "coordinator_process": "M1",
    "member": "M3",
    "member_process": "M3",
    "clock": "M3",
    "transport": "M3",
    "local_policy": "M3",
    "runtime_common": "M3",
    "events": "M3",
    "replay": "M3",
    "plant": "M2",
    "plant_process": "M2",
    "devices": "M2",
    "supervisor": "M2",
    "runtime": "M2",
    "process_entry": "M2",
    "faults": "M2",
    "cli": "M2",
    "__init__": "M1",
}


def main():
    purposes = {}
    for line in (ROOT / "plans/19-build-map.md").read_text().splitlines():
        match = re.search(
            r"([\w.-]+\.(?:py|tsx?|json|md|css|svg|html)|acl|requirements.lock)\s+(M[1-5]|All) — (.+)",
            line,
        )
        if match:
            purposes[match[1]] = (match[2], match[3])
    purposes["demo-events.jsonl"] = (
        "M5",
        "Six authored mock snapshot events for replay primitives; not a live recording",
    )
    purposes["snapshots.json"] = (
        "M5",
        "Checked initial, leased, stale, offline, recovering and infeasible UI fixtures",
    )
    files = []
    for folder in ("src", "web", "tests", "fixtures", "config", "docs", "scripts"):
        for p in (ROOT / folder).rglob("*"):
            if (
                not p.is_file()
                or any(x in p.parts for x in ("node_modules", "dist", "__pycache__"))
                or p.suffix in (".pyc",)
                or "egg-info" in str(p)
            ):
                continue
            files.append(p)
    files += [
        ROOT / x
        for x in (
            "README.md",
            ".gitignore",
            "pyproject.toml",
            "requirements.lock",
            "BUILD_PLAN.md",
        )
    ]
    lines = [
        "# Concrete architecture and file map",
        "",
        "Generated from the event checkout by `scripts/build_inventory.py`. This inventories implementation files; the historical `plans/` and `research/` remain the decision/evidence archive. Runtime artifacts, dependencies, caches and the ignored private `pleaseread.md` are excluded from the versioned inventory. Start work from [BUILD_PLAN](../BUILD_PLAN.md), and check [implementation status](implementation-status.md) for evidence versus pending work.",
        "",
        "Process separation: supervisor owns Mosquitto, coordinator, five members and five plants; API/evidence observes MQTT in its own process. Pure cores remain separate from `_process.py` adapters. This adds adapter files to plan 19 rather than mixing transport and deterministic arithmetic. Cost: several small lifecycle modules; benefit: unit tests stay independent of broker/process setup.",
        "",
        "The frontend tree and state ownership remain as specified in [plan 19](../plans/19-build-map.md). Source of state is the backend Snapshot; browser timers animate presentation only. REST/WS contracts are in [protocol](protocol.md).",
        "",
        "## Every implementation file",
        "",
        "| File | Owner | Purpose |",
        "|---|---|---|",
    ]
    for p in sorted(set(files)):
        relative = p.relative_to(ROOT)
        owner, purpose = purposes.get(
            p.name, ("M4" if relative.parts[0] == "web" else "M5", "")
        )
        if relative.parts[:2] == ("src", "truss"):
            owner = OWNERS.get(p.stem, "M5")
            purpose = (
                ast.get_docstring(ast.parse(p.read_text())) or "Package metadata"
            ).splitlines()[0]
        if not purpose:
            if p.suffix == ".md":
                purpose = next(
                    (
                        line.lstrip("# ")
                        for line in p.read_text().splitlines()
                        if line.startswith("#")
                    ),
                    "Build documentation",
                )
            elif p.name.endswith(".schema.json"):
                purpose = (
                    "Generated exact JSON Schema; regenerate with build_fixtures.py"
                )
            elif p.name == "openapi.json":
                purpose = "Generated current REST request/success-response contract"
            elif p.suffix == ".py":
                purpose = (
                    ast.get_docstring(ast.parse(p.read_text())) or "Build/test utility"
                ).splitlines()[0]
                explicit = re.match(r"(M[1-5]):", purpose)
                if explicit:
                    owner = explicit[1]
            elif p.name == "pyproject.toml":
                owner = "M1"
                purpose = (
                    "Python dependencies, package configuration and command entrypoint"
                )
            elif p.name == ".gitignore":
                owner = "M2"
                purpose = "Exclude local explanation, credentials, dependencies and run artifacts"
            else:
                purpose = "Build/configuration artifact; interface defined by consuming module"
        lines.append(
            f"| [`{relative}`](../{relative}) | {owner} | {purpose.replace('|', '/')} |"
        )
    lines += [
        "",
        "## Actual Python public interfaces and dependencies",
        "",
        "Signatures are extracted from code, not future promises. Pydantic model fields are fully specified in generated JSON Schema. Methods that orchestrate processes are documented in their modules and BUILD_PLAN gates. Leading-underscore helpers are private. `__init__` constructors are included because their arguments are part of the interface.",
        "",
    ]
    for p in sorted((ROOT / "src/truss").glob("*.py")):
        tree = ast.parse(p.read_text())
        exports = []
        deps = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                deps.update(a.name for a in node.names)
            if isinstance(node, ast.ImportFrom):
                deps.add("." * node.level + (node.module or ""))
        for node in tree.body:
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) and not node.name.startswith("_"):
                exports.append(f"{node.name}({ast.unparse(node.args)})")
            elif isinstance(node, ast.ClassDef):
                methods = [
                    x
                    for x in node.body
                    if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and (not x.name.startswith("_") or x.name == "__init__")
                ]
                exports.extend(
                    f"{node.name}.{m.name}({ast.unparse(m.args)})" for m in methods
                )
                if not methods:
                    exports.append(node.name + " — data model")
        lines += [
            f"### {p.stem} · {OWNERS.get(p.stem, 'M5')}",
            "",
            "Dependencies: "
            + (", ".join(f"`{d}`" for d in sorted(deps)) or "none")
            + ".",
            "",
            "```text",
            *exports,
            "```",
            "",
        ]
    lines += [
        "## Generated/local-only files",
        "",
        "`runtime/{run_id}/`: manifest.json, run.json, credentials.json (0600), hashed broker passwords, ACL/config, authority.sqlite and WAL/SHM, coordinator.lock, processes.json, per-role logs, frozen profiles/, events.jsonl, per-plant state.json and atomic temporary files, optional bounded faults.json. Supervisor owns this run directory. Never commit credentials or fabricate evidence from its logs.",
        "",
        "`.venv/`, `web/node_modules/`, `web/dist/`, test caches and dependency downloads under the user cache are public dependencies/build output, not reused project implementation. `pleaseread.md` is deliberately ignored and explains the project privately in plain language.",
        "",
        "AI and SGLang have been removed from the build scope. No model helper files or runtime dependencies are planned.",
    ]
    (ROOT / "docs/architecture.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
