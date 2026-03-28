$startupFolder = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs\Startup")
$vbsPath = [System.IO.Path]::Combine($startupFolder, "jrnl-lncher.vbs")
# Resolve uv from PATH so this script is portable across machines/users.
$uvCommand = Get-Command uv -ErrorAction Stop
$uvPath = $uvCommand.Source

# Use the current script directory as project root.
$projectDir = $PSScriptRoot

$vbsContent = @'
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "{0} run --directory {1} pythonw main.py", 0, False
'@ -f $uvPath, $projectDir

Set-Content -Path $vbsPath -Value $vbsContent -Encoding ASCII
Write-Host "Created startup script at: $vbsPath"
Write-Host "Using uv at: $uvPath"
Write-Host "Project directory: $projectDir"
Write-Host "The utility will now start automatically when you log in."
