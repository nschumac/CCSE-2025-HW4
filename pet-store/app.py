from typing import Dict, List, Optional, Any, Tuple

from flask import Flask, request, make_response, send_file
import requests
import re
import os
import pymongo
from pymongo import MongoClient
from pymongo.collection import Collection

app = Flask(__name__)

# HTTP Error Responses
ERROR_400 = ({"error": "Malformed data"}, 400)
ERROR_404 = ({"error": "Not found"}, 404)
ERROR_415_JSON = ({"error": "Expected application/json media type"}, 415)

# External API Configuration
NINJA_API_KEY = os.environ.get("NINJA_API_KEY", "ahOqiuJCApa117bE961tGQ==cGu4SfUgfPsZ4DgH")
NINJA_API_BASE_URL = "https://api.api-ninjas.com/v1/animals"
API_TIMEOUT_SECONDS = 5

# Environment Configuration
STORE_ID = os.environ.get("STORE_ID", "1")
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://mongo:27017/")
PORT = int(os.environ.get("PORT", "5001"))

# MongoDB Setup (each store instance gets its own DB)
mongo_client = MongoClient(MONGODB_URI, maxPoolSize=10)
db = mongo_client[f"petstore_{STORE_ID}"]

pet_types_collection: Collection = db["pet_types"]
# Case-insensitive uniqueness via normalized field
pet_types_collection.create_index([("type_lower", 1)], unique=True, sparse=True)

counter_collection: Collection = db["counters"]
counter_collection.create_index([("name", 1)], unique=True)

# Ensure pictures directory exists
os.makedirs("pictures", exist_ok=True)


def _get_next_id() -> int:
    """Get the next numeric ID using a MongoDB atomic counter."""
    counter = counter_collection.find_one_and_update(
        {"name": "pet_id"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=pymongo.ReturnDocument.AFTER,
    )
    return int(counter["value"])


def _find_pet_type_by_id(pet_type_id: int) -> Optional[Dict[str, Any]]:
    """Find a pet type by numeric ID."""
    pet_type = pet_types_collection.find_one({"id": pet_type_id})
    if pet_type:
        pet_type.pop("_id", None)
        pet_type.pop("type_lower", None)
    return pet_type


def _pet_type_exists_by_name(type_name: str) -> bool:
    """Check if a pet type exists by name (case-insensitive).
    
    Also checks the spaced version to handle camelCase inputs like 'GoldenRetriever'.
    """
    # Check both the raw name and the spaced version (for camelCase handling)
    raw_lower = type_name.lower()
    spaced_lower = _camel_to_spaced(type_name).lower()
    
    return pet_types_collection.find_one({
        "$or": [
            {"type_lower": raw_lower},
            {"type_lower": spaced_lower}
        ]
    }) is not None


def _validate_json_request() -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[Dict, int]]]:
    if not request.is_json:
        return None, ERROR_415_JSON

    data = request.get_json()
    if data is None:
        return None, ERROR_400

    return data, None


def _delete_picture_file(picture_path: str) -> None:
    if picture_path and picture_path != "NA":
        try:
            if os.path.exists(picture_path):
                os.remove(picture_path)
            else:
                p = os.path.join("pictures", picture_path)
                if os.path.exists(p):
                    os.remove(p)
        except OSError:
            # spec doesn't say this must be an error; ignore failures
            pass


def _get_image_mimetype(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".png"):
        return "image/png"
    return "image/jpeg"


def _camel_to_spaced(name: str) -> str:
    """Transform camelCase to 'Spaced Case' (e.g., 'GoldenRetriever' → 'Golden Retriever').
    
    If the name already contains spaces, return it as-is.
    """
    if ' ' in name:
        return name
    return re.sub(r'([A-Z])', r' \1', name).strip()


def query_ninja_api(animal_name: str) -> requests.Response:
    # Transform camelCase to "Spaced Case" for API (e.g., "GoldenRetriever" → "Golden Retriever")
    spaced_name = _camel_to_spaced(animal_name)
    
    return requests.get(
        f"{NINJA_API_BASE_URL}?name={spaced_name}",
        headers={"X-Api-Key": NINJA_API_KEY},
        timeout=API_TIMEOUT_SECONDS,
    )


