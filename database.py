"""
database.py — PostgreSQL persistence for the B de Blog rating system.

Replaces the old calificaciones.json flat file. Connection info comes
exclusively from environment variables (DATABASE_URL, RATING_HASH_SECRET) —
never hardcoded, never committed.

Kept intentionally simple for a small Flask app deployed on Vercel:
one short-lived connection per call, plain psycopg2, no ORM, no pool.
"""

import os
import hashlib
from contextlib import contextmanager

import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")
RATING_HASH_SECRET = os.environ.get("RATING_HASH_SECRET", "")

# Stable identifier -> content type, for every story and review that exists
# today. This is the single source of truth the API validates against, so a
# request can never write a rating for content that doesn't actually exist.
CONTENIDO_VALIDO = {
    # Historias
    "H_ElDiaQueElSol": "historia",
    "H_eLEco": "historia",
    "H_cyberRevuelta": "historia",
    "H_ElAmantePerdido": "historia",
    "H_cafeteria": "historia",
    "H_EscuadronImposible": "historia",
    "H_EscuadronImposibleII": "historia",
    "H_EscuadronImposibleIII": "historia",
    "H_EscuadronImposible_IV": "historia",
    "H_EscuadronImposible_V": "historia",
    "H_EscuadronImposible_VI": "historia",

    # Reseñas
    "rese_tfundacion_asimov": "resena",
    "rese_frankenstein_mary": "resena",
    "rese_fwtbt_Heminghway": "resena",
    "rese_Psicoanalista_Katzenbach": "resena",
    "rese_trilogiaCosmica_Lewis": "resena",
    "rese_ElMonje_Sharma": "resena",
    "rese_Vuelta80dias_Verne": "resena",
    "rese_1984_Orwell": "resena",
    "rese_JenkyllHyde_Stevenson": "resena",
    "rese_NaranjaMecanica_Burgess": "resena",
    "rese_Kybalion_Hermes": "resena",
    "rese_Transmetropolitan_WarrenEllis": "resena",
    "rese_CrimenCast_FDevsky": "resena",
    "rese_ViajeCentro_Verne": "resena",
    "rese_PoderAhora_Eckhart": "resena",
    "rese_MundoFeliz_Huxley": "resena",
    "rese_preacher_EnnisDillon": "resena",
    "rese_PetSematary_King": "resena",
    "rese_2001Odisea_Cclarke": "resena",
    "rese_FightClub_Palaniuk": "resena",
    "rese_trenAzul_Agata": "resena",
    "rese_SimboloPerdido_Brown": "resena",
    "rese_ElHombreMasRicoBabilonia_Clason": "resena",
    "rese_LaMaquinaDelTiempo_HGwells": "resena",
    "rese_ElHotelDeLosRecuerdos_dotatodi": "resena",
}


# Comments are only enabled for stories (not reviews), keyed by their
# template filename (e.g. "H_cafeteria.html"). Derived from the same
# CONTENIDO_VALIDO registry above so there's a single source of truth for
# "which stories exist" — adding a story to CONTENIDO_VALIDO is enough to
# make it commentable too.
HISTORIAS_VALIDAS = {
    f"{contenido}.html" for contenido, tipo in CONTENIDO_VALIDO.items() if tipo == "historia"
}


class DatabaseNotConfigured(RuntimeError):
    """Raised when DATABASE_URL is missing — lets callers return a clean 500
    instead of the app crashing at import time."""


def get_connection():
    if not DATABASE_URL:
        raise DatabaseNotConfigured(
            "DATABASE_URL no está configurada. Define la variable de entorno "
            "para habilitar el sistema de calificaciones."
        )
    return psycopg2.connect(DATABASE_URL, sslmode="require")


@contextmanager
def get_cursor(commit=False):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()


