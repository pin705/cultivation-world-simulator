from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

APP_NAME = "CultivationWorldSimulator"
DEV_APP_NAME = "CultivationWorldSimulator-dev"


def _workspace_hash() -> str:
    raw = os.environ.get("CWS_WORKSPACE_HASH")
    if raw:
        return raw
    digest = hashlib.md5(str(REPO_ROOT).encode("utf-8")).hexdigest()
    return digest[:8]


def _default_data_root() -> Path:
    explicit = os.environ.get("CWS_DATA_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()

    app_name = APP_NAME if getattr(sys, "frozen", False) else DEV_APP_NAME
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    root = base / app_name
    if app_name == DEV_APP_NAME:
        root = root / _workspace_hash()
    return root


def _iter_candidate_dirs(explicit_dir: str | None) -> list[Path]:
    if explicit_dir:
        return [Path(explicit_dir).expanduser().resolve()]

    candidates = [
        _default_data_root() / "logs",
        REPO_ROOT / "logs",
        Path.cwd().resolve() / "logs",
    ]

    unique: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return unique


def _iter_log_files(log_dirs: Iterable[Path], limit: int | None) -> list[Path]:
    files: list[Path] = []
    for log_dir in log_dirs:
        if not log_dir.exists():
            continue
        files.extend(sorted(log_dir.glob("*.log")))

    files = sorted(set(files))
    if limit is not None:
        return files[-limit:]
    return files


def _parse_interactions(log_files: Iterable[Path]) -> list[dict]:
    rows: list[dict] = []
    for log_file in log_files:
        with log_file.open("r", encoding="utf-8") as handle:
            for line in handle:
                if "LLM_INTERACTION: " not in line:
                    continue
                try:
                    json_str = line.split("LLM_INTERACTION: ", 1)[1].strip()
                    payload = json.loads(json_str)
                except (IndexError, json.JSONDecodeError):
                    continue
                payload["_log_file"] = str(log_file)
                rows.append(payload)
    return rows


def _build_report(rows: Iterable[dict]) -> tuple[list[dict], dict]:
    aggregates: dict[str, dict] = defaultdict(
        lambda: {
            "task_name": "unknown",
            "calls": 0,
            "skipped": 0,
            "prompt_chars": 0,
            "response_chars": 0,
            "duration_seconds": 0.0,
            "models": set(),
            "modes": set(),
            "categories": set(),
        }
    )

    total_calls = 0
    total_skipped = 0
    total_prompt_chars = 0
    total_response_chars = 0

    for row in rows:
        task_name = str(row.get("task_name") or "unknown")
        bucket = aggregates[task_name]
        bucket["task_name"] = task_name
        bucket["calls"] += 1
        bucket["prompt_chars"] += int(row.get("prompt_length") or 0)
        bucket["response_chars"] += int(row.get("response_length") or 0)
        bucket["duration_seconds"] += float(row.get("duration") or 0.0)

        model_name = str(row.get("model_name") or "unknown")
        if model_name:
            bucket["models"].add(model_name)
        mode = str(row.get("task_mode") or "")
        if mode:
            bucket["modes"].add(mode)
        category = str(row.get("task_category") or "")
        if category:
            bucket["categories"].add(category)

        if row.get("task_policy_decision") == "disabled" or model_name == "policy_skip":
            bucket["skipped"] += 1
            total_skipped += 1

        total_calls += 1
        total_prompt_chars += int(row.get("prompt_length") or 0)
        total_response_chars += int(row.get("response_length") or 0)

    report_rows: list[dict] = []
    for bucket in aggregates.values():
        calls = int(bucket["calls"])
        report_rows.append(
            {
                "task_name": bucket["task_name"],
                "calls": calls,
                "skipped": int(bucket["skipped"]),
                "skip_rate": round((bucket["skipped"] / calls), 4) if calls else 0.0,
                "prompt_chars": int(bucket["prompt_chars"]),
                "response_chars": int(bucket["response_chars"]),
                "avg_duration_seconds": round((bucket["duration_seconds"] / calls), 3) if calls else 0.0,
                "models": sorted(bucket["models"]),
                "modes": sorted(bucket["modes"]),
                "categories": sorted(bucket["categories"]),
            }
        )

    report_rows.sort(key=lambda row: (-row["prompt_chars"], -row["calls"], row["task_name"]))
    summary = {
        "total_calls": total_calls,
        "total_skipped": total_skipped,
        "total_prompt_chars": total_prompt_chars,
        "total_response_chars": total_response_chars,
    }
    return report_rows, summary


def _print_human_report(report_rows: list[dict], summary: dict, log_files: list[Path]) -> None:
    print("LLM Task Usage Report")
    print(f"Log files scanned: {len(log_files)}")
    print(f"Total calls: {summary['total_calls']}")
    print(f"Total skipped: {summary['total_skipped']}")
    print(f"Total prompt chars: {summary['total_prompt_chars']}")
    print(f"Total response chars: {summary['total_response_chars']}")
    print("")

    if not report_rows:
        print("No LLM interaction rows found.")
        return

    headers = [
        "task_name",
        "calls",
        "skipped",
        "skip_rate",
        "prompt_chars",
        "response_chars",
        "avg_duration_seconds",
    ]
    widths = {header: len(header) for header in headers}
    for row in report_rows:
        for header in headers:
            widths[header] = max(widths[header], len(str(row[header])))

    header_line = "  ".join(header.ljust(widths[header]) for header in headers)
    print(header_line)
    print("  ".join("-" * widths[header] for header in headers))

    for row in report_rows:
        print(
            "  ".join(
                str(row[header]).ljust(widths[header])
                for header in headers
            )
        )

    print("")
    for row in report_rows:
        print(
            f"- {row['task_name']}: models={','.join(row['models']) or '-'}; "
            f"modes={','.join(row['modes']) or '-'}; "
            f"categories={','.join(row['categories']) or '-'}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate LLM log usage by task_name for commercial AI cost reviews."
    )
    parser.add_argument(
        "--log-dir",
        help="Optional log directory. Defaults to data-root logs and ./logs when present.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only scan the most recent N log files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON instead of a human-readable table.",
    )
    args = parser.parse_args()

    log_dirs = _iter_candidate_dirs(args.log_dir)
    log_files = _iter_log_files(log_dirs, args.limit)
    rows = _parse_interactions(log_files)
    report_rows, summary = _build_report(rows)

    if args.json:
        print(
            json.dumps(
                {
                    "log_dirs": [str(path) for path in log_dirs],
                    "log_files": [str(path) for path in log_files],
                    "summary": summary,
                    "rows": report_rows,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    _print_human_report(report_rows, summary, log_files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
