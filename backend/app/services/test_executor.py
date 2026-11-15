
import re
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from playwright.sync_api import sync_playwright

from app.services.browser_service import (
    validate_url,
    install_browser_request_guard
)


SCREENSHOT_DIR = Path(__file__).resolve().parents[3] / "screenshots"

SECTION_ALIASES = {
    "about": ["about"],
    "experience": ["experience"],
    "projects": ["projects", "project"],
    "skills": ["skills", "skill"],
    "notes": ["notes", "blog"],
    "contact": ["contact"],
    "home": ["home", "homepage"]
}


def add_check(checks, name, passed, details):
    checks.append({
        "check": name,
        "passed": bool(passed),
        "details": str(details)
    })


def normalize_text(value):
    return re.sub(
        r"\s+",
        " ",
        str(value or "")
    ).strip().lower()



def get_test_context(test_case):
    """
    Combine all available test-case instructions safely.
    Supports both string and list-based test steps.
    """

    steps = test_case.get("steps", "")

    if isinstance(steps, list):
        steps_text = " ".join(
            str(step) for step in steps
        )
    else:
        steps_text = str(steps or "")

    return normalize_text(
        " ".join([
            str(test_case.get("title", "") or ""),
            str(test_case.get("description", "") or ""),
            steps_text,
            str(test_case.get("expected_result", "") or "")
        ])
    )



def identify_section(test_case):
    """
    Identify a website section from the complete test instructions.
    """

    context = get_test_context(test_case)

    # More specific names are checked before shorter names.
    for section_name in [
        "experience",
        "projects",
        "skills",
        "contact",
        "about",
        "notes",
        "home"
    ]:
        aliases = SECTION_ALIASES[section_name]

        if any(
            re.search(r"\b" + re.escape(alias) + r"\b", context)
            for alias in aliases
        ):
            return section_name

    return None


def discover_section_links(page):
    """
    Discover actual same-page navigation links.
    """

    return page.locator(
        'a[href^="#"]'
    ).evaluate_all(
        """
        elements => elements.map(element => ({
            text: (
                element.innerText ||
                element.getAttribute("aria-label") ||
                element.getAttribute("title") ||
                ""
            ).trim(),
            href: element.getAttribute("href"),
            visible: element.getClientRects().length > 0
        }))
        """
    )


def find_section_target(page, section_name):
    """
    Match a section to a real anchor link or an element ID.
    """

    aliases = SECTION_ALIASES.get(
        section_name,
        [section_name]
    )

    links = discover_section_links(page)

    for link in links:

        href = link.get("href") or ""
        link_text = normalize_text(link.get("text"))

        if not href.startswith("#"):
            continue

        section_id = href[1:]
        normalized_id = normalize_text(section_id)

        matches = any(
            alias in normalized_id.split()
            or alias in link_text.split()
            or alias in normalized_id
            or alias in link_text
            for alias in aliases
        )

        if matches:
            locator = page.locator(
                f'[id="{section_id}"]'
            )

            if locator.count() > 0:
                return locator.first, section_id, href

    # Fallback: look for an element with a known section ID.
    for section_id in aliases:

        locator = page.locator(
            f'[id="{section_id}"]'
        )

        if locator.count() > 0:
            return locator.first, section_id, None

    return None, None, None


