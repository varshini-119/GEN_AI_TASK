import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
import os
import re
import pandas as pd
from urllib.parse import urljoin
from gemini_model import model
import time

# List of websites to scrape
websites = [
    "https://www.ikea.com/in/en/",
    "https://www.lvmh.com",
    "https://www.chanel.com",
    "https://www.hermes.com",
    "https://www.gucci.com",
    "https://www.pradagroup.com",
    "https://www.burberry.com",
    "https://www.rolex.com",
    "https://www.patek.com",
    "https://www.omega.com"
]

# Keywords to prioritize for relevant pages
RELEVANT_KEYWORDS = ["about", "company", "history", "mission", "team", "leadership", "values"]

# Check if the website is blocked based on response content
def is_blocked(response):
    blocked_indicators = ["Access Denied", "403 Forbidden", "captcha", "blocked", "Cloudflare", "Security Challenge"]
    return any(indicator.lower() in response.text.lower() for indicator in blocked_indicators)

# Step 1: Extract relevant links from the homepage
def get_relevant_links(base_url):
    try:
        response = requests.get(base_url, timeout=10)
        
        # Check if the website is blocked
        if response.status_code in [403, 429] or is_blocked(response):
            return None  # Return None to indicate blockage
        
        response.raise_for_status()
    
    except requests.RequestException:
        return None  # Return None if request fails

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    relevant_links = set()

    # Find and filter links based on relevant keywords
    for link in soup.find_all("a", href=True):
        full_url = urljoin(base_url, link["href"])
        if any(keyword in full_url.lower() for keyword in RELEVANT_KEYWORDS):
            relevant_links.add(full_url)

    return list(relevant_links)

# Step 2: Scrape and combine text content from relevant pages
def scrape_combined_text(urls):
    combined_text = ""

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text(" ", strip=True)
            combined_text += f"\n--- Content from {url} ---\n{page_text}"

        except requests.RequestException:
            pass 

    return combined_text

# Step 3: Extract company details using AI
def extract_company_details(text, website):
    if not text:
        return {} 
    
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

        # Extract JSON from AI response
        json_match = re.search(r"\{.*\}", response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())

    except Exception:
        return {} # Return empty dictionary if extraction fails
    return {}  # Return empty dictionary if response is invalid

# Step 4: Process each website and save results to CSV
def main():
    all_data = []

    for website in websites:
        print(f"Processing: {website}")
        relevant_links = get_relevant_links(website)

        # If site is blocked, set fields as "Not Available"
        if relevant_links is None:
            print(f"{website} is blocked. Skipping...")
            company_data = {
                "Website": website,
                "mission_statement": "Not Available",
                "products_or_services": "Not Available",
                "founded": "Not Available",
                "headquarters": "Not Available",
                "key_executives": "Not Available",
                "notable_awards": "Not Available"
            }
        else:
            combined_text = scrape_combined_text(relevant_links)
            company_data = {"Website": website}

            # Extract company details
            extracted_data = extract_company_details(combined_text, website)

            # Merge extracted data with company data
            company_data.update(extracted_data)
        
        all_data.append(company_data)
        time.sleep(2)  # Prevent rate limiting

    # Save results to CSV
    df = pd.DataFrame(all_data)
    df.to_csv("companydata.csv", index=False, encoding="utf-8")

    print("✅ Extraction complete. Data saved in 'companydata.csv'.")

if __name__ == "__main__":
    main()
