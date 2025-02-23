import mysql.connector
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Define RedBus URLs for different states
STATE_URLS = {
     "Andhra Pradesh": "https://www.redbus.in/online-booking/apsrtc/?utm_source=rtchometile",
    "Assam": "https://www.redbus.in/online-booking/astc/?utm_source=rtchometile",
    "Chandigarh": "https://www.redbus.in/online-booking/chandigarh-transport-undertaking-ctu",
    "Himachal Pradesh": "https://www.redbus.in/online-booking/hrtc/?utm_source=rtchometile",
    "Jammu & Kashmir": "https://www.redbus.in/online-booking/jksrtc",
    "Assam (KAAC)": "https://www.redbus.in/online-booking/kaac-transport",
    "Goa": "https://www.redbus.in/online-booking/ktcl/?utm_source=rtchometile",
    "Kerala (KSRTC)": "https://www.redbus.in/online-booking/ksrtc-kerala/?utm_source=rtchometile",
    "Rajasthan": "https://www.redbus.in/online-booking/rsrtc/?utm_source=rtchometile",
    "West Bengal (SBSTC)": "https://www.redbus.in/online-booking/south-bengal-state-transport-corporation-sbstc/?utm_source=rtchometile",
    "Telangana (TSRTC)": "https://www.redbus.in/online-booking/tsrtc/?utm_source=rtchometile",
    "Uttar Pradesh": "https://www.redbus.in/online-booking/uttar-pradesh-state-road-transport-corporation-upsrtc/?utm_source=rtchometile",
    "West Bengal (WBTC)": "https://www.redbus.in/online-booking/wbtc-ctc/?utm_source=rtchometile",
    "West Bengal Transport": "https://www.redbus.in/online-booking/west-bengal-transport-corporation?utm_source=rtchometile"
}

# MySQL Database Setup
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Change this if your MySQL has a password
    "password": "",   # Default XAMPP MySQL has no password
    "database": "bus_details"
}

TABLE_NAME = "bus_info"

# Create MySQL Database & Table
def initialize_database():
    conn = mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    cursor = conn.cursor()

    # Create Database if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    conn.database = DB_CONFIG["database"]

    # Create Table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            Id INT AUTO_INCREMENT PRIMARY KEY,
            State VARCHAR(100),
            Route_Name TEXT,
            Route_Link TEXT,
            Bus_Name TEXT,
            Bus_Type TEXT,
            Departing_Time VARCHAR(100),
            Duration TEXT,
            Reaching_Time VARCHAR(100),
            Star_Rating FLOAT,
            Price FLOAT,
            Seat_Availability INT
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Initialize Selenium WebDriver
def initialize_driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    return driver

# Load a webpage
def load_page(driver, url):
    driver.get(url)
    time.sleep(5)  # Allow page to load

# Scrape bus routes
def scrape_bus_routes(driver):
    route_elements = driver.find_elements(By.CLASS_NAME, 'route')
    bus_routes_link = [route.get_attribute('href') for route in route_elements]
    bus_routes_name = [route.text.strip() for route in route_elements]
    return bus_routes_link, bus_routes_name

# Scrape bus details from a route
def scrape_bus_details(driver, url, route_name, state):
    try:
        driver.get(url)
        time.sleep(5)  # Allow the page to load

        try:
            view_buses_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "button"))
            )
            driver.execute_script("arguments[0].click();", view_buses_button)
            time.sleep(5)  # Wait for buses to load

            # Scroll down to load all buses
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            # Extract bus details
            bus_name_elements = driver.find_elements(By.CLASS_NAME, "travels.lh-24.f-bold.d-color")
            bus_type_elements = driver.find_elements(By.CLASS_NAME, "bus-type.f-12.m-top-16.l-color.evBus")
            departing_time_elements = driver.find_elements(By.CLASS_NAME, "dp-time.f-19.d-color.f-bold")
            duration_elements = driver.find_elements(By.CLASS_NAME, "dur.l-color.lh-24")
            reaching_time_elements = driver.find_elements(By.CLASS_NAME, "bp-time.f-19.d-color.disp-Inline")
            star_rating_elements = driver.find_elements(By.XPATH, "//div[@class='rating-sec lh-24']")
            price_elements = driver.find_elements(By.CLASS_NAME, "fare.d-block")
            seat_availability_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'seat-left m-top-30') or contains(@class, 'seat-left m-top-16')]")

            bus_details = []
            for i in range(len(bus_name_elements)):
                # Convert price: Remove 'INR ' and commas before converting
                price_text = price_elements[i].text.replace("INR ", "").replace(",", "")
                try:
                    price = float(price_text)
                except ValueError:
                    price = 0.0  # Default if conversion fails

                bus_detail = {
                    "State": state,
                    "Route_Name": route_name,
                    "Route_Link": url,
                    "Bus_Name": bus_name_elements[i].text,
                    "Bus_Type": bus_type_elements[i].text,
                    "Departing_Time": departing_time_elements[i].text,
                    "Duration": duration_elements[i].text,
                    "Reaching_Time": reaching_time_elements[i].text,
                    "Star_Rating": float(star_rating_elements[i].text) if i < len(star_rating_elements) else 0.0,
                    "Price": price,
                    "Seat_Availability": int(seat_availability_elements[i].text.split()[0]) if i < len(seat_availability_elements) else 0
                }
                bus_details.append(bus_detail)

            return bus_details

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return []

    except Exception as e:
        print(f"Error accessing {url}: {str(e)}")
        return []

# Save data to MySQL
def save_to_database(bus_data):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    for bus in bus_data:
        cursor.execute(f"""
            INSERT INTO {TABLE_NAME} 
            (State, Route_Name, Route_Link, Bus_Name, Bus_Type, Departing_Time, Duration, 
            Reaching_Time, Star_Rating, Price, Seat_Availability)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            bus["State"], bus["Route_Name"], bus["Route_Link"], bus["Bus_Name"], bus["Bus_Type"],
            bus["Departing_Time"], bus["Duration"], bus["Reaching_Time"], bus["Star_Rating"],
            bus["Price"], bus["Seat_Availability"]
        ))
    
    conn.commit()
    cursor.close()
    conn.close()

# Main scraping function
def scrape_all_states():
    driver = initialize_driver()
    all_bus_data = []

    for state, url in STATE_URLS.items():
        try:
            print(f"Scraping buses for {state}...")
            load_page(driver, url)
            bus_routes_link, bus_routes_name = scrape_bus_routes(driver)

            for link, name in zip(bus_routes_link, bus_routes_name):
                bus_details = scrape_bus_details(driver, link, name, state)
                if bus_details:
                    all_bus_data.extend(bus_details)

        except Exception as e:
            print(f"Error accessing {state} page: {str(e)}")

    driver.quit()
    save_to_database(all_bus_data)
    print("Scraping completed and data saved to MySQL.")

# Run the script
initialize_database()
scrape_all_states()
