#!/usr/bin/env python3
"""Check a builder-skill project's state files for the slips a script can see.

Run from the project root:

    python tools/check_state.py              # report errors and warnings
    python tools/check_state.py --strict     # warnings also fail
    python tools/check_state.py --pre-commit # for a git pre-commit hook: also
                                             # requires PROGRESS.md to be staged
                                             # whenever code is staged

Exit code 0 when there are no errors, 1 otherwise. Python 3.8+, standard
library only.

What it checks:
  * SPEC.md and PROGRESS.md exist and name exactly one tier and one phase
  * the state files the tier requires are present
  * every ticked item in the core gate and ship checklists has evidence
    written after the dash (or is marked n/a with a reason)
  * the project is not in Phase 3 or 4 with gate items still open, unless an
    override is recorded
  * every file containing a stub marker is listed under "Stubs / fakes"
  * PROGRESS.md was part of the last commit that changed code
  * small things: unfilled template placeholders, an overlong log

It checks form, not truth: it cannot tell whether the evidence is real.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

TIERS = ("Demo", "Tool", "Product")
FILES_BY_TIER = {
    "Demo": ["SPEC.md", "PROGRESS.md", "BACKLOG.md"],
    "Tool": ["SPEC.md", "PROGRESS.md", "BACKLOG.md", "DEPENDENCIES.md", "DECISIONS.md"],
    "Product": ["SPEC.md", "PROGRESS.md", "BACKLOG.md", "DEPENDENCIES.md", "DECISIONS.md"],
}
GATE_GROUPS_BY_TIER = {
    "Demo": ["All tiers"],
    "Tool": ["All tiers", "Tool and Product"],
    "Product": ["All tiers", "Tool and Product", "Product"],
}
STUB_MARKER = "TODO" + "(stub)"  # split so this file doesn't flag itself
SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__", "dist",
    "build", ".next", "target", ".idea", ".vscode", ".pytest_cache", ".mypy_cache",
}
MAX_SCAN_BYTES = 1_000_000
MAX_LOG_ENTRIES = 10
DASHES = ("\u2014", "\u2013", " -- ")  # em dash, en dash, double hyphen
ITEM_RE = re.compile(r"^\s*[-*]\s*\[( |x|X)\]\s*(.*)$")


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def field(text, name):
    """Value of a '**Name:** value' line, or None."""
    m = re.search(r"^\*\*%s:\*\*[ \t]*(.*)$" % re.escape(name), text, re.MULTILINE)
    return m.group(1).strip() if m else None


def section(text, heading_start):
    """Body of the first '## ' section whose title starts with heading_start."""
    lines = text.splitlines()
    body, inside = [], False
    for line in lines:
        if line.startswith("## "):
            if inside:
                break
            inside = line[3:].strip().lower().startswith(heading_start.lower())
            continue
        if inside:
            body.append(line)
    return "\n".join(body) if inside or body else None


def parse_tier(spec_text, report):
    raw = field(spec_text, "Tier")
    if raw is None:
        report.error("SPEC.md has no '**Tier:**' line.")
        return None
    head = raw
    for dash in DASHES:
        head = head.split(dash)[0]
    found = [t for t in TIERS if re.search(r"\b%s\b" % t, head)]
    if len(found) != 1:
        report.error("SPEC.md tier is not decided: '%s'. Pick one of Demo, Tool, Product." % raw)
        return None
    return found[0]


def parse_phase(progress_text, report):
    raw = field(progress_text, "Phase")
    if raw is None:
        report.error("PROGRESS.md has no '**Phase:**' line.")
        return None
    found = re.findall(r"\b([0-4])\b", raw)
    if len(found) != 1:
        report.error("PROGRESS.md phase is not decided: '%s'. Keep only the current phase." % raw)
        return None
    return int(found[0])


def evidence_of(item_text):
    """Text after the last dash separator, or '' if there is none."""
    best = -1
    width = 0
    for dash in DASHES:
        i = item_text.rfind(dash)
        if i > best:
            best, width = i, len(dash)
    if best < 0:
        return ""
    return item_text[best + width:].strip()


def checklist_items(body):
    """Yield (ticked, text) for each checkbox line in a section body."""
    for line in (body or "").splitlines():
        m = ITEM_RE.match(line)
        if m:
            yield m.group(1).lower() == "x", m.group(2).strip()


def is_na(text):
    return bool(re.match(r"n/?a\b", evidence_of(text), re.IGNORECASE))


def check_checklist(name, body, report):
    """Report ticked items lacking evidence. Return count of open items."""
    open_items = 0
    for ticked, text in checklist_items(body):
        ev = evidence_of(text)
        if ticked:
            if not ev or ev.startswith("<"):
                report.error("%s: ticked without evidence: '%s'" % (name, short(text)))
        elif is_na(text):
            if len(ev) < 8:
                report.warn("%s: marked n/a without a reason: '%s'" % (name, short(text)))
        else:
            open_items += 1
    return open_items


def short(text, n=70):
    return text if len(text) <= n else text[: n - 1] + "\u2026"


def meaningful_entries(body):
    """List-item lines that are filled in (not template placeholders)."""
    out = []
    for line in (body or "").splitlines():
        s = line.strip()
        if not s.startswith(("-", "*")):
            continue
        content = s[1:].strip()
        if not content or content in ("\u2026", "...") or content.startswith("<"):
            continue
        out.append(content)
    return out


def git(root, *args):
    try:
        res = subprocess.run(
            ["git", *args], cwd=str(root), capture_output=True, text=True, timeout=20
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0:
        return None
    return res.stdout


def project_files(root):
    """Tracked and untracked-but-not-ignored files, or a directory walk."""
    out = git(root, "ls-files", "--cached", "--others", "--exclude-standard")
    if out is not None:
        paths = [root / p for p in out.splitlines() if p.strip()]
    else:
        paths = [p for p in root.rglob("*") if p.is_file()]
    keep = []
    for p in paths:
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        keep.append(p)
    return keep


def is_code(path):
    return path.suffix.lower() not in (".md", ".txt", ".rst", "") or path.name in (
        "Makefile", "Dockerfile",
    )


def check_stubs(root, progress_text, report):
    stubs_body = section(progress_text, "Stubs") or ""
    for p in project_files(root):
        if p.suffix.lower() == ".md" or not p.is_file():
            continue
        try:
            if p.stat().st_size > MAX_SCAN_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if STUB_MARKER not in text:
            continue
        rel = p.relative_to(root).as_posix()
        if rel not in stubs_body and p.name not in stubs_body:
            report.error(
                "%s contains %s but is not listed under 'Stubs / fakes' in PROGRESS.md."
                % (rel, STUB_MARKER)
            )


def check_git(root, report, pre_commit):
    if git(root, "rev-parse", "--is-inside-work-tree") is None:
        return
    if pre_commit:
        staged = git(root, "diff", "--cached", "--name-only")
        names = [n for n in (staged or "").splitlines() if n.strip()]
        if any(is_code(Path(n)) for n in names) and "PROGRESS.md" not in names:
            report.error(
                "Code is staged but PROGRESS.md is not. Update it and stage it "
                "(or commit with --no-verify if this change truly doesn't affect it)."
            )
        return
    last = git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", "HEAD")
    if last is None:
        return
    names = [n for n in last.splitlines() if n.strip()]
    if any(is_code(Path(n)) for n in names) and "PROGRESS.md" not in names:
        report.warn("The last commit changed code without updating PROGRESS.md.")


def main():
    parser = argparse.ArgumentParser(description="Check builder-skill state files.")
    parser.add_argument("root", nargs="?", default=".", help="project root (default: .)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--pre-commit", action="store_true", help="git pre-commit mode")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = Report()
    spec_path, progress_path = root / "SPEC.md", root / "PROGRESS.md"

    if not spec_path.exists():
        print("ERROR: no SPEC.md in %s. Start with Phase 0, or adopt the project." % root)
        return 1

    spec = read(spec_path)
    tier = parse_tier(spec, report)
    if "<project name>" in spec:
        report.warn("SPEC.md still has the '<project name>' placeholder.")
    assumed = spec.count("(assumed)")
    # The template's own instruction line mentions "(assumed)" once.
    if "Mark anything guessed" in spec:
        assumed -= 1

    phase = None
    if not progress_path.exists():
        report.error("No PROGRESS.md. Create it from the template at the end of Phase 0.")
    else:
        progress = read(progress_path)
        phase = parse_phase(progress, report)
        if "<project name>" in progress:
            report.warn("PROGRESS.md still has the '<project name>' placeholder.")

        p_tier_raw = field(progress, "Tier")
        if tier and p_tier_raw:
            p_found = [t for t in TIERS if re.search(r"\b%s\b" % t, p_tier_raw)]
            if p_found != [tier]:
                report.warn("Tier in PROGRESS.md ('%s') doesn't match SPEC.md (%s)." % (p_tier_raw, tier))

        next_step = field(progress, "Next step")
        if not next_step or next_step in ("\u2026", "..."):
            report.warn("PROGRESS.md has no next step written.")

        gate = section(progress, "Core gate")
        gate_open = 0
        if gate is None:
            report.error("PROGRESS.md has no '## Core gate' section.")
        else:
            gate_open = check_checklist("Core gate", gate, report)
            if tier:
                for group in GATE_GROUPS_BY_TIER[tier]:
                    if not re.search(r"^###\s+%s\s*$" % re.escape(group), gate, re.MULTILINE):
                        report.warn("Core gate is missing the '%s' group required at %s tier." % (group, tier))

        ship = section(progress, "Ship")
        ship_open = check_checklist("Ship", ship, report) if ship is not None else 0

        overrides = meaningful_entries(section(progress, "Overrides"))
        if phase is not None and phase >= 3 and gate_open and not overrides:
            report.error(
                "Phase is %d but %d core gate item(s) are still open and no override is recorded. "
                "Finish the gate, or record the user's override." % (phase, gate_open)
            )
        if phase == 4 and ship is None and tier != "Demo":
            report.warn("Phase is 4 but PROGRESS.md has no '## Ship' checklist.")
        if phase == 4 and ship_open == 0 and ship is not None and gate_open:
            report.warn("Ship checklist is complete but the core gate still has open items.")

        log = meaningful_entries(section(progress, "Log"))
        if len(log) > MAX_LOG_ENTRIES:
            report.warn("Log has %d entries; keep the %d most recent." % (len(log), MAX_LOG_ENTRIES))

        if phase is not None and phase >= 2 and assumed > 0:
            report.warn("SPEC.md still has %d item(s) marked (assumed); confirm them with the user." % assumed)

        check_stubs(root, progress, report)

    if tier and (phase is None or phase >= 1):
        for name in FILES_BY_TIER[tier]:
            if not (root / name).exists():
                report.error("%s is required at %s tier but is missing." % (name, tier))

    check_git(root, report, args.pre_commit)

    for msg in report.errors:
        print("ERROR: " + msg)
    for msg in report.warnings:
        print("WARN:  " + msg)

    label = "tier %s, phase %s" % (tier or "?", phase if phase is not None else "?")
    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    print(
        "%s: %d error(s), %d warning(s) [%s]"
        % ("FAILED" if failed else "OK", len(report.errors), len(report.warnings), label)
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
