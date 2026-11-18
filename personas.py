"""
personas.py — Debater persona builder and manager for Debate Arena.

Supports:
- Built-in default personas for each debate format
- Loading custom personas from a YAML file
- Validation of required persona fields
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


# ---------------------------------------------------------------------------
# Debater data class
# ---------------------------------------------------------------------------

@dataclass
class Debater:
    """Represents a single AI debater agent."""
    name:      str
    position:  str          # "FOR" | "AGAINST" | "NEUTRAL" (Socratic moderator)
    expertise: str
    style:     str = "analytical and evidence-based"
    model:     str = "gpt-4o-mini"
    temperature: float = 0.65
    arguments: list[str] = field(default_factory=list)

    def __post_init__(self):
        self._llm = ChatOpenAI(model=self.model, temperature=self.temperature)

    def make_argument(
        self,
        topic: str,
        round_num: int,
        opponent_last: str = "",
        user_injection: str = "",
        format_hint: str = "",
    ) -> str:
        """
        Generates one round of debate argument.

        Args:
            topic:          The debate proposition.
            round_num:      Current round number.
            opponent_last:  Opponent's previous argument to rebut.
            user_injection: Optional counter-argument/question from the human user.
            format_hint:    Extra instruction based on debate format.
        """
        system_content = (
            f"You are {self.name}, a {self.expertise}. "
            f"Your debate style is {self.style}. "
            f"You are arguing {self.position} on this topic. "
            f"Be concise (under 160 words), persuasive, and use specific evidence or examples. "
            f"Round {round_num}."
        )
        if format_hint:
            system_content += f" {format_hint}"

        if opponent_last and user_injection:
            user_content = (
                f"Topic: {topic}\n\n"
                f"Your opponent just argued: '{opponent_last}'\n\n"
                f"The audience also raised this point: '{user_injection}'\n\n"
                f"Address both and reinforce your position:"
            )
        elif opponent_last:
            user_content = (
                f"Topic: {topic}\n\n"
                f"Your opponent argued: '{opponent_last}'\n\n"
                f"Rebut and strengthen your {self.position} position:"
            )
        else:
            user_content = (
                f"Topic: {topic}\n\n"
                f"Make your opening argument {self.position} this proposition:"
            )

        response = self._llm.invoke([
            SystemMessage(content=system_content),
            HumanMessage(content=user_content),
        ])
        argument = response.content.strip()
        self.arguments.append(argument)
        return argument

    def ask_question(self, topic: str, opponent_statement: str) -> str:
        """Generates a Socratic probing question (used in socratic format)."""
        response = self._llm.invoke([
            SystemMessage(content=(
                f"You are {self.name}, a {self.expertise} acting as a Socratic moderator. "
                f"Ask ONE incisive probing question that challenges or explores the argument. "
                f"Keep it under 50 words."
            )),
            HumanMessage(content=(
                f"Topic: {topic}\n\nStatement: '{opponent_statement}'\n\nAsk your probing question:"
            )),
        ])
        return response.content.strip()


# ---------------------------------------------------------------------------
# Persona manager
# ---------------------------------------------------------------------------

# Built-in default personas per format
_DEFAULTS: dict[str, list[dict]] = {
    "oxford": [
        {
            "name":      "Dr. Maya Patel",
            "position":  "FOR",
            "expertise": "AI safety researcher and cognitive scientist",
            "style":     "data-driven and optimistic, citing peer-reviewed studies",
        },
        {
            "name":      "Prof. James Okafor",
            "position":  "AGAINST",
            "expertise": "social philosopher and technology ethicist",
            "style":     "humanist, citing historical precedents and societal impact",
        },
    ],
    "lincoln": [
        {
            "name":      "Senator Leila Nkosi",
            "position":  "FOR",
            "expertise": "policy strategist and former tech industry advisor",
            "style":     "authoritative, policy-focused, using real-world case studies",
        },
        {
            "name":      "Dr. Yuki Tanaka",
            "position":  "AGAINST",
            "expertise": "labor economist and inequality researcher",
            "style":     "empirical, citing economic data and statistical models",
        },
    ],
    "socratic": [
        {
            "name":      "Alexis Vance",
            "position":  "FOR",
            "expertise": "futurist and technology venture capitalist",
            "style":     "visionary and bold, referencing innovation cycles",
        },
        {
            "name":      "Dr. Priya Sharma",
            "position":  "AGAINST",
            "expertise": "environmental scientist and systems thinker",
            "style":     "measured and interdisciplinary, emphasizing second-order effects",
        },
        {
            "name":      "Moderator Kai",
            "position":  "NEUTRAL",
            "expertise": "Socratic philosopher and debate facilitator",
            "style":     "questioning, neutral, probing assumptions",
            "model":     "gpt-4o",
            "temperature": 0.3,
        },
    ],
}


class PersonaManager:
    """Loads debater personas from YAML or returns built-in defaults."""

    def __init__(self, yaml_path: Optional[str] = None):
        self.yaml_path = yaml_path
        self._custom:  Optional[dict] = None

        if yaml_path and Path(yaml_path).exists():
            import yaml
            with open(yaml_path, encoding="utf-8") as f:
                self._custom = yaml.safe_load(f)

    def get_debaters(self, format_name: str) -> list[Debater]:
        """Returns a list of Debater instances for the given format."""
        if self._custom:
            raw = self._custom.get(format_name) or self._custom.get("debaters") or []
        else:
            raw = _DEFAULTS.get(format_name, _DEFAULTS["oxford"])

        debaters = []
        for d in raw:
            debaters.append(Debater(
                name=        d.get("name",        "Unknown"),
                position=    d.get("position",    "FOR"),
                expertise=   d.get("expertise",   "general expert"),
                style=       d.get("style",       "analytical"),
                model=       d.get("model",       "gpt-4o-mini"),
                temperature= float(d.get("temperature", 0.65)),
            ))
        return debaters
