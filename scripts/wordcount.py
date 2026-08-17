#!/usr/bin/env python3
import argparse
import json
import subprocess
from collections import defaultdict
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

START = "<!-- WRITING-STATS:START -->"
END = "<!-- WRITING-STATS:END -->"


def read_totals(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    totals = defaultdict(int)
    for entry in data["stats"]["dailyActivity"]:
        activity_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
        totals[activity_date] += sum(
            change.get("w", 0) for change in entry.get("changes", [])
        )
    return data, totals


def intensity(words: int, stops: dict) -> int:
    if words <= 0:
        return 0
    if words < stops["low"]:
        return 1
    if words < stops["medium"]:
        return 2
    if words < stops["high"]:
        return 3
    return 4


def display_date(day: date) -> str:
    return f"{day.strftime('%b')} {day.day}, {day.year}"


def build_svg(days, values, stops, colors, goal: int, as_of: date) -> str:
    cell, gap = 12, 3
    left, top = 34, 24
    columns = (len(days) + 6) // 7
    width = left + columns * (cell + gap) - gap + 3
    height = top + 7 * (cell + gap) - gap + 28
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Writing activity heatmap">',
        '<style>text{font:10px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;fill:#57606a}</style>',
        f'<title>Writing activity — goal: {goal:,} words/day</title>',
    ]

    for row, label in ((0, "Mon"), (2, "Wed"), (4, "Fri")):
        y = top + row * (cell + gap) + 10
        parts.append(f'<text x="0" y="{y}">{label}</text>')

    last_month = None
    for i, day in enumerate(days):
        column, row = divmod(i, 7)
        x = left + column * (cell + gap)
        y = top + row * (cell + gap)

        if day.month != last_month and day.day <= 7:
            month = day.strftime("%b") if day.month != 1 else day.strftime("%b %Y")
            parts.append(f'<text x="{x}" y="12">{escape(month)}</text>')
        last_month = day.month

        words = values.get(day, 0)
        fill = colors[str(intensity(words, stops))]
        opacity = "0.42" if day > as_of else "1"
        label = "future date" if day > as_of else f"{words:+,} net words"
        parts.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
            f'fill="{fill}" opacity="{opacity}"><title>'
            f'{escape(day.isoformat() + ": " + label)}</title></rect>'
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def replace_marked_block(path: Path, block: str):
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit(f"{path} must contain {START} and {END} on separate lines")
    before, remaining = text.split(START, 1)
    _, after = remaining.split(END, 1)
    path.write_text(before + START + "\n" + block + "\n" + END + after, encoding="utf-8")


def write_heatmap(repo: Path, svg: str):
    assets = repo / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "writing-heatmap.svg").write_text(svg, encoding="utf-8")


def git_commit_and_push(repo: Path, paths: list[str]):
    subprocess.run(["git", "-C", str(repo), "add", *paths], check=True)
    changed = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--quiet"]
    ).returncode != 0

    if changed:
        subprocess.run(
            ["git", "-C", str(repo), "commit", "-m", "chore: update writing stats"],
            check=True,
        )
        subprocess.run(["git", "-C", str(repo), "push"], check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Publish Keep the Rhythm statistics for Aug 2026 – Feb 2027."
    )
    parser.add_argument("--data", type=Path, required=True, help="Keep the Rhythm data.json")
    parser.add_argument(
        "--repo",
        type=Path,
        required=True,
        help="Local checkout of the GitHub profile repository",
    )
    parser.add_argument(
        "--garden-repo",
        type=Path,
        required=True,
        help="Local checkout of the digital-garden-jekyll-template repository",
    )
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=date(2026, 8, 12),
        help="YYYY-MM-DD; default: 2026-08-12",
    )
    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        default=date(2027, 2, 28),
        help="YYYY-MM-DD; default: 2027-02-28",
    )
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=date.today(),
        help="Do not include later dates in averages; default: today",
    )
    parser.add_argument("--commit", action="store_true", help="Commit and push generated changes")
    args = parser.parse_args()

    if args.end_date < args.start_date:
        raise SystemExit("--end-date must be on or after --start-date")

    data, totals = read_totals(args.data)
    settings = data["settings"]
    heatmap = settings["heatmapConfig"]
    goal = settings["dailyWritingGoal"]

    days = [
        args.start_date + timedelta(days=i)
        for i in range((args.end_date - args.start_date).days + 1)
    ]
    as_of = min(args.as_of, args.end_date)
    observed_days = [day for day in days if day <= as_of]
    values = {day: totals.get(day, 0) for day in days}

    net_total = sum(values[day] for day in observed_days)
    active_days = sum(values[day] > 0 for day in observed_days)
    calendar_average = net_total / len(observed_days) if observed_days else 0
    active_average = net_total / active_days if active_days else 0
    goal_days = sum(values[day] >= goal for day in observed_days)
    as_of_label = display_date(as_of)

    svg = build_svg(
        days,
        values,
        heatmap["intensityStops"],
        heatmap["colors"]["light"],
        goal,
        as_of,
    )
    write_heatmap(args.repo, svg)
    write_heatmap(args.garden_repo, svg)

    def stats_block(image_path: str) -> str:
        return f"""## Writing Stats

It's dissertation season through Feb '27.

**As of {as_of_label}:** {net_total:,} net words <br>
**Average:** {calendar_average:,.0f} net words/day ({active_average:,.0f} on {active_days} active days) <br>
**Goal met:** {goal_days}/{len(observed_days)} days at ≥ {goal:,} words per day

![GitHub-style heatmap of daily writing activity]({image_path})
"""

    replace_marked_block(
        args.repo / "README.md",
        stats_block("assets/writing-heatmap.svg"),
    )
    replace_marked_block(
        args.garden_repo / "_pages" / "about.md",
        stats_block("{{ '/assets/writing-heatmap.svg' | relative_url }}"),
    )

    if args.commit:
        git_commit_and_push(args.repo, ["README.md", "assets/writing-heatmap.svg"])
        git_commit_and_push(
            args.garden_repo,
            ["_pages/about.md", "assets/writing-heatmap.svg"],
        )


if __name__ == "__main__":
    main()
