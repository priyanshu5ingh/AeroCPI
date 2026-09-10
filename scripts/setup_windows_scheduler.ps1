# AeroCPI Windows Task Scheduler Setup Script
# Registers a scheduled task to run daily collection sweep automatically at 03:30 AM local time.

$TaskName = "AeroCPI_Daily_Observation_Collector"
$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
$PythonExe = "$ProjectRoot\backend\.venv\Scripts\python.exe"
$ScriptPath = "$ProjectRoot\scripts\run_daily_collection.py"
$LogPath = "$ProjectRoot\backend\logs\collection_scheduler.log"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "AeroCPI Windows Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "Task Name: $TaskName" -ForegroundColor Yellow
Write-Host "Python Executable: $PythonExe" -ForegroundColor Yellow
Write-Host "Script: $ScriptPath" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# Ensure python environment exists
if (-not (Test-Path $PythonExe)) {
    Write-Error "Python executable not found at $PythonExe. Please initialize .venv first."
    exit 1
}

# Ensure logs directory exists
$LogDir = Split-Path -Parent $LogPath
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

# Action definition
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "$ScriptPath --scheduled" `
    -WorkingDirectory $ProjectRoot.Path

# Trigger definition (Daily at 03:30 AM)
$Trigger = New-ScheduledTaskTrigger -Daily -At "03:30AM"

# Settings definition
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

# Unregister existing task if present
Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

# Register the scheduled task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Description "Daily AeroCPI observation collector sweep for 10 basket routes across 5 production APWs." `
        -ErrorAction Stop | Out-Null

    Write-Host "SUCCESS: Windows Scheduled Task '$TaskName' registered successfully!" -ForegroundColor Green
    Write-Host "Schedule: Daily at 03:30 AM" -ForegroundColor Green
    Write-Host "Logs: $LogPath" -ForegroundColor Green
} catch {
    Write-Warning "Registration without admin rights failed. Falling back to schtasks CLI..."
    $SchCmd = "schtasks /create /tn ""$TaskName"" /tr ""\""$PythonExe\"" \""$ScriptPath\"" --scheduled"" /sc daily /st 03:30 /f"
    Invoke-Expression $SchCmd
}
