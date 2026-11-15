
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

from playwright.sync_api import sync_playwright

from app.services.browser_service import (
    validate_url,
    install_browser_request_guard
)


MAX_PAGES = 10
MAX_LINKS_PER_PAGE = 30
MAX_HEADINGS = 100

IGNORED_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".webp", ".zip", ".rar", ".mp4", ".mp3",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"
}


def is_same_domain(url, hostname):
    parsed = urlparse(url)

    return (
        parsed.scheme in ("http", "https")
        and parsed.hostname == hostname
    )


def is_html_candidate(url):
    path = urlparse(url).path.lower()
    extension = Path(path).suffix

    return extension not in IGNORED_EXTENSIONS


def get_accessible_name(element):
    return (
        element.get_attribute("aria-label")
        or element.get_attribute("title")
        or element.inner_text()
        or element.get_attribute("value")
        or ""
    ).strip()

def discover_interactive_elements(page):
    """
    Discover interactive UI elements without activating them.
    Does not submit forms or trigger user actions.
    """

    return page.locator(
        "button, a[href], input, textarea, select, "
        "[role='button'], [role='link'], [role='tab'], "
        "[role='menuitem'], [role='checkbox'], "
        "[role='radio'], [role='switch'], "
        "[role='combobox'], [role='dialog'], "
        "[role='menu'], [role='listbox']"
    ).evaluate_all(
        """
        elements => elements.map((element, index) => {

            const tag = element.tagName.toLowerCase();

            const role = element.getAttribute("role") || "";

            const type = (
                element.getAttribute("type") || ""
            ).toLowerCase();

            const labelledBy = element.getAttribute(
                "aria-labelledby"
            );

            const referencedText = labelledBy
                ? labelledBy.split(" ")
                    .map(id => document.getElementById(id))
                    .filter(Boolean)
                    .map(item => item.innerText)
                    .join(" ")
                : "";

            const associatedLabel =
                element.labels && element.labels.length
                    ? Array.from(element.labels)
                        .map(label => label.innerText)
                        .join(" ")
                    : "";

            const accessibleName =
                element.getAttribute("aria-label") ||
                referencedText ||
                associatedLabel ||
                element.getAttribute("title") ||
                element.innerText ||
                element.getAttribute("placeholder") ||
                element.getAttribute("value") ||
                "";

            let category = "interactive";

            if (tag === "button" || role === "button") {
                category = "button";
            } else if (tag === "a" || role === "link") {
                category = "link";
            } else if (tag === "select" || role === "combobox") {
                category = "dropdown";
            } else if (role === "tab") {
                category = "tab";
            } else if (role === "menuitem") {
                category = "menu_item";
            } else if (role === "dialog" || tag === "dialog") {
                category = "dialog";
            } else if (role === "menu") {
                category = "menu";
            } else if (role === "listbox") {
                category = "listbox";
            } else if (
                type === "checkbox" || role === "checkbox"
            ) {
                category = "checkbox";
            } else if (
                type === "radio" || role === "radio"
            ) {
                category = "radio";
            } else if (role === "switch") {
                category = "switch";
            } else if (
                ["input", "textarea"].includes(tag)
            ) {
                category = "input";
            }

            const text = (accessibleName || "").trim();

            const actionText = (
                text + " " +
                (element.getAttribute("name") || "") + " " +
                (element.id || "")
            ).toLowerCase();

            const dangerousPattern =
                /delete|remove|purchase|buy now|checkout|pay now|submit|send email|send message|confirm order|place order|transfer|logout|log out/;

            const risk = dangerousPattern.test(actionText)
                ? "restricted"
                : "review_required";

            return {
                index: index + 1,
                category: category,
                tag: tag,
                role: role,
                text: text,
                id: element.id || "",
                name: element.getAttribute("name") || "",
                type: type,
                href: element.href || "",
                visible: element.getClientRects().length > 0,
                disabled: Boolean(element.disabled),
                required: Boolean(element.required),
                checked: (
                    ["checkbox", "radio"].includes(type)
                    ? Boolean(element.checked)
                    : null
                ),
                selected: (
                    element.getAttribute("aria-selected")
                ),
                expanded: (
                    element.getAttribute("aria-expanded")
                ),
                options: (
                    tag === "select"
                        ? Array.from(element.options).map(option => ({
                            text: option.text.trim(),
                            value: option.value
                        }))
                        : []
                ),
                risk: risk
            };
        })
        """
    )


