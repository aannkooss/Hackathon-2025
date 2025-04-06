import requests
from bs4 import BeautifulSoup
import urllib.parse
import argparse

BASE_URL = "https://podcastaddict.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def extract_slug_from_name(name):
    """Search Podcast Addict and extract human-readable podcast name from the first result."""
    query = urllib.parse.quote_plus(name)
    search_url = f"{BASE_URL}/?q={query}"
    print(f"\n🔍 Searching: {name} → {search_url}")

    try:
        response = requests.get(search_url, headers=HEADERS)

        soup = BeautifulSoup(response.text, 'html.parser')
        podcast_tab = soup.find("div", id="tab-podcasts")
        if not podcast_tab:
            print("❌ No podcast tab found.")
            return None

        first_result = podcast_tab.find("a", class_="clickeableItemRow")
        if not first_result:
            print("❌ No podcast result found.")
            return None

        href = first_result.get("href")
        if not href or "/podcast/" not in href:
            print("⚠️ Invalid podcast href.")
            return None

        # Extract the slug and convert to human-readable name
        slug = href.split("/podcast/")[-1].split("/")[0]
        readable_name = slug.replace("-", " ").replace("+", " ").strip()
        print(f"✅ Extracted name: {readable_name}")
        return readable_name

    except Exception as e:
        print(f"⚠️ Error while processing '{name}': {e}")
        return None

def extract_all_names(name_string):
    podcast_names = ""
    if not isinstance(name_string, str):
        for name in name_string:
            podcast_names += name + ","
    else: 
        podcast_names = name_string
    podcast_names = [name.strip() for name in podcast_names.split(",") if name.strip()]
    readable_names = []

    for podcast in podcast_names:
        result = extract_slug_from_name(podcast)
        if result:
            readable_names.append(result)

    return readable_names

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract podcast names from Podcast Addict search results.")
    parser.add_argument("--names", type=str, required=True, help="Comma-separated podcast names")
    args = parser.parse_args()

    final_names = extract_all_names(args.names)
    print("\n📋 Final extracted names:")
    for name in final_names:
        print(f"- {name}")
