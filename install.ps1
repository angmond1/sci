# sci-retr 설치 (Windows PowerShell)
# 사용: powershell -ExecutionPolicy Bypass -File .\install.ps1          (Claude: ~/.claude/skills)
#       powershell -ExecutionPolicy Bypass -File .\install.ps1 -Codex   (Codex: ~/.codex/skills)
# 하는 일:
#   1) 필요한 프로그램을 확인하고, 없으면 winget 으로 설치한다: Python 3.11 이상, Google Chrome
#   2) sci-retr, sci-index, sci-tldr 세 skill 폴더를 skills 폴더로 복사한다 (Claude 는 한 줄 요약 전용 에이전트 sci-tldr-writer 를 ~/.claude/agents 로)
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
$Packages = "requests pymupdf truststore beautifulsoup4 lxml openpyxl xlrd playwright"
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
$skills = @("sci-retr", "sci-index", "sci-tldr")
$destFull = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Dest).ProviderPath)
$destPrefix = if ($destFull.EndsWith('\')) { $destFull } else { "$destFull\" }
function Assert-InDestination([string]$path) {
    $full = [IO.Path]::GetFullPath($path)
    if (-not $full.StartsWith($destPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "설치 대상 경로가 목적지 밖입니다: $full"
    }
}
foreach ($skill in $skills) {
    $src = Join-Path $Root $skill
    if (-not (Test-Path -LiteralPath (Join-Path $src "SKILL.md") -PathType Leaf)) { throw "skill 폴더가 없습니다: $src" }
    $to = Join-Path $Dest $skill
    Assert-InDestination $to
    $srcFull = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $src).ProviderPath).TrimEnd('\')
    $toFull = [IO.Path]::GetFullPath($to).TrimEnd('\')
    if ($srcFull.Equals($toFull, [StringComparison]::OrdinalIgnoreCase) -or
        $srcFull.StartsWith("$toFull\", [StringComparison]::OrdinalIgnoreCase) -or
        $toFull.StartsWith("$srcFull\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "패키지 원본과 설치 대상 경로가 겹칩니다: $srcFull / $toFull"
    }
}
$stageRoot = Join-Path $Dest (".sci-retr-install-" + [Guid]::NewGuid().ToString('N'))
$backupRoot = Join-Path $stageRoot "backup"
Assert-InDestination $stageRoot
$backedUp = @()
$placed = @()
$installSucceeded = $false
$rollbackSucceeded = $true
try {
    New-Item -ItemType Directory -Path $stageRoot | Out-Null
    foreach ($skill in $skills) {
        $src = Join-Path $Root $skill
        $stage = Join-Path $stageRoot $skill
        Assert-InDestination $stage
        # 원본 설치본을 건드리기 전에 세 skill 을 모두 준비한다.
        robocopy $src $stage /E /XD _history __pycache__ /XF token.txt python.txt /NFL /NDL /NJH /NJS /NC /NS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "복사 실패: $skill (robocopy $LASTEXITCODE)" }
        if (-not (Test-Path -LiteralPath (Join-Path $stage 'SKILL.md') -PathType Leaf)) { throw "복사 결과에 SKILL.md 가 없습니다: $skill" }
        $tokenPath = Join-Path (Join-Path $Dest $skill) "token.txt"
        if (Test-Path -LiteralPath $tokenPath -PathType Leaf) {
            Copy-Item -LiteralPath $tokenPath -Destination (Join-Path $stage 'token.txt') -Force
        }
        $pythonPath = Join-Path (Join-Path $Dest $skill) 'python.txt'
        if (Test-Path -LiteralPath $pythonPath -PathType Leaf) {
            Copy-Item -LiteralPath $pythonPath -Destination (Join-Path $stage 'python.txt') -Force
        }
    }
    New-Item -ItemType Directory -Path $backupRoot | Out-Null
    foreach ($skill in $skills) {
        $to = Join-Path $Dest $skill
        $stage = Join-Path $stageRoot $skill
        $backup = Join-Path $backupRoot $skill
        Assert-InDestination $to
        Assert-InDestination $stage
        Assert-InDestination $backup
        if (Test-Path -LiteralPath $to) {
            Move-Item -LiteralPath $to -Destination $backup
            $backedUp += $skill
        }
        Move-Item -LiteralPath $stage -Destination $to
        $placed += $skill
        Write-Host "설치: $to"
        if (Test-Path -LiteralPath (Join-Path $to 'token.txt')) { Write-Host "  키·토큰 파일(token.txt)은 그대로 두었습니다." }
    }
    $installSucceeded = $true
} catch {
    $installError = $_
    for ($i = $skills.Count - 1; $i -ge 0; $i--) {
        $skill = $skills[$i]
        $to = Join-Path $Dest $skill
        $backup = Join-Path $backupRoot $skill
        try {
            if ($placed -contains $skill) {
                Assert-InDestination $to
                Remove-Item -LiteralPath $to -Recurse -Force
            }
            if ($backedUp -contains $skill) {
                Assert-InDestination $backup
                Move-Item -LiteralPath $backup -Destination $to
            }
        } catch {
            $rollbackSucceeded = $false
            Write-Warning "기존 설치 복구 실패 ($skill): $_"
        }
    }
    throw $installError
} finally {
    if ($installSucceeded -or $rollbackSucceeded) {
        # 백업에 junction 이 남아 있으면 링크만 제거한 뒤 임시 폴더를 지운다.
        foreach ($skill in $skills) {
            $backup = Join-Path $backupRoot $skill
            if (Test-Path -LiteralPath $backup) {
                $item = Get-Item -LiteralPath $backup -Force
                if ($item.LinkType) { [IO.Directory]::Delete($backup) }
            }
        }
        if (Test-Path -LiteralPath $stageRoot) {
            Assert-InDestination $stageRoot
            Remove-Item -LiteralPath $stageRoot -Recurse -Force
        }
    } else {
        Write-Warning "기존 설치 백업을 보존했습니다: $backupRoot"
    }
}
if (-not $Codex) {
    # 한 줄 요약 전용 에이전트: 도구 Read·Write, sonnet — 범용 에이전트보다 토큰·시간이 훨씬 적다 (sci-tldr 지침 6절)
    # ~/.claude/agents 는 하위 폴더까지 읽으므로 이 파일 하나만 맨 위에 둔다 (백업 폴더를 만들지 않는다)
    $agents = Join-Path $env:USERPROFILE ".claude\agents"
    New-Item -ItemType Directory -Force -Path $agents | Out-Null
    Copy-Item (Join-Path $Root "sci-tldr\agents\sci-tldr-writer.md") (Join-Path $agents "sci-tldr-writer.md") -Force
    Write-Host "설치: $(Join-Path $agents 'sci-tldr-writer.md') (한 줄 요약 전용 에이전트, 새 대화부터 인식)"
    # 웹 다운로드 전용 에이전트: 웹 목록 전체를 하나가 끝까지 받는다 (도구 Chrome·Bash·Read, sonnet·추론 medium — SKILL 5.5)
    Copy-Item (Join-Path $Root "sci-retr\agents\sci-retr-web.md") (Join-Path $agents "sci-retr-web.md") -Force
    Write-Host "설치: $(Join-Path $agents 'sci-retr-web.md') (웹 다운로드 전용 에이전트, 새 대화부터 인식)"
}

# 3) 파이썬 패키지
Write-Host "=== 3. 파이썬 패키지 설치: $py -m pip install ... (처음 설치면 1~2분 걸릴 수 있습니다)"
cmd /c "$py -m pip install --quiet --disable-pip-version-check $Packages"
if ($LASTEXITCODE -ne 0) {
    Write-Host "권한 문제일 수 있어 사용자 폴더(--user)로 다시 설치합니다."
    cmd /c "$py -m pip install --user --quiet --disable-pip-version-check $Packages"
    if ($LASTEXITCODE -ne 0) { throw "pip 설치 실패. 인터넷 연결을 확인하고 다시 실행하세요." }
}

# 이 skill 이 쓸 Python 을 기록한다 (Python 이 여러 개인 PC 에서 에이전트가 패키지 없는 python 을 부르지 않게)
$pyExe = cmd /c "$py -c ""import sys; print(sys.executable)"" 2>nul"
$pyExe = "$pyExe".Trim()
if ($pyExe) {
    [IO.File]::WriteAllText((Join-Path $Dest "sci-retr\python.txt"), $pyExe, (New-Object Text.UTF8Encoding($false)))
    Write-Host "[확인] 이 skill 이 쓸 Python: $pyExe (sci-retr\python.txt 에 기록)"
}

# 4) 점검
Write-Host "=== 4. 환경 점검"
$checkRoot = Join-Path $env:TEMP "sci-retr-check"
$doctorOut = @(cmd /c "$py `"$Dest\sci-retr\scripts\sci_collect.py`" doctor --kb-root `"$checkRoot`" 2>&1")
$doctorExit = $LASTEXITCODE
$doctorOut | ForEach-Object { Write-Host $_ }
Write-Host "(위 root 는 점검용 임시 폴더입니다. 논문을 저장할 폴더는 수집을 시작할 때 정합니다.)"
$needChromeSettings = [bool]($doctorOut | Select-String -Pattern "\[문제\] Chrome\(" -Quiet)
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
$n = 1
if ($doctorExit -ne 0 -or -not ($doctorOut | Select-String -Pattern '^=== 점검 끝: 문제 0, 주의 [0-9]+' -Quiet)) {
    throw "skill 파일은 설치했지만 환경 점검을 통과하지 못했습니다. 위의 [문제] 또는 오류를 고친 뒤 doctor 를 다시 실행하세요."
}
Write-Host "▼・ᴥ・▼  sci-retr 설치 완료"
if ($installed.Count -gt 0) { Write-Host "새로 설치한 프로그램: $($installed -join ', ')" }
Write-Host "이렇게 시작하세요:"
if ($needExt) { Write-Host "  $n) Claude in Chrome 확장 설치·로그인: $ExtUrl"; $n++ }
if ($needChromeSettings) { Write-Host "  $n) Chrome 설정: 위 점검에서 [문제] 로 나온 항목 고치기 (chrome://settings/content/pdfDocuments → 'PDF 다운로드', chrome://settings/downloads → '다운로드 전에 각 파일의 저장 위치 확인' 끄기)"; $n++ }
Write-Host "  $n) $app 에서 새 대화를 열거나 $app 를 다시 시작하기 (새 skill 을 읽게)"; $n++
Write-Host "  $n) 논문 목록 파일(Web of Science·Scopus 내보내기 또는 DOI 목록)을 대화창에 끌어다 놓고 'sci-retr 스킬로 논문 수집해줘'"
Write-Host "  참고) 특정 주제의 논문 목록은 Web of Science 나 Scopus 에서 검색해 내보내기(Export)로 만들 수 있습니다."
Write-Host "        Web of Science: https://www.webofscience.com/wos/woscc/smart-search"
Write-Host "        Scopus: https://www.scopus.com/pages/home#basic"
