# Assignment #4: CI/CD Pipeline for Pet Store Application

This project implements a GitHub Actions CI/CD pipeline for the Pet Store application with automated testing and query processing.

## Overview

The system consists of:
- **2 pet-store instances** (ports 5001, 5002) using separate databases within one MongoDB instance
- **1 pet-order instance** (port 5003) with its own separate MongoDB instance
- **GitHub Actions workflow** with 3 jobs: build, test, and query
- **Automated testing** using pytest
- **Query processing** for dynamic data queries

## Project Structure

```
homework_4/
├── .github/workflows/
│   └── assignment4.yml          # GitHub Actions workflow
├── tests/
│   └── assn4_tests.py          # Pytest test suite (9 tests)
├── pet-store/
│   ├── app.py                  # Pet store service
│   ├── Dockerfile              # Container build
│   └── requirements.txt        # Python dependencies
├── pet-order/
│   ├── app.py                  # Pet order service
│   ├── Dockerfile              # Container build
│   └── requirements.txt        # Python dependencies
├── scripts/
│   ├── setup_data.py           # Data setup script
│   └── query_processor.py      # Query execution script
├── docker-compose.yml          # Local testing setup
├── query.txt                   # Query input file
└── .env                        # Environment variables
```

## Setup Instructions

### 1. GitHub Repository Setup

1. Create a new GitHub repository
2. Add repository secret `NINJA_API_KEY`:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `NINJA_API_KEY`
   - Value: `ahOqiuJCApa117bE961tGQ==cGu4SfUgfPsZ4DgH`
   - Click "Add secret"

### 2. Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd homework_4
```

2. Create `.env` file (if not present):
```bash
echo "NINJA_API_KEY=ahOqiuJCApa117bE961tGQ==cGu4SfUgfPsZ4DgH" > .env
```

3. Start services:
```bash
docker-compose up -d
```

4. Verify services are running:
```bash
docker-compose ps
curl http://localhost:5001/pet-types
curl http://localhost:5002/pet-types
curl -H "OwnerPC: LovesPetsL2M3n4!" http://localhost:5003/transactions
```

### 3. Running Tests Locally

1. Install pytest:
```bash
pip install pytest requests
```

2. Run the test suite:
```bash
pytest -v tests/assn4_tests.py
```

### 4. Testing Query Processing

1. Start services (if not already running):
```bash
docker-compose up -d
```

2. Setup test data:
```bash
python3 scripts/setup_data.py
```

3. Process queries:
```bash
python3 scripts/query_processor.py query.txt response.txt
```

4. View results:
```bash
cat response.txt
```

## GitHub Actions Workflow

The workflow consists of 3 sequential jobs:

### Job 1: Build
- Builds Docker images for pet-store and pet-order
- Records workflow start time and submitters
- Generates build status in log.txt (lines 1-4)
- Saves images and artifacts

### Job 2: Test
- Loads Docker images from build job
- Starts MongoDB instances and service containers
- Executes pytest test suite (9 tests)
- Updates log.txt with container and test status (lines 5-8)
- Uploads test results (always, even on failure)

### Job 3: Query
- Loads Docker images and starts services
- Runs setup script to populate databases
- Executes query processor on query.txt
- Generates response.txt with query results
- Uploads response.txt artifact

## Artifacts Generated

1. **log.txt** - Workflow execution log containing:
   - Start time
   - Submitter names
   - Build status (pet-store, pet-order)
   - Container status (pet-store #1, pet-store #2, pet-order)
   - Test results

2. **assn4_test_results.txt** - Complete pytest output with verbose results

3. **response.txt** - Query execution results in the format:
   ```
   <status-code>
   <JSON-payload or NONE>
   ;
   ```

## Service Architecture

### Database Isolation Architecture
- **pet-store instances**: Both connect to the same MongoDB instance (`mongo-shared`) but use **separate databases**:
  - pet-store1 uses database `petstore_1` (configured via `STORE_ID=1`)
  - pet-store2 uses database `petstore_2` (configured via `STORE_ID=2`)
  - This ensures complete data isolation between the two stores
- **pet-order**: Uses a completely separate MongoDB instance (`mongo-order`) with database `pet_order_db`

### Port Mappings
- **5001**: pet-store instance #1
- **5002**: pet-store instance #2
- **5003**: pet-order service
- **27017**: MongoDB (internal, not exposed to host)

### Environment Variables

**pet-store:**
- `MONGODB_URI`: MongoDB connection string (both use `mongodb://mongo-shared:27017/`)
- `STORE_ID`: Database identifier (1 or 2) - determines which database to use (`petstore_1` or `petstore_2`)
- `PORT`: Service port (5001 or 5002)
- `NINJA_API_KEY`: API key for external pet information service

