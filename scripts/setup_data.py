#!/usr/bin/env python3
import requests

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

def main():
    # Step 1: POST to store 1
    r1 = requests.post(f"{BASE_URL_STORE_1}/pet-types", json=PET_TYPE1)
    id_1 = r1.json()["id"]
    
    r2 = requests.post(f"{BASE_URL_STORE_1}/pet-types", json=PET_TYPE2)
    id_2 = r2.json()["id"]
    
    r3 = requests.post(f"{BASE_URL_STORE_1}/pet-types", json=PET_TYPE3)
    id_3 = r3.json()["id"]
    
    # Step 2: POST to store 2
    r4 = requests.post(f"{BASE_URL_STORE_2}/pet-types", json=PET_TYPE1)
    id_4 = r4.json()["id"]
    
    r5 = requests.post(f"{BASE_URL_STORE_2}/pet-types", json=PET_TYPE2)
    id_5 = r5.json()["id"]
    
    r6 = requests.post(f"{BASE_URL_STORE_2}/pet-types", json=PET_TYPE4)
    id_6 = r6.json()["id"]
    
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

if __name__ == "__main__":
    main()