# Setup Git repository and push to GitHub
Write-Host "Setting up Git repository for Financial Harmonizer..."

# Make sure we're in the right directory
$currentDir = (Get-Location).Path
Write-Host "Current directory: $currentDir"

# Clean start - remove .git if it exists
if (Test-Path .\.git) {
    Write-Host "Removing existing .git directory"
    Remove-Item -Recurse -Force .\.git
}

# Initialize Git repository
Write-Host "Initializing Git repository"
git init

# Configure Git
Write-Host "Configuring Git"
git config user.name "HolyWill90"
git config user.email "your.email@example.com"

# Add all files
Write-Host "Adding files to Git"
git add .

# Create initial commit
Write-Host "Creating initial commit"
git commit -m "Initial commit: Financial Harmonizer project"

# Add remote repository
Write-Host "Adding remote repository"
git remote add origin https://github.com/HolyWill90/DataProcessor.git

# Push to GitHub (requires authentication)
Write-Host "Ready to push to GitHub"
Write-Host "Run this command to push: git push -u origin main"

Write-Host "Git setup complete!"