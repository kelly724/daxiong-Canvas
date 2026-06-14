import asyncio
import os
import unittest
import uuid
from unittest.mock import patch

import main


class CodexCliStallTimeoutTests(unittest.TestCase):
    def run_status_check(self, task_id, output_root, task, now_seconds, stopped):
        old_output_dir = main.OUTPUT_DIR
        old_tasks = dict(main.CODEX_CLI_TASKS)
        main.OUTPUT_DIR = output_root
        main.CODEX_CLI_TASKS.clear()
        main.CODEX_CLI_TASKS[task_id] = task
        try:
            with patch.object(main.time, "time", return_value=now_seconds):
                with patch.object(main, "codex_cli_stop_process", side_effect=lambda pid: stopped.append(pid)):
                    return asyncio.run(main.codex_cli_imagegen_status(task_id))
        finally:
            main.OUTPUT_DIR = old_output_dir
            main.CODEX_CLI_TASKS.clear()
            main.CODEX_CLI_TASKS.update(old_tasks)

    def test_status_fails_and_stops_running_task_after_five_minutes_without_output(self):
        output_root = os.path.join(main.BASE_DIR, "output", "_test_codex_cli_stall", uuid.uuid4().hex)
        task_id = "codex_img_stalled"
        task_dir = os.path.join(output_root, "codex-imagegen", task_id)
        stderr_path = os.path.join(task_dir, "stderr.log")
        os.makedirs(task_dir, exist_ok=True)
        with open(stderr_path, "w", encoding="utf-8") as f:
            f.write("started\n")

        now_seconds = 1_800_000_000
        stale_seconds = now_seconds - 301
        os.utime(stderr_path, (stale_seconds, stale_seconds))

        stopped = []
        result = self.run_status_check(task_id, output_root, {
            "success": True,
            "task_id": task_id,
            "status": "running",
            "images": [],
            "error": "",
            "pid": 12345,
            "started_at": int((now_seconds - 600) * 1000),
        }, now_seconds, stopped)

        self.assertEqual("failed", result["status"])
        self.assertIn("5", result["error"])
        self.assertIn(12345, stopped)

    def test_status_fails_running_task_after_five_minutes_even_when_logs_keep_updating(self):
        output_root = os.path.join(main.BASE_DIR, "output", "_test_codex_cli_stall", uuid.uuid4().hex)
        task_id = "codex_img_runtime"
        task_dir = os.path.join(output_root, "codex-imagegen", task_id)
        stderr_path = os.path.join(task_dir, "stderr.log")
        os.makedirs(task_dir, exist_ok=True)
        with open(stderr_path, "w", encoding="utf-8") as f:
            f.write("still thinking\n")

        now_seconds = 1_800_000_000
        os.utime(stderr_path, (now_seconds, now_seconds))

        stopped = []
        result = self.run_status_check(task_id, output_root, {
            "success": True,
            "task_id": task_id,
            "status": "running",
            "images": [],
            "error": "",
            "pid": 23456,
            "started_at": int((now_seconds - 301) * 1000),
        }, now_seconds, stopped)

        self.assertEqual("failed", result["status"])
        self.assertIn("5", result["error"])
        self.assertIn("runtime", result["error"].lower())
        self.assertIn(23456, stopped)

    def test_status_fails_running_task_when_safety_refusal_appears_in_logs(self):
        output_root = os.path.join(main.BASE_DIR, "output", "_test_codex_cli_stall", uuid.uuid4().hex)
        task_id = "codex_img_refused"
        task_dir = os.path.join(output_root, "codex-imagegen", task_id)
        stderr_path = os.path.join(task_dir, "stderr.log")
        os.makedirs(task_dir, exist_ok=True)
        with open(stderr_path, "w", encoding="utf-8") as f:
            f.write("图片安全系统拒绝了该提示，将继续尝试\n")

        now_seconds = 1_800_000_000
        os.utime(stderr_path, (now_seconds, now_seconds))

        stopped = []
        result = self.run_status_check(task_id, output_root, {
            "success": True,
            "task_id": task_id,
            "status": "running",
            "images": [],
            "error": "",
            "pid": 34567,
            "started_at": int((now_seconds - 60) * 1000),
        }, now_seconds, stopped)

        self.assertEqual("failed", result["status"])
        self.assertIn("safety", result["error"].lower())
        self.assertIn(34567, stopped)


if __name__ == "__main__":
    unittest.main()
