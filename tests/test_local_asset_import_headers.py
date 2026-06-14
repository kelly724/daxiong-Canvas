import unittest

import main


class LocalAssetImportHeaderTests(unittest.TestCase):
    def test_remote_asset_headers_include_page_origin_context(self):
        headers = main.local_asset_remote_request_headers("https://example.com/gallery/page?item=1")

        self.assertEqual("https://example.com/gallery/page?item=1", headers["Referer"])
        self.assertEqual("https://example.com", headers["Origin"])
        self.assertIn("image/", headers["Accept"])
        self.assertIn("Mozilla/", headers["User-Agent"])


if __name__ == "__main__":
    unittest.main()
