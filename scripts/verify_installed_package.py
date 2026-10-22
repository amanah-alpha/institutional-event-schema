#!/usr/bin/env python3
"""Run with the clean consumer venv's Python, outside the source checkout."""
import hashlib
import importlib
from importlib.resources import files
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
package = importlib.import_module("institutional_event_schema")
if Path(package.__file__).resolve().is_relative_to(ROOT):
    raise SystemExit("installed-package check must use an isolated consumer environment")
bundled = files("institutional_event_schema").joinpath("schemas")
expected_schemas = sorted((ROOT / "schema").glob("*.json"))
assert {path.name for path in bundled.iterdir() if path.name.endswith(".json")} == {path.name for path in expected_schemas}
for path in expected_schemas:
    assert bundled.joinpath(path.name).read_bytes() == path.read_bytes(), path.name
for path in sorted((ROOT / "fixtures/valid").glob("*.json")):
    assert package.validate(json.loads(path.read_text())) == [], path.name
fixture = json.loads((ROOT / "fixtures/valid/order.json").read_text())
assert package.validate(fixture) == []
with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "consumer.json"
    path.write_text(json.dumps(fixture))
    for operation in ("validate", "digest"):
        result = subprocess.run([sys.executable, "-m", "institutional_event_schema", operation,
                                 str(path), "--json"], cwd=directory,
                                capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["valid"], report
        if operation == "digest":
            expected = "sha256:" + hashlib.sha256(json.dumps(fixture, sort_keys=True,
                separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
            assert report["result"] == expected
    path.write_text('{"x":1,"x":2}')
    result = subprocess.run([sys.executable, "-m", "institutional_event_schema", "digest",
                             str(path), "--json"], cwd=directory, capture_output=True, text=True)
    assert result.returncode == 1
    assert json.loads(result.stdout)["diagnostics"][0]["code"] == "input.duplicate_key"
assert not any(name == "amanah_alpha" or name.startswith("amanah_alpha.") for name in sys.modules)
print("PASS: installed library, bundled schemas, valid input, digest and strict rejection outside checkout")
