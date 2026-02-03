#!/usr/bin/env python3
import requests
import sys
import time

BASE_URL_STORE_1 = "http://localhost:5001"
BASE_URL_STORE_2 = "http://localhost:5002"

# Pet Types
PET_TYPE1 = {"type": "GoldenRetriever"}
PET_TYPE2 = {"type": "AustralianShepherd"}
PET_TYPE3 = {"type": "Abyssinian"}
PET_TYPE4 = {"type": "bulldog"}

# Pets
PET1_TYPE1 = {"name": "Lander", "birthdate": "14-05-2020"}
PET2_TYPE1 = {"name": "Lanky"}
PET3_TYPE1 = {"name": "Shelly", "birthdate": "07-07-2019"}
PET4_TYPE2 = {"name": "Felicity", "birthdate": "27-11-2011"}
PET5_TYPE3 = {"name": "Muscles"}
PET6_TYPE3 = {"name": "Junior"}
PET7_TYPE4 = {"name": "Lazy", "birthdate": "07-08-2018"}
PET8_TYPE4 = {"name": "Lemon", "birthdate": "27-03-2020"}

def wait_for_services():
    """Wait for services to be ready"""
    max_retries = 30
    for i in range(max_retries):
        try:
            r1 = requests.get(f"{BASE_URL_STORE_1}/pet-types", timeout=2)
            r2 = requests.get(f"{BASE_URL_STORE_2}/pet-types", timeout=2)
            if r1.ok and r2.ok:
                print("Services are ready")
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    return False

def post_pet_type(url, pet_type_data, description):
    """POST a pet type and return its ID with error handling"""
    try:
        response = requests.post(url, json=pet_type_data, timeout=10)
        if response.status_code != 201:
            print(f"ERROR: {description} failed with status {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
        
        data = response.json()
        if "id" not in data:
            print(f"ERROR: {description} response missing 'id' field")
            print(f"Response: {data}")
            sys.exit(1)
            
        return data["id"]
    except requests.RequestException as e:
        print(f"ERROR: {description} request failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {description} unexpected error: {e}")
        sys.exit(1)

def main():
    # Wait for services to be ready
    if not wait_for_services():
        print("ERROR: Services did not become ready in time")
        sys.exit(1)
    
    # Step 1: POST to store 1
    id_1 = post_pet_type(f"{BASE_URL_STORE_1}/pet-types", PET_TYPE1, "POST PET_TYPE1 to store 1")
    id_2 = post_pet_type(f"{BASE_URL_STORE_1}/pet-types", PET_TYPE2, "POST PET_TYPE2 to store 1")
    id_3 = post_pet_type(f"{BASE_URL_STORE_1}/pet-types", PET_TYPE3, "POST PET_TYPE3 to store 1")
    
    # Step 2: POST to store 2
    id_4 = post_pet_type(f"{BASE_URL_STORE_2}/pet-types", PET_TYPE1, "POST PET_TYPE1 to store 2")
    id_5 = post_pet_type(f"{BASE_URL_STORE_2}/pet-types", PET_TYPE2, "POST PET_TYPE2 to store 2")
    id_6 = post_pet_type(f"{BASE_URL_STORE_2}/pet-types", PET_TYPE4, "POST PET_TYPE4 to store 2")
    
    # Step 3-4: POST pets to store 1
    requests.post(f"{BASE_URL_STORE_1}/pet-types/{id_1}/pets", json=PET1_TYPE1)
    requests.post(f"{BASE_URL_STORE_1}/pet-types/{id_1}/pets", json=PET2_TYPE1)
    requests.post(f"{BASE_URL_STORE_1}/pet-types/{id_3}/pets", json=PET5_TYPE3)
    requests.post(f"{BASE_URL_STORE_1}/pet-types/{id_3}/pets", json=PET6_TYPE3)
    
    # Step 5-7: POST pets to store 2
    requests.post(f"{BASE_URL_STORE_2}/pet-types/{id_4}/pets", json=PET3_TYPE1)
    requests.post(f"{BASE_URL_STORE_2}/pet-types/{id_5}/pets", json=PET4_TYPE2)
    requests.post(f"{BASE_URL_STORE_2}/pet-types/{id_6}/pets", json=PET7_TYPE4)
    requests.post(f"{BASE_URL_STORE_2}/pet-types/{id_6}/pets", json=PET8_TYPE4)
    
    print("Setup complete")
    return id_1, id_2, id_3, id_4, id_5, id_6

if __name__ == "__main__":
    main()