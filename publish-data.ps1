# Publish Plumas pesticide/herbicide data deliverables to the repo + site.
# Run on Windows:  pwsh .\publish-data.ps1 "optional commit message"
# Or let Claude Code run it for you.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# 1. Clear any stale lock left by an interrupted git process
if (Test-Path ".git\index.lock") {
    Remove-Item -Force ".git\index.lock"
    Write-Host "Removed stale .git\index.lock"
}

# 2. Build a commit message (timestamped if none given)
$msg = if ($args.Count -ge 1 -and $args[0]) { $args[0] }
       else { "Update Plumas pesticide data ($(Get-Date -Format 'yyyy-MM-dd'))" }

# 3. Stage ONLY data deliverables + config (never force the whole tree).
#    Add new patterns here as your data grows (e.g. a data\ folder).
$patterns = @(".gitattributes",
              "Plumas_Pesticide_Data_Source_Inventory.xlsx",
              "Plumas_Pesticide_Data_Brief_and_Requests.md",
              "data")
foreach ($p in $patterns) { if (Test-Path $p) { git add -- $p } }

# 4. Commit + push to main (which also updates the published site)
if (git diff --cached --quiet) {
    Write-Host "Nothing new to publish."
} else {
    git commit -m $msg
    git push origin main
    Write-Host "Published: $msg"
}
