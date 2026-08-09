from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generators.generate_synthetic_fixtures import (  # noqa: E402
    GENERATOR_VERSION,
    SOURCE_SYSTEM,
    write_corpus,
)
from scripts.validate_fixtures import build_validator, file_bytes, load_json  # noqa: E402


class GeneratorTests(unittest.TestCase):
    def test_same_seed_is_byte_for_byte_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            write_corpus(Path(first), 71)
            write_corpus(Path(second), 71)
            self.assertEqual(file_bytes(Path(first)), file_bytes(Path(second)))

    def test_different_seeds_change_controlled_values(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            write_corpus(Path(first), 71)
            write_corpus(Path(second), 72)
            first_files = file_bytes(Path(first))
            second_files = file_bytes(Path(second))
            self.assertEqual(first_files.keys(), second_files.keys())
            self.assertNotEqual(first_files, second_files)

    def test_generated_corpus_is_small_synthetic_and_schema_valid(self) -> None:
        validator = build_validator()
        with tempfile.TemporaryDirectory() as output:
            output_path = Path(output)
            write_corpus(output_path, 71)
            paths = sorted(output_path.rglob("*.json"))
            self.assertEqual(17, len(paths))
            for path in paths:
                with self.subTest(path=path.relative_to(output_path).as_posix()):
                    record = load_json(path)
                    validator.validate(record)
                    self.assertEqual(SOURCE_SYSTEM, record["source"]["source_system"])
                    self.assertTrue(record["source"]["source_record_id"].startswith("src-"))
                    self.assertTrue(record["occurred_at"].startswith("2025-01-15T"))

    def test_generator_has_no_network_or_system_clock_dependency(self) -> None:
        generator_path = ROOT / "generators" / "generate_synthetic_fixtures.py"
        tree = ast.parse(generator_path.read_text(encoding="utf-8"))
        imports = {
            node.names[0].name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
        }
        imports.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertTrue({"socket", "urllib", "requests", "faker", "time"}.isdisjoint(imports))
        clock_calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"now", "utcnow", "today", "time"}
        }
        self.assertEqual(set(), clock_calls)
        self.assertEqual("1.0.0", GENERATOR_VERSION)


if __name__ == "__main__":
    unittest.main()