def create_ninja_api_error_response(response: requests.Response) -> Tuple[Dict[str, str], int]:
    return ({"server error": f"API response code {response.status_code}"}, 500)


def extract_pet_type_from_api_response(original_name: str, api_data: Any) -> Optional[Dict[str, Any]]:
    original_lower = original_name.lower()
    
    if isinstance(api_data, list):
        for item in api_data:
            item_name_lower = item.get("name", "").lower()
            # Match either the original or the spaced version
            if item_name_lower == original_lower:
                api_data = item
                break

    if isinstance(api_data, list):
        # No exact match found - try first item if list is non-empty
        if len(api_data) > 0:
            api_data = api_data[0]
        else:
            return None

    taxonomy = api_data.get("taxonomy") or {}
    characteristics = api_data.get("characteristics") or {}

    attributes = _extract_attributes(characteristics)
    lifespan = _extract_lifespan(characteristics)

    return {
        "id": _get_next_id(),  # numeric id
        "type": api_data.get("name", original_name),
        "family": taxonomy.get("family", ""),
        "genus": taxonomy.get("genus", ""),
        "attributes": attributes,
        "lifespan": lifespan,
        "pets": [],
    }


def _extract_attributes(characteristics: Dict[str, Any]) -> List[str]:
    attrs_source = (
        characteristics.get("temperament")
        or characteristics.get("slogan")
        or characteristics.get("group_behavior")
        or ""
    )
    if not attrs_source:
        return []

    if "," in attrs_source:
        return [s.strip() for s in attrs_source.split(",") if s.strip()]
    return attrs_source.split()


def _extract_lifespan(characteristics: Dict[str, Any]) -> Optional[int]:
    lifespan_text = characteristics.get("lifespan")
    if lifespan_text:
        numbers = re.findall(r"\d+", str(lifespan_text))
        if numbers:
            return max(int(n) for n in numbers)
    return None


def download_and_save_image(url: str) -> str:
    try:
        # Some hosts reject default python UA
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=API_TIMEOUT_SECONDS)
    except requests.RequestException:
        return "NA"

    if not response.ok:
        return "NA"

    filename = (url.split("/")[-1] or "image").split("?")[0] or "image"
    filepath = os.path.join("pictures", filename)

    try:
        with open(filepath, "wb") as f:
            f.write(response.content)
    except OSError:
        return "NA"

    return filename


def parse_birthdate(date_str: str) -> Optional[Tuple[int, int, int]]:
    if not date_str:
        return None

    parts = date_str.strip().split("-")
    if len(parts) == 3:
        day_str, month_str, year_str = parts
    elif len(parts) == 2:
        # MM-YYYY → treat as 01-MM-YYYY
        day_str = "01"
        month_str, year_str = parts
    else:
        return None

    try:
        day = int(day_str)
        month = int(month_str)
        year = int(year_str)
    except ValueError:
        return None

    return (year, month, day)


def _pet_matches_date_filters(
    pet: Dict[str, Any],
    greater_than_date: Optional[Tuple[int, int, int]],
    less_than_date: Optional[Tuple[int, int, int]],
) -> bool:
    if not greater_than_date and not less_than_date:
        return True

    birthdate = pet.get("birthdate")
    if not birthdate or birthdate == "NA":
        return False

    parsed_birthdate = parse_birthdate(str(birthdate))
    if parsed_birthdate is None:
        return False

    if greater_than_date and not (parsed_birthdate > greater_than_date):
        return False
    if less_than_date and not (parsed_birthdate < less_than_date):
        return False

    return True


def _create_pet_object(data: Dict[str, Any]) -> Dict[str, Any]:
    name = data.get("name")

    birthdate = data.get("birthdate") if "birthdate" in data else None
    if not birthdate:
        birthdate = "NA"

    picture_url = data.get("picture-url") if "picture-url" in data else None
    if not picture_url:
        picture = "NA"
    else:
        picture = download_and_save_image(str(picture_url))
        if not picture:
            picture = "NA"

    return {"name": name, "birthdate": birthdate, "picture": picture}


