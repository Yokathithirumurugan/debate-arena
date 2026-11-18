"""
Debate Arena — Configurable multi-agent debate system.

Supports multiple debate formats, custom persona YAML configs, structured
scoring verdicts with fallacy detection, persistent transcript saving,
and optional user-injection of counter-arguments mid-debate.

Usage:
    python agent.py --topic "AI is more creative than humans"
    python agent.py --topic "Open source always beats proprietary software" --rounds 3
    python agent.py --topic "Space colonization is a moral imperative" --format oxford --rounds 2
    python agent.py --topic "Coffee is better than tea" --personas sample_personas.yaml
    python agent.py --topic "Nuclear energy is the best climate solution" --interactive
"""

import argparse
import sys

from dotenv import load_dotenv

from formats import DebateFormat, get_format
from personas import PersonaManager
from verdict import VerdictEngine

load_dotenv()


# ---------------------------------------------------------------------------
# Debate orchestrator
# ---------------------------------------------------------------------------

def run_debate(
    topic: str,
    rounds: int = 2,
    format_name: str = "oxford",
    personas_file: str | None = None,
    interactive: bool = False,
    save: bool = True,
) -> None:
    """
    Orchestrates a full debate session.

    Args:
        topic:         The proposition to debate.
        rounds:        Number of back-and-forth rounds.
        format_name:   "oxford" | "lincoln" | "panel" | "socratic"
        personas_file: Optional YAML file with custom debater personas.
        interactive:   Allow the user to inject counter-arguments each round.
        save:          Persist full transcript + verdict to debates/ folder.
    """
    # ── Load debater personas ─────────────────────────────────────────
    pm = PersonaManager(personas_file)
    debaters = pm.get_debaters(format_name)

    # ── Select debate format strategy ─────────────────────────────────
    fmt: DebateFormat = get_format(format_name, debaters, rounds)

    # ── Print header ──────────────────────────────────────────────────
    _print_header(topic, format_name, debaters, rounds)

    # ── Run the debate rounds ─────────────────────────────────────────
    transcript = fmt.run(topic, interactive=interactive)

    # ── Judge's verdict ───────────────────────────────────────────────
    print(f"\n{'═'*65}")
    print("🏛️  VERDICT & SCORING")
    print(f"{'═'*65}\n")

    engine = VerdictEngine()
    verdict = engine.evaluate(topic, debaters, transcript)
    engine.print_verdict(verdict)

    # ── Save transcript ───────────────────────────────────────────────
    if save:
        from transcript import save_transcript
        path = save_transcript(topic, format_name, debaters, transcript, verdict)
        print(f"\n💾 Full transcript saved → {path}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_header(topic: str, fmt: str, debaters: list, rounds: int) -> None:
    width = 65
    print(f"\n{'═' * width}")
    print(f"  ⚖️  DEBATE ARENA")
    print(f"{'═' * width}")
    print(f"  Topic  : {topic}")
    print(f"  Format : {fmt.upper()}")
    print(f"  Rounds : {rounds}")
    print(f"{'─' * width}")
    for d in debaters:
        emoji = "🟢" if d.position == "FOR" else ("🔴" if d.position == "AGAINST" else "🔵")
        print(f"  {emoji} {d.position:8s} │ {d.name}  ({d.expertise})")
    print(f"{'═' * width}\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Debate Arena — configurable multi-agent debate system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent.py --topic "AI is more creative than humans"
  python agent.py --topic "Remote work is better" --rounds 3 --format lincoln
  python agent.py --topic "Open source wins" --personas sample_personas.yaml
  python agent.py --topic "Coffee vs Tea" --interactive --no-save
        """,
    )
    parser.add_argument(
        "--topic", "-t",
        default="Artificial intelligence will ultimately benefit humanity more than it harms it",
        help="The debate proposition (default: AI benefits humanity)",
    )
    parser.add_argument(
        "--rounds", "-r",
        type=int, default=2,
        help="Number of debate rounds, 1–5 (default: 2)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["oxford", "lincoln", "socratic"],
        default="oxford",
        help="Debate format: oxford (2-side) | lincoln (rebuttal-focused) | socratic (Q&A) (default: oxford)",
    )
    parser.add_argument(
        "--personas",
        default=None,
        help="YAML file with custom debater personas (default: built-in personas)",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Let you inject a counter-argument or question each round",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not save the debate transcript to disk",
    )
    args = parser.parse_args()

    rounds = max(1, min(5, args.rounds))

    run_debate(
        topic=args.topic,
        rounds=rounds,
        format_name=args.format,
        personas_file=args.personas,
        interactive=args.interactive,
        save=not args.no_save,
    )


if __name__ == "__main__":
    main()
