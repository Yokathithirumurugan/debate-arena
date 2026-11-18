"""
transcript.py — Saves full debate transcripts to disk.

Saves each debate as a Markdown file in the debates/ folder with
a human-readable timestamp and topic slug in the filename.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from personas import Debater


def _slugify(text: str, max_len: int = 40) -> str:
    """Converts a string to a filename-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:max_len]


def save_transcript(
    topic:      str,
    fmt:        str,
    debaters:   list["Debater"],
    transcript: list[dict],
    verdict:    dict,
) -> str:
    """
    Saves the full debate transcript and verdict as a Markdown file.

    Returns:
        Path to the saved file.
    """
    debates_dir = Path("debates")
    debates_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug      = _slugify(topic)
    filepath  = debates_dir / f"{timestamp}_{slug}.md"

    lines = [
        f"# 🎭 Debate Arena — Transcript",
        f"",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| **Topic** | {topic} |",
        f"| **Format** | {fmt.upper()} |",
        f"| **Date** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
        f"| **Rounds** | {max(t.get('round', 0) for t in transcript if t.get('round', 0) < 90)} |",
        f"",
        "---",
        "",
        "## 👥 Debaters",
        "",
    ]

    for d in debaters:
        emoji = "🟢" if d.position == "FOR" else ("🔴" if d.position == "AGAINST" else "🔵")
        lines.append(f"- {emoji} **{d.name}** ({d.position}): {d.expertise}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📜 Debate Transcript")
    lines.append("")

    for turn in transcript:
        phase_tag = f" _{turn.get('phase', '').upper()}_" if "phase" in turn else ""
        emoji = "🟢" if turn["position"] == "FOR" else ("🔴" if turn["position"] == "AGAINST" else "🔵")
        rnd   = turn.get("round", "?")
        rnd_label = "Opening" if rnd == 0 else ("Closing" if rnd == 99 else f"Round {rnd}")
        lines.append(f"### {emoji} {turn['speaker']} — {rnd_label}{phase_tag}")
        lines.append("")
        lines.append(turn["content"])
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 🏛️ Judge's Verdict")
    lines.append("")

    # Winner
    winner = verdict.get("winner", "TIE")
    winner_name = verdict.get("winner_name", "")
    if winner == "TIE":
        lines.append("**Result:** 🤝 TIE")
    else:
        emoji = "🟢" if winner == "FOR" else "🔴"
        lines.append(f"**Winner:** {emoji} {winner_name} ({winner})")
    lines.append("")

    # Scores
    scores = verdict.get("scores", {})
    if scores:
        lines.append("### 📊 Scores")
        lines.append("")
        lines.append("| Category | FOR | AGAINST |")
        lines.append("|----------|-----|---------|")
        for cat in ["argumentation", "evidence", "rebuttal", "delivery", "total"]:
            f_score = scores.get("FOR",     {}).get(cat, "—")
            c_score = scores.get("AGAINST", {}).get(cat, "—")
            lines.append(f"| {cat.capitalize()} | {f_score} | {c_score} |")
        lines.append("")

    # Strongest args
    lines.append(f"**Strongest FOR argument:** {verdict.get('strongest_argument_FOR', 'N/A')}")
    lines.append("")
    lines.append(f"**Strongest AGAINST argument:** {verdict.get('strongest_argument_AGAINST', 'N/A')}")
    lines.append("")

    # Fallacies
    fallacies = verdict.get("fallacies_detected", [])
    if fallacies:
        lines.append("### ⚠️ Logical Fallacies")
        lines.append("")
        for f in fallacies:
            lines.append(f"- **{f.get('side')}** — {f.get('fallacy')}: \"{f.get('example', '')}\"")
        lines.append("")

    # Insights
    insights = verdict.get("key_insights", [])
    if insights:
        lines.append("### 💡 Key Insights")
        lines.append("")
        for ins in insights:
            lines.append(f"- {ins}")
        lines.append("")

    # Synthesis
    synthesis = verdict.get("synthesis", "")
    if synthesis:
        lines.append("### 🔭 Synthesis")
        lines.append("")
        lines.append(synthesis)
        lines.append("")

    # Judge notes
    notes = verdict.get("judge_notes", "")
    if notes:
        lines.append("### 📝 Judge's Notes")
        lines.append("")
        lines.append(notes)
        lines.append("")

    # Raw fallback
    if verdict.get("parse_error"):
        lines.append("### Raw Verdict (parse error)")
        lines.append("")
        lines.append("```")
        lines.append(verdict.get("raw_verdict", ""))
        lines.append("```")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return str(filepath)