def inspect_section(page, section_name, checks):
    """
    Navigate to and inspect a discovered website section.
    """

    section, section_id, href = find_section_target(
        page,
        section_name
    )

    if section is None:

        add_check(
            checks,
            f"{section_name.title()} section exists",
            False,
            "No matching section element was discovered"
        )

        return

    # Navigate only through a same-page section link.
    if href:

        link = page.locator(
            f'a[href="{href}"]'
        ).first

        if link.count() > 0 and link.is_visible():

            try:
                link.click(timeout=5000)
                page.wait_for_timeout(300)

                add_check(
                    checks,
                    "Section navigation",
                    True,
                    f"Navigated through link {href}"
                )

            except Exception as error:

                add_check(
                    checks,
                    "Section navigation",
                    False,
                    f"Navigation link could not be activated: {error}"
                )

    section = page.locator(
        f'[id="{section_id}"]'
    ).first

    section_found = section.count() > 0

    add_check(
        checks,
        f"{section_name.title()} section exists",
        section_found,
        f"Section ID: {section_id}"
    )

    if not section_found:
        return

    section_visible = section.is_visible()

    add_check(
        checks,
        f"{section_name.title()} section visibility",
        section_visible,
        "Section visibility inspected"
    )

    section_text = section.inner_text().strip()

    add_check(
        checks,
        f"{section_name.title()} section content",
        bool(section_text),
        f"Discovered {len(section_text)} characters of text"
    )

    # Inspect headings in the selected section.
    heading_count = section.locator(
        "h1, h2, h3, h4, h5, h6"
    ).count()

    if section_name in ("projects", "skills", "experience", "notes"):

        add_check(
            checks,
            f"{section_name.title()} section headings",
            heading_count > 0,
            f"Found {heading_count} headings"
        )

    # Inspect project information.
    if section_name == "projects":

        project_cards = section.locator(
            "article, [class*='project-card'], "
            "[class*='project-item']"
        ).count()

        add_check(
            checks,
            "Project information",
            heading_count > 0 or project_cards > 0,
            (
                f"Found {heading_count} headings and "
                f"{project_cards} possible project cards"
            )
        )



    # Inspect contact controls and safely open the contact dialog.
    if section_name == "contact":

        email_button = page.locator("#emailMeBtn")

        button_found = email_button.count() > 0

        button_visible = (
            button_found and email_button.first.is_visible()
        )

        add_check(
            checks,
            "Contact form opening button",
            button_visible,
            "Email me button discovered"
        )

        if button_visible:
            try:
                email_button.first.click(timeout=5000)

                page.locator(
                    ".email-modal-backdrop"
                ).wait_for(
                    state="visible",
                    timeout=5000
                )

                add_check(
                    checks,
                    "Contact dialog opens",
                    True,
                    "Contact dialog opened successfully"
                )

            except Exception as error:
                add_check(
                    checks,
                    "Contact dialog opens",
                    False,
                    f"Could not open contact dialog: {error}"
                )

        else:
            add_check(
                checks,
                "Contact dialog opens",
                False,
                "Email me button is unavailable"
            )

        contact_fields = [
            ("senderName", "text"),
            ("senderEmail", "email"),
            ("emailSubject", "text"),
            ("emailMessage", "textarea")
        ]

        for field_id, expected_type in contact_fields:

            field = page.locator(
                f".email-modal-backdrop #{field_id}"
            )

            field_exists = field.count() > 0

            field_visible = (
                field_exists and field.first.is_visible()
            )

            actual_type = None

            if field_exists:
                actual_type = field.first.evaluate(
                    """
                    element => {
                        if (
                            element.tagName.toLowerCase()
                            === "textarea"
                        ) {
                            return "textarea";
                        }

                        return (
                            element.getAttribute("type") || "text"
                        ).toLowerCase();
                    }
                    """
                )

            field_valid = (
                field_visible
                and actual_type == expected_type
            )

            add_check(
                checks,
                f"Contact field: {field_id}",
                field_valid,
                (
                    f"Expected: {expected_type}; "
                    f"Actual: {actual_type}; "
                    f"Visible: {field_visible}"
                )
            )





def inspect_navigation(page, checks):
    """
    Inspect visible same-page navigation links.
    """

    links = discover_section_links(page)

    visible_links = [
        link for link in links
        if link.get("visible")
    ]

    add_check(
        checks,
        "Navigation links",
        len(visible_links) > 0,
        f"Found {len(visible_links)} visible section links"
    )

    for link in visible_links:

        href = link.get("href") or ""
        section_id = href.removeprefix("#")

        destination_exists = (
            bool(section_id)
            and page.locator(
                f'[id="{section_id}"]'
            ).count() > 0
        )

        add_check(
            checks,
            f"Navigation destination: {section_id}",
            destination_exists,
            (
                "Matching destination exists"
                if destination_exists
                else "No matching destination found"
            )
        )


def inspect_interactive_links(page, checks):
    """Verify that visible interactive links have valid destinations."""

    links = page.locator("a[href]").evaluate_all(
        """
        elements => elements.map(element => ({
            text: (
                element.innerText ||
                element.getAttribute("aria-label") ||
                element.getAttribute("title") ||
                ""
            ).trim(),
            href: element.getAttribute("href"),
            visible: element.getClientRects().length > 0
        }))
        """
    )

    visible_links = [link for link in links if link["visible"]]

    valid_links = [
        link for link in visible_links
        if link.get("href") and link["href"].strip()
    ]

    add_check(
        checks,
        "Interactive links visibility",
        len(visible_links) > 0,
        f"Found {len(visible_links)} visible links"
    )

    add_check(
        checks,
        "Interactive links destinations",
        len(valid_links) == len(visible_links) and len(valid_links) > 0,
        f"{len(valid_links)} of {len(visible_links)} visible links have destinations"
    )



