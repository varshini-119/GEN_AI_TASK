import time
import re
import json
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from gemini_model import model

COMMON_KEYWORDS = [
    "mission", "vision", "values", "ethics", "sustainability", "leadership","about","company",    "executives", "our-story", "who-we-are", "governance", "team", "culture",
    "social-responsibility", "impact", "principles", "philosophy", "brand-story",
    "heritage", "legacy", "purpose", "csr", "initiatives", "innovation","history", "governance",
    "environment", "diversity", "inclusion", "careers", "investors", "partners","corporate", "leadership", "executives",
    "contact", "media", "news", "awards", "recognition", "CEO", "founder", "headquarters",
    "diversity", "inclusion", "careers", "investors", "locations", "suppliers"
]



# Step 1: Extract Relevant Links
def get_relevant_links(base_url, page):
    print(f"🔎 Navigating to {base_url}...")

    page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    })
    
    # Prevent detection
    page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) }")

    try:
        page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
    except Exception as e:
        print(f"❌ Failed to navigate: {e}")
        return []

    page.set_viewport_size({"width": 375, "height": 812})  # Mobile viewport
    soup = BeautifulSoup(page.content(), "html.parser")
    relevant_links = set()

    for link in soup.find_all("a", href=True):
        full_url = urljoin(base_url, link["href"])
        if any(keyword in full_url.lower() for keyword in COMMON_KEYWORDS):
            relevant_links.add(full_url)

    print(f"🔗 Found {len(relevant_links)} relevant links.")
    return list(relevant_links)

# Step 2: Scrape Text from Relevant Pages
def scrape_combined_text(urls, page):
    combined_text = ""
    for url in urls:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            # Scroll to load dynamic content
            for _ in range(2):
                page.keyboard.press("End")
                time.sleep(2)

            soup = BeautifulSoup(page.content(), "html.parser")
            page_text = soup.get_text(" ", strip=True)
            combined_text += f"\n--- Content from {url} ---\n{page_text}"

        except Exception as e:
            print(f"⚠️ Skipping {url} due to error: {e}")

    return combined_text

# Step 3: Extract Company Details using Gemini AI
def extract_company_details(text, website):
    if not text:
        return {"error": "No content available"}

    prompt = f"""
    Extract key company details from the following text about {website}.
    Return the response as a structured JSON object:
    
    Text: {text}

    Respond only with valid JSON:
    {{
        "mission_statement": "...",
        "products_or_services": "...",
        "founded": "...",
        "headquarters": "...",
        "key_executives": "...",
        "notable_awards": "..."
    }}
    """
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"❌ Gemini AI error: {e}")
        return {"error": "Gemini AI request failed"}

    return {"error": "Invalid response from AI"}

# Step 4: Save Extracted Data to CSV
def save_to_csv(company_data, filename="dynamic_websites_data.csv"):
    new_df = pd.DataFrame([company_data])

    try:
        existing_df = pd.read_csv(filename)
        final_df = pd.concat([existing_df, new_df], ignore_index=True)
    except FileNotFoundError:
        final_df = new_df  # If no existing file, create a new one

    final_df.to_csv(filename, index=False, encoding="utf-8")
    print(f"✅ Data saved to '{filename}'.")

# Main function
def main():
    urls= [
    "https://www.gucci.com/int/en/nst/about-gucci",
    "https://in.burberry.com/"]
    for url in urls:
        website = url
        print(f"🌐 Scraping website: {website}")

        with sync_playwright() as p:
            browser = p.webkit.launch(  # Use WebKit for better anti-bot handling
                headless=False,  # Run with UI to debug, change to True after testing
                args=[
                    "--disable-http2",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            page = browser.new_page()
            
            relevant_links = get_relevant_links(website, page)
            if not relevant_links:
                print(f"⚠️ No relevant links found for {website}")
                return
            
            combined_text = scrape_combined_text(relevant_links, page)
            extracted_data = extract_company_details(combined_text, website)

            dynamic_websites_data = {"Website": website}
            dynamic_websites_data.update(extracted_data)

            save_to_csv(dynamic_websites_data)

            browser.close()

    print("🚀 Scraping process completed.")

if __name__ == "__main__":
    main()
