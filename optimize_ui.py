"""
UI Optimization Tool for Financial Harmonizer

This script analyzes and optimizes the UI components to improve performance and maintainability.
"""
import os
import sys
from pathlib import Path
import importlib
import json
import time
import argparse
import logging
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ui_optimization.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent

def scan_imports(file_path):
    """Scan a file for import statements and analyze them."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Find all import statements
        import_lines = []
        import_pattern = re.compile(r'^(?:from\s+[\w.]+\s+import\s+.*|import\s+.*)$', re.MULTILINE)
        for match in import_pattern.finditer(content):
            import_lines.append(match.group(0))
        
        # Analyze circular imports
        circular_imports = []
        parent_dir = os.path.dirname(file_path)
        for imp in import_lines:
            if 'from' in imp:
                module = imp.split('from')[1].strip().split('import')[0].strip()
                if parent_dir.split(os.sep)[-1] in module:
                    circular_imports.append(imp)
            
        return {
            "file": str(file_path),
            "imports": import_lines,
            "circular_imports": circular_imports,
            "total_imports": len(import_lines)
        }
    except Exception as e:
        logger.error(f"Error scanning imports in {file_path}: {e}")
        return {
            "file": str(file_path),
            "imports": [],
            "circular_imports": [],
            "total_imports": 0,
            "error": str(e)
        }

def analyze_streamlit_ui(file_paths):
    """Analyze Streamlit UI files for specific performance issues."""
    results = []
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for session state issues
            session_state_count = content.count("st.session_state")
            redundant_session_state = False
            if session_state_count > 10:  # Arbitrary threshold for excessive use
                redundant_session_state = True
            
            # Check for rendering performance issues
            rerun_count = content.count("st.experimental_rerun")
            excessive_reruns = rerun_count > 3  # Arbitrary threshold
            
            # Check for data caching
            uses_caching = "@st.cache_data" in content or "@st.cache" in content
            
            results.append({
                "file": str(file_path),
                "session_state_count": session_state_count,
                "rerun_count": rerun_count,
                "uses_caching": uses_caching,
                "issues": {
                    "redundant_session_state": redundant_session_state,
                    "excessive_reruns": excessive_reruns,
                    "missing_caching": not uses_caching and "pd." in content  # Data operations without caching
                }
            })
        except Exception as e:
            logger.error(f"Error analyzing Streamlit file {file_path}: {e}")
            results.append({
                "file": str(file_path),
                "error": str(e)
            })
    
    return results

def analyze_tkinter_ui(file_paths):
    """Analyze Tkinter UI files for specific performance issues."""
    results = []
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for memory leaks (widgets not properly destroyed)
            proper_cleanup = "destroy" in content and "winfo_children" in content
            
            # Check for event handling issues
            event_handling_issues = "bind" in content and "unbind" not in content
            
            # Check for resource management
            resource_management_issues = "open(" in content and "close" not in content
            
            results.append({
                "file": str(file_path),
                "issues": {
                    "missing_widget_cleanup": not proper_cleanup,
                    "event_handling_issues": event_handling_issues,
                    "resource_management_issues": resource_management_issues
                }
            })
        except Exception as e:
            logger.error(f"Error analyzing Tkinter file {file_path}: {e}")
            results.append({
                "file": str(file_path),
                "error": str(e)
            })
    
    return results

def create_unified_launcher():
    """Create or update a unified UI launcher."""
    project_root = get_project_root()
    launcher_path = project_root / "ui_launcher.py"
    
    content = """
"""
    return str(launcher_path)

def create_optimization_recommendations(analysis_results):
    """Create a detailed optimization recommendations file."""
    project_root = get_project_root()
    recommendations_path = project_root / "UI_OPTIMIZATION_RECOMMENDATIONS.md"
    
    # Extract key insights
    circular_imports = sum(len(result["circular_imports"]) for result in analysis_results.get("imports", []))
    streamlit_issues = [result for result in analysis_results.get("streamlit", []) 
                        if any(result.get("issues", {}).values())]
    tkinter_issues = [result for result in analysis_results.get("tkinter", []) 
                      if any(result.get("issues", {}).values())]
    
    # Build recommendations document
    content = """# UI Optimization Recommendations

## Overview

This document provides recommendations for optimizing the Financial Harmonizer UI based on automated analysis.

## Key Findings

- **Circular Imports**: {circular_imports} potential circular imports identified
- **Streamlit Performance Issues**: {streamlit_issues} files with potential Streamlit-specific performance issues
- **Tkinter Performance Issues**: {tkinter_issues} files with potential Tkinter-specific performance issues

## Recommended Actions

### 1. UI Architecture Improvements

- **Implement a UI Factory Pattern**: Create a unified interface for both Streamlit and Tkinter UIs
- **Separate Business Logic**: Move business logic out of UI components into shared modules
- **Create Clear Entry Points**: Standardize on a single launcher for each UI type

### 2. Streamlit-Specific Optimizations

