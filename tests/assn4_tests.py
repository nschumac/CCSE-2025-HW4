import requests
import pytest

BASE_URL_STORE_1 = "http://localhost:5001"
BASE_URL_STORE_2 = "http://localhost:5002"
BASE_URL_ORDER = "http://localhost:5003"

# Pet Types
PET_TYPE1 = {"type": "Golden Retriever"}
PET_TYPE1_VAL = {
    "type": "Golden Retriever",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": [],
    "lifespan": 12
}

PET_TYPE2 = {"type": "Australian Shepherd"}
PET_TYPE2_VAL = {
    "type": "Australian Shepherd",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": ["Loyal", "outgoing", "and", "friendly"],
    "lifespan": 15
}

PET_TYPE3 = {"type": "Abyssinian"}
PET_TYPE3_VAL = {
    "type": "Abyssinian",
    "family": "Felidae",
    "genus": "Felis",
    "attributes": ["Intelligent", "and", "curious"],
    "lifespan": 13
}

PET_TYPE4 = {"type": "bulldog"}
PET_TYPE4_VAL = {
    "type": "bulldog",
    "family": "Canidae",
    "genus": "Canis",
    "attributes": ["Gentle", "calm", "and", "affectionate"],
    "lifespan": None
}

# Pets
PET1_TYPE1 = {"name": "Lander", "birthdate": "14-05-2020"}
PET2_TYPE1 = {"name": "Lanky"}
PET3_TYPE1 = {"name": "Shelly", "birthdate": "07-07-2019"}
PET4_TYPE2 = {"name": "Felicity", "birthdate": "27-11-2011"}
PET5_TYPE3 = {"name": "Muscles"}
PET6_TYPE3 = {"name": "Junior"}
PET7_TYPE4 = {"name": "Lazy", "birthdate": "07-08-2018"}
PET8_TYPE4 = {"name": "Lemon", "birthdate": "27-03-2020"}

# Global dictionary to store IDs between tests
pet_type_ids = {}


def test_01_post_pet_types_to_store1():
    """Test posting PET_TYPE1, PET_TYPE2, PET_TYPE3 to pet-store #1"""
    
    # POST PET_TYPE1
    response = requests.post(f"{BASE_URL_STORE_1}/pet-types", json=PET_TYPE1)
    assert response.status_code == 201
    data = response.json()
    assert data["family"] == PET_TYPE1_VAL["family"]
    assert data["genus"] == PET_TYPE1_VAL["genus"]
    assert "id" in data
    pet_type_ids["id_1"] = data["id"]
    
    # POST PET_TYPE2
    response = requests.post(f"{BASE_URL_STORE_1}/pet-types", json=PET_TYPE2)
    assert response.status_code == 201
    data = response.json()
    assert data["family"] == PET_TYPE2_VAL["family"]
    assert data["genus"] == PET_TYPE2_VAL["genus"]
    assert "id" in data
    pet_type_ids["id_2"] = data["id"]
    
    # POST PET_TYPE3
    response = requests.post(f"{BASE_URL_STORE_1}/pet-types", json=PET_TYPE3)
    assert response.status_code == 201
    data = response.json()
    assert data["family"] == PET_TYPE3_VAL["family"]
    assert data["genus"] == PET_TYPE3_VAL["genus"]
    assert "id" in data
    pet_type_ids["id_3"] = data["id"]
    
    # Verify all IDs are unique
    ids = [pet_type_ids["id_1"], pet_type_ids["id_2"], pet_type_ids["id_3"]]
    assert len(ids) == len(set(ids)), "IDs must be unique"


def test_02_post_pet_types_to_store2():
    """Test posting PET_TYPE1, PET_TYPE2, PET_TYPE4 to pet-store #2"""
    
    # POST PET_TYPE1
    response = requests.post(f"{BASE_URL_STORE_2}/pet-types", json=PET_TYPE1)
    assert response.status_code == 201
    data = response.json()
    assert data["family"] == PET_TYPE1_VAL["family"]
    assert data["genus"] == PET_TYPE1_VAL["genus"]
    assert "id" in data
    pet_type_ids["id_4"] = data["id"]
    
    # POST PET_TYPE2
    response = requests.post(f"{BASE_URL_STORE_2}/pet-types", json=PET_TYPE2)
    assert response.status_code == 201
    data = response.json()
    assert data["family"] == PET_TYPE2_VAL["family"]
    assert data["genus"] == PET_TYPE2_VAL["genus"]
    assert "id" in data
    pet_type_ids["id_5"] = data["id"]
    
    # POST PET_TYPE4
    response = requests.post(f"{BASE_URL_STORE_2}/pet-types", json=PET_TYPE4)
    assert response.status_code == 201
    data = response.json()
    assert data["family"] == PET_TYPE4_VAL["family"]
    assert data["genus"] == PET_TYPE4_VAL["genus"]
    assert "id" in data
    pet_type_ids["id_6"] = data["id"]
    
    # Verify all 6 IDs are unique
    all_ids = [pet_type_ids[f"id_{i}"] for i in range(1, 7)]
    assert len(all_ids) == len(set(all_ids)), "All IDs must be unique"


