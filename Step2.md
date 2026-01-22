# 1. Install updated dependencies
pip install -r requirements.txt

# 2. Generate migration for new models
alembic revision --autogenerate -m "Add workflow, barcode, project, and audit models"

# 3. Apply migrations
alembic upgrade head

# 4. Create superuser with new role system
python scripts/create_superuser.py director@pickupbiz.com 12345 "Admin" director

# 5. Start the server:
uvicorn app.main:app --reload --host 0.0.0.0 --port 5055