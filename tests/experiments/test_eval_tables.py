import tempfile
import unittest
from pathlib import Path

from experiments.augmented_llm_experiments.eval_tables import write_eval_tables


def record(phase, case, variant, passed):
    return {
        "model_id": "sample",
        "phase": phase,
        "case_id": case,
        "variant": variant,
        "score": {"pass": passed},
    }


class EvaluationTableTests(unittest.TestCase):
    def test_create_human_table(self):
        """Create unreviewed cells only for experiments that were run."""

        records = [
            record("selection", "greeting", "branch", True),
            record("answer", "summary", "branch", False),
            record("answer", "summary", "followup", True),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_eval_tables(records, root)
            content = (root / "sample" / "eval_table.md").read_text()
        auto, human = content.split("## Human evaluation", 1)
        self.assertIn(
            "| selection : greeting | [✅ PASS](branch.md#selection-greeting-pass) | — |",
            auto,
        )
        self.assertIn(
            "| answer : summary | [❌ FAILED](branch.md#answer-summary-fail) | [✅ PASS](followup.md#answer-summary-pass) |",
            auto,
        )
        self.assertIn(
            "| selection : greeting | [⬜](branch.md#selection-greeting-pass) | — |",
            human,
        )
        self.assertIn(
            "| answer : summary | [⬜](branch.md#answer-summary-fail) | [⬜](followup.md#answer-summary-pass) |",
            human,
        )

    def test_preserve_human_review_when_regenerated(self):
        """Keep user ratings and notes while updating automatic results."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = [record("selection", "greeting", "branch", True)]
            write_eval_tables(records, root)
            path = root / "sample" / "eval_table.md"
            content = path.read_text().replace("[⬜]", "[✅ PASS]")
            content += "My review: clear and correct.\n"
            path.write_text(content)
            records[0]["score"]["pass"] = False
            write_eval_tables(records, root)
            auto, human = path.read_text().split("## Human evaluation", 1)
            self.assertIn("[❌ FAILED](branch.md#selection-greeting-fail)", auto)
            self.assertIn("[✅ PASS](branch.md#selection-greeting-fail)", human)
            self.assertIn("My review: clear and correct.", human)

    def test_migrate_existing_human_table(self):
        """Retain human ratings and notes when combining the old columns."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "sample" / "eval_table.md"
            path.parent.mkdir()
            path.write_text(
                "# Previous table\n\n<!-- human-evaluation -->\n\n## Human evaluation\n\n"
                "| Experiment type | Case | [branch](branch.md) |\n"
                "| --- | --- | --- |\n"
                "| selection | greeting | ✅ PASS |\n\n"
                "### Review notes\n\nMy note.\n\n| A | B |\n| --- | --- |\n| x | y |\n"
            )
            write_eval_tables([record("selection", "greeting", "branch", False)], root)
            human = path.read_text().split("## Human evaluation", 1)[1]
            self.assertIn(
                "| selection : greeting | [✅ PASS](branch.md#selection-greeting-fail) |",
                human,
            )
            self.assertIn("My note.\n\n| A | B |\n| --- | --- |\n| x | y |", human)


if __name__ == "__main__":
    unittest.main()
