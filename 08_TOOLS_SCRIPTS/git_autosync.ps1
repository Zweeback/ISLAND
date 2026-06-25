# PowerShell script to automate Git synchronization for Zentrale Insel.
$ErrorActionPreference = "Stop"

$workspaceRoot = "$PSScriptRoot\.."

Write-Output "=== Git Autosync Daemon ==="
Write-Output "Workspace: $workspaceRoot"
Write-Output "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# 1. Clean up desktop.ini files to prevent git ref corruption on Windows
Write-Output "Cleaning up hidden desktop.ini files..."
Get-ChildItem -Path $workspaceRoot -Filter "desktop.ini" -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
    $path = $_.FullName
    try {
        Remove-Item -Path $path -Force
        Write-Output "Deleted desktop.ini: $path"
    } catch {
        Write-Warning "Could not delete $path : $_"
    }
}

# Change directory to workspace root
Set-Location -Path $workspaceRoot

# 2. Pull latest changes
Write-Output "`nPulling latest changes from remote..."
try {
    # Pull with rebase to avoid merge commits
    git pull origin main --rebase
    Write-Output "Git pull completed successfully."
} catch {
    Write-Warning "Failed to pull from remote: $_"
    # Continue anyway, we can try to push
}

# 3. Check for local modifications
$status = git status --porcelain
if ([string]::IsNullOrEmpty($status)) {
    Write-Output "`nNo local changes to commit."
} else {
    Write-Output "`nLocal changes detected:"
    Write-Output $status
    
    # Stage all changes
    Write-Output "Staging files..."
    git add .
    
    # Commit changes
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $commitMsg = "Autosync: $timestamp"
    Write-Output "Committing with message: '$commitMsg'"
    git commit -m $commitMsg
}

# 4. Push local changes
Write-Output "`nPushing changes to remote main branch..."
try {
    git push origin main
    Write-Output "Git push completed successfully!"
} catch {
    Write-Error "Failed to push to remote: $_"
}

Write-Output "`n=== Sync Completed! ==="
