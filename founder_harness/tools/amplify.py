#!/usr/bin/env python3
"""
Amplify - The Founder's Personal Harness CLI

Transform rough thoughts into polished, on-brand outputs.
This tool reads your identity and axioms to produce content that sounds exactly like you.

Usage:
    python amplify.py "Draft a team memo about pivoting Shadow Mode to focus on diff-checking"
    python amplify.py --type investor "Q3 update with metrics"
    python amplify.py --learn original.txt final.txt
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

# Load environment variables
load_dotenv()

# Rich console for pretty output
console = Console()

# Path configuration
HARNESS_ROOT = Path(__file__).parent.parent
CONTEXT_PATH = HARNESS_ROOT / "context"
LOGS_PATH = HARNESS_ROOT / "logs"

# Ensure logs directory exists
LOGS_PATH.mkdir(parents=True, exist_ok=True)


class FounderAmplifier:
    """
    The Founder's Personal Amplifier.
    
    Transforms raw intent into polished outputs by applying the founder's
    identity, axioms, and current context.
    """
    
    def __init__(self):
        """Initialize the amplifier by loading context files."""
        self.identity = self._load_context("identity.md")
        self.axioms = self._load_context("axioms.md")
        self.current_state = self._load_context("current_state.md")
        
        # Determine which LLM to use
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.openai_key and not self.anthropic_key:
            console.print("[yellow]Warning: No API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY[/yellow]")
    
    def _load_context(self, filename: str) -> str:
        """Load a context file."""
        path = CONTEXT_PATH / filename
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            console.print(f"[yellow]Warning: {filename} not found[/yellow]")
            return ""
    
    def _build_system_prompt(self, output_type: str = "general") -> str:
        """Build the system prompt from identity and axioms."""
        
        type_instructions = {
            "general": "Generate the appropriate output based on the request.",
            "email": "Write a clear, direct email. No fluff. Lead with the point.",
            "memo": "Write an internal memo. Be motivating but direct. Explain the why.",
            "investor": "Write an investor update. Lead with metrics. Be candid. Show momentum.",
            "spec": "Write a technical specification. Be precise. Include acceptance criteria.",
            "slack": "Write a Slack message. Keep it brief. Use appropriate emoji sparingly.",
            "tweet": "Write a tweet or thread. Punchy. Authentic. No corporate speak.",
            "decision": "Document a decision. State the decision, the reasoning, and the implications.",
        }
        
        instruction = type_instructions.get(output_type, type_instructions["general"])
        
        return f"""You are the Founder's Amplifier - an AI that writes EXACTLY like the founder.

Your job is to take rough, high-level intent and transform it into polished output 
that sounds 100% authentic to the founder's voice.

=== FOUNDER IDENTITY ===
{self.identity}

=== FOUNDER AXIOMS (Non-negotiable principles) ===
{self.axioms}

=== CURRENT COMPANY STATE ===
{self.current_state}

=== OUTPUT INSTRUCTIONS ===
Type: {output_type.upper()}
{instruction}

=== CRITICAL RULES ===
1. Write in the founder's EXACT voice - study the identity file
2. Apply the axioms to every decision and recommendation
3. Be aware of the current state when making suggestions
4. Never use words the founder doesn't use (check identity.md)
5. Be direct. Be confident. Cut the fluff.
6. If suggesting actions, make them specific and actionable
7. Match the energy and format to the output type

