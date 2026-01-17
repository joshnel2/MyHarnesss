#!/usr/bin/env python3
"""
Reflect - The Founder's Daily Discovery Report Generator

This script analyzes your work session and generates insights about your
decision-making patterns, preferences, and potential new axioms.

Usage:
    python reflect.py                    # Analyze today's session
    python reflect.py --days 7           # Analyze last 7 days
    python reflect.py --log "decision"   # Log a specific decision
    python reflect.py --propose "axiom"  # Propose a new axiom
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Load environment variables
load_dotenv()

# Rich console for pretty output
console = Console()

# Path configuration
HARNESS_ROOT = Path(__file__).parent.parent
CONTEXT_PATH = HARNESS_ROOT / "context"
LOGS_PATH = HARNESS_ROOT / "session_logs"
AXIOMS_FILE = CONTEXT_PATH / "axioms.md"
PATTERNS_FILE = CONTEXT_PATH / "patterns.md"

# Ensure directories exist
LOGS_PATH.mkdir(parents=True, exist_ok=True)


class SessionLogger:
    """Handles logging of decisions, rejections, and observations."""
    
    def __init__(self):
        self.session_file = LOGS_PATH / f"session_{datetime.now().strftime('%Y%m%d')}.json"
        self.session_data = self._load_session()
    
    def _load_session(self) -> dict:
        """Load existing session or create new one."""
        if self.session_file.exists():
            try:
                return json.loads(self.session_file.read_text())
            except json.JSONDecodeError:
                pass
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "started_at": datetime.now().isoformat(),
            "decisions": [],
            "rejections": [],
            "rewrites": [],
            "observations": [],
            "proposed_axioms": []
        }
    
    def _save_session(self):
        """Save session to file."""
        self.session_data["updated_at"] = datetime.now().isoformat()
        self.session_file.write_text(
            json.dumps(self.session_data, indent=2),
            encoding="utf-8"
        )
    
    def log_decision(self, context: str, decision: str, reasoning: str = ""):
        """Log a strategic decision."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "decision",
            "context": context,
            "decision": decision,
            "reasoning": reasoning
        }
        self.session_data["decisions"].append(entry)
        self._save_session()
        console.print(f"[green]✓ Decision logged[/green]")
        return entry
    
    def log_rejection(self, suggestion: str, reason: str):
        """Log a rejected suggestion with the principle violated."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "rejection",
            "suggestion": suggestion,
            "reason": reason
        }
        self.session_data["rejections"].append(entry)
        self._save_session()
        console.print(f"[yellow]✓ Rejection logged[/yellow]")
        return entry
    
    def log_observation(self, observation: str, category: str = "general"):
        """Log a general observation about working patterns."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "observation",
            "category": category,
            "observation": observation
        }
        self.session_data["observations"].append(entry)
        self._save_session()
        console.print(f"[cyan]✓ Observation logged[/cyan]")
        return entry
    
    def propose_axiom(self, axiom: str, derived_from: str = ""):
        """Propose a new axiom for consideration."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "proposed_axiom",
            "axiom": axiom,
            "derived_from": derived_from,
            "status": "pending"
        }
        self.session_data["proposed_axioms"].append(entry)
        self._save_session()
        console.print(f"[magenta]✓ Axiom proposed[/magenta]")
        return entry


class GitAnalyzer:
    """Analyzes git history for coding patterns."""
    
    def __init__(self, days: int = 1):
        self.since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    def get_recent_commits(self) -> list[dict]:
        """Get recent commits."""
        try:
            result = subprocess.run(
                ["git", "log", f"--since={self.since_date}", "--pretty=format:%H|%s|%ai"],
                capture_output=True,
                text=True,
                cwd=HARNESS_ROOT.parent.parent  # Go to repo root
            )
            
            commits = []
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|")
                    commits.append({
                        "hash": parts[0][:8],
                        "message": parts[1],
                        "date": parts[2] if len(parts) > 2 else ""
                    })
            return commits
        except Exception as e:
            console.print(f"[dim]Git analysis unavailable: {e}[/dim]")
            return []
    
    def get_changed_files(self) -> list[str]:
        """Get files changed in the period."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"--since={self.since_date}", "HEAD~10", "HEAD"],
                capture_output=True,
                text=True,
                cwd=HARNESS_ROOT.parent.parent
            )
            return [f for f in result.stdout.strip().split("\n") if f]
        except Exception:
            return []
    
    def get_file_change_stats(self) -> dict:
        """Get statistics about file changes."""
        try:
            result = subprocess.run(
                ["git", "diff", "--stat", "HEAD~10", "HEAD"],
                capture_output=True,
                text=True,
                cwd=HARNESS_ROOT.parent.parent
            )
            return {"raw_stats": result.stdout}
        except Exception:
            return {}


