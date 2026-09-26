#!/usr/bin/env bash
# sci-retr 설치 (macOS / Linux)
# 사용: bash ./install.sh            (Claude: ~/.claude/skills)
#       bash ./install.sh --codex    (Codex: ~/.codex/skills, CODEX_HOME 이 있으면 그 아래)
# 하는 일:
#   1) 필요한 프로그램을 확인하고, 없으면 설치한다: Python 3.11 이상, Google Chrome
#      (macOS 는 Homebrew 가 있으면 자동, Linux 는 관리자 권한이 필요해 안내만)
#   2) sci-retr, sci-index 두 skill 폴더를 skills 폴더로 복사한다
#   3) 파이썬 패키지를 설치한다 (시스템 Python 이 설치를 막으면 ~/.sci-retr/venv 가상환경에 설치)
#   4) 환경 점검(doctor)을 돌린다
# --no-auto-install 을 주면 프로그램을 설치하지 않고 안내만 한다.
# Windows 의 Git Bash 에서 실행하면 install.ps1 로 넘긴다.
set -euo pipefail
CODEX=0
NOAUTO=0
ROOT=""
for arg in "$@"; do
  case "$arg" in
    --codex) CODEX=1 ;;
    --no-auto-install) NOAUTO=1 ;;
    *) ROOT="$arg" ;;
  esac
done
ROOT="${ROOT:-$(cd "$(dirname "$0")" && pwd)}"
if [ "$CODEX" = 1 ]; then
  DEST="${CODEX_HOME:-$HOME/.codex}/skills"; APP="Codex"
else
  DEST="$HOME/.claude/skills"; APP="Claude"
fi
EXT_URL="https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn"
PACKAGES="requests pymupdf truststore beautifulsoup4 lxml openpyxl wiley-tdm playwright"
OS="$(uname -s)"
INSTALLED=""
export PYTHONIOENCODING=utf-8

# Windows 의 Git Bash 등에서 실행하면 PowerShell 설치 스크립트로 넘긴다
case "$OS" in
  MINGW*|MSYS*|CYGWIN*)
    echo "Windows 이므로 install.ps1 로 설치합니다."
    PS_ARGS=(-NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$ROOT/install.ps1")")
    if [ "$CODEX" = 1 ]; then PS_ARGS+=(-Codex); fi
    if [ "$NOAUTO" = 1 ]; then PS_ARGS+=(-NoAutoInstall); fi
    exec powershell.exe "${PS_ARGS[@]}"
    ;;
esac

find_python() {
  for cand in python3.12 python3.13 python3.11 python3 python; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 11) else 1)' 2>/dev/null; then
      echo "$cand"; return 0
    fi
  done
  return 1
}

echo "=== 1. 필요한 프로그램 확인"
PY="$(find_python || true)"
if [ -z "$PY" ] && [ "$NOAUTO" = 0 ] && [ "$OS" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
  echo "[설치] Python 이 없어 Homebrew 로 설치합니다 (python@3.12)"
  brew install python@3.12 && INSTALLED="$INSTALLED Python3.12"
  PY="$(find_python || true)"
fi
if [ -z "$PY" ]; then
  if [ "$OS" = "Darwin" ]; then
    echo "Python 3.11 이상이 필요합니다. https://www.python.org/downloads/ 설치 파일로 설치하거나 Homebrew(https://brew.sh) 설치 뒤 다시 실행하세요." >&2
  else
    echo "Python 3.11 이상이 필요합니다. 예: sudo apt install python3 python3-pip python3-venv (또는 배포판 패키지 관리자) 뒤 다시 실행하세요." >&2
  fi
  exit 1
fi
echo "[확인] Python  $PY ($("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])'))"

CHROME_OK=0
if [ "$OS" = "Darwin" ]; then
  if [ -d "/Applications/Google Chrome.app" ] || [ -d "$HOME/Applications/Google Chrome.app" ]; then
    CHROME_OK=1
  elif [ "$NOAUTO" = 0 ] && command -v brew >/dev/null 2>&1; then
    echo "[설치] Google Chrome 이 없어 Homebrew 로 설치합니다"
    brew install --cask google-chrome && CHROME_OK=1 && INSTALLED="$INSTALLED Chrome"
  fi
elif command -v google-chrome >/dev/null 2>&1 || command -v google-chrome-stable >/dev/null 2>&1; then
  CHROME_OK=1
fi
if [ "$CHROME_OK" = 1 ]; then
  echo "[확인] Chrome 있음"
else
  echo "[주의] Google Chrome 을 찾지 못했습니다. 웹 다운로드에 필요합니다: https://www.google.com/chrome/"
fi

