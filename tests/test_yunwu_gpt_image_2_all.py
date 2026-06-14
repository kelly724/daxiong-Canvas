import asyncio
import os
import unittest
from unittest.mock import patch

from PIL import Image

import main


class FakeImageResponse:
    status_code = 200
    text = '{"data":[{"url":"https://example.com/generated.png"}]}'

    def raise_for_status(self):
        return None

    def json(self):
        return {"created": 1, "data": [{"url": "https://example.com/generated.png"}]}


class RecordingAsyncClient:
    calls = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return FakeImageResponse()


class YunwuGptImage2AllTests(unittest.TestCase):
    def setUp(self):
        RecordingAsyncClient.calls = []
        os.makedirs(main.OUTPUT_OUTPUT_DIR, exist_ok=True)
        self.ref_name = "yunwu_gpt2_ref.png"
        self.ref_path = os.path.join(main.OUTPUT_OUTPUT_DIR, self.ref_name)
        Image.new("RGB", (8, 8), (255, 0, 0)).save(self.ref_path)

    def test_yunwu_gpt_image_2_all_reference_images_use_generations_json(self):
        async def fake_upload(ref_url):
            return {"url": f"https://temp.example/{os.path.basename(ref_url)}"}

        with patch.object(main.httpx, "AsyncClient", RecordingAsyncClient):
            with patch.object(main, "upload_local_image_to_cloud", side_effect=fake_upload):
                image, raw = asyncio.run(
                    main.generate_ai_image(
                        "将他们合并在一起",
                        "1024x1024",
                        "auto",
                        "gpt-image-2-all",
                        reference_images=[{"url": f"/assets/output/{self.ref_name}", "name": self.ref_name}],
                        provider_id="custom-api",
                    )
                )

        self.assertEqual("https://example.com/generated.png", image["value"])
        self.assertEqual(1, len(RecordingAsyncClient.calls))
        call = RecordingAsyncClient.calls[0]
        self.assertEqual("https://yunwu.ai/v1/images/generations", call["url"])
        self.assertNotIn("files", call)
        self.assertEqual("gpt-image-2-all", call["json"]["model"])
        self.assertEqual(["https://temp.example/yunwu_gpt2_ref.png"], call["json"]["image"])
        self.assertEqual(1, call["json"]["n"])
        self.assertNotIn("extra_body", call["json"])
        self.assertEqual({"created": 1, "data": [{"url": "https://example.com/generated.png"}]}, raw)

    def test_yunwu_gpt_image_2_all_remote_reference_images_pass_through(self):
        with patch.object(main.httpx, "AsyncClient", RecordingAsyncClient):
            image, raw = asyncio.run(
                main.generate_ai_image(
                    "将他们合并在一起",
                    "1024x1024",
                    "auto",
                    "gpt-image-2-all",
                    reference_images=[{"url": "https://cdn.example/ref.png", "name": "ref.png"}],
                    provider_id="custom-api",
                )
            )

        self.assertEqual("https://example.com/generated.png", image["value"])
        self.assertEqual(1, len(RecordingAsyncClient.calls))
        call = RecordingAsyncClient.calls[0]
        self.assertEqual("https://yunwu.ai/v1/images/generations", call["url"])
        self.assertNotIn("files", call)
        self.assertEqual("gpt-image-2-all", call["json"]["model"])
        self.assertEqual(["https://cdn.example/ref.png"], call["json"]["image"])
        self.assertEqual(1, call["json"]["n"])
        self.assertNotIn("extra_body", call["json"])
        self.assertEqual({"created": 1, "data": [{"url": "https://example.com/generated.png"}]}, raw)


if __name__ == "__main__":
    unittest.main()
