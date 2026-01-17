# Mirror Harness

> The Founder's Shadow - Observes, learns, and reflects your operational DNA.

The Mirror Harness is an observer system that watches how you work, captures your decision patterns, and reflects them back to you. It's designed to help you understand and codify your own leadership style.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     YOUR WORK SESSION                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│  │ Decide  │ →  │ Reject  │ →  │ Rewrite │                  │
│  └────┬────┘    └────┬────┘    └────┬────┘                  │
│       │              │              │                        │
│       ▼              ▼              ▼                        │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              MIRROR HARNESS OBSERVES                │    │
│  │  • Logs decisions to session_logs/                  │    │
│  │  • Tracks patterns in patterns.md                   │    │
│  │  • Proposes axioms for axioms.md                    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   reflect   │  ← Run at end of day
                    │     .py     │
                    └──────┬──────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   DISCOVERY     │
                  │    REPORT       │
                  │                 │
                  │ "You prioritized│
                  │  X over Y..."   │
                  └─────────────────┘
```

## Directory Structure

```
.founder_harness/
├── context/
│   ├── axioms.md       # The Law - confirmed principles
│   └── patterns.md     # Observed behaviors (candidates for axioms)
│
├── session_logs/       # Raw session data
│   └── session_*.json  # Daily logs
│
├── tools/
│   └── reflect.py      # Discovery Report generator
│
└── README.md

.cursor/rules/
└── founder-mirror.mdc  # The active Cursor rule
```

## Quick Start

### 1. The Rule is Already Active

Once you have `.cursor/rules/founder-mirror.mdc`, Cursor will automatically:
- Ask clarifying questions when uncertain
- Request feedback when you reject suggestions
- Propose logging strategic decisions

### 2. Log Decisions Throughout the Day

```bash
# Interactive logging
python .founder_harness/tools/reflect.py --log

# Quick decision log
python .founder_harness/tools/reflect.py --log-decision "Chose Postgres over MongoDB" --context "Need simplicity over flexibility"

# Propose an axiom
python .founder_harness/tools/reflect.py --propose "Never delay launch for cosmetic bugs"
```

### 3. Generate Your Discovery Report

```bash
# At end of day
python .founder_harness/tools/reflect.py

# Analyze last week
python .founder_harness/tools/reflect.py --days 7
```

## The Active Learning Loop

The `.cursor/rules/founder-mirror.mdc` file instructs Cursor to:

### When You Reject a Suggestion
> "I noticed you rejected that. What principle did I violate? I want to learn."

### When You Rewrite Output
Cursor silently observes tone and structural changes. After 3+ similar rewrites:
> "I've noticed you consistently [pattern]. Should I add this to your axioms?"

### When You Make Strategic Decisions
Watches for signals like "ignore that error", "prioritize speed", "keep it simple":
> "That sounds like a principle: '[inferred axiom]'. Should I log it?"

## The Files

### axioms.md - The Law

These are your confirmed, non-negotiable principles. The Cursor rule enforces these on every suggestion.

**Starter axiom:**
> Rule #1: If I haven't defined it, ask me. Do not guess.

### patterns.md - Observed Behaviors

This file tracks recurring patterns that aren't yet axioms. Review weekly and promote consistent patterns.

Categories tracked:
- Decision patterns
- Code style preferences
- Communication tone
- Rejection patterns
- Priority trade-offs
- Tool preferences

### session_logs/ - Raw Data

JSON logs of each session containing:
- Decisions made
- Suggestions rejected
- Observations noted
- Axioms proposed

## The Reflection Script

`reflect.py` analyzes your session data and git history to generate insights.

### Discovery Report Contents

1. **Today's Focus**: What themes emerged from your work
2. **Decision Patterns**: Trade-offs you made (X over Y)
3. **Observed Preferences**: Consistent behaviors
4. **Proposed New Axioms**: Concrete rules derived from patterns
5. **Questions for Reflection**: Prompts for deeper thinking

### Example Output

```
📊 Discovery Report

## Today's Focus
You spent most of your time on the authentication system, with a clear
emphasis on simplicity over feature completeness.

## Decision Patterns
- Prioritized shipping speed over comprehensive test coverage
- Chose synchronous processing when async would add complexity
- Rejected suggestions that added dependencies

## Observed Preferences
- Consistently used f-strings over .format()
- Preferred explicit error messages over generic ones
- Avoided class inheritance in favor of composition

## Proposed New Axioms
1. "Always prefer synchronous code unless async provides >10x performance gain"
2. "Error messages must include the specific value that caused the failure"

## Questions for Reflection
- You rejected 3 testing suggestions. Is speed more important than coverage right now?
- You're avoiding new dependencies. Is this a principle or a preference?
```

## Promoting Axioms

When patterns become consistent enough, promote them to axioms:

1. Run `reflect.py` to see proposed axioms
2. When prompted, select which to promote
3. They're automatically added to `axioms.md`
4. Cursor now enforces them on all future suggestions

## Best Practices

### Daily Ritual
1. Start the day by checking `current_state.md` (in the regular founder_harness)
2. Work normally - the Mirror observes passively
3. Log significant decisions when they happen
4. End the day with `python reflect.py`
5. Review and promote strong patterns

### Weekly Review
1. Run `python reflect.py --days 7`
2. Review `patterns.md` for emerging themes
3. Promote consistent patterns to axioms
4. Clean up patterns that didn't hold

### The Meta-Goal
Over time, your `axioms.md` becomes a complete operating manual for your company. New hires can read it. AI tools enforce it. Your leadership scales beyond your personal bandwidth.

---

*Part of the Harness Architecture - AI as an extension of human intelligence.*
