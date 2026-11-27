import os
from io import BytesIO
from pathlib import Path
from unittest import skipUnless

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from PIL import Image, ImageChops

RUN_BROWSER_TESTS = os.environ.get("RUN_BROWSER_TESTS") == "1"
UPDATE_VISUAL_BASELINES = os.environ.get("UPDATE_VISUAL_BASELINES") == "1"
if RUN_BROWSER_TESTS:
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
SNAPSHOT_PATH = Path(__file__).parent / "snapshots/admin-login.png"
DIAGNOSTICS_PATH = Path("/tmp/wasla-visual-regressions")
PIXEL_DIFFERENCE_THRESHOLD = 16
MAX_DIFFERENT_PIXEL_RATIO = 0.01


@skipUnless(RUN_BROWSER_TESTS, "Set RUN_BROWSER_TESTS=1 to run browser tests.")
class AdminLoginVisualRegressionTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright

        super().setUpClass()
        cls.playwright = sync_playwright().start()
        launch_options = {"headless": True}
        executable_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
        if executable_path:
            launch_options["executable_path"] = executable_path
        cls.browser = cls.playwright.chromium.launch(**launch_options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def test_admin_login_matches_visual_baseline(self):
        context = self.browser.new_context(
            color_scheme="light",
            device_scale_factor=1,
            locale="en-US",
            reduced_motion="reduce",
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        console_errors = []
        page_errors = []
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text) if message.type == "error" else None
            ),
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        try:
            response = page.goto(
                f"{self.live_server_url}/admin/login/?next=/admin/",
                wait_until="networkidle",
            )
            self.assertIsNotNone(response)
            self.assertEqual(response.status, 200)
            self.assertTrue(page.locator('input[name="username"]').is_visible())
            self.assertTrue(page.locator('input[name="password"]').is_visible())
            self.assertTrue(page.get_by_role("button").is_visible())

            screenshot = page.screenshot(
                animations="disabled",
                caret="hide",
                full_page=False,
                scale="css",
            )
        finally:
            context.close()

        self.assertEqual(console_errors, [])
        self.assertEqual(page_errors, [])

        if UPDATE_VISUAL_BASELINES:
            SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
            SNAPSHOT_PATH.write_bytes(screenshot)
            return

        self.assertTrue(
            SNAPSHOT_PATH.is_file(),
            "Visual baseline is missing. Run with UPDATE_VISUAL_BASELINES=1.",
        )
        baseline = Image.open(SNAPSHOT_PATH).convert("RGB")
        actual = Image.open(BytesIO(screenshot)).convert("RGB")
        self.assertEqual(actual.size, baseline.size)

        difference = ImageChops.difference(actual, baseline)
        red, green, blue = difference.split()
        maximum_difference = ImageChops.lighter(red, ImageChops.lighter(green, blue))
        histogram = maximum_difference.histogram()
        different_pixels = sum(histogram[PIXEL_DIFFERENCE_THRESHOLD + 1 :])
        different_pixel_ratio = different_pixels / (actual.width * actual.height)

        if different_pixel_ratio > MAX_DIFFERENT_PIXEL_RATIO:
            DIAGNOSTICS_PATH.mkdir(parents=True, exist_ok=True)
            actual.save(DIAGNOSTICS_PATH / "admin-login-actual.png")
            maximum_difference.save(DIAGNOSTICS_PATH / "admin-login-diff.png")

        self.assertLessEqual(
            different_pixel_ratio,
            MAX_DIFFERENT_PIXEL_RATIO,
            f"Admin login visual difference was {different_pixel_ratio:.2%}.",
        )