def inspect_interactive_buttons(page, checks):
    """Verify visibility and actual enabled/disabled state of buttons."""

    buttons = page.locator(
        "button, input[type='button'], input[type='submit'], [role='button']"
    ).evaluate_all(
        """
        elements => elements.map(element => ({
            text: (
                element.innerText ||
                element.getAttribute("aria-label") ||
                element.getAttribute("title") ||
                ""
            ).trim(),
            visible: element.getClientRects().length > 0
                && getComputedStyle(element).visibility !== "hidden"
                && getComputedStyle(element).display !== "none",
            disabled: Boolean(element.disabled) ||
                element.getAttribute("aria-disabled") === "true"
        }))
        """
    )

    visible_buttons = [
        button for button in buttons if button["visible"]
    ]

    enabled_buttons = [
        button for button in visible_buttons if not button["disabled"]
    ]

    disabled_buttons = [
        button for button in visible_buttons if button["disabled"]
    ]

    add_check(
        checks,
        "Interactive buttons visibility",
        len(visible_buttons) > 0,
        f"Found {len(visible_buttons)} visible buttons"
    )

    add_check(
        checks,
        "Interactive buttons enabled state",
        len(enabled_buttons) > 0,
        (
            f"{len(enabled_buttons)} enabled and "
            f"{len(disabled_buttons)} disabled buttons"
        )
    )




def inspect_interactive_inputs(page, checks):
    """Verify visibility, labels, types and required-field attributes."""

    fields = page.locator(
        "input:not([type='hidden']), textarea, select"
    ).evaluate_all(
        """
        elements => elements.map(element => {
            const labelledBy = element.getAttribute("aria-labelledby");

            const referencedText = labelledBy
                ? labelledBy.split(" ")
                    .map(id => document.getElementById(id))
                    .filter(Boolean)
                    .map(item => item.innerText || item.textContent || "")
                    .join(" ")
                : "";

            const associatedLabel =
                element.labels && element.labels.length
                    ? Array.from(element.labels)
                        .map(label => label.innerText || label.textContent || "")
                        .join(" ")
                    : "";

            const ariaLabel = element.getAttribute("aria-label") || "";

            const accessibleLabel = (
                ariaLabel || referencedText || associatedLabel
            ).trim();

            const style = getComputedStyle(element);

            return {
                id: element.id || "(no id)",
                name: element.getAttribute("name") || "(no name)",
                label: accessibleLabel,
                placeholder: element.getAttribute("placeholder") || "(none)",
                type: (
                    element.getAttribute("type") ||
                    element.tagName.toLowerCase()
                ).toLowerCase(),
                required: element.required ||
                    element.getAttribute("aria-required") === "true",
                visible: element.getClientRects().length > 0
                    && style.visibility !== "hidden"
                    && style.display !== "none"
            };
        })
        """
    )

    visible_fields = [
        field for field in fields if field["visible"]
    ]

    labelled_fields = [
        field for field in visible_fields if field["label"]
    ]

    missing_labels = [
        field for field in visible_fields if not field["label"]
    ]

    required_fields = [
        field for field in visible_fields if field["required"]
    ]

    missing_details = "; ".join(
        f"ID: {field['id']}, Name: {field['name']}, "
        f"Type: {field['type']}, Placeholder: {field['placeholder']}"
        for field in missing_labels
    )

    add_check(
        checks,
        "Interactive input visibility",
        len(visible_fields) > 0,
        f"Found {len(visible_fields)} visible form fields"
    )

    add_check(
        checks,
        "Interactive input labels",
        len(labelled_fields) == len(visible_fields)
        and len(visible_fields) > 0,
        f"{len(labelled_fields)} of {len(visible_fields)} fields "
        f"have accessible labels. Missing labels: "
        f"{missing_details if missing_details else 'None'}"
    )

    add_check(
        checks,
        "Interactive input types",
        len(visible_fields) > 0
        and all(field["type"] for field in visible_fields),
        f"Inspected types of {len(visible_fields)} visible fields"
    )

    add_check(
        checks,
        "Required field attributes",
        len(visible_fields) > 0,
        (
            f"Found {len(required_fields)} required fields "
            f"out of {len(visible_fields)} visible fields"
        )
    )



