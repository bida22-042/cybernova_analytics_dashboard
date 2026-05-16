# api.py
# CyberNova Analytics Real-Time Data Simulation API
# Student Name: Amantle Magotho
# Module: CET333 Product Development

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from faker import Faker
import random
import time
from datetime import datetime, timedelta
from threading import Thread
from collections import deque

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

fake = Faker()

# Service types with realistic prices
service_types = ["/aicyberassistant.php", "/networksecurityaudit.php", "/penetrationtesting.php", "/scheduleconsultation.php", "/webinar.php", "/whitepaper.php"]
service_prices = {
    "/aicyberassistant.php": 4200,
    "/networksecurityaudit.php": 3100,
    "/penetrationtesting.php": 5500,
    "/scheduleconsultation.php": 800,
    "/webinar.php": 0,
    "/whitepaper.php": 0,
}

marketing_sources = ["google_ads", "linkedin", "webinar", "email_campaign", "direct", "referral"]
industry_sectors = ["Financial", "Government", "SME", "Healthcare", "Retail", "Manufacturing"]
countries = {"Botswana": "168.167.0.0", "South Africa": "41.13.0.0", "Nigeria": "41.203.0.0", "Kenya": "41.80.0.0", "United Kingdom": "185.0.0.0", "United States": "128.0.0.0"}

data_buffer = deque(maxlen=500)

# Start date for data (January 1, 2024)
START_DATE = datetime(2024, 1, 1)

def generate_log_entry():
    # Spread data from January 2024 to present
    days_since_start = (datetime.now() - START_DATE).days
    days_ago = random.randint(0, max(days_since_start, 30))
    hours_ago = random.randint(0, 23)
    minutes_ago = random.randint(0, 59)
    timestamp = START_DATE + timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
    
    # Ensure timestamp is not in the future
    if timestamp > datetime.now():
        timestamp = datetime.now() - timedelta(hours=random.randint(1, 24))
    
    country = random.choice(list(countries.keys()))
    ip_parts = countries[country].split('.')
    ip = f"{ip_parts[0]}.{ip_parts[1]}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    service = random.choice(service_types)
    
    # 15% conversion rate for paid services
    is_conversion = random.random() < 0.15
    
    # Calculate revenue based on service price and conversion
    price = service_prices.get(service, 0)
    revenue = price * (1 if is_conversion else 0)
    
    satisfaction = random.randint(4, 5) if is_conversion else random.randint(1, 5)
    
    return {
        "timestamp": timestamp.isoformat(),
        "ip_address": ip,
        "country": country,
        "request": service,
        "status_code": 200,
        "marketing_source": random.choice(marketing_sources),
        "industry_sector": random.choice(industry_sectors),
        "satisfaction_rating": satisfaction,
        "converted_to_contract": 1 if is_conversion else 0,
        "revenue": revenue,  # Add revenue directly in API
        "webinar_registration": 1 if service == "/webinar.php" and random.random() < 0.3 else 0,
        "whitepaper_download": 1 if service == "/whitepaper.php" and random.random() < 0.4 else 0
    }

def generate_data_continuously():
    while True:
        data_buffer.append(generate_log_entry())
        time.sleep(0.5)

thread = Thread(target=generate_data_continuously, daemon=True)
thread.start()

# Pre-populate buffer with 500 records from 2024 to present
for i in range(500):
    data_buffer.append(generate_log_entry())

@app.get("/stream")
async def get_stream():
    return JSONResponse(content=list(data_buffer))

@app.get("/latest")
async def get_latest():
    if data_buffer:
        return JSONResponse(content=data_buffer[-1])
    return JSONResponse(content={})

@app.get("/health")
async def health_check():
    return {"status": "running", "buffer_size": len(data_buffer), "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)