def test_03_post_pets_to_store1_type1():
    """Test posting PET1_TYPE1 and PET2_TYPE1 to pet-store #1"""
    
    id_1 = pet_type_ids["id_1"]
    
    # POST PET1_TYPE1
    response = requests.post(f"{BASE_URL_STORE_1}/pet-types/{id_1}/pets", json=PET1_TYPE1)
    assert response.status_code == 201
    
    # POST PET2_TYPE1
    response = requests.post(f"{BASE_URL_STORE_1}/pet-types/{id_1}/pets", json=PET2_TYPE1)
    assert response.status_code == 201


def test_04_post_pets_to_store1_type3():
    """Test posting PET5_TYPE3 and PET6_TYPE3 to pet-store #1"""
    
    id_3 = pet_type_ids["id_3"]
    
    # POST PET5_TYPE3
    response = requests.post(f"{BASE_URL_STORE_1}/pet-types/{id_3}/pets", json=PET5_TYPE3)
    assert response.status_code == 201
    
    # POST PET6_TYPE3
    response = requests.post(f"{BASE_URL_STORE_1}/pet-types/{id_3}/pets", json=PET6_TYPE3)
    assert response.status_code == 201


def test_05_post_pet_to_store2_type1():
    """Test posting PET3_TYPE1 to pet-store #2"""
    
    id_4 = pet_type_ids["id_4"]
    
    response = requests.post(f"{BASE_URL_STORE_2}/pet-types/{id_4}/pets", json=PET3_TYPE1)
    assert response.status_code == 201


def test_06_post_pet_to_store2_type2():
    """Test posting PET4_TYPE2 to pet-store #2"""
    
    id_5 = pet_type_ids["id_5"]
    
    response = requests.post(f"{BASE_URL_STORE_2}/pet-types/{id_5}/pets", json=PET4_TYPE2)
    assert response.status_code == 201


def test_07_post_pets_to_store2_type4():
    """Test posting PET7_TYPE4 and PET8_TYPE4 to pet-store #2"""
    
    id_6 = pet_type_ids["id_6"]
    
    # POST PET7_TYPE4
    response = requests.post(f"{BASE_URL_STORE_2}/pet-types/{id_6}/pets", json=PET7_TYPE4)
    assert response.status_code == 201
    
    # POST PET8_TYPE4
    response = requests.post(f"{BASE_URL_STORE_2}/pet-types/{id_6}/pets", json=PET8_TYPE4)
    assert response.status_code == 201


def test_08_get_pet_type_by_id():
    """Test GET /pet-types/{id2} from pet-store #1"""
    
    id_2 = pet_type_ids["id_2"]
    
    response = requests.get(f"{BASE_URL_STORE_1}/pet-types/{id_2}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["type"] == PET_TYPE2_VAL["type"]
    assert data["family"] == PET_TYPE2_VAL["family"]
    assert data["genus"] == PET_TYPE2_VAL["genus"]
    assert data["attributes"] == PET_TYPE2_VAL["attributes"]
    assert data["lifespan"] == PET_TYPE2_VAL["lifespan"]


def test_09_get_pets_for_type():
    """Test GET /pet-types/{id6}/pets from pet-store #2"""
    
    id_6 = pet_type_ids["id_6"]
    
    response = requests.get(f"{BASE_URL_STORE_2}/pet-types/{id_6}/pets")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    # Verify both pets are present
    names = [pet["name"] for pet in data]
    assert "Lazy" in names
    assert "Lemon" in names
    
    # Verify pet details
    for pet in data:
        if pet["name"] == "Lazy":
            assert pet["birthdate"] == PET7_TYPE4["birthdate"]
        elif pet["name"] == "Lemon":
            assert pet["birthdate"] == PET8_TYPE4["birthdate"]