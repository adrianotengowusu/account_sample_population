import uuid
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from faker import Faker
import requests
import json

# ----------------- CONFIGURATION -----------------
KLAVIYO_PRIVATE_API_KEY = "YOUR_PRIVATE_API_KEY"
NUM_USERS = 10  # Number of simulated users
XML_PATH = "FGC Product Feed - Sheet1.xml"

# API endpoint for events as per the example.
EVENT_URL = "https://a.klaviyo.com/api/events"

# Headers required by the Klaviyo API.
HEADERS = {
    "accept": "application/vnd.api+json",
    "revision": "2025-01-15",
    "content-type": "application/vnd.api+json",
    "Authorization": f"Klaviyo-API-Key {KLAVIYO_PRIVATE_API_KEY}"
}

# A list of shipping countries (for simulation).
UK_COUNTRIES = ["United Kingdom", "Ireland", "Isle of Man", "Jersey", "Guernsey"]

# Initialize Faker for realistic dummy data.
faker = Faker()

# ----------------- LOAD PRODUCT DATA -----------------
def load_products_from_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    products = []
    for product in root.findall("product"):
        products.append({
            "id": product.find("id").text,
            "title": product.find("title").text,
            "price": float(product.find("price").text),
            "category": product.find("category").text,
            "url": product.find("url").text,
            "image_url": product.find("image_url").text,
            "inventory": int(product.find("inventory").text),
            "rating": float(product.find("rating").text),
        })
    return products

products = load_products_from_xml(XML_PATH)

# ----------------- PROFILE CREATION -----------------
def create_fake_profile():
    first_name = faker.first_name()
    last_name = faker.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}@klaviyo-demo.com"
    preferences = {
        "preference_type": random.choice(["glasses", "contact lenses"]),
        "frame_shape": random.choice(["round", "square", "rectangle", "aviator", "cat-eye"]),
        "preferred_colour": random.choice(["black", "brown", "blue", "red", "tortoise"]),
        "prescription": random.choice(["short-sighted", "long-sighted", "astigmatism"]),
        "subscriber": random.choice([True, False]),
        "source": random.choice(["newsletter", "partner_website", "google", "bing", "facebook", "instagram", "twitter", "linkedin"])
    }
    return {
        "id": str(uuid.uuid4()),
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        **preferences,
    }

# ----------------- TIMESTAMP UTILITY -----------------
def generate_random_timestamp_within_last_9_months():
    now = datetime.now()
    start_range = now - timedelta(days=270)  # Approximately 9 months
    random_days = random.randint(0, 270)
    random_seconds = random.randint(0, 86400)  # seconds in a day
    return start_range + timedelta(days=random_days, seconds=random_seconds)

# ----------------- EVENT CREATION -----------------
def send_event(profile, event_name, timestamp, product=None, quantity=1, completed_checkout=True, shipping_country=None):
    # Convert timestamp to ISO format (timestamp is a datetime object)
    ts_iso = timestamp.isoformat()
    
    # Build event properties from product info if provided.
    properties = {}
    if product:
        total_price = round(product["price"] * quantity, 2)
        properties.update({
            "product_id": product["id"],
            "product_name": product["title"],
            "quantity": quantity,
            "price_each": product["price"],
            "total_price": total_price,
            "category": product["category"],
            "image_url": product["image_url"],
            "product_url": product["url"]
        })
        if shipping_country:
            properties["shipping_country"] = shipping_country
        if event_name == "Started Checkout":
            properties["checkout_completed"] = completed_checkout
        value = total_price
    else:
        value = 0.0

    # Construct payload following the sample format.
    payload = {
        "data": {
            "type": "event",
            "attributes": {
                "properties": properties,
                "metric": {
                    "data": {
                        "type": "metric",
                        "attributes": {
                            "name": event_name
                        }
                    }
                },
                "profile": {
                    "data": {
                        "type": "profile",
                        "attributes": {
                            "email": profile["email"],
                            "first_name": profile["first_name"],
                            "last_name": profile["last_name"],
                            "properties": {
                                "Preference Type": profile["preference_type"],
                                "Frame Shape": profile["frame_shape"],
                                "Preferred Colour": profile["preferred_colour"],
                                "Prescription": profile["prescription"],
                                "Subscriber": profile["subscriber"],
                                "$source": profile["source"]
                            }
                        }
                    }
                },
                "time": ts_iso,
                "value": value
            }
        }
    }
    response = requests.post(EVENT_URL, headers=HEADERS, data=json.dumps(payload))
    print(f"Event '{event_name}' for {profile['email']} at {ts_iso}: Status {response.status_code}")
    return response

# ----------------- SIMULATION WORKFLOW -----------------
def simulate_users(n=NUM_USERS):
    for _ in range(n):
        profile = create_fake_profile()
        
        
        # Randomly simulate between 1 and 5 shopping sessions for this user.
        num_sessions = random.randint(1, 5)
        for _ in range(num_sessions):
            product = random.choice(products)
            quantity = random.randint(1, 4)

            # Get an initial timestamp for this session.
            session_timestamp = generate_random_timestamp_within_last_9_months()
            
            # Simulate an "Active on Site" event.
            send_event(profile, "Active on Site", timestamp=session_timestamp)
            
            # Event order within session:
            # 1. Viewed Product
            session_timestamp += timedelta(seconds=2)
            send_event(profile, "Viewed Product", timestamp=session_timestamp, product=product)
            
            # Increment timestamp by 2 seconds
            session_timestamp += timedelta(seconds=2)
            # 2. Added to Cart
            send_event(profile, "Added to Cart", timestamp=session_timestamp, product=product, quantity=quantity)
            
            # Increment timestamp by another 2 seconds
            session_timestamp += timedelta(seconds=2)
            # 3. Started Checkout (simulate checkout completion randomly)
            checkout_completed = random.choice([True, False])
            send_event(profile, "Started Checkout", timestamp=session_timestamp, product=product, quantity=quantity, completed_checkout=checkout_completed, shipping_country=random.choice(UK_COUNTRIES))
            

            if checkout_completed == False:
                continue

            # Increment timestamp by another 2 seconds
            session_timestamp += timedelta(seconds=2)
            # 4. Placed Order
            send_event(profile, "Placed Order", timestamp=session_timestamp, product=product, quantity=quantity, shipping_country=random.choice(UK_COUNTRIES))

# ----------------- MAIN EXECUTION -----------------
if __name__ == "__main__":
    simulate_users()
