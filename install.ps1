# Installs the CLI into a project-local virtual environment and creates a local knowledge store.
[CmdletBinding()]
param(
    [string]$Python = 'python',
    [string]$Config,
    [string]$Repository,
    [ValidateSet('lexical', 'sentence-transformers')][string]$Backend = 'lexical',
    [string]$Model,
    [string]$ModelRevision
)
$ErrorActionPreference = 'Stop'
if ($Backend -eq 'sentence-transformers' -and (-not $Model -or -not $ModelRevision)) {
    throw 'Semantic installation requires -Model and -ModelRevision.'
}
Get-Command git -ErrorAction Stop | Out-Null
Get-Command $Python -ErrorAction Stop | Out-Null
$venvDir = Join-Path $PSScriptRoot '.venv'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    & $Python -m venv $venvDir
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python virtual environment.' }
}
$package = if ($Backend -eq 'sentence-transformers') { "$PSScriptRoot[semantic]" } else { $PSScriptRoot }
& $venvPython -m pip install $package
if ($LASTEXITCODE -ne 0) { throw 'Installation failed. Setup has not run.' }
$setupArgs = @('-m', 'knowledge_agent')
if ($Config) { $setupArgs += @('--config', $Config) }
$setupArgs += 'setup'
if ($PSBoundParameters.ContainsKey('Backend') -or $Model -or $ModelRevision) { $setupArgs += @('--backend', $Backend) }
if ($Model) { $setupArgs += @('--model', $Model) }
if ($ModelRevision) { $setupArgs += @('--model-revision', $ModelRevision) }
if ($Repository) { $setupArgs += @('--repo', $Repository) }
& $venvPython @setupArgs
if ($LASTEXITCODE -ne 0) { throw 'Local setup failed. Review the error above before retrying.' }
Write-Host "Installed CLI: $(Join-Path $venvDir 'Scripts\knowledge-agent.exe')"
