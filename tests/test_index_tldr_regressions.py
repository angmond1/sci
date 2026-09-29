"""Offline regressions for index and one-line-summary source handling."""

from __future__ import annotations

import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sci-retr" / "scripts"))

import sci_index  # noqa: E402
import sci_tldr  # noqa: E402


class TldrApplyRegressionTests(unittest.TestCase):
    def test_compound_word_number_does_not_license_its_tens_part(self) -> None:
        problems = sci_tldr.check_tldr("이 연구는 반응을 20배 높였다.", "The reaction increased twenty-five times.")
        self.assertTrue(any("20" in problem for problem in problems))

    def test_formula_must_match_a_complete_source_token(self) -> None:
        problems = sci_tldr.check_tldr("이 연구는 Pd3Pb 촉매를 조사했다.", "Pd3Pb2 was investigated.")
        self.assertTrue(any("Pd3Pb" in problem for problem in problems))

    def make_index(self, root: Path) -> None:
        sci_index.write_index(root / "index.csv", [{"paper_id": "paper1", "제목": "Catalyst study", "원문상태": "전문"}], True)
        (root / "_collect").mkdir()

    def run_apply(self, root: Path, *files: Path) -> str:
        output = io.StringIO()
        args = SimpleNamespace(kb_root=str(root), files=[str(p) for p in files] or None)
        with contextlib.redirect_stdout(output):
            sci_tldr.cmd_apply(args)
        return sci_index.read_index(root / "index.csv")[0][0].get(sci_index.TLDR_COL, "")

    def test_missing_source_does_not_merge_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_index(root)
            result = {"paper_id": "paper1", "한줄요약": "이 연구는 Pt3Ni 촉매에서 91.3% 효율을 얻었다."}
            (root / "_collect" / "tldr_1.jsonl").write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")

            self.assertEqual("", self.run_apply(root))

    def test_result_uses_its_own_batch_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_index(root)
            work = root / "_collect"
            result = {"paper_id": "paper1", "한줄요약": "이 연구는 Pt3Ni 촉매에서 91.3% 효율을 얻었다."}
            result_path = work / "tldr_1.jsonl"
            result_path.write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
            (work / "tldr_src_1.json").write_text(json.dumps({"paper1": "Pd3Pb catalyst reached 81.3% efficiency."}), encoding="utf-8")
            (work / "tldr_src_2.json").write_text(json.dumps({"paper1": "Pt3Ni catalyst reached 91.3% efficiency."}), encoding="utf-8")

            self.assertEqual("", self.run_apply(root, result_path))


class IndexRegressionTests(unittest.TestCase):
    def test_registry_out_of_scope_survives_old_abstract_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            registry = root / "collection_registry.csv"
            with registry.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["paper_id", "status", "title", "year", "journal", "doi", "abstract"])
                writer.writeheader()
                writer.writerow({"paper_id": "paper1", "status": "out_of_scope", "title": "Catalyst study", "year": "2025", "journal": "Example", "doi": "10.1234/example", "abstract": "A short abstract."})
            paper = root / "papers" / "paper1"
            paper.mkdir(parents=True)
            (paper / "source.json").write_text(json.dumps({"access_status": "abstract_only"}), encoding="utf-8")

            rows, _ = sci_index.build_rows(root)

            self.assertEqual("범위밖-미수집", rows[0]["원문상태"])

    def test_keyword_extraction_stops_at_short_prose_sentence(self) -> None:
        text = "Keywords:\nThis study shows improved performance.\nIntroduction\n"
        self.assertEqual("", sci_index.find_keywords(text))


if __name__ == "__main__":
    unittest.main()
