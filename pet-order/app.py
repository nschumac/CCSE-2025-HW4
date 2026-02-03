from flask import Flask, request, jsonify
from pymongo import MongoClient
import requests
import os
import uuid
import random
from typing import Optional, Dict, List, Any

app = Flask(__name__)

# Configuration from environment variables
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://mongo:27017/')
PET_STORE_1_URL = os.environ.get('PET_STORE_1_URL', 'http://localhost:5001')
PET_STORE_2_URL = os.environ.get('PET_STORE_2_URL', 'http://localhost:5002')
PORT = int(os.environ.get('PORT', 5003))

# MongoDB setup
client = MongoClient(MONGODB_URI)
db = client['pet_order_db']
transactions_collection = db['transactions']

def get_pet_type_id(pet_type_str: str, store_num: int) -> Optional[str]:
    try:
        store_url = PET_STORE_1_URL if store_num == 1 else PET_STORE_2_URL
        response = requests.get(f"{store_url}/pet-types")
        if response.status_code == 200:
            pet_types = response.json()
            for pet_type_data in pet_types:
                # pet-store returns 'type' not 'name'
                if pet_type_data.get('type', '').lower() == pet_type_str.lower():
                    return pet_type_data.get('id')
    except requests.RequestException:
        pass
    return None

def get_available_pets(pet_type_str: str, store_num: int) -> List[Dict[str, Any]]:
    try:
        store_url = PET_STORE_1_URL if store_num == 1 else PET_STORE_2_URL
        
        # First get the pet-type ID
        pet_type_id = get_pet_type_id(pet_type_str, store_num)
        if pet_type_id is None:
            return []
        
        # Get pets of this type using the correct endpoint
        response = requests.get(f"{store_url}/pet-types/{pet_type_id}/pets")
        if response.status_code == 200:
            pets = response.json()
            # All pets returned from this endpoint are available
            return pets
    except requests.RequestException:
        pass
    return []

def delete_pet(pet_name: str, pet_type_str: str, store_num: int) -> bool:
    try:
        store_url = PET_STORE_1_URL if store_num == 1 else PET_STORE_2_URL
        
        # Get the pet-type ID first
        pet_type_id = get_pet_type_id(pet_type_str, store_num)
        if pet_type_id is None:
            return False
        
        # Use the correct endpoint structure
        response = requests.delete(f"{store_url}/pet-types/{pet_type_id}/pets/{pet_name}")
        return response.status_code == 204
    except requests.RequestException:
        return False

def find_and_purchase_pet(pet_type: str, store: Optional[int], pet_name: Optional[str]) -> Optional[Dict[str, Any]]:
    
    # Case 1: Both store and pet-name specified
    if store is not None and pet_name is not None:
        available_pets = get_available_pets(pet_type, store)
        for pet in available_pets:
            if pet.get('name') == pet_name:
                if delete_pet(pet_name, pet_type, store):
                    return {'store': store, 'pet_name': pet_name}
        return None
    
    # Case 2: Only store specified - choose random pet from that store
    if store is not None:
        available_pets = get_available_pets(pet_type, store)
        if available_pets:
            chosen_pet = random.choice(available_pets)
            if delete_pet(chosen_pet['name'], pet_type, store):
                return {'store': store, 'pet_name': chosen_pet['name']}
        return None
    
    # Case 3: No store specified - choose random pet from either store
    all_available_pets = []
    
    # Get pets from store 1
    pets_store_1 = get_available_pets(pet_type, 1)
    for pet in pets_store_1:
        pet['store'] = 1
        all_available_pets.append(pet)
    
    # Get pets from store 2
    pets_store_2 = get_available_pets(pet_type, 2)
    for pet in pets_store_2:
        pet['store'] = 2
        all_available_pets.append(pet)
    
    if all_available_pets:
        chosen_pet = random.choice(all_available_pets)
        if delete_pet(chosen_pet['name'], pet_type, chosen_pet['store']):
            return {'store': chosen_pet['store'], 'pet_name': chosen_pet['name']}
    
    return None

@app.route('/purchases', methods=['POST'])
def purchase_pet():
    # Check content type
    if request.content_type != 'application/json':
        return '', 415
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'purchaser' not in data or 'pet-type' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        purchaser = data['purchaser']
        pet_type = data['pet-type']
        store = data.get('store')  # Optional
        pet_name = data.get('pet-name')  # Optional
        
        # Validate store number if provided
        if store is not None and store not in [1, 2]:
            return jsonify({'error': 'Invalid store number'}), 400
        
        # Try to purchase the pet
        purchase_result = find_and_purchase_pet(pet_type, store, pet_name)
        
        if purchase_result is None:
            return jsonify({'error': 'No pet of this type is available'}), 400
        
        # Generate unique purchase ID
        purchase_id = str(uuid.uuid4())
        
        # Store transaction in MongoDB
        transaction = {
            'purchase-id': purchase_id,
            'purchaser': purchaser,
            'pet-type': pet_type,
            'store': purchase_result['store'],
            'pet-name': purchase_result['pet_name']
        }
        
        transactions_collection.insert_one(transaction)
        
        # Return success response
        response_data = {
            'purchase-id': purchase_id,
            'purchaser': purchaser,
            'pet-type': pet_type,
            'store': purchase_result['store'],
            'pet-name': purchase_result['pet_name']
        }
        
        return jsonify(response_data), 201
    
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/transactions', methods=['GET'])
def get_transactions():
    # Check authentication header
    auth_header = request.headers.get('OwnerPC')
    if auth_header != 'LovesPetsL2M3n4!':
        return '', 401
    
    # Build query from query string parameters
    query = {}
    
    # Check for store filter
    if 'store' in request.args:
        try:
            store_num = int(request.args.get('store'))
            query['store'] = store_num
        except ValueError:
            pass
    
    # Check for pet-type filter
    if 'pet-type' in request.args:
        query['pet-type'] = request.args.get('pet-type')
    
    # Check for purchaser filter
    if 'purchaser' in request.args:
        query['purchaser'] = request.args.get('purchaser')
    
    # Query MongoDB
    transactions = list(transactions_collection.find(query, {'_id': 0}))
    
    return jsonify(transactions), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed'}), 405

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)