**pet-order:**
- `MONGODB_URI`: MongoDB connection string
- `PORT`: Service port (5003)
- `PET_STORE_1_URL`: URL for pet-store #1
- `PET_STORE_2_URL`: URL for pet-store #2

## Test Suite

The pytest suite includes 9 tests:

1. **test_01_post_pet_types_to_store1**: POST 3 pet-types to store #1
2. **test_02_post_pet_types_to_store2**: POST 3 pet-types to store #2
3. **test_03_post_pets_to_store1_type1**: POST 2 pets (Golden Retriever) to store #1
4. **test_04_post_pets_to_store1_type3**: POST 2 pets (Abyssinian) to store #1
5. **test_05_post_pet_to_store2_type1**: POST 1 pet (Golden Retriever) to store #2
6. **test_06_post_pet_to_store2_type2**: POST 1 pet (Australian Shepherd) to store #2
7. **test_07_post_pets_to_store2_type4**: POST 2 pets (bulldog) to store #2
8. **test_08_get_pet_type_by_id**: GET pet-type by ID from store #1
9. **test_09_get_pets_for_type**: GET pets for specific type from store #2

## Query File Format

The `query.txt` file supports two types of entries:

### Query Entry
```
query: <store-num>,<field>=<value>;
```
Example:
```
query: 1,family=Canidae;
query: 2,type=bulldog;
```

### Purchase Entry
```
purchase: <JSON-purchase-object>;
```
Example:
```
purchase: {"purchaser":"John","pet-type":"Golden Retriever","store":1,"pet-name":"Lander","purchase-id":"p1"};
```

## Troubleshooting

### Services Not Starting
```bash
# Check logs
docker-compose logs pet-store1
docker-compose logs pet-store2
docker-compose logs pet-order

# Restart services
docker-compose down
docker-compose up -d
```

### Tests Failing
```bash
# Ensure services are running
docker-compose ps

# Check service health
curl http://localhost:5001/pet-types
curl http://localhost:5002/pet-types

# View detailed test output
pytest -v tests/assn4_tests.py
```

### GitHub Actions Failures
1. Check workflow logs in GitHub Actions tab
2. Verify `NINJA_API_KEY` secret is set
3. Review artifact contents (log.txt, assn4_test_results.txt)
4. Ensure query.txt is in repository root

## Cleanup

Stop and remove all containers:
```bash
docker-compose down -v
```

Remove Docker images:
```bash
docker rmi pet-store:latest pet-order:latest
```

## Key Changes from Homework 2

1. **Database Isolation**: Both pet-store instances connect to same MongoDB instance but use separate databases (`petstore_1`, `petstore_2`) via `STORE_ID` environment variable
2. **API Key**: Read from environment variable instead of hardcoded
3. **No /kill Endpoints**: Removed from both services
4. **No Restart Policies**: Docker compose has no `restart: always`
5. **No uuid Package**: Removed from pet-order requirements (built-in)

## Authors

See Partners.txt for team member information.

## License

This project is part of Cloud Computing coursework.