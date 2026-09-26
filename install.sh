#!/usr/bin/env bash
# sci-retr 설치 (macOS / Linux)
# 사용: bash ./install.sh
# 하는 일: sci-retr, sci-index 두 skill 폴더를 ~/.claude/skills/ 로 복사하고 파이썬 패키지를 설치한다.
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")" && pwd)}"
DEST="$HOME/.claude/skills"
mkdir -p "$DEST"

for skill in sci-retr sci-index; do
  src="$ROOT/$skill"
  [ -f "$src/SKILL.md" ] || { echo "skill 폴더가 없습니다: $src" >&2; exit 1; }
  rm -rf "$DEST/$skill"
  mkdir -p "$DEST/$skill"
  (cd "$src" && tar --exclude='_history' --exclude='__pycache__' -cf - .) | (cd "$DEST/$skill" && tar -xf -)
  echo "설치: $DEST/$skill"
done

PY=""
for cand in python3.12 python3.11 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then PY="$cand"; break; fi
done
[ -n "$PY" ] || { echo "Python 3.11 이상이 필요합니다." >&2; exit 1; }
echo "패키지 설치: $PY -m pip install ..."
"$PY" -m pip install --quiet --disable-pip-version-check requests pymupdf truststore beautifulsoup4 lxml openpyxl wiley-tdm playwright

cat <<EOF

설치 완료. Claude 를 재시작한 뒤 이렇게 시작하세요:
  1) Chrome 설정: chrome://settings/content/pdfDocuments 를 'PDF 다운로드' 로, chrome://settings/downloads 의 '저장 위치 확인' 은 끄기
  2) 점검: $PY "$DEST/sci-retr/scripts/sci_collect.py" doctor --kb-root <논문 폴더>
  3) 대화창에 '이 DOI 목록 논문 받아줘' 라고 말하면 sci-retr 이 시작됩니다.
EOF
