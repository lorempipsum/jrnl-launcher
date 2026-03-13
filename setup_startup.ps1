$startupFolder = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs\Startup")
$vbsPath = [System.IO.Path]::Combine($startupFolder, "jrnl-lncher.vbs")
$uvPath = "C:\Users\maxwe\.local\bin\uv.exe"
$projectDir = "C:\Users\maxwe\repos\jrnl-lncher"

$vbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "$uvPath run --directory $projectDir pythonw main.py", 0, False
"@

Set-Content -Path $vbsPath -Value $vbsContent
Write-Host "Created startup script at: $vbsPath"
Write-Host "The utility will now start automatically when you log in."
