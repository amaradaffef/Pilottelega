<#
.SYNOPSIS
  Cycle d'automatisation Git : commit -> push -> PR -> merge (squash) -> retour main.

.DESCRIPTION
  Pensé pour le workflow "une PR par action" de Pilottelega. À lancer depuis un
  worktree/branche de feature (PAS depuis main). Fait :
    1. git add -A + commit (si changements)
    2. push -u origin <branche>
    3. gh pr create (si pas déjà ouverte)
    4. gh pr merge --squash --admin --delete-branch
  Nécessite gh authentifié.

.PARAMETER Message
  Message de commit ET titre de PR.

.PARAMETER Base
  Branche cible du merge. Défaut: main.

.EXAMPLE
  ./auto-pr.ps1 -Message "spec: feature specification"
#>
param(
  [Parameter(Mandatory = $true)][string]$Message,
  [string]$Base = "main"
)

$ErrorActionPreference = "Stop"

$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -eq $Base) {
  throw "Refus: vous êtes sur '$Base'. Travaillez sur une branche de feature."
}

# 1. Commit si des changements existent
git add -A
$pending = git status --porcelain
if ($pending) {
  git commit -m $Message
  Write-Host "[OK] Commit créé sur $branch"
} else {
  Write-Host "[INFO] Aucun changement à committer"
}

# 2. Push
git push -u origin $branch
Write-Host "[OK] Branche poussée: $branch"

# 3. PR (créer si absente)
$prExists = $true
try { gh pr view $branch --json number -q .number 2>$null | Out-Null } catch { $prExists = $false }
if (-not $prExists) {
  gh pr create --base $Base --head $branch --title $Message --body $Message
  Write-Host "[OK] PR créée"
} else {
  Write-Host "[INFO] PR déjà existante pour $branch"
}

# 4. Merge squash (force admin pour automatiser, supprime la branche)
gh pr merge $branch --squash --admin --delete-branch
Write-Host "[OK] PR mergée (squash) dans $Base"
