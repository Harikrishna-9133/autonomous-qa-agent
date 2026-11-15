
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4
import ipaddress
import socket

from playwright.sync_api import sync_playwright


SCREENSHOT_DIR = Path(__file__).resolve().parents[3] / "screenshots"

EXPECTED_NAVIGATION = [
    "About",
    "Experience",
    "Projects",
    "Skills",
    "Notes",
    "Contact"
]


def validate_url(url: str):
    if not isinstance(url, str) or not url:
        raise ValueError("A valid website URL is required")

    if url != url.strip() or any(ord(char) < 32 for char in url):
        raise ValueError("URL contains invalid whitespace or control characters")

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise ValueError("Invalid website URL")

    if parsed.scheme not in ("http", "https") or not hostname:
        raise ValueError("Only valid HTTP and HTTPS URLs are allowed")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed")

    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Invalid website port")

    hostname = hostname.rstrip(".").lower()

    if (
        hostname == "localhost"
        or hostname.endswith(".localhost")
        or hostname.endswith(".local")
        or hostname.endswith(".internal")
    ):
        raise ValueError("Local or internal hostnames are not allowed")

    try:
        addresses = socket.getaddrinfo(
            hostname,
            port,
            type=socket.SOCK_STREAM
        )

        if not addresses:
            raise ValueError("Website hostname could not be resolved")

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])

            if not ip.is_global:
                raise ValueError(
                    "Private or local network addresses are not allowed"
                )

    except socket.gaierror:
        raise ValueError("Website hostname could not be resolved")
    except OSError:
        raise ValueError("Unable to validate website hostname")

def guard_browser_request(route):
    request_url = route.request.url

    try:
        validate_url(request_url)
    except (ValueError, OSError):
        route.abort()
        return

    route.continue_()


def install_browser_request_guard(context):
    context.route("**/*", guard_browser_request)


def run_homepage_test(url: str, run_id: int):
    validate_url(url)

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    screenshot_file = SCREENSHOT_DIR / (
        f"run_{run_id}_{uuid4().hex[:8]}.png"
    )

    checks = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            context = browser.new_context(
            viewport={"width": 1366, "height": 768}
)

            install_browser_request_guard(context)

            page = context.new_page()

            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            page_title = page.title()
            status_code = response.status if response else None

            # Check 1: Homepage HTTP response
            homepage_passed = (
                status_code is not None
                and 200 <= status_code < 400
            )

            checks.append({
                "name": "Homepage loading",
                "passed": homepage_passed,
                "details": f"HTTP status: {status_code}"
            })

            # Check 2: Navigation links
            missing_navigation = []

            for label in EXPECTED_NAVIGATION:
                links = page.get_by_role(
                    "link",
                    name=label,
                    exact=False
                )

                visible = any(
                    links.nth(i).is_visible()
                    for i in range(links.count())
                )

                if not visible:
                    missing_navigation.append(label)

            navigation_passed = len(missing_navigation) == 0

            checks.append({
                "name": "Portfolio navigation",
                "passed": navigation_passed,
                "details": (
                    "All expected navigation links are visible"
                    if navigation_passed
                    else f"Missing links: {missing_navigation}"
                )
            })

            # Check 3: Introduction and professional role
            body_text = page.locator("body").inner_text().lower()

            name_found = "hari krishna digiventi" in body_text

            role_found = (
                "ai engineer" in body_text
                or "software engineer" in body_text
            )

            introduction_passed = name_found and role_found

            checks.append({
                "name": "Portfolio introduction",
                "passed": introduction_passed,
                "details": {
                    "name_found": name_found,
                    "professional_role_found": role_found
                }
            })

            page.screenshot(
                path=str(screenshot_file),
                full_page=True
            )

            total_passed = sum(
                check["passed"] for check in checks
            )

            all_passed = total_passed == len(checks)

            return {
                "url": url,
                "title": page_title,
                "status_code": status_code,
                "passed": all_passed,
                "actual_result": (
                    f"{total_passed} of {len(checks)} checks passed"
                ),
                "error_message": None if all_passed else (
                    "One or more portfolio checks failed"
                ),
                "checks": checks,
                "screenshot_path": str(screenshot_file)
            }

        finally:
            browser.close()