class ReflectionEngine:
    """Generates Discovery Reports by analyzing session data and git history."""
    
    def __init__(self, days: int = 1):
        self.days = days
        self.git = GitAnalyzer(days)
        self.sessions = self._load_sessions()
    
    def _load_sessions(self) -> list[dict]:
        """Load session logs for the analysis period."""
        sessions = []
        cutoff = datetime.now() - timedelta(days=self.days)
        
        for log_file in sorted(LOGS_PATH.glob("session_*.json")):
            try:
                data = json.loads(log_file.read_text())
                session_date = datetime.strptime(data.get("date", "1900-01-01"), "%Y-%m-%d")
                if session_date >= cutoff:
                    sessions.append(data)
            except (json.JSONDecodeError, ValueError):
                continue
        
        return sessions
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM for analysis."""
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1500
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"[LLM unavailable: {e}]"
        
        elif anthropic_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=anthropic_key)
                response = client.messages.create(
                    model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                return f"[LLM unavailable: {e}]"
        
        return "[No API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY]"
    
    def _aggregate_session_data(self) -> dict:
        """Aggregate data from all sessions in the period."""
        aggregated = {
            "total_decisions": 0,
            "total_rejections": 0,
            "total_observations": 0,
            "proposed_axioms": [],
            "all_decisions": [],
            "all_rejections": [],
            "all_observations": []
        }
        
        for session in self.sessions:
            aggregated["total_decisions"] += len(session.get("decisions", []))
            aggregated["total_rejections"] += len(session.get("rejections", []))
            aggregated["total_observations"] += len(session.get("observations", []))
            aggregated["proposed_axioms"].extend(session.get("proposed_axioms", []))
            aggregated["all_decisions"].extend(session.get("decisions", []))
            aggregated["all_rejections"].extend(session.get("rejections", []))
            aggregated["all_observations"].extend(session.get("observations", []))
        
        return aggregated
    
    def generate_report(self) -> str:
        """Generate the Discovery Report."""
        session_data = self._aggregate_session_data()
        commits = self.git.get_recent_commits()
        changed_files = self.git.get_changed_files()
        
        # Build the analysis prompt
        prompt = f"""You are analyzing the Founder's work patterns to generate a Discovery Report.

## Session Data (Last {self.days} day(s))

### Decisions Made ({session_data['total_decisions']})
{json.dumps(session_data['all_decisions'], indent=2) if session_data['all_decisions'] else 'No decisions logged'}

### Suggestions Rejected ({session_data['total_rejections']})
{json.dumps(session_data['all_rejections'], indent=2) if session_data['all_rejections'] else 'No rejections logged'}

### Observations ({session_data['total_observations']})
{json.dumps(session_data['all_observations'], indent=2) if session_data['all_observations'] else 'No observations logged'}

### Proposed Axioms
{json.dumps(session_data['proposed_axioms'], indent=2) if session_data['proposed_axioms'] else 'No axioms proposed'}

## Git Activity

### Recent Commits ({len(commits)})
{json.dumps(commits, indent=2) if commits else 'No commits in period'}

### Files Changed
{', '.join(changed_files[:20]) if changed_files else 'No files changed'}

---

Generate a Discovery Report with these sections:

1. **Today's Focus**: What did the founder prioritize? What themes emerge?

2. **Decision Patterns**: What trade-offs did they make? (e.g., "Prioritized X over Y")

3. **Observed Preferences**: Any consistent behaviors? (e.g., "Avoided library Z", "Preferred short functions")

4. **Proposed New Axioms**: Based on the patterns, suggest 1-3 concrete axioms in this format:
   - "Always [specific behavior] when [specific context]"
   - "Never [specific anti-pattern] because [reason]"

5. **Questions for Reflection**: 2-3 questions the founder should consider.

