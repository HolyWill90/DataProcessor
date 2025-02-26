"""
Repository Status Analysis Tool
"""
import os
import subprocess
from pathlib import Path

def run_command(command):
    """Run a command and return its output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

def analyze_repo():
    """Analyze the repository status."""
    output_file = 'repo_status.txt'
    
    with open(output_file, 'w') as f:
        # Check repo status
        f.write("=== GIT STATUS ===\n")
        status = run_command('git status')
        f.write(status + "\n\n")
        
        # Check staged files
        f.write("=== STAGED FILES ===\n")
        staged = run_command('git ls-files --stage')
        f.write(staged + "\n\n")
        
        # Check directory structure
        f.write("=== DIRECTORY STRUCTURE ===\n")
        dir_structure = run_command('dir /b /s')
        f.write(dir_structure + "\n\n")
        
        # Check ignored files
        f.write("=== IGNORED FILES ===\n")
        ignored = run_command('git ls-files --ignored --exclude-standard --others')
        f.write(ignored + "\n\n")
        
        # Check untracked files
        f.write("=== UNTRACKED FILES ===\n")
        untracked = run_command('git ls-files --others --exclude-standard')
        f.write(untracked + "\n\n")
    
    print(f"Repository status saved to {output_file}")

if __name__ == "__main__":
    analyze_repo()