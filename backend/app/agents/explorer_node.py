
import asyncio
import inspect
import re

from app.services.website_explorer import explore_website


# Map website section names to Planner feature names.
FEATURE_ALIASES = {
    "homepage": [
        "home", "homepage", "main page"
    ],
    "about": [
        "about", "about me", "profile"
    ],
    "experience": [
        "experience", "work experience", "career"
    ],
    "projects": [
        "project", "projects", "portfolio work"
    ],
    "skills": [
        "skill", "skills", "technologies", "tech stack"
    ],
    "notes": [
        "notes", "blog", "blogs", "articles", "writing"
    ],
    "contact": [
        "contact", "contact me", "get in touch"
    ]
}


def normalize_text(value: str) -> str:
    """Normalize text for reliable feature matching."""
    value = value.lower().replace("-", " ").replace("_", " ")
    return re.sub(r"[^a-z0-9\s]", " ", value).strip()


def extract_features(exploration_data: dict) -> list[str]:
    """
    Extract website features from the actual Explorer response.

    Reads:
    - section_links
    - pages
    - page headings
    - discovered_links
    """

    discovered_features = ["homepage"]

    # 1. Read same-page navigation sections.
    section_links = exploration_data.get("section_links", [])

    # 2. Read pages, headings and internal links.
    pages = exploration_data.get("pages", [])

    text_sources = []

    for section in section_links:
        text_sources.append(section.get("section_id", ""))
        text_sources.append(section.get("text", ""))

    for page in pages:
        text_sources.append(page.get("page_title", ""))

        for heading in page.get("headings", []):
            text_sources.append(heading.get("text", ""))

        for link in page.get("discovered_links", []):
            text_sources.append(link.get("text", ""))

    # Combine all discovered website text.
    website_text = normalize_text(" ".join(
        str(item) for item in text_sources if item
    ))

    # 3. Match discovered website content to known features.
    for feature, aliases in FEATURE_ALIASES.items():

        for alias in aliases:
            normalized_alias = normalize_text(alias)

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(normalized_alias)
                + r"(?![a-z0-9])"
            )

            if re.search(pattern, website_text):
                if feature not in discovered_features:
                    discovered_features.append(feature)

                break

    # 4. Navigation is a separate testable feature.
    if section_links:
        if "navigation" not in discovered_features:
            discovered_features.append("navigation")

    elif any(
        page.get("discovered_links")
        for page in pages
    ):
        discovered_features.append("navigation")

    return discovered_features


async def explorer_node(state: dict) -> dict:
    """
    LangGraph Explorer Node.

    Explores the authorized website and extracts
    features for automatic test planning.
    """

    try:
        website_url = state.get("website_url")

        if not website_url:
            raise ValueError("Website URL is missing.")

        print("Explorer Node started.")
        print(f"Exploring website: {website_url}")

        # Run synchronous Playwright outside the asyncio event loop.
        exploration_data = await asyncio.to_thread(
            explore_website,
            website_url
        )

        if inspect.isawaitable(exploration_data):
            exploration_data = await exploration_data

        if not isinstance(exploration_data, dict):
            raise ValueError(
                "Website Explorer returned an invalid response."
            )

        discovered_features = extract_features(exploration_data)

        summary = exploration_data.get("summary", {})

        print(
            f"Pages visited: "
            f"{summary.get('total_pages_visited', 0)}"
        )

        print(
            f"Sections discovered: "
            f"{summary.get('total_sections_discovered', 0)}"
        )

        print(
            f"Features discovered: {discovered_features}"
        )

        return {
            "exploration_data": exploration_data,
            "discovered_features": discovered_features,
            "current_step": "explorer_completed",
            "workflow_status": "running",
            "errors": state.get("errors", [])
        }

    except Exception as error:
        print(f"Explorer Node error: {error}")

        return {
            "current_step": "explorer_failed",
            "workflow_status": "failed",
            "errors": state.get("errors", [])
            + [f"Website exploration failed: {str(error)}"]
        }
