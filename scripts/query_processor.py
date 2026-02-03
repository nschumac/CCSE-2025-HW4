#!/usr/bin/env python3
import sys
import requests
import json
import re

def parse_query_line(line):
    """Parse a query line and return type and details"""
    line = line.strip()
    
    if line.startswith("query:"):
        # Extract query details
        match = re.match(r"query:\s*(\d+),(.+?);", line)
        if match:
            store_num = int(match.group(1))
            query_string = match.group(2)
            return "query", {"store": store_num, "query_string": query_string}
    
    elif line.startswith("purchase:"):
        # Extract JSON purchase
        match = re.match(r"purchase:\s*(.+?);", line)
        if match:
            json_str = match.group(1)
            purchase_data = json.loads(json_str)
            return "purchase", purchase_data
    
    return None, None

def execute_query(store_num, query_string):
    """Execute a GET /pet-types query"""
    base_url = f"http://localhost:{5000 + store_num}"
    url = f"{base_url}/pet-types?{query_string}"
    
    try:
        response = requests.get(url)
        return response.status_code, response.json() if response.status_code == 200 else None
    except Exception as e:
        return 500, None

def execute_purchase(purchase_data):
    """Execute a POST /purchases request"""
    url = "http://localhost:5003/purchases"
    
    try:
        response = requests.post(url, json=purchase_data, headers={"Content-Type": "application/json"})
        return response.status_code, response.json() if response.status_code == 201 else None
    except Exception as e:
        return 500, None

def format_response(status_code, payload):
    """Format a response entry"""
    result = f"{status_code}\n"
    
    if payload is None or (status_code != 200 and status_code != 201):
        result += "NONE\n"
    else:
        result += json.dumps(payload, indent=2) + "\n"
    
    result += ";\n"
    return result

def main():
    if len(sys.argv) != 3:
        print("Usage: query_processor.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    results = []
    
    for line in lines:
        entry_type, details = parse_query_line(line)
        
        if entry_type == "query":
            status_code, payload = execute_query(details["store"], details["query_string"])
            results.append(format_response(status_code, payload))
        
        elif entry_type == "purchase":
            status_code, payload = execute_purchase(details)
            results.append(format_response(status_code, payload))
    
    with open(output_file, 'w') as f:
        f.writelines(results)

if __name__ == "__main__":
    main()