#!/usr/bin/env python3
"""
Crystallize Memory - Turn temporary logs into permanent axioms.

This script:
1. Reads session_diffs.json (temporary observations)
2. Groups similar lessons together
3. Uses an LLM to synthesize them into clear axioms
4. Appends new axioms to patterns.md (or axioms.md if high confidence)
5. Clears the processed logs

Usage:
    python crystallize_memory.py              # Process all pending diffs
    python crystallize_memory.py --dry-run    # Preview without writing
    python crystallize_memory.py --threshold 3  # Require 3+ similar lessons
    python crystallize_memory.py --promote    # Also check patterns for promotion to axioms
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

# Load environment variables
load_dotenv()

# Rich console
console = Console()

# Paths
HARNESS_ROOT = Path(__file__).parent.parent
LOGS_PATH = HARNESS_ROOT / "logs"
CONTEXT_PATH = HARNESS_ROOT / "context"
DIFFS_FILE = LOGS_PATH / "session_diffs.json"
PATTERNS_FILE = CONTEXT_PATH / "patterns.md"
AXIOMS_FILE = CONTEXT_PATH / "axioms.md"


class MemoryCrystallizer:
    """
    Transforms temporary session diffs into permanent learned patterns.
    
    The crystallization process:
    1. Load raw diffs from session_diffs.json
    2. Group by category and similarity
    3. Synthesize grouped lessons into axioms via LLM
    4. Append to patterns.md (or axioms.md for high-confidence clusters)
    5. Archive processed diffs
    """
    
    def __init__(self, threshold: int = 2, dry_run: bool = False):
        """
        Initialize the crystallizer.
        
        Args:
            threshold: Minimum lessons needed to crystallize (default 2)
            dry_run: If True, preview only without writing
        """
        self.threshold = threshold
        self.dry_run = dry_run
        self.diffs = self._load_diffs()
        
    def _load_diffs(self) -> list[dict]:
        """Load session diffs from JSON file."""
        if not DIFFS_FILE.exists():
            return []
        
        try:
            data = json.loads(DIFFS_FILE.read_text())
            return data.get("entries", [])
        except json.JSONDecodeError:
            console.print("[yellow]Warning: Could not parse session_diffs.json[/yellow]")
            return []
    
    def _save_diffs(self, entries: list[dict]):
        """Save remaining diffs back to file."""
        if self.dry_run:
            return
            
        data = {
            "version": "1.0",
            "description": "Log of founder corrections. Processed by crystallize_memory.py",
            "last_crystallized": datetime.now().isoformat(),
            "entries": entries
        }
        DIFFS_FILE.write_text(json.dumps(data, indent=2))
    
    def _group_lessons(self) -> dict[str, list[dict]]:
        """Group lessons by category and similarity."""
        groups = defaultdict(list)
        
        for diff in self.diffs:
            category = diff.get("category", "general")
            lesson = diff.get("lesson", "")
            
            # Create a grouping key from category + simplified lesson
            key = f"{category}:{self._simplify_lesson(lesson)}"
            groups[key].append(diff)
        
        return dict(groups)
    
    def _simplify_lesson(self, lesson: str) -> str:
        """Simplify a lesson for grouping purposes."""
        # Normalize: lowercase, remove punctuation, take first few words
        simplified = lesson.lower()
        # Remove common words that don't add meaning
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", 
                     "being", "have", "has", "had", "do", "does", "did", "will",
                     "would", "could", "should", "may", "might", "must", "shall"}
        words = [w for w in simplified.split() if w not in stopwords]
        # Take first 5 significant words as the key
        return " ".join(words[:5])
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM for synthesis."""
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
                    max_tokens=500
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                console.print(f"[red]OpenAI error: {e}[/red]")
                return ""
        
        elif anthropic_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=anthropic_key)
                response = client.messages.create(
                    model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            except Exception as e:
                console.print(f"[red]Anthropic error: {e}[/red]")
                return ""
        
        # Fallback: simple aggregation without LLM
        console.print("[yellow]No API key. Using simple aggregation.[/yellow]")
        return ""
    
    def _synthesize_axiom(self, lessons: list[dict]) -> Optional[dict]:
        """
        Synthesize multiple similar lessons into a single axiom.
        
        Args:
            lessons: List of similar lesson diffs
            
        Returns:
            Synthesized axiom dict or None
        """
        if len(lessons) < self.threshold:
            return None
        
        # Build synthesis prompt
        lessons_text = "\n".join([
            f"- Trigger: {l.get('trigger', 'unknown')}\n  Lesson: {l.get('lesson', 'unknown')}"
            for l in lessons
        ])
        
        category = lessons[0].get("category", "general")
        
        prompt = f"""You are synthesizing multiple observations into a single, clear axiom.

Category: {category}
Number of observations: {len(lessons)}

Observations:
{lessons_text}

Synthesize these into ONE clear, actionable axiom. Rules:
1. Be specific and concrete
2. Use imperative voice ("Always X" or "Never Y")
3. Include the reason briefly
4. Keep it to 1-2 sentences max

Output format:
AXIOM: [Your synthesized axiom]
CONFIDENCE: [high/medium based on consistency]
CATEGORY: [{category}]"""

        response = self._call_llm(prompt)
        
        if response:
            # Parse the response
            axiom_line = ""
            confidence = "medium"
            
            for line in response.split("\n"):
                if line.startswith("AXIOM:"):
                    axiom_line = line.replace("AXIOM:", "").strip()
                elif line.startswith("CONFIDENCE:"):
                    conf = line.replace("CONFIDENCE:", "").strip().lower()
                    if "high" in conf:
                        confidence = "high"
            
            if axiom_line:
                return {
                    "axiom": axiom_line,
                    "confidence": confidence,
                    "category": category,
                    "source_count": len(lessons),
                    "crystallized_at": datetime.now().isoformat()
                }
        
        # Fallback: use the most common lesson
        lesson_counts = defaultdict(int)
        for l in lessons:
            lesson_counts[l.get("lesson", "")] += 1
        
        most_common = max(lesson_counts.items(), key=lambda x: x[1])
        return {
            "axiom": most_common[0],
            "confidence": "medium" if len(lessons) >= 3 else "low",
            "category": category,
            "source_count": len(lessons),
            "crystallized_at": datetime.now().isoformat()
        }
    
    def _append_to_patterns(self, axiom: dict):
        """Append a crystallized axiom to patterns.md."""
        if self.dry_run:
            return
        
        content = PATTERNS_FILE.read_text() if PATTERNS_FILE.exists() else ""
        
        # Find the appropriate section
        category = axiom["category"].title()
        section_header = f"## {category} Patterns"
        
        # Build the new entry
        timestamp = datetime.now().strftime("%Y-%m-%d")
        entry = f"\n- **[{timestamp}]** {axiom['axiom']} _(from {axiom['source_count']} observations, {axiom['confidence']} confidence)_\n"
        
        # Insert into the right section or at the anchor
        if section_header in content:
            # Add after the section header
            content = content.replace(
                section_header,
                section_header + entry
            )
        elif "<!-- PATTERN_ANCHOR:" in content:
            content = content.replace(
                "<!-- PATTERN_ANCHOR:",
                entry + "\n<!-- PATTERN_ANCHOR:"
            )
        else:
            content += f"\n{section_header}\n{entry}"
        
        # Update the count
        if "*Patterns Learned:" in content:
            import re
            content = re.sub(
                r"\*Patterns Learned: \d+\*",
                f"*Patterns Learned: {self._count_patterns(content)}*",
                content
            )
        
        # Update last crystallized
        content = content.replace(
            "*Last Crystallized: Never*",
            f"*Last Crystallized: {timestamp}*"
        )
        content = re.sub(
            r"\*Last Crystallized: \d{4}-\d{2}-\d{2}\*",
            f"*Last Crystallized: {timestamp}*",
            content
        )
        
        PATTERNS_FILE.write_text(content)
    
    def _append_to_axioms(self, axiom: dict):
        """Append a high-confidence axiom directly to axioms.md."""
        if self.dry_run:
            return
        
        content = AXIOMS_FILE.read_text() if AXIOMS_FILE.exists() else ""
        
        # Find the appropriate section
        category = axiom["category"].title()
        section_map = {
            "code": "## Technical Axioms",
            "communication": "## Communication Axioms",
            "decision": "## Strategic Axioms",
            "style": "## Communication Axioms",
        }
        section_header = section_map.get(axiom["category"], "## Operational Axioms")
        
        # Build the new entry
        timestamp = datetime.now().strftime("%Y-%m-%d")
        entry = f"\n### [{timestamp}] {axiom['axiom']}\n_Crystallized from {axiom['source_count']} consistent observations._\n"
        
        # Insert into the right section
        if section_header in content:
            content = content.replace(
                section_header,
                section_header + entry
            )
        elif "<!-- CRYSTALLIZE_ANCHOR:" in content:
            content = content.replace(
                "<!-- CRYSTALLIZE_ANCHOR:",
                entry + "\n<!-- CRYSTALLIZE_ANCHOR:"
            )
        else:
            content += entry
        
        # Update metadata
        import re
        content = re.sub(
            r"\*Last Crystallized: [^*]+\*",
            f"*Last Crystallized: {timestamp}*",
            content
        )
        
        AXIOMS_FILE.write_text(content)
    
    def _count_patterns(self, content: str) -> int:
        """Count the number of patterns in the file."""
        return content.count("- **[")
    
    def _archive_processed(self, processed_keys: set[str]):
        """Archive processed diffs and keep unprocessed ones."""
        remaining = []
        groups = self._group_lessons()
        
        for key, lessons in groups.items():
            if key in processed_keys:
                # Archive to a separate file
                if not self.dry_run:
                    archive_file = LOGS_PATH / f"archive_{datetime.now().strftime('%Y%m%d')}.json"
                    existing = []
                    if archive_file.exists():
                        try:
                            existing = json.loads(archive_file.read_text())
                        except:
                            existing = []
                    existing.extend(lessons)
                    archive_file.write_text(json.dumps(existing, indent=2))
            else:
                remaining.extend(lessons)
        
        self._save_diffs(remaining)
    
    def crystallize(self) -> list[dict]:
        """
        Run the crystallization process.
        
        Returns:
            List of crystallized axioms
        """
        if not self.diffs:
            console.print("[dim]No session diffs to process.[/dim]")
            return []
        
        console.print(Panel(
            f"Processing {len(self.diffs)} session diffs...",
            title="💎 Crystallizing Memory",
            border_style="magenta"
        ))
        
        # Group lessons
        groups = self._group_lessons()
        
        # Show groups
        table = Table(title="Lesson Groups")
        table.add_column("Category", style="cyan")
        table.add_column("Pattern", style="white")
        table.add_column("Count", style="green")
        table.add_column("Status", style="yellow")
        
        crystallized = []
        processed_keys = set()
        
        for key, lessons in sorted(groups.items(), key=lambda x: -len(x[1])):
            category, pattern = key.split(":", 1) if ":" in key else ("general", key)
            count = len(lessons)
            
            if count >= self.threshold:
                status = "→ Crystallizing"
                axiom = self._synthesize_axiom(lessons)
                if axiom:
                    crystallized.append(axiom)
                    processed_keys.add(key)
            else:
                status = f"Need {self.threshold - count} more"
            
            table.add_row(category, pattern[:40], str(count), status)
        
        console.print(table)
        
        if not crystallized:
            console.print("\n[dim]No patterns met the threshold for crystallization.[/dim]")
            return []
        
        # Show crystallized axioms
        console.print(f"\n[bold green]Crystallized {len(crystallized)} axiom(s):[/bold green]\n")
        
        for i, axiom in enumerate(crystallized, 1):
            confidence_color = "green" if axiom["confidence"] == "high" else "yellow"
            console.print(f"  {i}. [{confidence_color}]{axiom['confidence'].upper()}[/{confidence_color}] {axiom['axiom']}")
            console.print(f"     [dim]Category: {axiom['category']} | Sources: {axiom['source_count']}[/dim]\n")
        
        if self.dry_run:
            console.print("[yellow]DRY RUN - No files modified[/yellow]")
            return crystallized
        
        # Confirm and write
        if Confirm.ask("\nWrite these axioms to memory?"):
            for axiom in crystallized:
                if axiom["confidence"] == "high" and axiom["source_count"] >= 5:
                    # High confidence + many sources = promote to axioms.md
                    self._append_to_axioms(axiom)
                    console.print(f"[green]✓ Promoted to axioms.md: {axiom['axiom'][:50]}...[/green]")
                else:
                    # Otherwise, add to patterns.md
                    self._append_to_patterns(axiom)
                    console.print(f"[cyan]✓ Added to patterns.md: {axiom['axiom'][:50]}...[/cyan]")
            
            # Archive processed diffs
            self._archive_processed(processed_keys)
            console.print(f"\n[dim]Processed diffs archived. {len(self.diffs) - len(processed_keys)} remain.[/dim]")
        else:
            console.print("[dim]Cancelled. No changes made.[/dim]")
        
        return crystallized


def promote_patterns():
    """Check patterns.md for items ready to promote to axioms.md."""
    console.print(Panel(
        "Checking patterns for promotion to axioms...",
        title="⬆️ Pattern Promotion",
        border_style="blue"
    ))
    
    if not PATTERNS_FILE.exists():
        console.print("[dim]No patterns file found.[/dim]")
        return
    
    content = PATTERNS_FILE.read_text()
    
    # Find high-confidence patterns
    import re
    high_conf_patterns = re.findall(
        r"- \*\*\[([^\]]+)\]\*\* ([^_]+)_\(from (\d+) observations, high confidence\)_",
        content
    )
    
    if not high_conf_patterns:
        console.print("[dim]No high-confidence patterns ready for promotion.[/dim]")
        return
    
    console.print(f"Found {len(high_conf_patterns)} high-confidence pattern(s):\n")
    
    for i, (date, axiom, count) in enumerate(high_conf_patterns, 1):
        console.print(f"  {i}. {axiom.strip()} (from {count} observations)")
    
    if Confirm.ask("\nPromote these to axioms.md?"):
        axioms_content = AXIOMS_FILE.read_text() if AXIOMS_FILE.exists() else ""
        
        for date, axiom, count in high_conf_patterns:
            entry = f"\n### [Promoted {datetime.now().strftime('%Y-%m-%d')}] {axiom.strip()}\n_Originally observed on {date}, promoted from {count} observations._\n"
            
            if "## Operational Axioms" in axioms_content:
                axioms_content = axioms_content.replace(
                    "## Operational Axioms",
                    "## Operational Axioms" + entry
                )
            else:
                axioms_content += entry
        
        AXIOMS_FILE.write_text(axioms_content)
        console.print(f"[green]✓ Promoted {len(high_conf_patterns)} pattern(s) to axioms.md[/green]")


def show_status():
    """Show current status of the memory system."""
    console.print(Panel(
        "Founder's Harness Memory Status",
        title="📊 Status",
        border_style="cyan"
    ))
    
    # Count diffs
    diff_count = 0
    if DIFFS_FILE.exists():
        try:
            data = json.loads(DIFFS_FILE.read_text())
            diff_count = len(data.get("entries", []))
        except:
            pass
    
    # Count patterns
    pattern_count = 0
    if PATTERNS_FILE.exists():
        pattern_count = PATTERNS_FILE.read_text().count("- **[")
    
    # Count axioms
    axiom_count = 0
    if AXIOMS_FILE.exists():
        axiom_count = AXIOMS_FILE.read_text().count("### ")
    
    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("Location", style="dim")
    
    table.add_row("Pending Diffs", str(diff_count), "logs/session_diffs.json")
    table.add_row("Learned Patterns", str(pattern_count), "context/patterns.md")
    table.add_row("Permanent Axioms", str(axiom_count), "context/axioms.md")
    
    console.print(table)
    
    if diff_count >= 5:
        console.print(f"\n[yellow]You have {diff_count} pending diffs. Consider running crystallization.[/yellow]")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Crystallize Memory - Turn session diffs into permanent axioms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Crystallize pending diffs
  %(prog)s --dry-run          # Preview without writing
  %(prog)s --threshold 5      # Require 5+ similar lessons
  %(prog)s --promote          # Check patterns for promotion
  %(prog)s --status           # Show memory status
        """
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview only, don't write files"
    )
    
    parser.add_argument(
        "--threshold", "-t",
        type=int,
        default=2,
        help="Minimum lessons needed to crystallize (default: 2)"
    )
    
    parser.add_argument(
        "--promote", "-p",
        action="store_true",
        help="Check patterns.md for items to promote to axioms.md"
    )
    
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show memory system status"
    )
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
        return
    
    if args.promote:
        promote_patterns()
        return
    
    crystallizer = MemoryCrystallizer(
        threshold=args.threshold,
        dry_run=args.dry_run
    )
    crystallizer.crystallize()


if __name__ == "__main__":
    main()