""".format(
        circular_imports=circular_imports,
        streamlit_issues=len(streamlit_issues),
        tkinter_issues=len(tkinter_issues)
    )
    
    # Add Streamlit recommendations
    if streamlit_issues:
        for issue in streamlit_issues:
            file = Path(issue["file"]).name
            content += f"#### {file}\n\n"
            
            if issue.get("issues", {}).get("redundant_session_state"):
                content += f"- **Reduce Session State Usage**: The file uses session state {issue.get('session_state_count', 0)} times, which may impact performance. Consider consolidating related state variables.\n"
            
            if issue.get("issues", {}).get("excessive_reruns"):
                content += f"- **Minimize Page Reruns**: The file uses `st.experimental_rerun()` {issue.get('rerun_count', 0)} times. Consider using callbacks and other patterns to reduce full page reruns.\n"
            
            if issue.get("issues", {}).get("missing_caching"):
                content += "- **Implement Caching**: Add `@st.cache_data` decorators to data loading and processing functions to improve performance.\n"
            
            content += "\n"
    else:
        content += "No major Streamlit optimization issues detected.\n\n"
    
    # Add Tkinter recommendations
    content += "\n### 3. Tkinter-Specific Optimizations\n\n"
    
    if tkinter_issues:
        for issue in tkinter_issues:
            file = Path(issue["file"]).name
            content += f"#### {file}\n\n"
            
            if issue.get("issues", {}).get("missing_widget_cleanup"):
                content += "- **Improve Widget Cleanup**: Ensure all widgets are properly destroyed when no longer needed to prevent memory leaks.\n"
            
            if issue.get("issues", {}).get("event_handling_issues"):
                content += "- **Fix Event Handling**: Make sure event bindings are properly managed with corresponding unbinds when appropriate.\n"
            
            if issue.get("issues", {}).get("resource_management_issues"):
                content += "- **Resource Management**: Ensure all opened resources (files, connections) are properly closed.\n"
            
            content += "\n"
    else:
        content += "No major Tkinter optimization issues detected.\n\n"
    
    # Add general recommendations
    content += """
### 4. General Code Quality Improvements

- **Reduce Import Dependencies**: Minimize imports between UI components to prevent circular dependencies
- **Standardize Error Handling**: Implement consistent error handling across all UI components
- **Add Performance Metrics**: Add timing and performance tracking to identify bottlenecks

## Implementation Strategy

1. **Quick Wins**: Apply caching and reduce redundant session state usage
2. **Mid-term**: Refactor UI architecture to separate business logic
3. **Long-term**: Implement unified UI factory pattern

## Testing Recommendations

- Create automated tests for UI components
- Measure rendering performance before and after optimizations
- Test both UIs (Streamlit and Tkinter) with the same operations
"""
    
    with open(recommendations_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Created optimization recommendations at {recommendations_path}")
    return str(recommendations_path)

def optimize_streamlit_files(files, apply_changes=False):
    """Optimize Streamlit files."""
    results = []
    
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            changes = []
            
            # Add caching to data operations
            if "pd." in content and "@st.cache" not in content:
                pattern = r"(def\s+\w+\([^)]*\):)(\s+)([^\n]*pd\.)"
                if re.search(pattern, content):
                    content = re.sub(pattern, r"@st.cache_data\n\1\2\3", content)
                    changes.append("Added @st.cache_data to data processing functions")
            
            # Replace deprecated functions
            if "st.experimental_rerun" in content:
                content = content.replace("st.experimental_rerun", "st.rerun")
                changes.append("Replaced st.experimental_rerun with st.rerun")
            
            # Optimize session state access
            if "st.session_state" in content:
                # Extract session state variables into a single dictionary at the start of functions
                if re.search(r"def\s+\w+\([^)]*\):\s+", content):
                    pattern = r"(def\s+\w+\([^)]*\):)(\s+)(?!if\s+\"[\w_]+\"\s+not\s+in\s+st\.session_state)"
                    replacement = r"\1\2# Extract session state variables\2session_state = st.session_state\2"
                    content = re.sub(pattern, replacement, content)
                    # Replace individual st.session_state accesses with session_state
                    content = re.sub(r"st\.session_state\.(\w+)", r"session_state.\1", content)
                    changes.append("Optimized session state access pattern")
            
            # Apply changes if requested
            if apply_changes and changes and content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                logger.info(f"Applied optimizations to {file_path}")
            
            results.append({
                "file": str(file_path),
                "changes": changes,
                "optimized": len(changes) > 0
            })
            
        except Exception as e:
            logger.error(f"Error optimizing Streamlit file {file_path}: {e}")
            results.append({
                "file": str(file_path),
                "error": str(e),
                "optimized": False
            })
    
    return results

def create_ui_wrapper():
    """Create a UI wrapper that provides a unified interface to both UI types."""
    project_root = get_project_root()
    wrapper_path = project_root / "ui_wrapper.py"
    
    content = """
