"""
init_db.py — one-off, explicit way to create the `calificaciones` table.

The Flask app already calls database.init_db() on every cold start (it's a
CREATE TABLE IF NOT EXISTS, safe to repeat), so running this script by hand
is optional. It's here for anyone who'd rather initialize the database as a
deliberate, visible step — e.g. right after provisioning Postgres on Vercel,
before the app has received its first request.

Usage:
    DATABASE_URL=postgres://... python init_db.py
or, with a local .env file already containing DATABASE_URL:
    python init_db.py
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import database as db


def main():
    if not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL no está configurada. Define la variable de entorno e intenta de nuevo.")
        sys.exit(1)

    print("Conectando y creando la tabla 'calificaciones' (si no existe)...")
    db.init_db()
    print("Listo. La tabla 'calificaciones' está lista para usarse.")


if __name__ == "__main__":
    main()
