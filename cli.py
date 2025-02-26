import os
import typer
import json
from pathlib import Path
from typing import Optional, List, Dict
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID

from harmonizer_app import FinancialHarmonizer

app = typer.Typer(help="Financial Data Harmonizer CLI")
console = Console()

@app.command("process-file")
def process_file(
    file_path: Path = typer.Argument(..., help="Path to the file to process"),
    provider: str = typer.Argument(..., help="Provider name for processing this file"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to configuration file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to save the output"),
    format: str = typer.Option("csv", "--format", "-f", help="Output format (csv or excel)"),
):
    """Process a single file with the specified provider configuration."""
    if not file_path.exists():
        console.print(f"[bold red]Error:[/bold red] File {file_path} not found.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Processing file:[/bold green] {file_path}")
    console.print(f"[bold green]Provider:[/bold green] {provider}")
    
    harmonizer = FinancialHarmonizer(config_path=config_path)
    result = harmonizer.process_file(file_path=file_path, provider_name=provider)
    
    if result["success"]:
        console.print(f"[bold green]Success![/bold green] Processed {result['row_count']} rows.")
        
        if output:
            export_result = harmonizer.export_results(output_path=str(output), format=format)
            if export_result["success"]:
                console.print(f"[bold green]Data exported to:[/bold green] {export_result['path']}")
                console.print(f"[bold green]Logs exported to:[/bold green] {export_result['log_path']}")
            else:
                console.print(f"[bold red]Export error:[/bold red] {export_result['error']}")
        else:
            # Display summary of data
            display_data_summary(result["data"])
    else:
        console.print(f"[bold red]Error processing file:[/bold red] {result['error']}")
        raise typer.Exit(1)

@app.command("process-directory")
def process_directory(
    directory_path: Path = typer.Argument(..., help="Path to the directory to process"),
    mapping_file: Path = typer.Argument(..., help="Path to provider mapping JSON file"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to configuration file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to save the output"),
    format: str = typer.Option("csv", "--format", "-f", help="Output format (csv or excel)"),
):
    """Process all compatible files in a directory using provider mapping."""
    if not directory_path.exists() or not directory_path.is_dir():
        console.print(f"[bold red]Error:[/bold red] Directory {directory_path} not found or is not a directory.")
        raise typer.Exit(1)
    
    if not mapping_file.exists():
        console.print(f"[bold red]Error:[/bold red] Mapping file {mapping_file} not found.")
        raise typer.Exit(1)
    
    try:
        with open(mapping_file, 'r') as f:
            provider_mapping = json.load(f)
    except json.JSONDecodeError:
        console.print(f"[bold red]Error:[/bold red] Invalid JSON in mapping file.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Processing directory:[/bold green] {directory_path}")
    console.print(f"[bold green]Provider mappings:[/bold green] {len(provider_mapping)} patterns")
    
    harmonizer = FinancialHarmonizer(config_path=config_path)
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing files...", total=None)
        result = harmonizer.process_directory(directory_path=directory_path, provider_mapping=provider_mapping)
        progress.update(task, completed=100)
    
    if result["success"]:
        console.print(f"[bold green]Success![/bold green] Processed {result['processed']} files.")
        console.print(f"[bold yellow]Skipped:[/bold yellow] {result['skipped']} files (no provider mapping).")
        console.print(f"[bold red]Errors:[/bold red] {result['errors']} files.")
        
        if output and harmonizer.master_data is not None and not harmonizer.master_data.empty:
            export_result = harmonizer.export_results(output_path=str(output), format=format)
            if export_result["success"]:
                console.print(f"[bold green]Data exported to:[/bold green] {export_result['path']}")
                console.print(f"[bold green]Logs exported to:[/bold green] {export_result['log_path']}")
            else:
                console.print(f"[bold red]Export error:[/bold red] {export_result['error']}")
        elif harmonizer.master_data is not None:
            # Display summary of data
            display_data_summary(harmonizer.master_data)
    else:
        console.print(f"[bold red]Error processing directory:[/bold red] {result['error']}")
        raise typer.Exit(1)

@app.command("process-sharepoint")
def process_sharepoint(
    folder_path: str = typer.Argument(..., help="Path to SharePoint folder to process"),
    mapping_file: Path = typer.Argument(..., help="Path to provider mapping JSON file"),
    config_path: Path = typer.Argument(..., help="Path to configuration file with SharePoint credentials"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to save the output"),
    format: str = typer.Option("csv", "--format", "-f", help="Output format (csv or excel)"),
):
    """Process files from a SharePoint folder using provider mapping."""
    if not config_path.exists():
        console.print(f"[bold red]Error:[/bold red] Config file {config_path} not found.")
        raise typer.Exit(1)
    
    if not mapping_file.exists():
        console.print(f"[bold red]Error:[/bold red] Mapping file {mapping_file} not found.")
        raise typer.Exit(1)
    
    try:
        with open(mapping_file, 'r') as f:
            provider_mapping = json.load(f)
    except json.JSONDecodeError:
        console.print(f"[bold red]Error:[/bold red] Invalid JSON in mapping file.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Processing SharePoint folder:[/bold green] {folder_path}")
    console.print(f"[bold green]Provider mappings:[/bold green] {len(provider_mapping)} patterns")
    
    harmonizer = FinancialHarmonizer(config_path=config_path)
    
    if not harmonizer.sharepoint:
        console.print(f"[bold red]Error:[/bold red] SharePoint connector not configured in the configuration file.")
        raise typer.Exit(1)
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing SharePoint files...", total=None)
        result = harmonizer.process_sharepoint_folder(folder_path=folder_path, provider_mapping=provider_mapping)
        progress.update(task, completed=100)
    
    if result["success"]:
        console.print(f"[bold green]Success![/bold green] Processed {result['processed']} files.")
        console.print(f"[bold yellow]Skipped:[/bold yellow] {result['skipped']} files (no provider mapping).")
        console.print(f"[bold red]Errors:[/bold red] {result['errors']} files.")
        
        if output and harmonizer.master_data is not None and not harmonizer.master_data.empty:
            export_result = harmonizer.export_results(output_path=str(output), format=format)
            if export_result["success"]:
                console.print(f"[bold green]Data exported to:[/bold green] {export_result['path']}")
                console.print(f"[bold green]Logs exported to:[/bold green] {export_result['log_path']}")
            else:
                console.print(f"[bold red]Export error:[/bold red] {export_result['error']}")
        elif harmonizer.master_data is not None:
            # Display summary of data
            display_data_summary(harmonizer.master_data)
    else:
        console.print(f"[bold red]Error processing SharePoint folder:[/bold red] {result.get('error', 'Unknown error')}")
        raise typer.Exit(1)

@app.command("create-provider")
def create_provider(
    name: str = typer.Argument(..., help="Name of the provider"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Directory to save the provider config"),
):
    """Create a new provider configuration template."""
    from config.providers import ProviderConfig
    
    # Create a template provider config
    template = {
        "ProviderName": name,
        "Flags": ["StandardFormat"],
        "Synonyms": [
            {
                "LogicalField": "date",
                "AlternateNames": ["Date", "Transaction Date", "Invoice Date"]
            },
            {
                "LogicalField": "amount",
                "AlternateNames": ["Amount", "Total", "Invoice Amount"]
            },
            {
                "LogicalField": "description",
                "AlternateNames": ["Description", "Details", "Line Item"]
            },
            {
                "LogicalField": "reference",
                "AlternateNames": ["Reference", "Ref", "Invoice Number"]
            }
        ],
        "FilterTable": [
            "[amount] <> 0",
            "[description] <> null"
        ],
        "Calculations": [
            {
                "NewField": "gst_amt",
                "Expression": "([amount] * 0.15)"
            },
            {
                "NewField": "excl_gst",
                "Expression": "([amount] - [gst_amt])"
            }
        ],
        "HardcodedFields": [
            {
                "FieldName": "provider",
                "Value": name
            }
        ],
        "HeaderExtraction": [
            {
                "FieldName": "invoice_period",
                "StartDelim": "Period:",
                "EndDelim": "Invoice",
                "CleanupSteps": [
                    {
                        "type": "trim"
                    }
                ]
            }
        ]
    }
    
    # Initialize the provider config with custom output directory if specified
    provider_config = ProviderConfig(config_dir=output_dir if output_dir else None)
    
    try:
        provider_config.save_provider(template)
        output_path = os.path.join(provider_config.config_dir, f"{name}.json")
        console.print(f"[bold green]Provider configuration created:[/bold green] {output_path}")
    except Exception as e:
        console.print(f"[bold red]Error creating provider configuration:[/bold red] {str(e)}")
        raise typer.Exit(1)

def display_data_summary(df):
    """Display a summary of the DataFrame."""
    console.print("\n[bold blue]Data Summary:[/bold blue]")
    console.print(f"Rows: {len(df)}")
    console.print(f"Columns: {len(df.columns)}")
    
    # Display column names
    console.print("\n[bold blue]Columns:[/bold blue]")
    col_table = Table(show_header=True, header_style="bold green")
    col_table.add_column("Column Name")
    col_table.add_column("Data Type")
    col_table.add_column("Sample Values")
    
    # Sample a few columns to display
    sample_cols = df.columns[:10] if len(df.columns) > 10 else df.columns
    for col in sample_cols:
        sample_vals = df[col].dropna().astype(str).head(3).tolist()
        if len(sample_vals) > 0:
            sample_str = ", ".join(sample_vals[:3])
            if len(sample_str) > 50:
                sample_str = sample_str[:47] + "..."
        else:
            sample_str = "(No non-null values)"
            
        col_table.add_row(col, str(df[col].dtype), sample_str)
    
    if len(df.columns) > 10:
        col_table.add_row("...", "...", "...")
        
    console.print(col_table)

if __name__ == "__main__":
    app()