echo "=== 2. skill 설치 ($APP)"
mkdir -p "$DEST"
for skill in sci-retr sci-index; do
  src="$ROOT/$skill"
  [ -f "$src/SKILL.md" ] || { echo "skill 폴더가 없습니다: $src" >&2; exit 1; }
  rm -rf "$DEST/$skill"
  mkdir -p "$DEST/$skill"
  (cd "$src" && tar --exclude='_history' --exclude='__pycache__' -cf - .) | (cd "$DEST/$skill" && tar -xf -)
  echo "설치: $DEST/$skill"
done

echo "=== 3. 파이썬 패키지 설치: $PY -m pip install ... (처음 설치면 1~2분 걸릴 수 있습니다)"
PIP_LOG="${TMPDIR:-/tmp}/sci-retr-pip.log"
# shellcheck disable=SC2086
if ! "$PY" -m pip install --quiet --disable-pip-version-check $PACKAGES 2>"$PIP_LOG"; then
  if grep -qiE "externally-managed|No module named pip" "$PIP_LOG"; then
    VENV="$HOME/.sci-retr/venv"
    echo "시스템 Python 에 패키지를 넣을 수 없어 가상환경($VENV)에 설치합니다."
    if ! "$PY" -m venv "$VENV"; then
      echo "가상환경을 만들지 못했습니다. 예: sudo apt install python3-venv python3-pip 뒤 다시 실행하세요." >&2
      exit 1
    fi
    PY="$VENV/bin/python"
    # shellcheck disable=SC2086
    "$PY" -m pip install --quiet --disable-pip-version-check $PACKAGES
    echo "앞으로 sci-retr 명령은 이 Python 으로 실행합니다: $PY"
  else
    cat "$PIP_LOG" >&2
    echo "pip 설치 실패. 인터넷 연결을 확인하고 다시 실행하세요." >&2
    exit 1
  fi
fi

# 이 skill 이 쓸 Python 을 기록한다 (Python 이 여러 개인 PC 에서 에이전트가 패키지 없는 python 을 부르지 않게)
PY_EXE="$("$PY" -c 'import sys; print(sys.executable)')"
printf '%s\n' "$PY_EXE" > "$DEST/sci-retr/python.txt"
echo "[확인] 이 skill 이 쓸 Python: $PY_EXE (sci-retr/python.txt 에 기록)"

echo "=== 4. 환경 점검"
CHECK_ROOT="${TMPDIR:-/tmp}/sci-retr-check"
DOCTOR_OUT="$("$PY" "$DEST/sci-retr/scripts/sci_collect.py" doctor --kb-root "$CHECK_ROOT" 2>&1 || true)"
echo "$DOCTOR_OUT"
echo "(위 root 는 점검용 임시 폴더입니다. 논문을 저장할 폴더는 수집을 시작할 때 정합니다.)"
NEED_CHROME_SET=0
if echo "$DOCTOR_OUT" | grep -q "\[문제\] Chrome("; then NEED_CHROME_SET=1; fi
NEED_EXT=0
if [ "$CODEX" = 0 ] && echo "$DOCTOR_OUT" | grep -q "Claude in Chrome 확장 없음"; then
  NEED_EXT=1
  echo "Claude in Chrome 확장이 없어 Chrome 웹스토어 페이지를 엽니다. 'Chrome에 추가'를 누르고 Claude 계정으로 로그인해 주세요."
  if [ "$OS" = "Darwin" ]; then
    open -a "Google Chrome" "$EXT_URL" 2>/dev/null || open "$EXT_URL" || true
  else
    xdg-open "$EXT_URL" >/dev/null 2>&1 || true
  fi
fi

echo ""
echo "▼・ᴥ・▼  sci-retr 설치 완료"
if [ -n "$INSTALLED" ]; then echo "새로 설치한 프로그램:$INSTALLED"; fi
echo "이렇게 시작하세요:"
N=1
if [ "$NEED_EXT" = 1 ]; then echo "  $N) Claude in Chrome 확장 설치·로그인: $EXT_URL"; N=$((N + 1)); fi
if [ "$NEED_CHROME_SET" = 1 ]; then
  echo "  $N) Chrome 설정: 위 점검에서 [문제] 로 나온 항목 고치기 (chrome://settings/content/pdfDocuments → 'PDF 다운로드', chrome://settings/downloads → '다운로드 전에 각 파일의 저장 위치 확인' 끄기)"
  N=$((N + 1))
fi
echo "  $N) $APP 에서 새 대화를 열거나 $APP 를 다시 시작하기 (새 skill 을 읽게)"
N=$((N + 1))
echo "  $N) 논문 목록 파일(Web of Science·Scopus 내보내기 또는 DOI 목록)을 대화창에 끌어다 놓고 'sci-retr 스킬로 논문 수집해줘'"