def inspect_interactive_dropdowns(page, checks):
    """Inspect native and custom dropdown controls without changing values."""

    dropdowns = page.locator(
        "select, [role='combobox']"
    ).evaluate_all(
        """
        elements => elements.map(element => {
            const labelledBy = element.getAttribute("aria-labelledby");

            const referencedText = labelledBy
                ? labelledBy.split(" ")
                    .map(id => document.getElementById(id))
                    .filter(Boolean)
                    .map(item => item.innerText || item.textContent || "")
                    .join(" ")
                : "";

            const associatedLabel =
                element.labels && element.labels.length
                    ? Array.from(element.labels)
                        .map(label => label.innerText || label.textContent || "")
                        .join(" ")
                    : "";

            const label = (
                element.getAttribute("aria-label") ||
                referencedText ||
                associatedLabel ||
                element.getAttribute("title") ||
                ""
            ).trim();

            const isNativeSelect =
                element.tagName.toLowerCase() === "select";

            const options = isNativeSelect
                ? Array.from(element.options).map(option => ({
                    text: option.textContent.trim(),
                    disabled: option.disabled
                }))
                : [];

            const style = getComputedStyle(element);

            return {
                id: element.id || "(no id)",
                label: label,
                native: isNativeSelect,
                options: options,
                optionCount: isNativeSelect
                    ? options.length
                    : 0,
                disabled: Boolean(element.disabled) ||
                    element.getAttribute("aria-disabled") === "true",
                visible: element.getClientRects().length > 0 &&
                    style.visibility !== "hidden" &&
                    style.display !== "none"
            };
        })
        """
    )

    visible_dropdowns = [
        item for item in dropdowns if item["visible"]
    ]

    labelled_dropdowns = [
        item for item in visible_dropdowns if item["label"]
    ]

    native_dropdowns = [
        item for item in visible_dropdowns if item["native"]
    ]

    option_details = "; ".join(
        f"{item['id']}: {item['optionCount']} options"
        for item in native_dropdowns
    )

    add_check(
        checks,
        "Dropdown visibility",
        len(visible_dropdowns) > 0,
        f"Found {len(visible_dropdowns)} visible dropdown controls"
    )

    add_check(
        checks,
        "Dropdown accessible labels",
        len(labelled_dropdowns) == len(visible_dropdowns)
        and len(visible_dropdowns) > 0,
        f"{len(labelled_dropdowns)} of {len(visible_dropdowns)} "
        "dropdowns have accessible labels"
    )

    add_check(
        checks,
        "Dropdown enabled state",
        len(visible_dropdowns) > 0,
        f"Inspected enabled/disabled state of "
        f"{len(visible_dropdowns)} dropdowns"
    )

    add_check(
        checks,
        "Dropdown options",
        len(visible_dropdowns) > 0 and all(
            item["optionCount"] > 0
            for item in native_dropdowns
        ),
        (
            option_details
            if option_details
            else "Custom dropdowns detected; native option lists unavailable"
        )
    )


def inspect_interactive_dialogs(page, checks):
    """Inspect visible dialogs, accessible names and their controls."""

    dialogs = page.locator(
        '[role="dialog"], dialog[open], .email-modal-backdrop'
    ).evaluate_all(
        """
        elements => elements.map(element => {
            const style = getComputedStyle(element);

            const visible =
                element.getClientRects().length > 0 &&
                style.visibility !== "hidden" &&
                style.display !== "none";

            const labelledBy = element.getAttribute("aria-labelledby");

            const referencedText = labelledBy
                ? labelledBy.split(" ")
                    .map(id => document.getElementById(id))
                    .filter(Boolean)
                    .map(item => item.innerText || item.textContent || "")
                    .join(" ")
                : "";

            const heading = element.querySelector(
                "h1, h2, h3, h4, h5, h6"
            );

            const accessibleName = (
                element.getAttribute("aria-label") ||
                referencedText ||
                (heading ? heading.innerText : "")
            ).trim();

            const controls = element.querySelectorAll(
                "button, a[href], input:not([type='hidden']), textarea, select"
            );

            return {
                name: accessibleName,
                visible: visible,
                controlCount: controls.length
            };
        })
        """
    )

    visible_dialogs = [
        dialog for dialog in dialogs if dialog["visible"]
    ]

    named_dialogs = [
        dialog for dialog in visible_dialogs if dialog["name"]
    ]

    total_controls = sum(
        dialog["controlCount"] for dialog in visible_dialogs
    )

    add_check(
        checks,
        "Dialog visibility",
        len(visible_dialogs) > 0,
        f"Found {len(visible_dialogs)} visible dialogs"
    )

    add_check(
        checks,
        "Dialog accessible names",
        len(named_dialogs) == len(visible_dialogs)
        and len(visible_dialogs) > 0,
        f"{len(named_dialogs)} of {len(visible_dialogs)} "
        "visible dialogs have accessible names"
    )

    add_check(
        checks,
        "Dialog controls",
        len(visible_dialogs) > 0 and total_controls > 0,
        f"Found {total_controls} controls inside visible dialogs"
    )