def _find_pet_index(pets: List[Dict[str, Any]], pet_name: str) -> Optional[int]:
    for idx, pet in enumerate(pets):
        if pet.get("name") == pet_name:
            return idx
    return None


def _update_pet_picture(old_picture: str, data: Dict[str, Any]) -> str:
    if "picture-url" not in data:
        # If picture-url is not provided, remove the picture (per spec)
        _delete_picture_file(old_picture)
        return "NA"

    new_picture_url = data.get("picture-url")
    if not new_picture_url:
        _delete_picture_file(old_picture)
        return "NA"

    new_picture = download_and_save_image(str(new_picture_url))
    if not new_picture:
        new_picture = "NA"

    if old_picture != new_picture:
        _delete_picture_file(old_picture)

    return new_picture


@app.route("/pet-types", methods=["POST"])
def create_pet_type():
    data, error = _validate_json_request()
    if error:
        return error

    # Validate that the payload contains ONLY 'type'
    if set(data.keys()) != {"type"}:
        return ERROR_400

    pet_type = data.get("type")
    if not pet_type:
        return ERROR_400

    if _pet_type_exists_by_name(str(pet_type)):
        return ERROR_400

    api_response = query_ninja_api(str(pet_type))
    if not api_response.ok:
        if api_response.status_code in (400, 404):
            return ERROR_400
        return create_ninja_api_error_response(api_response)

    api_json = api_response.json()
    pet_type_data = extract_pet_type_from_api_response(str(pet_type), api_json)
    if pet_type_data is None:
        return ERROR_400

    pet_type_data["type_lower"] = str(pet_type_data["type"]).lower()

    try:
        pet_types_collection.insert_one(pet_type_data)
    except pymongo.errors.DuplicateKeyError:
        return ERROR_400

    pet_type_data.pop("_id", None)
    pet_type_data.pop("type_lower", None)
    return make_response(pet_type_data, 201)


@app.route("/pet-types", methods=["GET"])
def get_pet_types():
    filters = {
        "id": request.args.get("id"),
        "type": request.args.get("type"),
        "family": request.args.get("family"),
        "genus": request.args.get("genus"),
        "lifespan": request.args.get("lifespan"),
        "hasAttribute": request.args.get("hasAttribute"),
    }

    query: Dict[str, Any] = {}

    if filters["id"]:
        try:
            query["id"] = int(filters["id"])
        except ValueError:
            # invalid numeric id -> no results
            return make_response([], 200)

    if filters["type"]:
        query["type"] = {"$regex": f"^{re.escape(filters['type'])}$", "$options": "i"}

    if filters["family"]:
        query["family"] = {"$regex": f"^{re.escape(filters['family'])}$", "$options": "i"}

    if filters["genus"]:
        query["genus"] = {"$regex": f"^{re.escape(filters['genus'])}$", "$options": "i"}

    if filters["lifespan"]:
        try:
            query["lifespan"] = int(filters["lifespan"])
        except ValueError:
            pass

    if filters["hasAttribute"]:
        # Regex on array field matches any element
        query["attributes"] = {
            "$regex": f"^{re.escape(filters['hasAttribute'])}$",
            "$options": "i",
        }

    cursor = pet_types_collection.find(query)
    results: List[Dict[str, Any]] = []

    for doc in cursor:
        doc.pop("_id", None)
        doc.pop("type_lower", None)
        results.append(doc)

    return make_response(results, 200)


@app.route("/pet-types/<int:id>", methods=["GET"])
def get_pet_type_by_id(id: int):
    pet_type = _find_pet_type_by_id(id)
    if pet_type:
        return (pet_type, 200)
    return ERROR_404


@app.route("/pet-types/<int:id>", methods=["DELETE"])
def delete_pet_type_by_id(id: int):
    pet_type = _find_pet_type_by_id(id)
    if not pet_type:
        return ERROR_404

    if len(pet_type.get("pets", [])) != 0:
        return ERROR_400

    pet_types_collection.delete_one({"id": id})
    return ("", 204)