You ARE the founder. Write like it.
"""
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM API."""
        if self.openai_key:
            return self._call_openai(system_prompt, user_prompt)
        elif self.anthropic_key:
            return self._call_anthropic(system_prompt, user_prompt)
        else:
            return self._stub_response(user_prompt)
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Call OpenAI API."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_key)
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            console.print(f"[red]OpenAI API error: {e}[/red]")
            return self._stub_response(user_prompt)
    
    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Call Anthropic API."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return response.content[0].text
        except Exception as e:
            console.print(f"[red]Anthropic API error: {e}[/red]")
            return self._stub_response(user_prompt)
    
    def _stub_response(self, user_prompt: str) -> str:
        """Generate a stub response when no API key is configured."""
        return f"""[STUB RESPONSE - Configure API Key]

Your request: {user_prompt}

To enable the Amplifier:
1. Copy .env.example to .env
2. Add your OPENAI_API_KEY or ANTHROPIC_API_KEY
3. Run this command again

Your identity and axioms have been loaded and are ready.
"""
    
    def amplify(
        self,
        raw_thought: str,
        output_type: str = "general",
        save_draft: bool = True
    ) -> dict:
        """
        Transform a raw thought into polished output.
        
        Args:
            raw_thought: The founder's rough idea or command
            output_type: Type of output (email, memo, investor, spec, etc.)
            save_draft: Whether to save the draft for learning
            
        Returns:
            Dict with the input, output, and metadata
        """
        console.print(Panel(
            f"[bold]Input:[/bold] {raw_thought[:100]}{'...' if len(raw_thought) > 100 else ''}\n"
            f"[bold]Type:[/bold] {output_type}",
            title="🚀 Amplifying",
            border_style="cyan"
        ))
        
        # Build prompts
        system_prompt = self._build_system_prompt(output_type)
        user_prompt = f"""Transform this raw thought into a polished {output_type}:

---
{raw_thought}
---

Write the complete output. Make it sound exactly like the founder wrote it themselves."""
        
        # Call LLM
        output = self._call_llm(system_prompt, user_prompt)
        
        # Build result
        result = {
            "id": f"amplify_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "input": raw_thought,
            "output_type": output_type,
            "output": output,
            "status": "draft"
        }
        
        # Save draft for learning
        if save_draft:
            self._save_draft(result)
        
        return result
    
    def _save_draft(self, result: dict) -> Path:
        """Save a draft to the logs directory."""
        filename = f"{result['id']}.json"
        path = LOGS_PATH / filename
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        console.print(f"[dim]📝 Draft saved: {path}[/dim]")
        return path


def learn_from_founder(original_draft: str, final_version: str) -> Optional[str]:
    """
    Extract learning from the founder's edits and update axioms.
    
    This function:
    1. Compares the original draft to the founder's final version
    2. Uses an LLM to extract the style/logic differences
    3. Appends a new rule to axioms.md
    
    Args:
        original_draft: The AI-generated draft
        final_version: The founder's edited version
        
    Returns:
        The extracted learning, or None if failed
    """
    console.print(Panel(
        "Analyzing your edits to extract learnings...",
        title="🧠 Shadow Learning",
        border_style="magenta"
    ))
    
    # Load current axioms to provide context
    axioms_path = CONTEXT_PATH / "axioms.md"
    try:
        current_axioms = axioms_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        console.print("[red]Error: axioms.md not found[/red]")
        return None
    
    # Build the learning extraction prompt
    system_prompt = """You are analyzing the difference between an AI-generated draft and 
the founder's edited final version. Your job is to extract SPECIFIC, ACTIONABLE learnings 
about the founder's preferences.

Focus on:
- Tone and word choice changes
- Structural changes (what was moved, removed, added)
- Specific phrases or patterns the founder prefers
- Things the AI got wrong that should be avoided

Output format:
- One clear, specific learning
- Written as a rule that can be added to the axioms
- Keep it brief but precise"""

    user_prompt = f"""Compare these two versions and extract one key learning:

=== ORIGINAL DRAFT (AI-generated) ===
{original_draft}

=== FINAL VERSION (Founder-edited) ===
{final_version}

What specific pattern or preference should the AI learn from these edits?
Write it as a brief rule (1-2 sentences max)."""

    # Call LLM
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    learning = None
    
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            learning = response.choices[0].message.content.strip()
        except Exception as e:
            console.print(f"[red]Error extracting learning: {e}[/red]")
            return None
    elif anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                max_tokens=200,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            learning = response.content[0].text.strip()
        except Exception as e:
            console.print(f"[red]Error extracting learning: {e}[/red]")
            return None
    else:
        console.print("[yellow]No API key configured. Cannot extract learning.[/yellow]")
        return None
    
    if learning:
        # Append to axioms.md
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        learning_entry = f"\n- **[{timestamp}]**: {learning}"
        
        # Find the learning anchor and append
        if "<!-- LEARNING_ANCHOR:" in current_axioms:
            # Insert before the anchor
            updated_axioms = current_axioms.replace(
                "<!-- LEARNING_ANCHOR:",
                f"{learning_entry}\n\n<!-- LEARNING_ANCHOR:"
            )
        else:
            # Append at the end
            updated_axioms = current_axioms + f"\n\n## Learned Patterns\n{learning_entry}\n"
        
        axioms_path.write_text(updated_axioms, encoding="utf-8")
        
        console.print(Panel(
            f"[green]Learned:[/green] {learning}",
            title="✅ Learning Recorded",
            border_style="green"
        ))
        
        # Also log the full learning event
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "learning",
            "original_draft": original_draft,
            "final_version": final_version,
            "extracted_learning": learning
        }
        log_path = LOGS_PATH / f"learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_path.write_text(json.dumps(log_entry, indent=2), encoding="utf-8")
    
    return learning


