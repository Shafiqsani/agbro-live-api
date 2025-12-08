import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

# Target URL
URL = "https://www.agbro.com/"

def get_rates():
    # Headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(URL, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        rates_data = []

        # 1. Find all "Info Boxes" (the cards)
        cards = soup.find_all("div", class_="woodmart-info-box")

        for card in cards:
            try:
                # 2. Extract City Name
                # We skip the card if it doesn't have a subtitle (like the Date card)
                city_tag = card.find("div", class_="info-box-subtitle")
                if not city_tag:
                    continue 
                
                city = city_tag.get_text(strip=True)

                # 3. Extract Price
                # The price is inside the .info-box-inner div, usually inside a <strong> tag
                price_container = card.find("div", class_="info-box-inner")
                price = "0"
                if price_container:
                    # We find the first <strong> tag which holds the main price
                    strong_tag = price_container.find("strong")
                    if strong_tag:
                        price = strong_tag.get_text(strip=True)

                # 4. Extract Trend (Up/Down)
                trend = "stable"
                # The HTML uses <i class="arrow down"> or <i class="arrow up">
                arrow_icon = card.find("i", class_="arrow")
                if arrow_icon:
                    icon_classes = arrow_icon.get("class", [])
                    if "down" in icon_classes:
                        trend = "down"
                    elif "up" in icon_classes:
                        trend = "up"
                
                # 5. Extract Trend Change Value (e.g., -5 or +6)
                # It is usually in the inner span with color #333333
                change_value = ""
                # We look for the text like (-5)
                all_text = price_container.get_text() if price_container else ""
                # Regex to find text inside parentheses like (-5) or (+6)
                match = re.search(r'\(([-+]\d+)\)', all_text)
                if match:
                    change_value = match.group(1)

                # 6. Extract DOC Rate (The button at the bottom)
                doc_rate = "N/A"
                btn_wrapper = card.find("div", class_="woodmart-button-wrapper")
                if btn_wrapper:
                    link_tag = btn_wrapper.find("a")
                    if link_tag:
                        # Text is usually "DOC: 120.5". We split by ":" to get just the number
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
                    "doc_rate": doc_rate
                })

            except AttributeError as e:
                continue
        
        # Create Final Output
        output = {
            "status": "success",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "agbro.com",
            "data": rates_data
        }

        # Save to JSON file
        with open("rates.json", "w") as f:
            json.dump(output, f, indent=4)
            print("✅ Success! Scraped data saved to rates.json")

    except Exception as e:
        print(f"❌ Error: {e}")
        error_data = {"status": "error", "message": str(e)}
        with open("rates.json", "w") as f:
            json.dump(error_data, f)

if __name__ == "__main__":
    get_rates()