
import re


def investigate_bug(test_result):
    """
    Evidence-aware, rule-based bug investigation engine.

    Uses execution errors, failed Playwright checks and
    original test-case information to classify failures.

    Compatible with existing callers that provide only
    error_message, actual_result and screenshot_path.
    """

    error_message = getattr(test_result, "error_message", None) or ""
    actual_result = getattr(test_result, "actual_result", None) or ""
    screenshot_path = getattr(test_result, "screenshot_path", None)

    checks = getattr(test_result, "checks", None) or []

    test_title = getattr(test_result, "test_title", None) or ""
    test_description = getattr(test_result, "test_description", None) or ""
    test_steps = getattr(test_result, "test_steps", None) or ""
    expected_result = getattr(test_result, "expected_result", None) or ""

    error_text = f"{error_message} {actual_result}".lower().strip()

    # --------------------------------------------------
    # 1. Extract failed-check evidence
    # --------------------------------------------------

    failed_checks = []

    for check in checks:
        if not isinstance(check, dict):
            continue

        if check.get("passed") is False:
            name = str(check.get("name") or "Unnamed check")
            details = str(check.get("details") or "No details provided")

            failed_checks.append({
                "name": name,
                "details": details
            })

    failed_check_summary = "; ".join(
        f"{item['name']}: {item['details']}"
        for item in failed_checks
    )

    evidence_text = (
        f"{error_text} {failed_check_summary}".lower()
    )

    # --------------------------------------------------
    # 2. Default investigation
    # --------------------------------------------------

    title = "Unclassified Test Failure"
    description = "The test failed, but the exact cause could not be determined."
    severity = "medium"
    failure_type = "unknown"
    component = "unknown"

    root_cause = "Insufficient information to identify the exact cause."

    suggested_fix = (
        "Review execution logs and reproduce the failure."
    )

    reproduction_steps = (
        "1. Open the registered website.\n"
        "2. Execute the failed test again.\n"
        "3. Review browser output and error details."
    )

    # --------------------------------------------------
    # 3. Python application errors
    # --------------------------------------------------

    python_errors = {
        "attributeerror": "Python attempted to access an unavailable object attribute.",
        "typeerror": "An operation received an incompatible data type or argument.",
        "keyerror": "The application attempted to access a missing dictionary key.",
        "nameerror": "The application referenced an undefined variable or name.",
        "importerror": "A required Python module or object could not be imported.",
        "modulenotfounderror": "A required Python package or module is unavailable.",
        "indexerror": "The application attempted to access an invalid sequence index.",
        "valueerror": "The application received an invalid value."
    }

    matched_exception = next(
        (
            exception
            for exception in python_errors
            if exception in error_text
        ),
        None
    )

    # --------------------------------------------------
    # 4. Evidence-based failure classification
    # --------------------------------------------------

    if matched_exception or "has no attribute" in error_text:
        title = "Backend Application Error"
        description = "A Python application error interrupted test execution."
        severity = "high"
        failure_type = "application_error"
        component = "backend_application"

        root_cause = (
            f"{matched_exception}: {python_errors[matched_exception]}"
            if matched_exception
            else error_message or actual_result
        )

        suggested_fix = (
            "Inspect the traceback, verify object types and function arguments, "
            "check database session handling and missing attributes, "
            "and add a regression test."
        )

    elif any(value in error_text for value in [
        "err_name_not_resolved",
        "name resolution",
        "failed to resolve",
        "dns lookup",
        "dns resolution"
    ]):
        title = "DNS Resolution Failure"
        description = "The browser could not resolve the target website hostname."
        severity = "high"
        failure_type = "infrastructure_error"
        component = "dns"

        root_cause = (
            "The target hostname could not be resolved to an IP address."
        )

        suggested_fix = (
            "Verify the domain spelling, DNS records, DNS server availability "
            "and network configuration."
        )

    elif any(value in error_text for value in [
        "connection refused",
        "connection reset",
        "network is unreachable",
        "connection timed out",
        "failed to connect"
    ]):
        title = "Network Connection Failure"
        description = "The test runner could not establish a connection."
        severity = "high"
        failure_type = "infrastructure_error"
        component = "network"

        root_cause = (
            "The connection to the target service could not be established "
            "or was interrupted."
        )

        suggested_fix = (
            "Check server availability, network connectivity, firewall rules, "
            "service ports and connection limits."
        )

    elif any(value in error_text for value in [
        "certificate verify failed",
        "cert_authority_invalid",
        "certificate error",
        "ssl"
    ]):
        title = "SSL Certificate Failure"
        description = "The browser could not establish a trusted HTTPS connection."
        severity = "high"
        failure_type = "infrastructure_error"
        component = "ssl_certificate"

        root_cause = (
            "The HTTPS certificate could not be validated or the TLS handshake failed."
        )

        suggested_fix = (
            "Check certificate validity, expiration, hostname matching, "
            "certificate chain and TLS configuration."
        )

    else:
        http_match = re.search(
            r"\bhttp\s+(4\d{2}|5\d{2})\b",
            error_text
        )

        if http_match:
            status_code = int(http_match.group(1))

            title = f"Website HTTP {status_code} Error"
            failure_type = "website_error"
            component = (
                "website_server"
                if status_code >= 500
                else "website_endpoint"
            )

            if status_code >= 500:
                severity = "high"
                description = "The website server returned a server-side error."
                root_cause = (
                    f"The server returned HTTP {status_code}, "
                    "indicating a server-side failure."
                )
                suggested_fix = (
                    "Inspect server logs, application exceptions, database "
                    "connectivity and service health."
                )

            elif status_code == 404:
                severity = "medium"
                description = "The requested website resource could not be found."
                root_cause = (
                    "The requested route or resource returned HTTP 404."
                )
                suggested_fix = (
                    "Verify the URL, routing configuration, resource existence "
                    "and navigation destination."
                )

            elif status_code in (401, 403):
                severity = "medium"
                description = (
                    "The requested resource requires authorization or permission."
                )
                root_cause = (
                    f"The server rejected the request with HTTP {status_code}."
                )
                suggested_fix = (
                    "Verify authentication, access permissions, session validity "
                    "and authorization rules."
                )

            else:
                severity = "medium"
                description = "The website returned a client-side HTTP error."
                root_cause = f"The server returned HTTP {status_code}."
                suggested_fix = (
                    "Inspect the request URL, request parameters, authentication "
                    "and endpoint configuration."
                )

        elif any(value in error_text for value in [
            "browser has been closed",
            "browser closed",
            "target closed",
            "page crashed",
            "playwright",
            "browser launch"
        ]):
            title = "Browser Execution Failure"
            description = "The browser automation process could not complete."
            severity = "high"
            failure_type = "browser_error"
            component = "browser_executor"

            root_cause = (
                "The browser process, page or automation session "
                "terminated unexpectedly."
            )

            suggested_fix = (
                "Verify browser installation, Playwright compatibility, "
                "available system resources and browser lifecycle management."
            )

        elif any(value in evidence_text for value in [
            "missing links",
            "missing link",
            "missing navigation",
            "navigation link not found"
        ]):
            title = "Website Navigation Link Failure"
            description = (
                "An expected navigation link was missing from the website."
            )
            severity = "medium"
            failure_type = "website_error"
            component = "website_navigation"

            root_cause = (
                "The website did not provide one or more expected navigation "
                "links. The navigation menu or rendered link elements "
                "may be incomplete."
            )

            suggested_fix = (
                "Inspect the navigation menu, verify link text and href "
                "attributes, and confirm that the destination exists."
            )

        elif failed_checks:
            title = "Website Functional or UI Check Failure"
            description = (
                f"{len(failed_checks)} execution check(s) failed. "
                "The individual check evidence is available below."
            )
            severity = "medium"
            failure_type = "website_ui_error"
            component = "website_ui"

            root_cause = (
                "One or more expected website conditions were not satisfied. "
                "The failed check details should be reviewed to determine "
                "whether the cause is a website defect, changed UI or "
                "an outdated test expectation."
            )

            suggested_fix = (
                "Reproduce each failed check, inspect the affected DOM "
                "elements and browser screenshot, and verify the expected "
                "behavior before changing the website or test."
            )

        elif any(value in error_text for value in [
            "element not found",
            "no element",
            "missing element",
            "locator"
        ]):
            title = "Website Element or Locator Failure"
            description = (
                "An expected website element could not be located."
            )
            severity = "medium"
            failure_type = "test_design_error"
            component = "test_executor"

            root_cause = (
                "The expected element or locator was not found in the "
                "rendered page. This may indicate a changed website "
                "structure or an outdated test locator."
            )

            suggested_fix = (
                "Inspect the DOM, verify element text and selectors, "
                "check page loading and update the test expectation "
                "if the website has changed."
            )

        elif "navigation" in error_text or "redirect" in error_text:
            title = "Website Navigation Failure"
            description = "An expected navigation operation did not complete."
            severity = "medium"
            failure_type = "website_error"
            component = "website_navigation"

            root_cause = (
                "The expected destination or navigation transition was not reached."
            )

            suggested_fix = (
                "Verify navigation links, route definitions, redirects, "
                "destination URLs and page loading behavior."
            )

        elif any(value in error_text for value in [
            "not visible",
            "visibility",
            "hidden element"
        ]):
            title = "Website Element Visibility Failure"
            description = "An expected element was not visible to the browser."
            severity = "medium"
            failure_type = "website_ui_error"
            component = "website_ui"

            root_cause = (
                "The expected element was hidden, obscured or not displayed."
            )

            suggested_fix = (
                "Inspect CSS visibility, responsive layout, overlays, "
                "element state and viewport dimensions."
            )

        elif "timeout" in error_text or "timed out" in error_text:
            title = "Website Loading or Execution Timeout"
            description = (
                "The expected browser operation did not finish within its time limit."
            )
            severity = "medium"
            failure_type = "browser_error"
            component = "browser_executor"

            root_cause = (
                "The page, network request or expected browser operation "
                "exceeded its configured timeout."
            )

            suggested_fix = (
                "Inspect network conditions, page load performance, locator "
                "wait conditions and timeout configuration."
            )

        elif error_message:
            title = "Test Execution Error"
            description = "An unexpected error occurred during test execution."
            severity = "medium"
            failure_type = "unknown"
            component = "unknown"

            root_cause = error_message

            suggested_fix = (
                "Review the full execution logs and reproduce the failure "
                "before applying a corrective change."
            )

    # --------------------------------------------------
    # 5. Add original test-case context
    # --------------------------------------------------

    context_parts = []

    if test_title:
        context_parts.append(f"Test case: {test_title}")

    if test_description:
        context_parts.append(f"Test description: {test_description}")

    if expected_result:
        context_parts.append(f"Expected result: {expected_result}")

    if context_parts:
        description += "\n\nTest context:\n" + "\n".join(context_parts)

    # --------------------------------------------------
    # 6. Add actual failed-check evidence
    # --------------------------------------------------

    if failed_checks:
        evidence_lines = [
            f"- {item['name']}: {item['details']}"
            for item in failed_checks
        ]

        description += (
            "\n\nFailed execution checks:\n"
            + "\n".join(evidence_lines)
        )

        root_cause += (
            "\n\nObserved evidence: "
            + failed_check_summary
        )

    elif checks:
        description += (
            f"\n\nExecution evidence: {len(checks)} check(s) "
            "were recorded, but no explicitly failed checks were identified."
        )

    # --------------------------------------------------
    # 7. Generate test-specific reproduction steps
    # --------------------------------------------------

    reproduction_parts = []

    if test_title:
        reproduction_parts.append(f"1. Open the registered website and locate: {test_title}.")
    else:
        reproduction_parts.append("1. Open the registered website.")

    if test_steps:
        reproduction_parts.append(
            f"2. Follow the original test steps: {test_steps}"
        )
    else:
        reproduction_parts.append(
            "2. Repeat the actions performed by the failed test."
        )

    if failed_checks:
        reproduction_parts.append(
            "3. Inspect the failed checks: "
            + failed_check_summary
        )
    else:
        reproduction_parts.append(
            "3. Review browser output, screenshot and error details."
        )

    reproduction_steps = "\n".join(reproduction_parts)

    # --------------------------------------------------
    # 8. Preserve existing output contract
    # --------------------------------------------------

    return {
        "title": title,
        "description": description,
        "severity": severity,
        "failure_type": failure_type,
        "component": component,
        "root_cause": root_cause,
        "suggested_fix": suggested_fix,
        "reproduction_steps": reproduction_steps,
        "screenshot_path": screenshot_path
    }