@app.route("/pet-types/<int:id>/pets", methods=["POST"])
def create_pet(id: int):
    pet_type = _find_pet_type_by_id(id)
    if not pet_type:
        return ERROR_404

    data, error = _validate_json_request()
    if error:
        return error

    pet_name = data.get("name")
    if not pet_name:
        return ERROR_400

    # Duplicate pet names within the same pet type
    for existing_pet in pet_type.get("pets", []):
        if existing_pet.get("name") == pet_name:
            return ERROR_400

    pet_object = _create_pet_object(data)

    pet_types_collection.update_one({"id": id}, {"$push": {"pets": pet_object}})
    return make_response(pet_object, 201)


@app.route("/pet-types/<int:id>/pets", methods=["GET"])
def get_pets(id: int):
    pet_type = _find_pet_type_by_id(id)
    if not pet_type:
        return ERROR_404

    pets = pet_type.get("pets", [])

    birthdate_gt = request.args.get("birthdateGT")
    birthdate_lt = request.args.get("birthdateLT")

    greater_than = parse_birthdate(birthdate_gt) if birthdate_gt else None
    less_than = parse_birthdate(birthdate_lt) if birthdate_lt else None

    filtered_pets = [pet for pet in pets if _pet_matches_date_filters(pet, greater_than, less_than)]
    return make_response(filtered_pets, 200)


@app.route("/pet-types/<int:id>/pets/<name>", methods=["GET"])
def get_pet_by_name(id: int, name: str):
    pet_type = _find_pet_type_by_id(id)
    if not pet_type:
        return ERROR_404

    for pet in pet_type.get("pets", []):
        if pet.get("name") == name:
            return make_response(pet, 200)

    return ERROR_404


@app.route("/pet-types/<int:id>/pets/<name>", methods=["DELETE"])
def delete_pet_by_name(id: int, name: str):
    pet_type = _find_pet_type_by_id(id)
    if not pet_type:
        return ERROR_404

    pets = pet_type.get("pets", [])
    pet_index = _find_pet_index(pets, name)
    if pet_index is None:
        return ERROR_404

    pet = pets[pet_index]
    _delete_picture_file(pet.get("picture"))

    pet_types_collection.update_one({"id": id}, {"$pull": {"pets": {"name": name}}})
    return ("", 204)


@app.route("/pet-types/<int:id>/pets/<name>", methods=["PUT"])
def update_pet_by_name(id: int, name: str):
    pet_type = _find_pet_type_by_id(id)
    if not pet_type:
        return ERROR_404

    data, error = _validate_json_request()
    if error:
        return error

    new_name = data.get("name")
    if not new_name:
        return ERROR_400

    pets = pet_type.get("pets", [])
    pet_index = _find_pet_index(pets, name)
    if pet_index is None:
        return ERROR_404

    # Prevent rename collision with another pet in the same pet-type
    for i, p in enumerate(pets):
        if i != pet_index and p.get("name") == new_name:
            return ERROR_400

    old_pet = pets[pet_index]
    old_picture = old_pet.get("picture", "NA")
    old_birthdate = old_pet.get("birthdate", "NA")

    # Only update birthdate if provided; otherwise keep
    if "birthdate" in data:
        new_birthdate = data.get("birthdate")
        if not new_birthdate:
            new_birthdate = "NA"
    else:
        new_birthdate = old_birthdate

    new_picture = _update_pet_picture(old_picture, data)

    updated_pet = {"name": new_name, "birthdate": new_birthdate, "picture": new_picture}

    pet_types_collection.update_one({"id": id}, {"$set": {f"pets.{pet_index}": updated_pet}})
    return make_response(updated_pet, 200)


@app.route("/pictures/<file_name>", methods=["GET"])
def get_picture(file_name: str):
    # Check both current directory and pictures directory
    if os.path.isfile(file_name):
        mimetype = _get_image_mimetype(file_name)
        return send_file(file_name, mimetype=mimetype), 200

    picture_path = os.path.join("pictures", file_name)
    if os.path.isfile(picture_path):
        mimetype = _get_image_mimetype(file_name)
        return send_file(picture_path, mimetype=mimetype), 200

    return ERROR_404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)