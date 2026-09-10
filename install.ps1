# Install the skill where your agent looks for skills (Windows PowerShell).
#   .\install.ps1 -Agent codex            ->  .\.agents\skills\<slug>   (Codex; Cursor and Gemini CLI read it too)
#   .\install.ps1 -Agent claude           ->  .\.claude\skills\<slug>
#   .\install.ps1 -Agent cursor           ->  .\.cursor\skills\<slug>
#   .\install.ps1 -Agent gemini           ->  .\.gemini\skills\<slug>
#   .\install.ps1 -Agent copilot          ->  .\.github\skills\<slug>   (-Global: ~\.copilot\skills\<slug>)
#   .\install.ps1 -Agent all
#   add -Global to install under your user profile instead of the current folder
#   add -Into C:\path\to\project to install into another project folder
param(
  [Parameter(Mandatory=$true)][ValidateSet("codex","claude","cursor","gemini","copilot","all")][string]$Agent,
  [switch]$Global,
  [string]$Into = (Get-Location).Path
)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
# Exactly one skill folder ships under skills\. Refuse to run unless it is real: an empty slug
# would make the destination the skills root itself, and removing that deletes every installed skill.
$skillDir = Get-ChildItem -Directory -LiteralPath (Join-Path $here "skills") -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $skillDir -or -not (Test-Path -LiteralPath (Join-Path $skillDir.FullName "SKILL.md") -PathType Leaf)) {
  Write-Host "No skill found under $here\skills\ (expected skills\<slug>\SKILL.md). Nothing installed."
  exit 1
}
$slug = $skillDir.Name
$src = $skillDir.FullName
$agents = if ($Agent -eq "all") { @("codex","claude","cursor","gemini","copilot") } else { @($Agent) }
foreach ($a in $agents) {
  $dir = switch ($a) {
    "codex"   {".agents\skills"}
    "claude"  {".claude\skills"}
    "cursor"  {".cursor\skills"}
    "gemini"  {".gemini\skills"}
    "copilot" { if ($Global) {".copilot\skills"} else {".github\skills"} }
  }
  $base = if ($Global) { Join-Path $HOME $dir } else { Join-Path $Into $dir }
  New-Item -ItemType Directory -Force -Path $base | Out-Null
  # -LiteralPath throughout: a folder name with [ or ] is a path, never a wildcard.
  $dest = Join-Path $base $slug
  if (Test-Path -LiteralPath $dest) {
    $item = Get-Item -LiteralPath $dest -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
      # A junction or symlink: remove the link itself, never the folder it points to.
      [IO.Directory]::Delete($dest)
    } else {
      Remove-Item -LiteralPath $dest -Recurse -Force
    }
  }
  Copy-Item -LiteralPath $src -Destination $dest -Recurse
  Write-Host "copied  $src -> $dest"
}
Write-Host "Done. Restart your agent so it re-scans skills."
