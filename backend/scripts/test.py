import sys
import os

# Add the parent directory (backend/) to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, Base
import models

# Creates all tables defined in models.py (including data_snapshots)
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")