# Harness Architecture

> An AI-native system that acts as an extension of human intelligence.

The Harness is a Human-in-the-Loop AI framework designed to augment decision-making while maintaining accountability, transparency, and control. It's built on the Microsoft Amplifier pattern, treating AI as an extension of the Fulcrum (the human principal) rather than a replacement.

## Core Concepts

### The Fulcrum
The human principal whose intelligence the Harness extends. All decisions flow through the Fulcrum, and the Harness operates within defined boundaries.

### The Harness
The AI agent system that:
- Loads and internalizes context (identity, directives, knowledge)
- Executes tasks using LLM assistance
- Validates outputs against ethical constraints
- Logs all actions for review (Shadow Mode)

### Shadow Mode
A learning loop where all AI outputs are logged but NOT executed. This allows:
- Trust calibration over time
- Human review of AI reasoning
- Pattern identification for improvement
- Safe experimentation

## Architecture

```
harness-architecture/
├── context/                 # The "Bit" - Defines WHO the Harness represents
│   ├── identity.md          # Voice, style, biographical context
│   ├── prime_directive.md   # Non-negotiable rules, ethical constraints
│   └── knowledge_base.md    # Domain expertise, business facts
│
├── core/                    # The Brain - Python logic
│   ├── __init__.py          # Module exports
│   └── harness.py           # Main Harness class
│
├── logs/                    # Memory - Shadow Mode storage
│   └── shadow_*.json        # Logged outputs for review
│
├── templates/               # Schemas - Structured data formats
│   └── case_context.json    # Legal case JSON schema
│
├── .cursorrules             # Cursor AI configuration
├── .env.example             # Environment variable template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd harness-architecture

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
# Choose either OpenAI or Anthropic
```

### 3. Customize Context

Edit the files in `/context` to reflect your identity:

- **identity.md**: Your voice, style, and professional bio
- **prime_directive.md**: Your non-negotiable rules and ethical boundaries
- **knowledge_base.md**: Key facts about your business and domain

### 4. Run the Harness

```python
from core import Harness

# Initialize the Harness (loads context automatically)
harness = Harness(mode="shadow")

# Run a task
result = harness.run_task(
    task="Draft a response to the client inquiry about case status",
    context={"case_id": "CASE-2024-001234", "status": "discovery"}
)

# Review the output
print(result["output"])
print(result["validation"])
```

### CLI Mode

```bash
# Run interactive CLI
python -m core.harness
```

## Usage Examples

### Basic Task Execution

```python
from core import Harness

harness = Harness()

result = harness.run_task(
    task="Summarize the key issues in this matter",
    context={
        "case_type": "civil_litigation",
        "description": "Contract dispute regarding software deliverables"
    }
)
```

### Reviewing Shadow Logs

```python
# Get recent shadow mode logs
logs = harness.get_shadow_logs(limit=5)

for log in logs:
    print(f"Task: {log['task']}")
    print(f"Status: {log['review_status']}")
    print("---")
```

### Approving a Shadow Log

```python
# After human review, approve a log entry
harness.approve_shadow_log(
    log_id="shadow_20240115_143022",
    reviewed_by="Josh Nelson",
    notes="Output is accurate and appropriate for client communication"
)
```

## Prime Directive Highlights

The Harness operates under strict constraints defined in `context/prime_directive.md`:

| Rule | Description |
|------|-------------|
| Human-in-the-Loop | Every external-facing output requires human approval |
| No Fabrication | Never invent facts, citations, or case law |
| Transparency | Always cite sources and explain reasoning |
| Confidentiality | Client data is privileged and protected |
| Shadow Default | Log first, execute only after approval |

## Validation

The Harness validates all outputs before returning them:

- **Fabrication Check**: Scans for uncertain language that might indicate made-up content
- **Action Check**: Blocks language suggesting unauthorized actions were taken
- **Uncertainty Check**: Ensures appropriate hedging in complex outputs
- **Emergency Stop**: Recognizes `HALT_HARNESS` keyword to stop all operations

## Integration with Cursor

The `.cursorrules` file configures Cursor AI to:

1. Read `context/prime_directive.md` before generating code
2. Follow the Harness's ethical constraints
3. Maintain proper file organization
4. Include human approval gates in generated code

This makes Cursor itself part of the Harness system.

## Legal Case Management

This system is designed to eventually power an AI-native legal case management backend. The `templates/case_context.json` schema defines the structure for legal cases, including:

- Case identification and status
- Client information (confidential)
- Matter details and jurisdiction
- Timeline and deadlines
- Document tracking
- Task management
- Billing information
- Harness-specific configuration per case

## Security Considerations

- API keys are stored in `.env` (never committed)
- Client-identifiable information should never be logged to external services
- All logs are local and gitignored
- Shadow Mode provides audit trail for compliance

## Development

### Running Tests

```bash
pytest tests/ -v --cov=core
```

### Type Checking

```bash
mypy core/
```

### Linting

```bash
ruff check core/
```

## Roadmap

- [ ] Production mode with approval workflows
- [ ] Integration with document management systems
- [ ] Multi-case context switching
- [ ] Confidence scoring and auto-approval thresholds
- [ ] API endpoints for external integration
- [ ] Dashboard for Shadow Mode review

## License

[Your License Here]

---

*Built with the Harness Architecture - AI as an extension of human intelligence.*