def explore_website(url: str):
    """
    Explore a website using bounded, same-domain crawling.

    The explorer does not submit forms or click buttons.
    It collects page structure and navigation information.
    """

    validate_url(url)

    original_url = url
    original_host = urlparse(url).hostname

    # Queue stores pages waiting to be explored.
    pending_urls = deque([url])

    # Track visited pages to avoid duplicate visits.
    visited_urls = set()

    pages = []
    all_section_links = []
    all_discovered_links = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            context = browser.new_context(
                viewport={"width": 1366, "height": 768}
            )
            install_browser_request_guard(context)
            page = context.new_page()

            while pending_urls and len(pages) < MAX_PAGES:

                current_url = pending_urls.popleft()

                # Remove URL fragments for page deduplication.
                current_url = urldefrag(current_url)[0]

                if current_url in visited_urls:
                    continue

                if not is_same_domain(current_url, original_host):
                    continue

                if not is_html_candidate(current_url):
                    continue

                # Validate every URL before navigation.
                validate_url(current_url)

                visited_urls.add(current_url)

                try:
                    response = page.goto(
                        current_url,
                        wait_until="domcontentloaded",
                        timeout=30000
                    )

                    final_url = urldefrag(page.url)[0]
                    final_host = urlparse(final_url).hostname

                    # Stop if navigation redirects to another hostname.
                    if final_host != original_host:
                        continue

                    page_title = page.title()

                    # Collect headings.
                    headings = page.locator(
                        "h1, h2, h3, h4, h5, h6"
                    ).evaluate_all(
                        """
                        elements => elements.map(element => ({
                            tag: element.tagName.toLowerCase(),
                            text: (element.innerText || "").trim()
                        })).filter(item => item.text.length > 0)
                        """
                    )

                    headings = headings[:MAX_HEADINGS]

                    # Collect links.
                    raw_links = page.locator(
                        "a[href]"
                    ).evaluate_all(
                        """
                        elements => elements.map(element => ({
                            text: (
                                element.innerText ||
                                element.getAttribute("aria-label") ||
                                element.getAttribute("title") ||
                                ""
                            ).trim(),
                            href: element.href,
                            visible: element.getClientRects().length > 0
                        }))
                        """
                    )

                    page_links = []
                    seen_page_links = set()

                    for link in raw_links:

                        link_url = urljoin(
                            final_url,
                            link["href"]
                        )

                        parsed_link = urlparse(link_url)

                        if parsed_link.scheme not in ("http", "https"):
                            continue

                        if parsed_link.hostname != original_host:
                            continue

                        # Handle same-page section navigation.
                        if parsed_link.fragment:
                            section = {
                                "page_url": final_url,
                                "section_id": parsed_link.fragment,
                                "text": link["text"],
                                "visible": link["visible"]
                            }

                            if section not in all_section_links:
                                all_section_links.append(section)

                        clean_url = urldefrag(link_url)[0]

                        if clean_url == final_url:
                            continue

                        if not is_html_candidate(clean_url):
                            continue

                        if clean_url in seen_page_links:
                            continue

                        seen_page_links.add(clean_url)

                        page_links.append({
                            "text": link["text"],
                            "url": clean_url,
                            "visible": link["visible"]
                        })

                        if clean_url not in visited_urls:
                            if clean_url not in pending_urls:
                                pending_urls.append(clean_url)

                        if len(page_links) >= MAX_LINKS_PER_PAGE:
                            break

                    # Collect buttons and accessible names.
                    buttons = page.locator(
                        "button, input[type='button'], "
                        "input[type='submit'], [role='button']"
                    ).evaluate_all(
                        """
                        elements => elements.map(element => {
                            const labelledBy = element.getAttribute(
                                "aria-labelledby"
                            );

                            const referencedText = labelledBy
                                ? labelledBy.split(" ").map(id => {
                                    const label = document.getElementById(id);
                                    return label ? label.innerText : "";
                                  }).join(" ")
                                : "";

                            const text =
                                element.getAttribute("aria-label") ||
                                referencedText ||
                                element.getAttribute("title") ||
                                element.innerText ||
                                element.value ||
                                "";

                            return {
                                text: text.trim(),
                                type: element.getAttribute("type") || "button",
                                visible: element.getClientRects().length > 0,
                                disabled: Boolean(element.disabled)
                            };
                        })
                        """
                    )

                    # Collect forms without submitting them.
                    forms = page.locator("form").evaluate_all(
                        """
                        elements => elements.map((form, index) => ({
                            index: index + 1,
                            action: form.action || "",
                            method: (form.method || "get").toUpperCase(),
                            input_count: form.querySelectorAll(
                                "input, textarea, select"
                            ).length
                        }))
                        """
                    )


                    # Collect input fields with accessible labels.
                    inputs = page.locator(
                        "input, textarea, select"
                    ).evaluate_all(
                        """
                        elements => elements.map(element => {
                            const labelledBy =
                                element.getAttribute("aria-labelledby");

                            const referencedLabel = labelledBy
                                ? labelledBy.split(" ")
                                    .map(id => document.getElementById(id))
                                    .filter(Boolean)
                                    .map(label => label.innerText)
                                    .join(" ")
                                : "";

                            const associatedLabel =
                                element.labels && element.labels.length
                                    ? Array.from(element.labels)
                                        .map(label => label.innerText)
                                        .join(" ")
                                    : "";

                            const label =
                                element.getAttribute("aria-label") ||
                                referencedLabel ||
                                associatedLabel ||
                                element.getAttribute("placeholder") ||
                                element.getAttribute("name") ||
                                "";

                            return {
                                tag: element.tagName.toLowerCase(),
                                type: element.getAttribute("type") || "",
                                id: element.id || "",
                                name: element.getAttribute("name") || "",
                                label: label.trim(),
                                placeholder:
                                    element.getAttribute("placeholder") || "",
                                visible: element.getClientRects().length > 0,
                                required: Boolean(element.required),
                                disabled: Boolean(element.disabled),
                                checked:
                                    ["checkbox", "radio"].includes(
                                        (element.getAttribute("type") || "")
                                            .toLowerCase()
                                    )
                                    ? Boolean(element.checked)
                                    : null,
                                options:
                                    element.tagName.toLowerCase() === "select"
                                        ? Array.from(element.options).map(
                                            option => ({
                                                text: option.text.trim(),
                                                value: option.value
                                            })
                                        )
                                        : []
                            };
                        })
                        """
                    )

                    # Discover interactive elements without clicking or submitting them.
                    interactive_elements = discover_interactive_elements(page)[:200]


                    page_data = {
                        "url": final_url,
                        "page_title": page_title,
                        "http_status": response.status if response else None,
                        "headings": headings,
                        "discovered_links": page_links,
                        "buttons": buttons,
"forms": forms,
"inputs": inputs,
"interactive_elements": interactive_elements,
                        "summary": {
    "total_headings": len(headings),
    "total_links": len(page_links),
    "total_buttons": len(buttons),
    "total_forms": len(forms),
    "total_inputs": len(inputs),
    "total_interactive_elements": len(interactive_elements)
}
                    }

                    pages.append(page_data)
                    all_discovered_links.extend(page_links)

                except Exception as error:
                    pages.append({
                        "url": current_url,
                        "page_title": "",
                        "http_status": None,
                        "error": str(error),
                        "headings": [],
                        "discovered_links": [],
                        "buttons": [],
"forms": [],
"inputs": [],
"interactive_elements": [],
                        "summary": {
    "total_headings": 0,
    "total_links": 0,
    "total_buttons": 0,
    "total_forms": 0,
    "total_inputs": 0,
    "total_interactive_elements": 0
}
                    })

            return {
                "requested_url": original_url,
                "pages": pages,
                "section_links": all_section_links,
                "summary": {
                    "total_pages_visited": len(pages),
                    "total_sections_discovered": len(all_section_links),
                    "total_internal_links": len(all_discovered_links),
                    "maximum_pages": MAX_PAGES
                }
            }

        finally:
            browser.close()
