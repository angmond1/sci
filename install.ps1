# sci-retr 설치 (Windows PowerShell)
# 사용: powershell -ExecutionPolicy Bypass -File .\install.ps1          (Claude: ~/.claude/skills)
#       powershell -ExecutionPolicy Bypass -File .\install.ps1 -Codex   (Codex: ~/.codex/skills)
# 하는 일:
#   1) 필요한 프로그램을 확인하고, 없으면 winget 으로 설치한다: Python 3.11 이상, Google Chrome
#   2) sci-retr, sci-index 두 skill 폴더를 skills 폴더로 복사한다
#   3) 파이썬 패키지를 설치한다
#   4) 환경 점검(doctor)을 돌리고, Claude 용이면 Claude in Chrome 확장이 없을 때 웹스토어 페이지를 연다
# -NoAutoInstall 을 주면 프로그램을 설치하지 않고 안내만 한다.
param(
    [string]$Root = $PSScriptRoot,
    [switch]$Codex,
    [string]$Dest = "",
    [switch]$NoAutoInstall
)
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }
$env:PYTHONIOENCODING = "utf-8"

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
$ExtId = "fcoeoabgfenejglbffodgkkbkcdhcgfn"
$ExtUrl = "https://chromewebstore.google.com/detail/claude/$ExtId"
$Packages = "requests pymupdf truststore beautifulsoup4 lxml openpyxl wiley-tdm playwright"
$installed = @()

function Update-SessionPath {
    $m = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $u = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$m;$u"
}

function Get-PyVersion([string]$cand) {
    # 3.12 → 312. 없거나 실행이 안 되면 0
    $out = cmd /c "$cand -c ""import sys; print(sys.version_info[0] * 100 + sys.version_info[1])"" 2>nul"
    if ($LASTEXITCODE -eq 0 -and $out) {
        $v = 0
        if ([int]::TryParse("$out".Trim(), [ref]$v)) { return $v }
    }
    return 0
}

