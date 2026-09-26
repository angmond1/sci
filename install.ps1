# sci-retr 설치 (Windows PowerShell)
# 사용: powershell -ExecutionPolicy Bypass -File .\install.ps1          (Claude: ~/.claude/skills)
#       powershell -ExecutionPolicy Bypass -File .\install.ps1 -Codex   (Codex: ~/.codex/skills)
# 하는 일: sci-retr, sci-index 두 skill 폴더를 skills 폴더로 복사하고 파이썬 패키지를 설치한다.
param(
    [string]$Root = $PSScriptRoot,
    [switch]$Codex,
    [string]$Dest = ""
)
$ErrorActionPreference = "Stop"
$app = "Claude"
if ($Codex) { $app = "Codex" }
if (-not $Dest) {
    if ($Codex) {
        $codexHome = $env:CODEX_HOME
        if (-not $codexHome) { $codexHome = Join-Path $env:USERPROFILE ".codex" }
        $Dest = Join-Path $codexHome "skills"
    } else {
        $Dest = Join-Path $env:USERPROFILE ".claude\skills"
    }
}
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

foreach ($skill in @("sci-retr", "sci-index")) {
    $src = Join-Path $Root $skill
    if (-not (Test-Path (Join-Path $src "SKILL.md"))) { throw "skill 폴더가 없습니다: $src" }
    $to = Join-Path $Dest $skill
    if (Test-Path $to) {
        $item = Get-Item $to -Force
        if ($item.LinkType) { cmd /c rmdir "$to" | Out-Null }     # 링크(junction)면 링크만 지운다
        else { Remove-Item -Recurse -Force $to }
    }
    # _history·__pycache__ 는 빼고 복사
    robocopy $src $to /E /XD _history __pycache__ /NFL /NDL /NJH /NJS /NC /NS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "복사 실패: $skill (robocopy $LASTEXITCODE)" }
    Write-Host "설치: $to"
}

# 파이썬 패키지
$py = $null
foreach ($cand in @("py -3.12", "py -3.11", "py -3", "python")) {
    cmd /c "$cand --version >nul 2>&1"
    if ($LASTEXITCODE -eq 0) { $py = $cand; break }
}
if (-not $py) { throw "Python 3.11 이상이 필요합니다. https://www.python.org/downloads/ 에서 설치한 뒤 다시 실행하세요." }
Write-Host "패키지 설치: $py -m pip install ..."
cmd /c "$py -m pip install --quiet --disable-pip-version-check requests pymupdf truststore beautifulsoup4 lxml openpyxl wiley-tdm playwright"
if ($LASTEXITCODE -ne 0) { throw "pip 설치 실패" }

Write-Host ""
Write-Host "▼・ᴥ・▼  sci-retr 설치 완료"
Write-Host "$app 를 재시작한 뒤 이렇게 시작하세요:"
Write-Host "  1) Chrome 설정: chrome://settings/content/pdfDocuments 를 'PDF 다운로드' 로, chrome://settings/downloads 의 '저장 위치 확인' 은 끄기"
Write-Host "  2) 점검: $py `"$Dest\sci-retr\scripts\sci_collect.py`" doctor --kb-root <논문 폴더>"
Write-Host "  3) 대화창에 '이 DOI 목록 논문 받아줘' 라고 말하면 sci-retr 이 시작됩니다."
