from pathlib import Path
import unittest


class GithubSyncButtonTests(unittest.TestCase):
    def test_home_sidebar_has_persistent_github_sync_button(self):
        html = Path("static/index.html").read_text(encoding="utf-8")

        self.assertIn('id="github-sync-btn"', html)
        self.assertIn('onclick="runProjectUpdate()"', html)
        self.assertIn('aria-label="GitHub 一键同步"', html)
        self.assertIn('title="GitHub 一键同步"', html)
        self.assertIn('class="github-mark"', html)
        self.assertIn('data-i18n="update.githubSync"', html)


if __name__ == "__main__":
    unittest.main()
