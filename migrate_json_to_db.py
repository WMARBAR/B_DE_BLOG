"""
migrate_json_to_db.py — OPTIONAL, manual, one-time migration of ratings from
the old calificaciones.json flat file into PostgreSQL.

This script is never run automatically by the app. It does not delete or
modify calificaciones.json. Run it by hand, once, only if you want the
historical ratings already collected under the old system to carry over.

Usage:
    python migrate_json_to_db.py            # preview only, writes nothing
    python migrate_json_to_db.py --apply     # actually write to the database

Requires DATABASE_URL and RATING_HASH_SECRET to be set (via .env or the
environment) — the raw IPs stored in the old JSON file are hashed exactly
the same way a live vote would be before they ever touch Postgres.
"""

import json
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import database as db

JSON_PATH = "calificaciones.json"


def main():
    apply_changes = "--apply" in sys.argv

    if not os.path.exists(JSON_PATH):
        print(f"No se encontró {JSON_PATH}. Nada que migrar.")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print(f"{JSON_PATH} está vacío. Nada que migrar.")
        return

    if apply_changes and not os.environ.get("DATABASE_URL"):
        print("ERROR: DATABASE_URL no está configurada.")
        sys.exit(1)
    if apply_changes and not os.environ.get("RATING_HASH_SECRET"):
        print("ERROR: RATING_HASH_SECRET no está configurada.")
        sys.exit(1)

    if apply_changes:
        db.init_db()

    plan = []
    skipped = []

    for contenido, votos_por_ip in data.items():
        tipo = db.CONTENIDO_VALIDO.get(contenido)
        if tipo is None:
            skipped.append(contenido)
            continue
        for ip, calificacion in votos_por_ip.items():
            plan.append((contenido, tipo, ip, int(calificacion)))

    print(f"Encontrados {len(plan)} votos para migrar desde {JSON_PATH}.")
    if skipped:
        print(f"Contenido no reconocido (se omite): {', '.join(skipped)}")

    if not apply_changes:
        print("\nModo vista previa (no se escribió nada). Para aplicar la migración:")
        print("    python migrate_json_to_db.py --apply")
        for contenido, tipo, ip, calificacion in plan:
            print(f"  [preview] {contenido} ({tipo}): {calificacion}★")
        return

    migrated = 0
    for contenido, tipo, ip, calificacion in plan:
        ip_hash = db.hash_ip(ip)
        db.upsert_calificacion(contenido, tipo, ip_hash, calificacion)
        migrated += 1

    print(f"\nMigración completa: {migrated} votos escritos en PostgreSQL.")
    print(f"{JSON_PATH} no fue modificado ni eliminado.")


if __name__ == "__main__":
    main()