def interactive_learn():
    """Interactive mode for submitting learnings."""
    console.print(Panel(
        "Paste the original draft, then your edited version.\n"
        "The system will extract what it should learn.",
        title="🧠 Interactive Learning Mode",
        border_style="magenta"
    ))
    
    console.print("\n[bold]Paste the ORIGINAL draft (press Enter twice when done):[/bold]")
    original_lines = []
    while True:
        line = input()
        if line == "":
            if original_lines and original_lines[-1] == "":
                break
        original_lines.append(line)
    original_draft = "\n".join(original_lines[:-1])  # Remove trailing empty line
    
    console.print("\n[bold]Paste your EDITED version (press Enter twice when done):[/bold]")
    final_lines = []
    while True:
        line = input()
        if line == "":
            if final_lines and final_lines[-1] == "":
                break
        final_lines.append(line)
    final_version = "\n".join(final_lines[:-1])
    
    learn_from_founder(original_draft, final_version)


def list_recent_drafts(limit: int = 5):
    """List recent drafts for review."""
    drafts = sorted(
        LOGS_PATH.glob("amplify_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )[:limit]
    
    if not drafts:
        console.print("[dim]No drafts found.[/dim]")
        return
    
    console.print(Panel(
        f"Showing {len(drafts)} most recent drafts",
        title="📋 Recent Drafts",
        border_style="blue"
    ))
    
    for draft_path in drafts:
        try:
            draft = json.loads(draft_path.read_text())
            console.print(f"\n[bold cyan]{draft['id']}[/bold cyan]")
            console.print(f"  Type: {draft.get('output_type', 'general')}")
            console.print(f"  Input: {draft['input'][:60]}...")
            console.print(f"  Status: {draft.get('status', 'draft')}")
        except Exception as e:
            console.print(f"[red]Error reading {draft_path}: {e}[/red]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Amplify - Transform rough thoughts into polished, on-brand outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Tell the team we're pivoting Shadow Mode"
  %(prog)s --type email "Follow up with investor about demo"
  %(prog)s --type investor "Q3 metrics and roadmap update"
  %(prog)s --type spec "Shadow Mode diff-checking feature"
  %(prog)s --learn original.txt final.txt
  %(prog)s --interactive-learn
  %(prog)s --drafts
        """
    )
    
    parser.add_argument(
        "thought",
        nargs="?",
        help="Your raw thought or command to amplify"
    )
    
    parser.add_argument(
        "--type", "-t",
        choices=["general", "email", "memo", "investor", "spec", "slack", "tweet", "decision"],
        default="general",
        help="Type of output to generate (default: general)"
    )
    
    parser.add_argument(
        "--learn",
        nargs=2,
        metavar=("ORIGINAL", "FINAL"),
        help="Learn from your edits: provide original draft file and final version file"
    )
    
    parser.add_argument(
        "--interactive-learn", "-i",
        action="store_true",
        help="Interactive mode to paste and learn from your edits"
    )
    
    parser.add_argument(
        "--drafts", "-d",
        action="store_true",
        help="List recent drafts"
    )
    
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save the draft for learning"
    )
    
    args = parser.parse_args()
    
    # Handle different modes
    if args.drafts:
        list_recent_drafts()
        return
    
    if args.interactive_learn:
        interactive_learn()
        return
    
    if args.learn:
        original_file, final_file = args.learn
        try:
            original = Path(original_file).read_text(encoding="utf-8")
            final = Path(final_file).read_text(encoding="utf-8")
            learn_from_founder(original, final)
        except FileNotFoundError as e:
            console.print(f"[red]File not found: {e}[/red]")
            sys.exit(1)
        return
    
    if not args.thought:
        parser.print_help()
        console.print("\n[yellow]Provide a thought to amplify, or use --help for options[/yellow]")
        sys.exit(1)
    
    # Main amplification flow
    amplifier = FounderAmplifier()
    result = amplifier.amplify(
        args.thought,
        output_type=args.type,
        save_draft=not args.no_save
    )
    
    # Display result
    console.print("\n")
    console.print(Panel(
        Markdown(result["output"]),
        title=f"📤 Output ({args.type})",
        border_style="green"
    ))
    
    # Prompt for learning
    console.print("\n[dim]Edit this output? Run: amplify.py --interactive-learn[/dim]")


if __name__ == "__main__":
    main()
