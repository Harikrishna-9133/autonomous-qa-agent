
from pprint import pprint

from app.services.website_explorer import explore_website
from app.agents.explorer_node import extract_features


url = "https://harikrishnaportfolio-nine.vercel.app/"

print("\nStarting website exploration...\n")

# Step 1: Explore the website
result = explore_website(url)


# Step 2: Display exploration summary
print("\n========== EXPLORATION SUMMARY ==========")
pprint(result["summary"])


# Step 3: Display discovered pages and elements
for page in result["pages"]:
    print("\n========== PAGE DETAILS ==========")
    print("URL:", page.get("url"))
    print("Title:", page.get("page_title"))
    print("HTTP Status:", page.get("http_status"))
    print("Headings:", page.get("headings"))
    print("Buttons:", page.get("buttons"))
    print("Forms:", page.get("forms"))
    print("Inputs:", page.get("inputs"))


# Step 4: Automatically detect website features
print("\n========== AUTOMATIC FEATURE DETECTION ==========")

features = extract_features(result)

for feature in features:
    print("-", feature)

print("\nTotal detected features:", len(features))


print("\n========== EXPLORATION COMPLETED ==========")
