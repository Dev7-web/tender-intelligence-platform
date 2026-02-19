"""Initialize MongoDB indexes."""

import asyncio

from app.database.mongodb import create_indexes


if __name__ == "__main__":
    asyncio.run(create_indexes())
