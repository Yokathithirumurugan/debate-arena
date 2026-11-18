# ⚖️ Debate Arena

A configurable multi-agent debate system where custom AI personas argue any topic across multiple structured debate formats — with per-round scoring, fallacy detection, rhetorical analysis, and persistent transcripts.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎭 Custom Personas | Define your own debaters in a YAML file (name, expertise, style, model, temperature) |
| 📐 Multiple Formats | Oxford (classic 2-side), Lincoln-Douglas (value-based rebuttal), Socratic (Q&A with moderator) |
| 🏆 Structured Verdict | Per-side scores across 4 rubrics: Argumentation, Evidence, Rebuttal, Delivery |
| ⚠️ Fallacy Detection | AI judge identifies logical fallacies with examples from the transcript |
| 🎭 Rhetorical Analysis | Detects rhetorical techniques used by each side |
| 💾 Persistent Transcripts | Full debate saved as Markdown to `debates/` with timestamp slug |
| 🎤 Interactive Mode | Inject your own counter-argument or audience question each round |
| 🔵 Socratic Moderator | Neutral AI moderator probes debaters' assumptions with Socratic questions |

## 🛠️ Tech Stack

- **LLM**: GPT-4o (judge + Socratic moderator) + GPT-4o-mini (debaters)
- **Framework**: LangChain (direct message orchestration)
- **Config**: PyYAML, python-dotenv
- **Architecture**: Strategy pattern (swappable format classes) + Dataclass-based debaters

## 🚀 Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/debate-arena.git
cd debate-arena

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## 📖 Usage

### Quick Start — Default Oxford Debate
```bash
python agent.py --topic "AI is more creative than humans"
```

### Choose Your Format
```bash
# Oxford: classic 2-side (FOR vs AGAINST)
python agent.py --topic "Open source always beats proprietary software" --format oxford

# Lincoln-Douglas: value-based with opening/rebuttal/closing phases
python agent.py --topic "Privacy is more important than security" --format lincoln --rounds 2

# Socratic: neutral moderator probes both sides with questions
python agent.py --topic "Free will is an illusion" --format socratic --rounds 2
```

### Custom Personas via YAML
```bash
python agent.py --topic "Nuclear energy is essential for climate goals" --personas sample_personas.yaml
```

### Interactive Mode — You Inject Arguments
```bash
python agent.py --topic "Remote work is better than in-office" --interactive
# After each round, you can type a counter-argument or question
```

### Extended Debate
```bash
python agent.py --topic "Space colonization is a moral imperative" --rounds 4 --format lincoln
```

### Skip Saving Transcript
```bash
python agent.py --topic "Coffee is better than tea" --no-save
```

## 📂 Project Structure

```
debate-arena/
├── agent.py               # Main orchestrator — CLI, debate runner
├── personas.py            # Debater dataclass + PersonaManager (YAML or built-in)
├── formats.py             # Debate formats: OxfordFormat, LincolnFormat, SocraticFormat
├── verdict.py             # VerdictEngine — GPT-4o judge with structured JSON scoring
├── transcript.py          # Saves full Markdown transcripts to debates/
├── sample_personas.yaml   # Example custom persona config
├── requirements.txt
├── .env.example
└── debates/               # Auto-created; timestamped debate transcripts
```

## 🏗️ Architecture

```
CLI args
   ↓
PersonaManager    ← YAML or built-in defaults
   ↓ (list of Debater instances)
DebateFormat      ← Strategy: Oxford | Lincoln | Socratic
   ↓ (each Debater.make_argument() calls GPT-4o-mini)
Transcript list
   ↓
VerdictEngine     ← GPT-4o judge
   ↓ (structured JSON: scores, fallacies, rhetoric, synthesis)
transcript.py     ← saved Markdown file
```

## 📊 Sample Output

```
═════════════════════════════════════════════════════════════════
  ⚖️  DEBATE ARENA
═════════════════════════════════════════════════════════════════
  Topic  : AI is more creative than humans
  Format : OXFORD
  Rounds : 2
─────────────────────────────────────────────────────────────────
  🟢 FOR      │ Dr. Maya Patel  (AI safety researcher and cognitive scientist)
  🔴 AGAINST  │ Prof. James Okafor  (social philosopher and technology ethicist)
═════════════════════════════════════════════════════════════════

─────────────────────────────────────────────────────────────────
  🕐 Round 1 of 2
─────────────────────────────────────────────────────────────────

🟢 Dr. Maya Patel [FOR]:
─────────────────────────────────────────────────────────────
AI systems like DALL-E 3 and GPT-4 have demonstrated creative outputs
indistinguishable from human-generated work in blind studies...

🏛️  VERDICT & SCORING
═════════════════════════════════════════════════════════════════

🏆 WINNER: Prof. James Okafor (AGAINST)

📊 SCOREBOARD
───────────────────────────────────────────────────────
Category           FOR    AGAINST
───────────────────────────────────────────────────────
  Argumentation      7         9
  Evidence           6         8
  Rebuttal           7         8
  Delivery           8         8
───────────────────────────────────────────────────────
  TOTAL             28        33
```

## 📝 Transcript Format

Each debate is saved to `debates/YYYYMMDD_HHMMSS_topic-slug.md` with:
- Full debater profiles
- Every argument per round with phase labels
- Structured verdict: scores, fallacies, rhetorical techniques, synthesis

## 📄 License

MIT