function Find-Python {
    foreach ($cand in @("py -3.12", "py -3.13", "py -3.11", "py -3", "python", "python3")) {
        if ((Get-PyVersion $cand) -ge 311) { return $cand }
    }
    foreach ($ver in @("312", "313", "311")) {   # 설치 직후 PATH 가 안 잡혔을 때
        $p = Join-Path $env:LOCALAPPDATA "Programs\Python\Python$ver\python.exe"
        if ((Test-Path $p) -and ((Get-PyVersion "`"$p`"") -ge 311)) { return "`"$p`"" }
    }
    return $null
}

function Find-Chrome {
    $cands = @(
        (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
        (Join-Path $env:LOCALAPPDATA "Google\Chrome\Application\chrome.exe")
    )
    foreach ($p in $cands) { if ($p -and (Test-Path $p)) { return $p } }
    return $null
}

function Install-WithWinget([string]$id, [string]$name, [string[]]$extra) {
    if ($NoAutoInstall) { return $false }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Warning "$name 이(가) 없는데 winget 도 없어 자동 설치를 할 수 없습니다. Microsoft Store 에서 '앱 설치 관리자'를 설치하거나 $name 을(를) 직접 설치한 뒤 다시 실행하세요."
        return $false
    }
    Write-Host "[설치] $name 이(가) 없어 winget 으로 설치합니다 ($id). 관리자 확인 창이 뜨면 '예'를 눌러 주세요."
    # winget 출력은 화면으로만 보낸다 (함수 반환값에 섞이면 실패해도 참이 된다)
    & winget install -e --id $id --source winget --silent --accept-source-agreements --accept-package-agreements @extra | Out-Host
    $ok = ($LASTEXITCODE -eq 0)
    if (-not $ok -and $extra.Count -gt 0) {
        & winget install -e --id $id --source winget --silent --accept-source-agreements --accept-package-agreements | Out-Host
        $ok = ($LASTEXITCODE -eq 0)
    }
    Update-SessionPath
    return $ok
}

function Test-ClaudeExtension {
    $ud = Join-Path $env:LOCALAPPDATA "Google\Chrome\User Data"
    $ls = Join-Path $ud "Local State"
    if (-not (Test-Path $ls)) { return $null }
    $prof = "Default"
    try {
        $j = Get-Content $ls -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($j.profile.last_used) { $prof = $j.profile.last_used }
    } catch { }
    return (Test-Path (Join-Path $ud "$prof\Extensions\$ExtId"))
}

# 1) 필요한 프로그램
Write-Host "=== 1. 필요한 프로그램 확인"
$py = Find-Python
if (-not $py) {
    [void](Install-WithWinget "Python.Python.3.12" "Python 3.12" @("--scope", "user"))
    $py = Find-Python
    if ($py) { $installed += "Python 3.12" }
}
if (-not $py) { throw "Python 3.11 이상을 찾지 못했습니다. https://www.python.org/downloads/ 에서 설치한 뒤('Add python.exe to PATH' 체크) 다시 실행하세요." }
Write-Host "[확인] Python  $py ($((Get-PyVersion $py) / 100))"

$chrome = Find-Chrome
if (-not $chrome) {
    [void](Install-WithWinget "Google.Chrome" "Google Chrome" @())
    $chrome = Find-Chrome
    if ($chrome) { $installed += "Google Chrome" }
}
if ($chrome) { Write-Host "[확인] Chrome  $chrome" }
else { Write-Warning "Google Chrome 을 찾지 못했습니다. 웹 다운로드에 필요합니다: https://www.google.com/chrome/" }

# 2) skill 복사
Write-Host "=== 2. skill 설치 ($app)"
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

# 3) 파이썬 패키지
Write-Host "=== 3. 파이썬 패키지 설치: $py -m pip install ..."
cmd /c "$py -m pip install --quiet --disable-pip-version-check $Packages"
if ($LASTEXITCODE -ne 0) {
    Write-Host "권한 문제일 수 있어 사용자 폴더(--user)로 다시 설치합니다."
    cmd /c "$py -m pip install --user --quiet --disable-pip-version-check $Packages"
    if ($LASTEXITCODE -ne 0) { throw "pip 설치 실패. 인터넷 연결을 확인하고 다시 실행하세요." }
}

# 4) 점검
Write-Host "=== 4. 환경 점검"
$checkRoot = Join-Path $env:TEMP "sci-retr-check"
cmd /c "$py `"$Dest\sci-retr\scripts\sci_collect.py`" doctor --kb-root `"$checkRoot`""
$needExt = $false
if (-not $Codex) {
    $ext = Test-ClaudeExtension
    if ($ext -eq $false) {
        $needExt = $true
        if ($chrome) {
            Write-Host "Claude in Chrome 확장이 없어 Chrome 웹스토어 페이지를 엽니다. 'Chrome에 추가'를 누르고 Claude 계정으로 로그인해 주세요."
            Start-Process $chrome $ExtUrl
        }
    }
}

Write-Host ""
Write-Host "▼・ᴥ・▼  sci-retr 설치 완료"
if ($installed.Count -gt 0) { Write-Host "새로 설치한 프로그램: $($installed -join ', ')" }
Write-Host "$app 를 재시작한 뒤 이렇게 시작하세요:"
$n = 1
if ($needExt) { Write-Host "  $n) Claude in Chrome 확장 설치·로그인: $ExtUrl"; $n++ }
Write-Host "  $n) Chrome 설정: chrome://settings/content/pdfDocuments 를 'PDF 다운로드' 로, chrome://settings/downloads 의 '저장 위치 확인' 은 끄기 (위 점검에서 [문제] 로 나온 것만)"; $n++
Write-Host "  $n) 대화창에 '이 DOI 목록 논문 받아줘' 라고 말하면 sci-retr 이 시작됩니다."
