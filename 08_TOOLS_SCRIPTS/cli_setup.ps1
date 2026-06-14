# PowerShell script to repair PATH and install missing developer CLIs / libraries.
$ErrorActionPreference = "Continue"

Write-Output "=== Zentrale Insel CLI Setup & Repair ==="

# 1. Update PATH for Python 3.12
Write-Output "`n[1/4] Configuring Python 3.12 in User PATH..."
$pythonDir = "C:\Users\derzw\AppData\Local\Programs\Python\Python312"
$scriptsDir = "C:\Users\derzw\AppData\Local\Programs\Python\Python312\Scripts"
$userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
$pathParts = $userPath -split ";"

$updated = $false
if ($pathParts -notcontains $pythonDir) {
    $userPath = $userPath + ";" + $pythonDir
    $updated = $true
    Write-Output "Added Python directory to PATH: $pythonDir"
}
if ($pathParts -notcontains $scriptsDir) {
    $userPath = $userPath + ";" + $scriptsDir
    $updated = $true
    Write-Output "Added Python Scripts directory to PATH: $scriptsDir"
}

if ($updated) {
    [System.Environment]::SetEnvironmentVariable("PATH", $userPath, "User")
    Write-Output "User PATH environment variable updated in Windows Registry."
    # Update current session PATH too
    $env:PATH = $env:PATH + ";" + $pythonDir + ";" + $scriptsDir
} else {
    Write-Output "Python directories are already present in PATH."
}

# 2. Install Firebase and Genkit CLIs via npm
Write-Output "`n[2/4] Installing Firebase Tools and Genkit CLI globally..."

# Check if npm is available
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Output "Running npm install -g firebase-tools..."
    npm install -g firebase-tools --no-audit --no-fund
    
    Write-Output "Running npm install -g @genkit-ai/cli..."
    npm install -g @genkit-ai/cli --no-audit --no-fund
} else {
    Write-Warning "npm was not found. Please ensure Node.js is installed."
}

# 3. Install Google Cloud SDK via winget
Write-Output "`n[3/4] Checking and Installing Google Cloud SDK..."
$wingetPath = "C:\Users\derzw\AppData\Local\Microsoft\WindowsApps\winget.exe"

if (Test-Path $wingetPath) {
    Write-Output "Found winget at $wingetPath."
    # Check if gcloud is already installed/available
    if (Get-Command gcloud -ErrorAction SilentlyContinue) {
        Write-Output "gcloud CLI is already installed and in PATH."
    } else {
        Write-Output "Installing Google Cloud SDK via winget..."
        # Launch winget installation
        & $wingetPath install Google.CloudSDK --silent --accept-package-agreements --accept-source-agreements
        Write-Output "Installation triggered. Note: If a UAC prompt is shown, please accept it. You may need to restart your terminal for gcloud to register in PATH."
    }
} else {
    Write-Warning "winget was not found at standard path. Skipping Google Cloud SDK installation via winget. Please install Google Cloud SDK manually."
}

# 4. Install Python Dependencies
Write-Output "`n[4/4] Installing Python dependencies..."
$uvPath = "$scriptsDir\uv.exe"
$pipPath = "$scriptsDir\pip.exe"

$packages = @("fastapi", "uvicorn", "openai", "google-genai", "google-generativeai", "anthropic", "python-dotenv", "requests")

if (Test-Path $uvPath) {
    Write-Output "Using uv for lightning fast installation..."
    & $uvPath pip install $packages
} elseif (Test-Path $pipPath) {
    Write-Output "Using pip for installation..."
    & $pipPath install $packages
} else {
    Write-Warning "Neither uv nor pip was found at standard Python locations."
}

Write-Output "`n=== Setup Completed! ==="
Write-Output "Please restart your terminal or IDE for all environment variable updates to fully propagate."
