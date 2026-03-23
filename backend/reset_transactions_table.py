from sqlalchemy import text
from app.core.db import engine

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS transactions"))
    conn.commit()

print("transactions table dropped successfully.")