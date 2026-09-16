"""One-off script: create all tables defined in app.models against DATABASE_URL.

Usage:
    ./venv/Scripts/python.exe init_db.py
"""

from app.database import Base, engine
from app import models  # noqa: F401  (import registers models on Base.metadata)


def main():
    Base.metadata.create_all(bind=engine)
    print("Tables created:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    main()
