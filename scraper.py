import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

# Target URL
URL = "https://www.agbro.com/"

def get_rates():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        rates_data = []

        cards = soup.find_all("div", class_="woodmart-info-box")

        for card in cards:
            try:
                # --- 1. CITY ---
                city_tag = card.find("div", class_="info-box-subtitle")
                if not city_tag:
                    continue 
                city = city_tag.get_text(strip=True)

                # --- 2. MAIN PRICE ---
                price_container = card.find("div", class_="info-box-inner")
                price = "0"
                if price_container:
                    strong_tag = price_container.find("strong")
                    if strong_tag:
                        price = strong_tag.get_text(strip=True)

                # --- 3. TREND & CHANGE ---
                trend = "stable"
                arrow_icon = card.find("i", class_="arrow")
                if arrow_icon:
                    icon_classes = arrow_icon.get("class", [])
                    if "down" in icon_classes:
                        trend = "down"
                    elif "up" in icon_classes:
                        trend = "up"
                
                change_value = ""
                all_text = price_container.get_text() if price_container else ""
                match_change = re.search(r'\(([-+]\d+)\)', all_text)
                if match_change:
                    change_value = match_change.group(1)

                # --- 4. OPEN & CLOSE (NEW!) ---
                open_rate = "N/A"
                close_rate = "N/A"
                
                # We search all paragraphs in the card for a pattern like "325 – 315"
                # The site uses a special en-dash (–), so we check for both types of dashes.
                paragraphs = card.find_all("p")
                for p in paragraphs:
                    p_text = p.get_text(strip=True)
                    # Regex explanation: (\d+) means capture digits, \s*[–-]\s* means allow dash with spaces
                    match_range = re.search(r'(\d+)\s*[–-]\s*(\d+)', p_text)
                    if match_range:
                        open_rate = match_range.group(1)
                        close_rate = match_range.group(2)
                        break # Stop once found

                # --- 5. DOC RATE ---
                doc_rate = "N/A"
                btn_wrapper = card.find("div", class_="woodmart-button-wrapper")
                if btn_wrapper:
                    link_tag = btn_wrapper.find("a")
                    if link_tag:
                        raw_text = link_tag.get_text(strip=True)
                        if ":" in raw_text:
                            doc_rate = raw_text.split(":")[1].strip()
                        else:
                            doc_rate = raw_text

                rates_data.append({
                    "city": city,
                    "price": price,
                    "trend": trend,
                    "change": change_value,
                    "open_rate": open_rate,   # New Field
                    "close_rate": close_rate, # New Field
                    "doc_rate": doc_rate
                })

            except AttributeError:
                continue
        
        output = {
            "status": "success",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "agbro.com",
            "data": rates_data
        }

        with open("rates.json", "w") as f:
            json.dump(output, f, indent=4)
            print("✅ Data with Open/Close scraped successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        error_data = {"status": "error", "message": str(e)}
        with open("rates.json", "w") as f:
            json.dump(error_data, f)

if __name__ == "__main__":
    get_rates()