"""
    
    with open(wrapper_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Created UI wrapper at {wrapper_path}")
    return str(wrapper_path)

def analyze_ui():
    """Analyze UI files for optimization opportunities."""
    project_root = get_project_root()
    
    # Find UI files
    streamlit_ui_files = []
    tkinter_ui_files = []
    shared_ui_files = []
    
    # Streamlit UI files
    streamlit_ui_dir = project_root / "ui"
    if streamlit_ui_dir.exists():
        streamlit_ui_files = list(streamlit_ui_dir.glob("**/*.py"))
    
    # Tkinter UI files
    tkinter_ui_dir = project_root / "ui_tkinter"
    if tkinter_ui_dir.exists():
        tkinter_ui_files = list(tkinter_ui_dir.glob("**/*.py"))
    
    # Additional UI-related files
    for file in project_root.glob("*.py"):
        if any(term in file.name.lower() for term in ["ui", "streamlit", "tkinter", "app"]):
            shared_ui_files.append(file)
    
    logger.info(f"Found {len(streamlit_ui_files)} Streamlit UI files")
    logger.info(f"Found {len(tkinter_ui_files)} Tkinter UI files")
    logger.info(f"Found {len(shared_ui_files)} shared UI files")
    
    # Analyze imports
    all_ui_files = streamlit_ui_files + tkinter_ui_files + shared_ui_files
    import_analysis = [scan_imports(file) for file in all_ui_files]
    
    # Analyze specific UI frameworks
    streamlit_analysis = analyze_streamlit_ui(streamlit_ui_files + [f for f in shared_ui_files if "streamlit" in f.name.lower()])
    tkinter_analysis = analyze_tkinter_ui(tkinter_ui_files + [f for f in shared_ui_files if "tkinter" in f.name.lower()])
    
    # Compile results
    analysis_results = {
        "imports": import_analysis,
        "streamlit": streamlit_analysis,
        "tkinter": tkinter_analysis,
        "summary": {
            "streamlit_files": len(streamlit_ui_files),
            "tkinter_files": len(tkinter_ui_files),
            "shared_files": len(shared_ui_files),
            "total_imports": sum(result["total_imports"] for result in import_analysis),
            "circular_imports": sum(len(result["circular_imports"]) for result in import_analysis)
        }
    }
    
    # Save analysis results
    results_path = project_root / "ui_analysis_results.json"
    with open(results_path, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    logger.info(f"Saved analysis results to {results_path}")
    
    return analysis_results, all_ui_files, streamlit_ui_files

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Optimize UI components")
    parser.add_argument('--analyze', action='store_true', help='Analyze UI components without applying changes')
    parser.add_argument('--apply', action='store_true', help='Apply optimization changes')
    parser.add_argument('--create-wrapper', action='store_true', help='Create a unified UI wrapper')
    
    args = parser.parse_args()
    
    print("============================================================")
    print(" FINANCIAL HARMONIZER UI OPTIMIZATION TOOL")
    print("============================================================")
    print("")
    
    if not any([args.analyze, args.apply, args.create_wrapper]):
        print("No action specified. Running analysis only.")
        args.analyze = True
    
    # Analyze UI files
    print("Analyzing UI components...")
    analysis_results, all_ui_files, streamlit_ui_files = analyze_ui()
    
    # Create recommendations
    print("Creating optimization recommendations...")
    recommendations_path = create_optimization_recommendations(analysis_results)
    
    # Apply optimizations if requested
    if args.apply:
        print("\nApplying optimizations...")
        optimize_results = optimize_streamlit_files(streamlit_ui_files, apply_changes=True)
        
        optimized_count = sum(1 for result in optimize_results if result.get("optimized", False))
        print(f"Applied optimizations to {optimized_count} files")
        
        # List the changes made
        for result in optimize_results:
            if result.get("optimized", False):
                print(f"\n{result['file']}:")
                for change in result.get("changes", []):
                    print(f"  - {change}")
    
    # Create UI wrapper if requested
    if args.create_wrapper:
        print("\nCreating unified UI wrapper...")
        wrapper_path = create_ui_wrapper()
        print(f"Created UI wrapper at {wrapper_path}")
    
    print("\n============================================================")
    print(" OPTIMIZATION SUMMARY")
    print("============================================================")
    
    print(f"Total UI files analyzed: {len(all_ui_files)}")
    print(f"Streamlit files: {analysis_results['summary']['streamlit_files']}")
    print(f"Tkinter files: {analysis_results['summary']['tkinter_files']}")
    print(f"Shared UI files: {analysis_results['summary']['shared_files']}")
    print(f"Total imports: {analysis_results['summary']['total_imports']}")
    print(f"Potential circular imports: {analysis_results['summary']['circular_imports']}")
    
    print(f"\nOptimization recommendations written to: {recommendations_path}")
    
    if not args.apply:
        print("\nTo apply optimizations, run:")
        print("python -m financial_harmonizer.optimize_ui --apply")
    
    if not args.create_wrapper:
        print("\nTo create a unified UI wrapper, run:")
        print("python -m financial_harmonizer.optimize_ui --create-wrapper")

if __name__ == "__main__":
    main()