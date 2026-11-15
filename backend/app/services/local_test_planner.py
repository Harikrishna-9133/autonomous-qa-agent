
def generate_test_plan(
    project_name: str,
    website_url: str,
    description: str,
    features: list[str],
    number_of_tests: int = 5,
    interactive_elements: list[dict] | None = None
) -> dict:

    if not features and not interactive_elements:
        raise ValueError(
        "At least one website feature or interactive element is required"
    )

    if not 1 <= number_of_tests <= 15:
        raise ValueError("number_of_tests must be between 1 and 15")

    # Predefined test scenarios for common website features
    templates = {
        "homepage": {
            "title": "Verify Homepage Loading",
            "description": "Check whether the website homepage loads correctly.",
            "steps": [
                "Open the website URL.",
                "Wait for the page to load.",
                "Check the HTTP response status.",
                "Verify that the page body contains visible content."
            ],
            "expected_result": "The homepage loads successfully and displays content.",
            "priority": "high"
        },
        "navigation": {
            "title": "Verify Website Navigation",
            "description": "Check that the website navigation links are available.",
            "steps": [
                "Open the website.",
                "Locate the navigation menu.",
                "Check that the expected navigation items are visible.",
                "Verify that navigation items have valid destinations."
            ],
            "expected_result": "The expected navigation items are available and have valid destinations.",
            "priority": "high"
        },
        "about": {
            "title": "Verify About Section",
            "description": "Check the About section of the website.",
            "steps": [
                "Open the website.",
                "Locate the About section.",
                "Verify that the section is visible.",
                "Check that the section contains meaningful text."
            ],
            "expected_result": "The About section is visible and contains content.",
            "priority": "medium"
        },
        "experience": {
            "title": "Verify Experience Section",
            "description": "Check the Experience section.",
            "steps": [
                "Open the website.",
                "Navigate to the Experience section.",
                "Verify that experience details are displayed."
            ],
            "expected_result": "The Experience section is visible and displays experience information.",
            "priority": "medium"
        },
        "projects": {
            "title": "Verify Projects Section",
            "description": "Check the projects displayed on the website.",
            "steps": [
                "Open the website.",
                "Navigate to the Projects section.",
                "Verify that project information is displayed."
            ],
            "expected_result": "The Projects section is visible and displays project information.",
            "priority": "high"
        },
        "skills": {
            "title": "Verify Skills Section",
            "description": "Check the skills displayed on the website.",
            "steps": [
                "Open the website.",
                "Navigate to the Skills section.",
                "Verify that skill information is displayed."
            ],
            "expected_result": "The Skills section is visible and displays skill information.",
            "priority": "medium"
        },
        "notes": {
            "title": "Verify Notes Section",
            "description": "Check the Notes section.",
            "steps": [
                "Open the website.",
                "Navigate to the Notes section.",
                "Verify that the section is visible."
            ],
            "expected_result": "The Notes section is visible and displays its content.",
            "priority": "low"
        },
        "contact": {
            "title": "Verify Contact Section",
            "description": "Check the website contact section.",
            "steps": [
                "Open the website.",
                "Navigate to the Contact section.",
                "Verify that contact information or a contact form is displayed."
            ],
            "expected_result": "The Contact section is visible and provides contact information or a form.",
            "priority": "high"
        },
        "responsive": {
            "title": "Verify Responsive Navigation",
            "description": "Check website navigation at a mobile viewport size.",
            "steps": [
                "Open the website.",
                "Set the browser viewport to 375 by 812 pixels.",
                "Check that the navigation menu is accessible.",
                "Verify that the page does not overflow horizontally."
            ],
            "expected_result": "The website navigation remains accessible and the page fits the mobile viewport.",
            "priority": "medium"
        }
    }


    interactive_templates = {
        "link": {
            "title": "Verify Interactive Navigation Links",
            "description": "Verify that discovered navigation links have valid destinations.",
            "steps": [
                "Open the website.",
                "Locate the discovered navigation links.",
                "Verify that the links are visible.",
                "Check that each link has a valid destination."
            ],
            "expected_result": "Discovered navigation links are visible and have valid destinations.",
            "priority": "high"
        },
        "button": {
            "title": "Verify Interactive Buttons",
            "description": "Check the visibility and enabled state of discovered buttons.",
            "steps": [
                "Open the website.",
                "Locate the discovered buttons.",
                "Verify that the buttons are visible.",
                "Check that the buttons are enabled or disabled as expected."
            ],
            "expected_result": "Discovered buttons have valid visibility and enabled states.",
            "priority": "medium"
        },
        "input": {
            "title": "Verify Form Input Fields",
            "description": "Check the labels, visibility and types of discovered form fields.",
            "steps": [
                "Open the website.",
                "Locate the discovered input fields.",
                "Verify their visibility and accessible labels.",
                "Check that their input types are correct."
            ],
            "expected_result": "Discovered form fields have accessible labels and valid input types.",
            "priority": "high"
        },
        "dropdown": {
            "title": "Verify Dropdown Controls",
            "description": "Check discovered dropdown controls and their available options.",
            "steps": [
                "Open the website.",
                "Locate the discovered dropdown controls.",
                "Verify that the dropdowns are visible.",
                "Inspect the available options."
            ],
            "expected_result": "Dropdown controls are visible and contain their available options.",
            "priority": "medium"
        },
        "dialog": {
            "title": "Verify Dialog Elements",
            "description": "Check the visibility and accessibility of discovered dialogs.",
            "steps": [
                "Open the website.",
                "Locate the discovered dialog elements.",
                "Verify their visibility.",
                "Check their accessible names."
            ],
            "expected_result": "Discovered dialogs are accessible and have valid visibility.",
            "priority": "medium"
        }
    }


    generated_cases = []
    used_features = set()

        # Reserve slots for interactive element scenarios.
    feature_test_limit = (
        max(1, number_of_tests - 3)
        if interactive_elements
        else number_of_tests
    )

    # Generate scenarios based on supplied features.
    for feature in features:
        if len(generated_cases) >= feature_test_limit:
            break

        feature_key = feature.lower().strip()

        if feature_key in used_features:
            continue

        used_features.add(feature_key)

        scenario = None

        for keyword, template in templates.items():
            if keyword in feature_key:
                scenario = template
                break

        # Generic scenario for an unsupported feature
        if scenario is None:
            scenario = {
                "title": f"Verify {feature.title()}",
                "description": f"Check the {feature} feature of {project_name}.",
                "steps": [
                    f"Open the website: {website_url}",
                    f"Locate the {feature} feature.",
                    "Verify that the feature is visible.",
                    "Check that the feature displays relevant content."
                ],
                "expected_result": f"The {feature} feature is visible and displays relevant content.",
                "priority": "medium"
            }

        generated_cases.append({
            "title": scenario["title"],
            "description": scenario["description"],
            "steps": scenario["steps"],
            "expected_result": scenario["expected_result"],
            "priority": scenario["priority"]
        })



    # Generate element-aware scenarios from discovered interactive elements.
    supported_categories = {
        "link": {
            "title": "Verify Interactive Navigation Links",
            "description": "Verify discovered links and their destinations.",
            "steps": [
                "Open the website.",
                "Locate the discovered navigation links.",
                "Verify that the links are visible.",
                "Check that each link has a valid destination."
            ],
            "expected_result": (
                "Discovered navigation links are visible "
                "and have valid destinations."
            ),
            "priority": "high"
        },
        "button": {
            "title": "Verify Interactive Buttons",
            "description": "Verify discovered buttons and their enabled states.",
            "steps": [
                "Open the website.",
                "Locate the discovered buttons.",
                "Verify that the buttons are visible.",
                "Check the enabled and disabled states of the buttons."
            ],
            "expected_result": (
                "Discovered buttons have valid visibility "
                "and enabled states."
            ),
            "priority": "medium"
        },
        "input": {
            "title": "Verify Form Input Fields",
            "description": "Verify discovered form fields, labels, types and required attributes.",
            "steps": [
                "Open the website.",
                "Locate the discovered input fields.",
                "Verify their visibility and accessible labels.",
                "Check their input types and required-field attributes."
            ],
            "expected_result": (
                "Discovered form fields are visible and have "
                "accessible labels, valid types and inspectable "
                "required-field attributes."
            ),
            "priority": "high"
        },
        "dropdown": {
            "title": "Verify Dropdown Controls",
            "description": "Verify discovered dropdown controls and their options.",
            "steps": [
                "Open the website.",
                "Locate the discovered dropdown controls.",
                "Verify that the dropdowns are visible.",
                "Inspect their available options."
            ],
            "expected_result": (
                "Dropdown controls are visible and their "
                "available options can be inspected."
            ),
            "priority": "medium"
        },
        "dialog": {
            "title": "Verify Dialog Elements",
            "description": "Verify discovered dialogs and their accessible names.",
            "steps": [
                "Open the website.",
                "Locate the discovered dialog elements.",
                "Verify their visibility.",
                "Check their accessible names."
            ],
            "expected_result": (
                "Discovered dialogs are visible and have "
                "valid accessible names."
            ),
            "priority": "medium"
        }
    }

    # Group only visible, non-restricted elements by supported category.
    elements_by_category = {}

    for element in (interactive_elements or []):
        category = str(element.get("category", "")).lower()

        if category not in supported_categories:
            continue

        if element.get("risk") == "restricted":
            continue

        if not element.get("visible", False):
            continue

        elements_by_category.setdefault(category, []).append(element)


    interactive_test_limit = number_of_tests - len(generated_cases)

    category_priority = [
        "link",
        "button",
        "input",
        "dropdown",
        "dialog"
    ]

    for category in category_priority:
        elements = elements_by_category.get(category, [])

        if not elements:
            continue

        if interactive_test_limit <= 0:
            break

        scenario = supported_categories[category]

        # Use actual discovered names to make the scenario informative.
        element_names = []

        for element in elements:
            name = (
                element.get("text")
                or element.get("name")
                or element.get("id")
                or element.get("type")
                or category
            )

            name = " ".join(str(name).split())

            if name and name not in element_names:
                element_names.append(name)

        displayed_names = element_names[:5]
        details = ", ".join(displayed_names)

        if len(element_names) > 5:
            details += f", and {len(element_names) - 5} more"

        generated_cases.append({
            "title": scenario["title"],
            "description": (
                f"{scenario['description']} "
                f"Discovered {len(elements)} visible {category} "
                f"element(s): {details or 'Unnamed elements'}."
            ),
            "steps": scenario["steps"],
            "expected_result": scenario["expected_result"],
            "priority": scenario["priority"]
        })

        interactive_test_limit -= 1




    if not generated_cases:
        raise ValueError("No test scenarios could be generated")

    return {"test_cases": generated_cases}