def init_db():
    """Idempotent — safe to call on every cold start. Every statement here
    is CREATE TABLE/INDEX IF NOT EXISTS: it never drops or resets anything,
    so existing production data (ratings, comments) is always preserved."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS calificaciones (
                id BIGSERIAL PRIMARY KEY,
                contenido VARCHAR(150) NOT NULL,
                tipo VARCHAR(20) NOT NULL
                    CHECK (tipo IN ('historia', 'resena')),
                ip_hash VARCHAR(64) NOT NULL,
                calificacion SMALLINT NOT NULL
                    CHECK (calificacion BETWEEN 1 AND 5),
                fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (contenido, ip_hash)
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_calificaciones_contenido "
            "ON calificaciones (contenido);"
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS comentarios (
                id SERIAL PRIMARY KEY,
                historia VARCHAR(255) NOT NULL,
                apodo VARCHAR(50) NOT NULL,
                comentario VARCHAR(1000) NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_comentarios_historia "
            "ON comentarios (historia);"
        )


def hash_ip(ip: str) -> str:
    """Deterministic, one-way — the raw IP is never stored."""
    payload = f"{ip}{RATING_HASH_SECRET}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def upsert_calificacion(contenido: str, tipo: str, ip_hash: str, calificacion: int) -> dict:
    """Insert a new rating, or update this visitor's existing one. Returns
    the fresh stats (promedio, total_votos, mi_calificacion) in one round trip."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO calificaciones (contenido, tipo, ip_hash, calificacion)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (contenido, ip_hash)
            DO UPDATE SET calificacion = EXCLUDED.calificacion, fecha = NOW();
            """,
            (contenido, tipo, ip_hash, calificacion),
        )
        cur.execute(
            """
            SELECT COALESCE(AVG(calificacion), 0) AS promedio, COUNT(*) AS total_votos
            FROM calificaciones WHERE contenido = %s;
            """,
            (contenido,),
        )
        row = cur.fetchone()

    return {
        "promedio": round(float(row["promedio"]), 2) if row["total_votos"] else 0,
        "total_votos": row["total_votos"],
        "mi_calificacion": calificacion,
    }


def get_stats(contenido: str, ip_hash: str = None) -> dict:
    """Average, vote count, and (if ip_hash given) this visitor's own rating."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT COALESCE(AVG(calificacion), 0) AS promedio, COUNT(*) AS total_votos
            FROM calificaciones WHERE contenido = %s;
            """,
            (contenido,),
        )
        row = cur.fetchone()

        mi_calificacion = None
        if ip_hash:
            cur.execute(
                "SELECT calificacion FROM calificaciones WHERE contenido = %s AND ip_hash = %s;",
                (contenido, ip_hash),
            )
            mine = cur.fetchone()
            mi_calificacion = mine["calificacion"] if mine else None

    return {
        "promedio": round(float(row["promedio"]), 2) if row["total_votos"] else 0,
        "total_votos": row["total_votos"],
        "mi_calificacion": mi_calificacion,
    }


def get_all_stats() -> dict:
    """One query for every content id's average + vote count — used by the
    index pages so they don't fire 30 separate requests."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT contenido, COALESCE(AVG(calificacion), 0) AS promedio, COUNT(*) AS total_votos
            FROM calificaciones GROUP BY contenido;
            """
        )
        rows = cur.fetchall()

    return {
        row["contenido"]: {
            "promedio": round(float(row["promedio"]), 2),
            "total_votos": row["total_votos"],
        }
        for row in rows
    }


def crear_comentario(historia: str, apodo: str, comentario: str) -> dict:
    """Insert one comment and return the stored row (id + server-assigned
    fecha) in the same round trip, so the frontend can render it immediately
    without a follow-up GET."""
    with get_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO comentarios (historia, apodo, comentario)
            VALUES (%s, %s, %s)
            RETURNING id, historia, apodo, comentario, fecha;
            """,
            (historia, apodo, comentario),
        )
        row = cur.fetchone()

    return dict(row)


def obtener_comentarios(historia: str) -> list:
    """All comments for one story, newest first."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, historia, apodo, comentario, fecha
            FROM comentarios
            WHERE historia = %s
            ORDER BY fecha DESC;
            """,
            (historia,),
        )
        rows = cur.fetchall()

    return [dict(row) for row in rows]
