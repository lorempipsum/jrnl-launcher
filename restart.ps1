# Restart jrnl-lncher: kill existing instance and start a new one

$processName = "python"
$scriptName  = "main.py"
$scriptDir   = $PSScriptRoot

# Kill the instance holding the lock socket on port 56789
$conn = Get-NetTCPConnection -LocalPort 56789 -LocalAddress 127.0.0.1 -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host "Killing PID $($conn.OwningProcess) (port 56789)"
    Stop-Process -Id $conn.OwningProcess -Force
} else {
    Write-Host "No running jrnl-lncher instance found."
}

Start-Sleep -Milliseconds 500

# Start a new instance detached (no window)
$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Error "python not found in PATH"
    exit 1
}

Write-Host "Starting jrnl-lncher..."
Start-Process -FilePath $pythonExe `
              -ArgumentList "`"$scriptDir\$scriptName`"" `
              -WorkingDirectory $scriptDir `
              -WindowStyle Hidden
Write-Host "Done."
