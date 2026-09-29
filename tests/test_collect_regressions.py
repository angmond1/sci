"""Offline regressions for collection inputs and existing paper files.

Run with the Python interpreter recorded by the sci-retr installation. The
fixtures live in temporary directories and never contact publisher sites.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "sci-retr" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import sci_collect as collect  # noqa: E402


class CollectRegressions(unittest.TestCase):
    def test_invalid_pdf_retry_keeps_existing_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pid = "2026_Test_Smith"
            ctx = collect.Ctx(kb_root=root, work=root / "_collect", config=collect.DEFAULT_CONFIG, env={})
            pdf = collect.paper_dir(ctx, pid) / "pdf" / f"{pid}.pdf"
            previous = b"previous valid paper bytes"
            pdf.write_bytes(previous)
            row = {"paper_id": pid, "doi": "10.1000/example", "title": "Test paper", "year": "2026",
                   "publisher": "generic", "journal": "Example", "journal_abbrev": "Ex", "volume": "1",
                   "issue": "1", "pages": "1-2", "authors": "Smith", "corresponding": "Smith", "abstract": ""}
            outcome = collect.write_paper(ctx, row, collect.Outcome(method="retry", pdf_data=b"%PDF-broken"))
            self.assertEqual("failed", outcome.status)
            self.assertEqual(previous, pdf.read_bytes())

    def test_empty_retry_keeps_existing_html_and_xml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pid = "2026_Test_Smith"
            ctx = collect.Ctx(kb_root=root, work=root / "_collect", config=collect.DEFAULT_CONFIG, env={})
            paper = collect.paper_dir(ctx, pid)
            html = paper / "html" / f"{pid}.html"
            xml = paper / "xml" / f"{pid}.xml"
            html.write_text("previous article HTML", encoding="utf-8")
            xml.write_bytes(b"previous article XML")
            row = {"paper_id": pid, "doi": "10.1000/example", "title": "Test paper", "year": "2026",
                   "publisher": "generic", "journal": "Example", "journal_abbrev": "Ex", "volume": "1",
                   "issue": "1", "pages": "1-2", "authors": "Smith", "corresponding": "Smith", "abstract": ""}
            outcome = collect.write_paper(ctx, row, collect.Outcome(method="retry", html_raw="<html></html>", xml_raw=b"<x/>"))
            self.assertEqual("failed", outcome.status)
            self.assertEqual("previous article HTML", html.read_text(encoding="utf-8"))
            self.assertEqual(b"previous article XML", xml.read_bytes())

    def test_new_si_does_not_replace_existing_si(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pid = "2026_Test_Smith"
            ctx = collect.Ctx(
                kb_root=root,
                work=root / "_collect",
                config=collect.DEFAULT_CONFIG,
                env={},
            )
            si_dir = collect.paper_dir(ctx, pid) / "pdf"
            old = b"%PDF-old supporting information"
            new = b"%PDF-new supporting information"
            (si_dir / f"{pid}_SI.pdf").write_bytes(old)

            with patch.object(collect.time, "sleep", return_value=None):
                count = collect.save_si(
                    ctx,
                    pid,
                    lambda _url: (new, "application/pdf"),
                    ["https://example.org/new-supplement.pdf"],
                )

            files = list(si_dir.glob(f"{pid}_SI*.pdf"))
            self.assertEqual(count, 1)
            self.assertCountEqual([p.read_bytes() for p in files], [old, new])

    def test_wos_plain_text_uses_record_doi_not_cited_reference_dois(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export = Path(tmp) / "savedrecs.txt"
            export.write_text(
                "FN Clarivate Analytics Web of Science\n"
                "VR 1.0\n"
                "PT J\n"
                "TI Example article\n"
                "DI 10.1000/primary-paper\n"
                "CR Doe J, 2024, SOME JOURNAL, DOI 10.2000/cited-paper\n"
                "ER\n"
                "EF\n",
                encoding="utf-8",
            )
            self.assertEqual(collect.read_dois([str(export)]), ["10.1000/primary-paper"])

    def test_wos_tabular_text_uses_di_column_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export = Path(tmp) / "savedrecs.txt"
            export.write_text("TI\tDI\tCR\nExample\t10.1000/primary\tCited, DOI 10.2000/reference\n", encoding="utf-8")
            self.assertEqual(["10.1000/primary"], collect.read_dois([str(export)]))

    def test_legacy_xls_failure_is_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export = Path(tmp) / "savedrecs.xls"
            export.write_bytes(b"not an Excel workbook")
            with self.assertRaises(SystemExit) as error:
                collect.read_dois([str(export)])
            self.assertIn(".xls", str(error.exception).lower())

    def test_html_xls_uses_doi_column_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export = Path(tmp) / "savedrecs.xls"
            export.write_text(
                "<table><tr><th>Title</th><th>DOI</th><th>Cited References</th></tr>"
                "<tr><td>Example</td><td>10.1000/primary</td><td>10.2000/reference</td></tr></table>",
                encoding="utf-8",
            )
            self.assertEqual(["10.1000/primary"], collect.read_dois([str(export)]))

    def test_missing_input_does_not_fall_back_to_existing_registry(self) -> None:
        with self.assertRaises(SystemExit):
            collect.read_dois(["C:/missing/savedrecs.xls"])

    def test_wiley_alias_respects_env_file_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env_file = root / ".env"
            token_file = root / "token.txt"
            env_file.write_text("WILEY_TDM_TOKEN = env-file-token\n", encoding="utf-8")
            token_file.write_text("TDM_API_TOKEN = lower-priority-token\n", encoding="utf-8")
            with patch.object(collect, "TOKEN_FILE", token_file), patch.dict(os.environ, {}, clear=True):
                env = collect.load_env(env_file)
            self.assertEqual(env["TDM_API_TOKEN"], "env-file-token")


if __name__ == "__main__":
    unittest.main()
