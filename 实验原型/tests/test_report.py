import json
from pathlib import Path
import tempfile
import unittest
from gpsmap.report import write_report


class ReportTests(unittest.TestCase):
    def test_partial_report_does_not_claim_complete_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            (dest / "suite_run.json").write_text(json.dumps({"datasets": 1, "all_planned_datasets_in_input_were_run": False}))
            write_report(dest, [])
            content = (dest / "实验结果.md").read_text()
            self.assertIn("本次运行 1 条轨迹", content)
            self.assertIn("不代表完整预设套件", content)
            self.assertNotIn("全部预设路线和种子保留", content)

    def test_full_input_scope_does_not_claim_unseen_scenarios(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            (dest / "suite_run.json").write_text(json.dumps({"datasets": 7, "all_planned_datasets_in_input_were_run": True}))
            write_report(dest, [])
            self.assertIn("未筛选输入数据集目录中的轨迹", (dest / "实验结果.md").read_text())


if __name__ == "__main__":
    unittest.main()
