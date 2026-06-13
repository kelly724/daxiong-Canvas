import os
import unittest
import uuid

import main


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?"
    b"\x00\x05\xfe\x02\xfeA\xe2'5\x00\x00\x00\x00IEND\xaeB`\x82"
)


class CodexCliImageHarvestTests(unittest.TestCase):
    def with_codex_paths(self, output_root, generated_root, callback):
        old_output_dir = main.OUTPUT_DIR
        old_roots = getattr(main, "CODEX_CLI_EXTERNAL_IMAGE_ROOTS", None)
        main.OUTPUT_DIR = output_root
        main.CODEX_CLI_EXTERNAL_IMAGE_ROOTS = [generated_root]
        try:
            return callback()
        finally:
            main.OUTPUT_DIR = old_output_dir
            if old_roots is None:
                try:
                    delattr(main, "CODEX_CLI_EXTERNAL_IMAGE_ROOTS")
                except AttributeError:
                    pass
            else:
                main.CODEX_CLI_EXTERNAL_IMAGE_ROOTS = old_roots

    def test_harvest_copies_only_codex_generated_images_from_result_message(self):
        root = os.path.join(main.BASE_DIR, "output", "_test_codex_cli", uuid.uuid4().hex)
        generated_root = os.path.join(root, "codex-cache", "generated_images")
        unsafe_root = os.path.join(root, "private-pictures")
        output_root = os.path.join(root, "project-output")
        safe_source = os.path.join(generated_root, "run-1", "safe.png")
        unsafe_source = os.path.join(unsafe_root, "private.png")
        task_id = "codex_img_test"
        task_dir = os.path.join(output_root, "codex-imagegen", task_id)

        os.makedirs(os.path.dirname(safe_source), exist_ok=True)
        os.makedirs(os.path.dirname(unsafe_source), exist_ok=True)
        os.makedirs(task_dir, exist_ok=True)
        with open(safe_source, "wb") as f:
            f.write(PNG_BYTES)
        with open(unsafe_source, "wb") as f:
            f.write(PNG_BYTES)
        with open(os.path.join(task_dir, "result_message.txt"), "w", encoding="utf-8") as f:
            f.write(
                "saved: "
                f"`{safe_source}` "
                "ignore this unrelated local image: "
                f"`{unsafe_source}`"
            )

        images = self.with_codex_paths(
            output_root,
            generated_root,
            lambda: main.codex_cli_harvest_external_images(task_id),
        )

        self.assertEqual(1, len(images))
        self.assertEqual("codex-output-1.png", os.path.basename(images[0]["localPath"]))
        self.assertTrue(os.path.isfile(images[0]["localPath"]))
        with open(images[0]["localPath"], "rb") as f:
            self.assertEqual(PNG_BYTES, f.read())

    def test_harvest_recovers_images_from_running_codex_session_directory(self):
        root = os.path.join(main.BASE_DIR, "output", "_test_codex_cli", uuid.uuid4().hex)
        generated_root = os.path.join(root, "codex-cache", "generated_images")
        output_root = os.path.join(root, "project-output")
        session_id = "019ebf72-c947-73d3-ab98-9927aa7e0429"
        source = os.path.join(generated_root, session_id, "generated.png")
        task_id = "codex_img_running"
        task_dir = os.path.join(output_root, "codex-imagegen", task_id)

        os.makedirs(os.path.dirname(source), exist_ok=True)
        os.makedirs(task_dir, exist_ok=True)
        with open(source, "wb") as f:
            f.write(PNG_BYTES)
        with open(os.path.join(task_dir, "stderr.log"), "w", encoding="utf-8") as f:
            f.write(f"session id: {session_id}\n")

        images = self.with_codex_paths(
            output_root,
            generated_root,
            lambda: main.codex_cli_harvest_external_images(task_id),
        )

        self.assertEqual(1, len(images))
        self.assertEqual("codex-output-1.png", os.path.basename(images[0]["localPath"]))
        with open(images[0]["localPath"], "rb") as f:
            self.assertEqual(PNG_BYTES, f.read())


if __name__ == "__main__":
    unittest.main()
