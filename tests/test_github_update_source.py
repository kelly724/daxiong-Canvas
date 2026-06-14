import unittest

import main


class GithubUpdateSourceTests(unittest.TestCase):
    def test_update_source_uses_daxiong_canvas_main_branch(self):
        repo = "yzhe3778-ai/daxiong-Canvas"

        self.assertEqual(f"https://github.com/{repo}", main.GITHUB_REPO_URL)
        self.assertEqual(f"https://raw.githubusercontent.com/{repo}/main/VERSION", main.GITHUB_VERSION_URL)
        self.assertEqual(
            f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1",
            main.GITHUB_TREE_URL,
        )
        self.assertEqual(f"https://raw.githubusercontent.com/{repo}/main", main.GITHUB_RAW_ROOT)
        self.assertEqual(
            f"https://raw.githubusercontent.com/{repo}/main/static/update-notes.json",
            main.GITHUB_UPDATE_NOTES_URL,
        )


if __name__ == "__main__":
    unittest.main()
