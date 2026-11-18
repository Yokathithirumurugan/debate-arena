"""
verdict.py — Structured verdict engine for Debate Arena.

Uses GPT-4o to produce a rich, structured evaluation of the debate:
- Per-side scores (Argumentation, Evidence, Rebuttal, Delivery)
- Winner declaration with reasoning
- Strongest argument per side
- Logical fallacy detection
- Rhetorical technique analysis
- Balanced synthesis conclusion
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

if TYPE_CHECKING:
    from personas import Debater


# ---------------------------------------------------------------------------
# Verdict schema (returned as structured dict)
# ---------------------------------------------------------------------------

VERDICT_SCHEMA = """{
  "winner": "FOR | AGAINST | TIE",
  "winner_name": "debater name",
  "scores": {
    "FOR":     {"argumentation": 1-10, "evidence": 1-10, "rebuttal": 1-10, "delivery": 1-10, "total": 1-40},
    "AGAINST": {"argumentation": 1-10, "evidence": 1-10, "rebuttal": 1-10, "delivery": 1-10, "total": 1-40}
  },
  "strongest_argument_FOR":     "one sentence",
  "strongest_argument_AGAINST": "one sentence",
  "fallacies_detected": [
    {"side": "FOR|AGAINST", "fallacy": "name", "example": "brief quote or paraphrase"}
  ],
  "rhetorical_techniques": {
    "FOR":     ["list of techniques used"],
    "AGAINST": ["list of techniques used"]
  },
  "key_insights": ["3-4 bullet-point insights about the debate"],
  "synthesis": "2-3 sentence balanced conclusion that integrates both perspectives",
  "judge_notes": "2-3 sentences on overall debate quality and what could have been argued better"
}"""

VERDICT_SYSTEM_PROMPT = f"""You are a world-class debate judge with expertise in formal argumentation, rhetoric, and logic.
Evaluate the debate transcript below and return ONLY valid JSON matching this schema exactly:

{VERDICT_SCHEMA}

Be impartial. Base scores on argument quality, not position merit. Return ONLY the JSON object, no markdown."""


# ---------------------------------------------------------------------------
# Verdict engine
# ---------------------------------------------------------------------------

class VerdictEngine:
    """Evaluates a completed debate and returns a structured verdict."""

    def __init__(self):
        self._llm = ChatOpenAI(model="gpt-4o", temperature=0)

    def evaluate(
        self,
        topic: str,
        debaters: list["Debater"],
        transcript: list[dict],
    ) -> dict:
        """
        Runs the judge evaluation and returns a parsed verdict dict.

        Args:
            topic:      Debate proposition.
            debaters:   List of Debater instances.
            transcript: Full debate transcript.

        Returns:
            Structured verdict dict.
        """
        # Format transcript for the judge
        transcript_text = self._format_transcript(transcript)
        debater_info    = "\n".join(
            f"- {d.name} ({d.position}): {d.expertise}"
            for d in debaters if d.position != "NEUTRAL"
        )

        messages = [
            SystemMessage(content=VERDICT_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Topic: \"{topic}\"\n\n"
                f"Debaters:\n{debater_info}\n\n"
                f"Full Transcript:\n{transcript_text}\n\n"
                f"Provide your verdict as JSON:"
            )),
        ]

        response = self._llm.invoke(messages)
        return self._parse_json(response.content)

    # ------------------------------------------------------------------
    # Printing
    # ------------------------------------------------------------------

    @staticmethod
    def print_verdict(verdict: dict) -> None:
        """Pretty-prints the structured verdict."""
        winner = verdict.get("winner", "TIE")
        winner_name = verdict.get("winner_name", "")

        # Winner banner
        if winner == "TIE":
            print("🤝 RESULT: TIE — Both sides argued equally well\n")
        elif winner == "FOR":
            print(f"🏆 WINNER: {winner_name} (FOR)\n")
        else:
            print(f"🏆 WINNER: {winner_name} (AGAINST)\n")

        # Scores table
        scores = verdict.get("scores", {})
        print("📊 SCOREBOARD")
        print(f"{'─'*55}")
        print(f"{'Category':<18} {'FOR':>8} {'AGAINST':>10}")
        print(f"{'─'*55}")
        categories = ["argumentation", "evidence", "rebuttal", "delivery"]
        for cat in categories:
            for_score  = scores.get("FOR",     {}).get(cat, "—")
            con_score  = scores.get("AGAINST", {}).get(cat, "—")
            print(f"  {cat.capitalize():<16} {str(for_score):>8} {str(con_score):>10}")
        print(f"{'─'*55}")
        for_total = scores.get("FOR",     {}).get("total", "—")
        con_total = scores.get("AGAINST", {}).get("total", "—")
        print(f"  {'TOTAL':<16} {str(for_total):>8} {str(con_total):>10}")
        print()

        # Strongest arguments
        print("💪 STRONGEST ARGUMENTS")
        print(f"  🟢 FOR:     {verdict.get('strongest_argument_FOR', 'N/A')}")
        print(f"  🔴 AGAINST: {verdict.get('strongest_argument_AGAINST', 'N/A')}")
        print()

        # Rhetorical techniques
        rhet = verdict.get("rhetorical_techniques", {})
        if rhet:
            print("🎭 RHETORICAL TECHNIQUES DETECTED")
            for side, techniques in rhet.items():
                emoji = "🟢" if side == "FOR" else "🔴"
                print(f"  {emoji} {side}: {', '.join(techniques)}")
            print()

        # Fallacies
        fallacies = verdict.get("fallacies_detected", [])
        if fallacies:
            print("⚠️  LOGICAL FALLACIES DETECTED")
            for f in fallacies:
                emoji = "🟢" if f.get("side") == "FOR" else "🔴"
                print(f"  {emoji} {f.get('side')} — {f.get('fallacy', 'Unknown')}: \"{f.get('example', '')}\"")
            print()

        # Key insights
        insights = verdict.get("key_insights", [])
        if insights:
            print("💡 KEY INSIGHTS")
            for ins in insights:
                print(f"  • {ins}")
            print()

        # Synthesis
        synthesis = verdict.get("synthesis", "")
        if synthesis:
            print("🔭 SYNTHESIS CONCLUSION")
            print(f"  {synthesis}")
            print()

        # Judge notes
        notes = verdict.get("judge_notes", "")
        if notes:
            print("📝 JUDGE'S NOTES")
            print(f"  {notes}")
            print()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _format_transcript(transcript: list[dict]) -> str:
        lines = []
        for turn in transcript:
            phase = f"[{turn['phase']}] " if "phase" in turn else ""
            lines.append(
                f"[Round {turn.get('round', '?')}] {phase}{turn['speaker']} ({turn['position']}):\n"
                f"{turn['content']}\n"
            )
        return "\n".join(lines)

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Extracts and parses JSON from the LLM response."""
        cleaned = text.strip()
        # Strip markdown code fences if present
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        # Find outermost JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: return raw text wrapped in a dict
            return {"raw_verdict": text, "parse_error": True}