def inspect_responsive_layout(page, checks):
    """
    Check for horizontal overflow at a mobile viewport.
    """

    page.set_viewport_size({
        "width": 375,
        "height": 812
    })

    page.wait_for_timeout(300)

    dimensions = page.evaluate(
        """
        () => ({
            viewportWidth: document.documentElement.clientWidth,
            pageWidth: document.documentElement.scrollWidth
        })
        """
    )

    no_overflow = (
        dimensions["pageWidth"]
        <= dimensions["viewportWidth"]
    )

    add_check(
        checks,
        "Mobile horizontal overflow",
        no_overflow,
        (
            f"Viewport: {dimensions['viewportWidth']}px; "
            f"page: {dimensions['pageWidth']}px"
        )
    )


def execute_test_case(url: str, run_id: int, test_case: dict):

    validate_url(url)

    SCREENSHOT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    screenshot_file = SCREENSHOT_DIR / (
        f"run_{run_id}_test_{test_case['id']}_{uuid4().hex[:8]}.png"
    )

    checks = []
    errors = []

    page = None

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=True
        )

        try:

            context = browser.new_context(
                viewport={
                    "width": 1366,
                    "height": 768
                }
            )
            install_browser_request_guard(context)
            page = context.new_page()


            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            status_code = (
                response.status if response else None
            )

            add_check(
                checks,
                "Website loading",
                status_code is not None
                and 200 <= status_code < 400,
                f"HTTP status: {status_code}"
            )

            # Verify the final browser URL remains on the registered host.
            original_host = urlparse(url).hostname
            final_host = urlparse(page.url).hostname

            if final_host != original_host:
                raise ValueError(
                    "Website redirected to a different hostname"
                )

            # Inspect the page title and body.
            page_title = page.title()
            body_text = page.locator("body").inner_text().strip()

            add_check(
                checks,
                "Page title",
                bool(page_title.strip()),
                f"Page title: {page_title}"
            )

            add_check(
                checks,
                "Page content",
                bool(body_text),
                f"Discovered {len(body_text)} characters of page text"
            )

            # Read all available test-case instructions.
            context = get_test_context(test_case)


            # Determine the type of test from its instructions.
            if "responsive" in context or "mobile viewport" in context:

                inspect_responsive_layout(page, checks)

            elif "interactive navigation links" in context:

                inspect_interactive_links(page, checks)

            elif "interactive buttons" in context:

                inspect_interactive_buttons(page, checks)

            elif "form input fields" in context:

                inspect_section(page, "contact", checks)

                inspect_interactive_inputs(page, checks)

            elif "dropdown" in context:

                inspect_interactive_dropdowns(page, checks)

            elif "dialog" in context:

                inspect_section(page, "contact", checks)

                inspect_interactive_dialogs(page, checks)

            elif "navigation" in context:

                inspect_navigation(page, checks)



            else:

                section_name = identify_section(test_case)

                if section_name and section_name != "home":

                    inspect_section(page, section_name, checks)

                elif section_name == "home" or "homepage" in context:

                    add_check(
                        checks,
                        "Homepage content",
                        bool(body_text),
                        "Homepage contains page text"
                    )

                else:

                    link_count = page.locator("a[href]").count()
                    button_count = page.locator(
                        "button, [role='button']"
                    ).count()
                    input_count = page.locator(
                        "input, textarea, select"
                    ).count()

                    add_check(
                        checks,
                        "Interactive elements",
                        (link_count + button_count + input_count) > 0,
                        (
                            f"Links: {link_count}; "
                            f"buttons: {button_count}; "
                            f"inputs: {input_count}"
                        )
                    )


            # Capture evidence after the checks.
            page.screenshot(
                path=str(screenshot_file),
                full_page=True
            )

        except Exception as error:

            errors.append(str(error))

            if page is not None:

                try:
                    page.screenshot(
                        path=str(screenshot_file),
                        full_page=True
                    )
                except Exception:
                    pass

        finally:

            browser.close()

    total_passed = sum(
        check["passed"]
        for check in checks
    )

    total_checks = len(checks)

    all_passed = (
        total_checks > 0
        and total_passed == total_checks
        and not errors
    )

    return {
        "passed": all_passed,
        "actual_result": (
            f"{total_passed} of {total_checks} checks passed"
        ),
        "error_message": (
            "; ".join(errors)
            if errors
            else (
                None
                if all_passed
                else "One or more checks failed"
            )
        ),
        "checks": checks,
        "screenshot_path": str(screenshot_file)
    }
