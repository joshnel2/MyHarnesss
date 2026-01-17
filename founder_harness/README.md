# Founder's Harness

> Your personal amplifier. Transform rough thoughts into polished, on-brand outputs.

The Founder's Harness is a CLI tool that acts as an extension of your leadership. It ingests your intent, applies your DNA (values, voice, axioms), and produces high-fidelity outputs that sound exactly like you.

## The Philosophy

You stop "doing" work and start "directing" it.

Instead of writing emails, memos, and specs yourself, you give rough commands and the Harness produces polished outputs that match your voice perfectly. When you edit its outputs, it learns your preferences automatically.

## Quick Start

```bash
# From the repository root
cd founder_harness/tools

# Amplify a thought
python amplify.py "Tell the team we're pivoting Shadow Mode to focus on diff-checking"

# Specify output type
python amplify.py --type email "Follow up with the investor about our demo"
python amplify.py --type memo "Explain why we're delaying the launch by one week"
python amplify.py --type investor "Q3 update with our latest metrics"
python amplify.py --type spec "Shadow Mode diff-checking feature requirements"
```

## Output Types

| Type | Use Case |
|------|----------|
| `general` | Default - the system figures out the best format |
| `email` | External or internal emails |
| `memo` | Team communications and announcements |
| `investor` | Investor updates and board communications |
| `spec` | Technical specifications and requirements |
| `slack` | Quick Slack messages |
| `tweet` | Twitter/X posts or threads |
| `decision` | Decision documentation |

## The Learning Loop

The killer feature: the Harness learns from your edits.

### Automatic Learning

Every time you edit an output, you can teach the Harness:

```bash
# After editing a draft, run:
python amplify.py --learn original_draft.txt my_edited_version.txt

# Or use interactive mode:
python amplify.py --interactive-learn
```

The system will:
1. Compare your edit to the original
2. Extract the pattern or preference
3. Append it to `axioms.md` automatically

### Example Learning

**Original draft**: "I hope this update finds you well. We've made progress on..."

**Your edit**: "Quick update: we shipped Shadow Mode and closed two new customers."

**Extracted learning**: "Never open with pleasantries. Lead with the news."

This learning is now permanently encoded in your axioms.

## Directory Structure

```
founder_harness/
├── context/               # Your "DNA"
│   ├── identity.md        # Your voice, style, communication patterns
│   ├── axioms.md          # Non-negotiable business principles
│   └── current_state.md   # Live company context (update weekly)
│
├── tools/
│   └── amplify.py         # The main CLI tool
│
└── logs/                  # Shadow Learning storage
    └── *.json             # Draft history and learning logs
```

## Setup

### 1. Configure Your Context

The most important step. Fill out these files with YOUR specific information:

**`context/identity.md`**
- Your communication style
- Words you use / don't use
- How you write to different audiences

**`context/axioms.md`**
- Your non-negotiable principles
- Decision-making frameworks
- Operational rules (e.g., "No meetings on Tuesdays")

**`context/current_state.md`**
- Current sprint focus
- This week's priorities
- Key metrics
- Team status

### 2. Set Your API Key

```bash
# In the repo root, copy and edit .env
cp .env.example .env
# Add OPENAI_API_KEY or ANTHROPIC_API_KEY
```

### 3. Start Amplifying

```bash
python founder_harness/tools/amplify.py "Your rough thought here"
```

## The Daily Workflow

### Morning Routine

1. Update `current_state.md` with today's priorities
2. Open terminal instead of email
3. Amplify your communications

### Example Session

```bash
# Morning standup message
$ python amplify.py --type slack "Team update: focus on Shadow Mode, I'm heads down on investor deck"

# Investor follow-up
$ python amplify.py --type email "Thanks for the meeting yesterday, sending deck with updated metrics"

# Technical decision
$ python amplify.py --type decision "We're using PostgreSQL over MongoDB because simplicity matters more than flexibility for our use case"

# Team memo
$ python amplify.py --type memo "We're cutting feature X from the roadmap. Here's why."
```

## Advanced Usage

### View Recent Drafts

```bash
python amplify.py --drafts
```

### Don't Save Draft (for sensitive content)

```bash
python amplify.py --no-save "Confidential thought here"
```

### Interactive Learning Mode

```bash
python amplify.py --interactive-learn
# Paste original draft
# Paste your edited version
# System extracts and records the learning
```

## Best Practices for Axioms

### Bad Axioms

```
- We like good code
- Be nice to customers
- Move fast
```

### Good Axioms

```
- If a feature takes >4 hours, cut the scope and ship
- Never use "hope this finds you well" in emails—lead with the point
- All technical decisions must be documented within 24 hours
- Customer response time: same day for bugs, next morning for features
- No meetings on Tuesdays (Focus Day)
```

The more specific your axioms, the better the outputs.

## The Meta-Goal

This harness isn't just for you. Eventually:

1. **Train it well** - Spend a month editing outputs and running `--learn`
2. **Share with team** - Give read access to your axioms
3. **"Consult Founder Bot"** - Team members can ask "What would the founder do?"

You're building the digital version of your leadership.

---

*Part of the Harness Architecture - AI as an extension of human intelligence.*
