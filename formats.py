"""
formats.py — Debate format strategies for Debate Arena.

Implements three distinct debate formats, each producing a structured
transcript list of {"speaker", "position", "round", "content"} dicts.

Formats:
  oxford   — Classic 2-side back-and-forth (FOR vs AGAINST)
  lincoln  — Rebuttal-heavy format with explicit rebuttal phase
  socratic — Q&A driven by a neutral Socratic moderator
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from personas import Debater


# ---------------------------------------------------------------------------
# Abstract base format
# ---------------------------------------------------------------------------

class DebateFormat(ABC):
    """Abstract base class for all debate formats."""

    def __init__(self, debaters: list["Debater"], rounds: int):
        self.debaters = debaters
        self.rounds   = rounds

    @abstractmethod
    def run(self, topic: str, interactive: bool = False) -> list[dict]:
        """
        Executes the debate and returns a transcript.

        Returns:
            List of turn dicts: {"speaker", "position", "round", "content"}
        """
        ...

    # Shared helper: print a debater's turn
    @staticmethod
    def _print_turn(debater: "Debater", argument: str, round_num: int) -> None:
        emoji = "🟢" if debater.position == "FOR" else ("🔴" if debater.position == "AGAINST" else "🔵")
        print(f"\n{emoji} {debater.name} [{debater.position}]:")
        print(f"{'─' * 55}")
        print(argument)
        print()

    # Shared helper: get optional user injection
    @staticmethod
    def _get_user_injection() -> str:
        try:
            line = input("  🎤 Your counter-argument or question (Enter to skip): ").strip()
            return line
        except (KeyboardInterrupt, EOFError):
            return ""


# ---------------------------------------------------------------------------
# Oxford format: classic 2-side debate
# ---------------------------------------------------------------------------

class OxfordFormat(DebateFormat):
    """
    Oxford-style: FOR and AGAINST debaters alternate arguments.
    Each round: FOR argues → AGAINST rebuts → next round.
    """

    def run(self, topic: str, interactive: bool = False) -> list[dict]:
        transcript = []
        pro  = next((d for d in self.debaters if d.position == "FOR"), self.debaters[0])
        con  = next((d for d in self.debaters if d.position == "AGAINST"), self.debaters[-1])

        last_pro = ""
        last_con = ""

        for rnd in range(1, self.rounds + 1):
            print(f"\n{'─'*65}")
            print(f"  🕐 Round {rnd} of {self.rounds}")
            print(f"{'─'*65}")

            # User injection (for con's rebuttal)
            user_inject = ""
            if interactive and rnd > 1:
                user_inject = self._get_user_injection()
                if user_inject:
                    print(f"  📢 Audience: {user_inject}\n")

            # PRO turn
            pro_arg = pro.make_argument(
                topic, rnd, opponent_last=last_con,
                user_injection=user_inject,
                format_hint="Oxford format: make a structured argument with a clear claim and evidence."
            )
            self._print_turn(pro, pro_arg, rnd)
            transcript.append({"speaker": pro.name, "position": "FOR",     "round": rnd, "content": pro_arg})

            # CON turn
            con_arg = con.make_argument(
                topic, rnd, opponent_last=pro_arg,
                format_hint="Oxford format: directly rebut the previous argument, then advance your own claim."
            )
            self._print_turn(con, con_arg, rnd)
            transcript.append({"speaker": con.name, "position": "AGAINST", "round": rnd, "content": con_arg})

            last_pro = pro_arg
            last_con = con_arg

        return transcript


# ---------------------------------------------------------------------------
# Lincoln-Douglas format: rebuttal-focused
# ---------------------------------------------------------------------------

class LincolnFormat(DebateFormat):
    """
    Lincoln-Douglas style: opening statements → cross-examination rebuttal phase
    → closing statements. Each round is a cross-examination exchange.
    """

    def run(self, topic: str, interactive: bool = False) -> list[dict]:
        transcript = []
        pro = next((d for d in self.debaters if d.position == "FOR"), self.debaters[0])
        con = next((d for d in self.debaters if d.position == "AGAINST"), self.debaters[-1])

        # ── Opening statements ────────────────────────────────────────
        print(f"\n{'─'*65}")
        print("  📜 OPENING STATEMENTS")
        print(f"{'─'*65}")

        pro_open = pro.make_argument(
            topic, 1,
            format_hint="Lincoln-Douglas: deliver a value-based opening statement. State your core value and criterion clearly."
        )
        self._print_turn(pro, pro_open, 1)
        transcript.append({"speaker": pro.name,  "position": "FOR",     "round": 0, "content": pro_open, "phase": "opening"})

        con_open = con.make_argument(
            topic, 1, opponent_last=pro_open,
            format_hint="Lincoln-Douglas: challenge the opponent's value framework and present your own criterion."
        )
        self._print_turn(con, con_open, 1)
        transcript.append({"speaker": con.name, "position": "AGAINST", "round": 0, "content": con_open, "phase": "opening"})

        # ── Cross-examination rounds ───────────────────────────────────
        last_pro = pro_open
        last_con = con_open

        for rnd in range(1, self.rounds + 1):
            print(f"\n{'─'*65}")
            print(f"  ⚔️  Cross-Examination Round {rnd} of {self.rounds}")
            print(f"{'─'*65}")

            user_inject = ""
            if interactive:
                user_inject = self._get_user_injection()
                if user_inject:
                    print(f"  📢 Audience raises: {user_inject}\n")

            # Pro rebuttal
            pro_arg = pro.make_argument(
                topic, rnd, opponent_last=last_con,
                user_injection=user_inject,
                format_hint="Lincoln-Douglas cross-exam: attack your opponent's criterion and defend your own value."
            )
            self._print_turn(pro, pro_arg, rnd)
            transcript.append({"speaker": pro.name, "position": "FOR",     "round": rnd, "content": pro_arg, "phase": "rebuttal"})

            # Con rebuttal
            con_arg = con.make_argument(
                topic, rnd, opponent_last=pro_arg,
                format_hint="Lincoln-Douglas cross-exam: expose logical flaws and reinforce your value framework."
            )
            self._print_turn(con, con_arg, rnd)
            transcript.append({"speaker": con.name, "position": "AGAINST", "round": rnd, "content": con_arg, "phase": "rebuttal"})

            last_pro = pro_arg
            last_con = con_arg

        # ── Closing statements ────────────────────────────────────────
        print(f"\n{'─'*65}")
        print("  🎯 CLOSING STATEMENTS")
        print(f"{'─'*65}")

        pro_close = pro.make_argument(
            topic, self.rounds + 1, opponent_last=last_con,
            format_hint="Lincoln-Douglas closing: summarize why your value framework should prevail. Keep it powerful and concise."
        )
        self._print_turn(pro, pro_close, self.rounds + 1)
        transcript.append({"speaker": pro.name, "position": "FOR",     "round": 99, "content": pro_close, "phase": "closing"})

        con_close = con.make_argument(
            topic, self.rounds + 1, opponent_last=pro_close,
            format_hint="Lincoln-Douglas closing: deliver a compelling final argument. Leave the judge with a clear choice."
        )
        self._print_turn(con, con_close, self.rounds + 1)
        transcript.append({"speaker": con.name, "position": "AGAINST", "round": 99, "content": con_close, "phase": "closing"})

        return transcript


# ---------------------------------------------------------------------------
# Socratic format: moderator-driven Q&A
# ---------------------------------------------------------------------------

class SocraticFormat(DebateFormat):
    """
    Socratic format: a neutral moderator poses probing questions to each
    debater, challenging their assumptions. Debaters respond and are then
    questioned by the moderator again.
    """

    def run(self, topic: str, interactive: bool = False) -> list[dict]:
        transcript = []
        pro  = next((d for d in self.debaters if d.position == "FOR"), self.debaters[0])
        con  = next((d for d in self.debaters if d.position == "AGAINST"), self.debaters[-1])
        mod  = next((d for d in self.debaters if d.position == "NEUTRAL"), None)

        if mod is None:
            # Fallback: use a temporary moderator-style debater
            from personas import Debater
            mod = Debater(
                name="Moderator", position="NEUTRAL",
                expertise="Socratic philosopher", style="probing and neutral",
                model="gpt-4o", temperature=0.3,
            )

        last_pro = ""
        last_con = ""

        for rnd in range(1, self.rounds + 1):
            print(f"\n{'─'*65}")
            print(f"  🔍 Socratic Round {rnd} of {self.rounds}")
            print(f"{'─'*65}")

            # PRO presents position
            pro_arg = pro.make_argument(
                topic, rnd, opponent_last=last_con,
                format_hint="Socratic format: state your position clearly — you will be questioned on it."
            )
            self._print_turn(pro, pro_arg, rnd)
            transcript.append({"speaker": pro.name, "position": "FOR",     "round": rnd, "content": pro_arg})

            # Moderator questions PRO
            mod_q_pro = mod.ask_question(topic, pro_arg)
            print(f"\n🔵 {mod.name} asks {pro.name}:")
            print(f"{'─' * 55}")
            print(mod_q_pro)
            transcript.append({"speaker": mod.name, "position": "NEUTRAL", "round": rnd, "content": f"[Question to FOR] {mod_q_pro}"})

            # PRO responds to Socratic question
            pro_resp = pro.make_argument(
                topic, rnd,
                opponent_last=mod_q_pro,
                format_hint="Socratic response: answer the moderator's probing question thoughtfully."
            )
            self._print_turn(pro, pro_resp, rnd)
            transcript.append({"speaker": pro.name, "position": "FOR", "round": rnd, "content": f"[Socratic response] {pro_resp}"})

            # CON presents position
            con_arg = con.make_argument(
                topic, rnd, opponent_last=pro_resp,
                format_hint="Socratic format: state your counter-position — you will be questioned on it."
            )
            self._print_turn(con, con_arg, rnd)
            transcript.append({"speaker": con.name, "position": "AGAINST", "round": rnd, "content": con_arg})

            # Moderator questions CON
            mod_q_con = mod.ask_question(topic, con_arg)
            print(f"\n🔵 {mod.name} asks {con.name}:")
            print(f"{'─' * 55}")
            print(mod_q_con)
            transcript.append({"speaker": mod.name, "position": "NEUTRAL", "round": rnd, "content": f"[Question to AGAINST] {mod_q_con}"})

            # CON responds to Socratic question
            con_resp = con.make_argument(
                topic, rnd,
                opponent_last=mod_q_con,
                format_hint="Socratic response: answer the moderator's probing question with precision."
            )
            self._print_turn(con, con_resp, rnd)
            transcript.append({"speaker": con.name, "position": "AGAINST", "round": rnd, "content": f"[Socratic response] {con_resp}"})

            # Optional user injection
            if interactive:
                user_q = self._get_user_injection()
                if user_q:
                    print(f"\n  📢 Audience Question: {user_q}")
                    transcript.append({"speaker": "Audience", "position": "N/A", "round": rnd, "content": user_q})

            last_pro = pro_resp
            last_con = con_resp

        return transcript


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def get_format(name: str, debaters: list, rounds: int) -> DebateFormat:
    """Returns the appropriate DebateFormat instance."""
    formats = {
        "oxford":   OxfordFormat,
        "lincoln":  LincolnFormat,
        "socratic": SocraticFormat,
    }
    cls = formats.get(name, OxfordFormat)
    return cls(debaters, rounds)
