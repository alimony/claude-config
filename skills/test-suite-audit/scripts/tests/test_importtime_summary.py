from __future__ import annotations

import json
import subprocess
import sys

import importtime_summary


def test_ranks_a_real_importtime_log(tmp_path, capsys):
    proc = subprocess.run(
        [sys.executable, "-X", "importtime", "-c", "import json, xml.etree.ElementTree, email.mime.text"],
        capture_output=True, text=True, check=True,
    )
    log = tmp_path / "importtime.log"
    log.write_text(proc.stderr)
    out = tmp_path / "imports.json"
    assert importtime_summary.main([str(log), "--json-out", str(out)]) == 0
    data = json.loads(out.read_text())
    assert data["modules"] > 10 and data["total_seconds"] > 0
    top_level = {e["module"] for e in data["top_level"]}
    assert {"json", "xml.etree.ElementTree"} & top_level or "email.mime.text" in top_level
    assert "root packages by self time" in capsys.readouterr().out


def test_empty_log_is_an_error(tmp_path):
    log = tmp_path / "empty.log"
    log.write_text("nothing here\n")
    assert importtime_summary.main([str(log)]) == 1
