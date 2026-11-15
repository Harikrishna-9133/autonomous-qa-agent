
from types import SimpleNamespace

from app.services.bug_investigator import investigate_bug


test_cases = [
    {
        "name": "Missing Contact Link",
        "error": "missing links: contact",
        "expected": "website_error",
    },
    {
        "name": "Python Attribute Error",
        "error": "'dict' object has no attribute 'query'",
        "expected": "application_error",
    },
    {
        "name": "DNS Failure",
        "error": "net::ERR_NAME_NOT_RESOLVED",
        "expected": "infrastructure_error",
    },
    {
        "name": "Browser Crash",
        "error": "Page crashed during Playwright execution",
        "expected": "browser_error",
    },
    {
        "name": "HTTP 500 Error",
        "error": "HTTP 500 Internal Server Error",
        "expected": "website_error",
    },
    {
        "name": "Missing Element",
        "error": "Element not found: login button",
        "expected": "test_design_error",
    },
    {
        "name": "Navigation Failure",
        "error": "Navigation failed while opening dashboard",
        "expected": "website_error",
    },
    {
        "name": "Execution Timeout",
        "error": "Timeout while waiting for page load",
        "expected": "browser_error",
    },
]


print("\nADVANCED BUG INVESTIGATOR TESTS")
print("=" * 55)

passed = 0
failed = 0

for test in test_cases:
    test_result = SimpleNamespace(
        error_message=test["error"],
        actual_result="Test failed",
        screenshot_path=None,
    )

    analysis = investigate_bug(test_result)

    actual = analysis["failure_type"]
    expected = test["expected"]

    if actual == expected:
        print(f"PASS: {test['name']}")
        passed += 1
    else:
        print(f"FAIL: {test['name']}")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
        failed += 1

    print(f"  Severity: {analysis['severity']}")
    print(f"  Component: {analysis['component']}")
    print()

print("=" * 55)
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Total:  {len(test_cases)}")

if failed:
    raise SystemExit(1)

print("\nAll bug investigator tests passed!")
