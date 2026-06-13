import unittest

import main


class LovartVideoResolutionTests(unittest.TestCase):
    def test_preserves_480p_resolution_preference(self):
        self.assertEqual("480p", main.lovart_video_resolution_preference("480p"))
        self.assertEqual("480p", main.lovart_video_resolution_preference("480"))

    def test_480p_prompt_requests_low_cost_tier(self):
        payload = main.CanvasVideoRequest(
            prompt="A woman holding a weapon stands on a cliff.",
            resolution="480p",
        )

        prompt = main.lovart_video_prompt(payload)

        self.assertIn("480P low-cost video tier", prompt)
        self.assertIn("Do not generate 720P or 1080P", prompt)


if __name__ == "__main__":
    unittest.main()
