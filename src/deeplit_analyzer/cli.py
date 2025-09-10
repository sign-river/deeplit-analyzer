"""Command-line interface for DeepLit Analyzer."""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from .analyzer import DeepLitAnalyzer
from .config import Config

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="DeepLit Analyzer")
def main():
    """DeepLit Analyzer - AI-powered academic literature analysis tool."""
    pass


@main.command()
@click.argument("paper_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file path")
@click.option("--format", "output_format", type=click.Choice(["json", "markdown", "txt"]), 
              default="markdown", help="Output format")
def analyze(paper_file: Path, output: Path, output_format: str):
    """Analyze a research paper file."""
    
    console.print(f"🔍 Analyzing paper: [blue]{paper_file}[/blue]")
    
    try:
        # Read the paper
        with open(paper_file, 'r', encoding='utf-8') as f:
            paper_text = f.read()
        
        # Initialize analyzer
        config = Config.load()
        if not config.validate_api_key():
            console.print("[red]❌ Error: DeepSeek API key not configured. Please set DEEPSEEK_API_KEY environment variable.[/red]")
            return
            
        analyzer = DeepLitAnalyzer(config)
        
        # Perform analysis
        with console.status("[bold green]Processing with AI..."):
            results = analyzer.analyze_paper(paper_text)
        
        if results["error"]:
            console.print(f"[red]❌ Analysis failed: {results['error']}[/red]")
            return
        
        # Format and display results
        if output_format == "json":
            output_text = json.dumps(results, indent=2, ensure_ascii=False)
            if not output:
                console.print(output_text)
        elif output_format == "markdown":
            output_text = format_markdown_output(results)
            if not output:
                console.print(Markdown(output_text))
        else:  # txt
            output_text = format_text_output(results)
            if not output:
                console.print(output_text)
        
        # Save to file if requested
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            console.print(f"✅ Results saved to [green]{output}[/green]")
        
        console.print("✅ Analysis complete!")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@main.command()
@click.argument("paper_file", type=click.Path(exists=True, path_type=Path))
@click.argument("section_title", required=False)
def summarize(paper_file: Path, section_title: str = ""):
    """Summarize a paper or specific section."""
    
    console.print(f"📝 Summarizing: [blue]{paper_file}[/blue]")
    
    try:
        with open(paper_file, 'r', encoding='utf-8') as f:
            paper_text = f.read()
        
        config = Config.load()
        if not config.validate_api_key():
            console.print("[red]❌ Error: DeepSeek API key not configured.[/red]")
            return
            
        analyzer = DeepLitAnalyzer(config)
        
        with console.status("[bold green]Generating summary..."):
            if section_title:
                summary = analyzer.summarize_section(paper_text, section_title)
            else:
                summary = analyzer.generate_abstract(paper_text)
        
        console.print(Panel(summary, title="📋 Summary", border_style="blue"))
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@main.command()
def config():
    """Show current configuration."""
    
    config = Config.load()
    
    table = Table(title="DeepLit Analyzer Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("API Key", "✅ Configured" if config.validate_api_key() else "❌ Missing")
    table.add_row("Base URL", config.deepseek_base_url)
    table.add_row("Max Tokens", str(config.max_tokens))
    table.add_row("Temperature", str(config.temperature))
    table.add_row("Output Format", config.output_format)
    table.add_row("Include Evidence", "Yes" if config.include_evidence else "No")
    
    console.print(table)


def format_markdown_output(results: dict) -> str:
    """Format analysis results as markdown."""
    md = f"""# Literature Analysis Results

## Abstract
{results['abstract']}

## Key Points
"""
    for i, point in enumerate(results['key_points'], 1):
        md += f"{i}. {point}\n"
    
    return md


def format_text_output(results: dict) -> str:
    """Format analysis results as plain text."""
    text = "LITERATURE ANALYSIS RESULTS\n"
    text += "=" * 50 + "\n\n"
    text += f"ABSTRACT:\n{results['abstract']}\n\n"
    text += "KEY POINTS:\n"
    for i, point in enumerate(results['key_points'], 1):
        text += f"{i}. {point}\n"
    
    return text


if __name__ == "__main__":
    main()