Be specific and actionable. Use direct language. No fluff."""

        return self._call_llm(prompt)
    
    def display_report(self):
        """Generate and display the Discovery Report."""
        console.print(Panel(
            f"Analyzing work from the last {self.days} day(s)...",
            title="🔍 Generating Discovery Report",
            border_style="cyan"
        ))
        
        # Show quick stats
        session_data = self._aggregate_session_data()
        commits = self.git.get_recent_commits()
        
        stats_table = Table(title="Quick Stats")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")
        stats_table.add_row("Decisions Logged", str(session_data["total_decisions"]))
        stats_table.add_row("Rejections Logged", str(session_data["total_rejections"]))
        stats_table.add_row("Observations", str(session_data["total_observations"]))
        stats_table.add_row("Proposed Axioms", str(len(session_data["proposed_axioms"])))
        stats_table.add_row("Git Commits", str(len(commits)))
        console.print(stats_table)
        
        # Generate and display report
        report = self.generate_report()
        
        console.print("\n")
        console.print(Panel(
            Markdown(report),
            title="📊 Discovery Report",
            border_style="green"
        ))
        
        # Save report
        report_file = LOGS_PATH / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_file.write_text(f"# Discovery Report\n\n*Generated: {datetime.now().isoformat()}*\n\n{report}")
        console.print(f"\n[dim]Report saved: {report_file}[/dim]")
        
        # Prompt for axiom confirmation
        if session_data["proposed_axioms"]:
            console.print("\n[bold]Pending Axiom Proposals:[/bold]")
            for i, axiom in enumerate(session_data["proposed_axioms"], 1):
                console.print(f"  {i}. {axiom['axiom']}")
            
            if Confirm.ask("\nPromote any axioms to the official rulebook?"):
                self._promote_axioms(session_data["proposed_axioms"])
    
    def _promote_axioms(self, axioms: list[dict]):
        """Promote proposed axioms to axioms.md."""
        console.print("\nEnter the numbers of axioms to promote (comma-separated), or 'skip':")
        selection = Prompt.ask("Selection")
        
        if selection.lower() == "skip":
            return
        
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            selected = [axioms[i] for i in indices if 0 <= i < len(axioms)]
        except ValueError:
            console.print("[red]Invalid selection[/red]")
            return
        
        # Read current axioms
        axioms_content = AXIOMS_FILE.read_text() if AXIOMS_FILE.exists() else ""
        
        # Append new axioms
        timestamp = datetime.now().strftime("%Y-%m-%d")
        new_entries = []
        for axiom in selected:
            new_entries.append(f"\n### [{timestamp}] {axiom['axiom']}\n*Derived from: {axiom.get('derived_from', 'session observation')}*\n")
        
        # Insert before the Axiom Log section
        if "## Axiom Log" in axioms_content:
            axioms_content = axioms_content.replace(
                "## Axiom Log",
                "\n".join(new_entries) + "\n## Axiom Log"
            )
        else:
            axioms_content += "\n" + "\n".join(new_entries)
        
        AXIOMS_FILE.write_text(axioms_content)
        console.print(f"[green]✓ {len(selected)} axiom(s) promoted to the rulebook[/green]")


def interactive_log():
    """Interactive mode for logging decisions."""
    logger = SessionLogger()
    
    console.print(Panel(
        "What would you like to log?",
        title="📝 Session Logger",
        border_style="blue"
    ))
    
    log_type = Prompt.ask(
        "Type",
        choices=["decision", "rejection", "observation", "axiom"],
        default="decision"
    )
    
    if log_type == "decision":
        context = Prompt.ask("Context (what was the situation?)")
        decision = Prompt.ask("Decision (what did you decide?)")
        reasoning = Prompt.ask("Reasoning (why?)", default="")
        logger.log_decision(context, decision, reasoning)
    
    elif log_type == "rejection":
        suggestion = Prompt.ask("What suggestion did you reject?")
        reason = Prompt.ask("What principle did it violate?")
        logger.log_rejection(suggestion, reason)
    
    elif log_type == "observation":
        observation = Prompt.ask("What did you observe?")
        category = Prompt.ask("Category", default="general")
        logger.log_observation(observation, category)
    
    elif log_type == "axiom":
        axiom = Prompt.ask("Proposed axiom")
        derived_from = Prompt.ask("Derived from (context)", default="")
        logger.propose_axiom(axiom, derived_from)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Reflect - Generate Discovery Reports from your work patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                        # Generate today's report
  %(prog)s --days 7               # Analyze last 7 days
  %(prog)s --log                  # Log a decision interactively
  %(prog)s --log-decision "chose X" --context "needed speed"
  %(prog)s --propose "Always ship on Friday"
        """
    )
    
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=1,
        help="Number of days to analyze (default: 1)"
    )
    
    parser.add_argument(
        "--log", "-l",
        action="store_true",
        help="Interactive logging mode"
    )
    
    parser.add_argument(
        "--log-decision",
        metavar="DECISION",
        help="Log a quick decision"
    )
    
    parser.add_argument(
        "--context",
        help="Context for --log-decision"
    )
    
    parser.add_argument(
        "--propose",
        metavar="AXIOM",
        help="Propose a new axiom"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show session statistics only"
    )
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.log:
        interactive_log()
        return
    
    if args.log_decision:
        logger = SessionLogger()
        logger.log_decision(
            context=args.context or "Quick log",
            decision=args.log_decision
        )
        return
    
    if args.propose:
        logger = SessionLogger()
        logger.propose_axiom(args.propose)
        return
    
    # Generate reflection report
    engine = ReflectionEngine(days=args.days)
    engine.display_report()


if __name__ == "__main__":
    main()
