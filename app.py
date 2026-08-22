from flask import Flask, render_template, request, jsonify
import os

try:
    from dotenv import load_dotenv
    load_dotenv()  # loads .env for local development only; no-op in production
except ImportError:
    pass

import database as db

app = Flask(__name__)

# Idempotent — safe to run on every cold start. If DATABASE_URL isn't set
# (e.g. local dev without Postgres configured yet), the app still boots;
# only the /api/* rating endpoints will fail until it's configured.
try:
    db.init_db()
except db.DatabaseNotConfigured:
    app.logger.warning("DATABASE_URL no configurada: el sistema de calificaciones está deshabilitado.")
except Exception:
    app.logger.exception("No se pudo inicializar la tabla de calificaciones.")


def get_client_ip():
    """The app runs behind Vercel's proxy, which sets X-Forwarded-For at the
    edge (the client cannot spoof what Vercel appends). We take the first
    address in that chain — the original visitor — falling back to
    remote_addr for local development where no proxy is involved."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'


@app.route('/api/calificar', methods=['POST'])
def api_calificar():
    data = request.get_json(silent=True) or {}
    contenido = data.get('contenido')
    tipo = data.get('tipo')

    if not contenido or contenido not in db.CONTENIDO_VALIDO:
        return jsonify({"success": False, "error": "El contenido indicado no existe."}), 400

    if tipo != db.CONTENIDO_VALIDO[contenido]:
        return jsonify({"success": False, "error": "El tipo no coincide con el contenido."}), 400

    try:
        calificacion = int(data.get('calificacion'))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "La calificación debe ser un número entero."}), 400

    if calificacion < 1 or calificacion > 5:
        return jsonify({"success": False, "error": "La calificación debe estar entre 1 y 5."}), 400

    ip_hash = db.hash_ip(get_client_ip())

    try:
        stats = db.upsert_calificacion(contenido, tipo, ip_hash, calificacion)
    except db.DatabaseNotConfigured as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception:
        app.logger.exception("Error guardando calificación para %s", contenido)
        return jsonify({"success": False, "error": "No se pudo guardar la calificación. Intenta más tarde."}), 500

    return jsonify({
        "success": True,
        "promedio": stats["promedio"],
        "total_votos": stats["total_votos"],
        "mi_calificacion": stats["mi_calificacion"],
    })


@app.route('/api/calificacion/<contenido>')
def api_obtener_calificacion(contenido):
    if contenido not in db.CONTENIDO_VALIDO:
        return jsonify({"success": False, "error": "El contenido indicado no existe."}), 404

    ip_hash = db.hash_ip(get_client_ip())

    try:
        stats = db.get_stats(contenido, ip_hash)
    except db.DatabaseNotConfigured as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception:
        app.logger.exception("Error consultando calificación para %s", contenido)
        return jsonify({"success": False, "error": "No se pudo consultar la calificación."}), 500

    return jsonify({"success": True, **stats})


@app.route('/api/calificaciones')
def api_obtener_calificaciones():
    try:
        stats = db.get_all_stats()
    except db.DatabaseNotConfigured as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception:
        app.logger.exception("Error consultando calificaciones")
        return jsonify({"success": False, "error": "No se pudieron consultar las calificaciones."}), 500

    return jsonify({"success": True, "calificaciones": stats})


def _serializar_comentario(row):
    """Copy the row with `fecha` as an explicit ISO string, so the JSON
    shape doesn't depend on Flask's default datetime encoding."""
    out = dict(row)
    if out.get("fecha") is not None:
        out["fecha"] = out["fecha"].isoformat()
    return out


@app.route('/api/comentarios', methods=['POST'])
def api_crear_comentario():
    data = request.get_json(silent=True) or {}
    historia = data.get('historia')
    apodo = (data.get('apodo') or '').strip()
    comentario = (data.get('comentario') or '').strip()

    if not historia or historia not in db.HISTORIAS_VALIDAS:
        return jsonify({"success": False, "error": "La historia indicada no existe."}), 400

    if not apodo:
        return jsonify({"success": False, "error": "El apodo no puede estar vacío."}), 400
    if len(apodo) > 50:
        return jsonify({"success": False, "error": "El apodo no puede superar 50 caracteres."}), 400

    if not comentario:
        return jsonify({"success": False, "error": "El comentario no puede estar vacío."}), 400
    if len(comentario) > 1000:
        return jsonify({"success": False, "error": "El comentario no puede superar 1000 caracteres."}), 400

    try:
        nuevo = db.crear_comentario(historia, apodo, comentario)
    except db.DatabaseNotConfigured as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception:
        app.logger.exception("Error guardando comentario para %s", historia)
        return jsonify({"success": False, "error": "No se pudo publicar el comentario. Intenta más tarde."}), 500

    return jsonify({"success": True, "comentario": _serializar_comentario(nuevo)}), 201


@app.route('/api/comentarios/<historia>')
def api_obtener_comentarios(historia):
    if historia not in db.HISTORIAS_VALIDAS:
        return jsonify({"success": False, "error": "La historia indicada no existe."}), 404

    try:
        comentarios = db.obtener_comentarios(historia)
    except db.DatabaseNotConfigured as e:
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception:
        app.logger.exception("Error consultando comentarios para %s", historia)
        return jsonify({"success": False, "error": "No se pudieron consultar los comentarios."}), 500

    return jsonify({"success": True, "comentarios": [_serializar_comentario(c) for c in comentarios]})


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/historias')
def historias():
    return render_template('historias.html')

@app.route('/H_ElDiaQueElSol')
def H_ElDiaQueElSol():
    return render_template('H_ElDiaQueElSol.html')

@app.route('/H_eLEco')
def H_eLEco():
    return render_template('H_eLEco.html')

@app.route('/H_cyberRevuelta')
def H_cyberRevuelta():
    return render_template('H_cyberRevuelta.html')  # Archivo H_cyberRevuelta.html


@app.route('/H_ElAmantePerdido')
def H_ElAmantePerdido():
    return render_template('H_ElAmantePerdido.html')  # Archivo H_ElAmantePerdido.html

@app.route('/H_cafeteria')
def H_cafeteria():
    return render_template('H_cafeteria.html')  # Archivo H_cafeteria.html

@app.route('/H_EscuadronImposible')
def H_EscuadronImposible():
    return render_template('H_EscuadronImposible.html')  # Archivo H_EscuadronImposible.html

@app.route('/H_EscuadronImposibleII')
def H_EscuadronImposibleII():
    return render_template('H_EscuadronImposibleII.html')  # Archivo H_EscuadronImposibleII.html

@app.route('/resenas')
def resenas():
    return render_template('resenas.html')  # reseñas.html

@app.route('/rese_tfundacion_asimov')
def rese_tfundacion_asimov():
    return render_template('rese_tfundacion_asimov.html')  # rese_tfundacion_asimov.html

@app.route('/rese_frankenstein_mary')
def rese_frankenstein_mary():
    return render_template('rese_frankenstein_mary.html')  # Archivo rese_frankenstein_mary

@app.route('/rese_fwtbt_Heminghway')
def rese_fwtbt_Heminghway():
    return render_template('rese_fwtbt_Heminghway.html')  # Archivo rese_fwtbt_Heminghway

@app.route('/rese_trilogiaCosmica_Lewis')
def rese_trilogiaCosmica_Lewis():
    return render_template('rese_trilogiaCosmica_Lewis.html')  # Archivo rese_trilogiaCosmica_Lewis

@app.route('/rese_ElMonje_Sharma')
def rese_ElMonje_Sharma():
    return render_template('rese_ElMonje_Sharma.html')  # Archivo rese_ElMonje_Sharma

@app.route('/rese_Vuelta80dias_Verne')
def rese_Vuelta80dias_Verne():
    return render_template('rese_Vuelta80dias_Verne.html')  # Archivo rese_Vuelta80dias_Verne

@app.route('/rese_1984_Orwell')
def rese_1984_Orwell():
    return render_template('rese_1984_Orwell.html')  # Archivo rese_1984_Orwell

@app.route('/rese_JenkyllHyde_Stevenson')
def rese_JenkyllHyde_Stevenson():
    return render_template('rese_JenkyllHyde_Stevenson.html')  # Archivo rese_JenkyllHyde_Stevenson

@app.route('/rese_NaranjaMecanica_Burgess')
def rese_NaranjaMecanica_Burgess():
    return render_template('rese_NaranjaMecanica_Burgess.html')  # Archivo rese_NaranjaMecanica_Burgess

@app.route('/rese_Kybalion_Hermes')
def rese_Kybalion_Hermes():
    return render_template('rese_Kybalion_Hermes.html')  # Archivo rese_Kybalion_Hermes

@app.route('/rese_CrimenCast_FDevsky')
def rese_CrimenCast_FDevsky():
    return render_template('rese_CrimenCast_FDevsky.html')  # Archivo rese_CrimenCast_FDevsky


@app.route('/rese_ViajeCentro_Verne')
def rese_ViajeCentro_Verne():
    return render_template('rese_ViajeCentro_Verne.html')  # Archivo rese_ViajeCentro_Verne

@app.route('/rese_PoderAhora_Eckhart')
def rese_PoderAhora_Eckhart():
    return render_template('rese_PoderAhora_Eckhart.html')  # Archivo rese_PoderAhora_Eckhart

@app.route('/rese_MundoFeliz_Huxley')
def rese_MundoFeliz_Huxley():
    return render_template('rese_MundoFeliz_Huxley.html')  # Archivo rese_MundoFeliz_Huxley

@app.route('/rese_preacher_EnnisDillon')
def rese_preacher_EnnisDillon():
    return render_template('rese_preacher_EnnisDillon.html')  # Archivo rese_preacher_EnnisDillon

@app.route('/rese_Transmetropolitan_WarrenEllis')
def rese_Transmetropolitan_WarrenEllis():
    return render_template('rese_Transmetropolitan_WarrenEllis.html')  # Archivo rese_Transmetropolitan_WarrenEllis

@app.route('/rese_PetSematary_King')
def rese_PetSematary_King():
    return render_template('rese_PetSematary_King.html')  # Archivo rese_PetSematary_King

@app.route('/rese_2001Odisea_Cclarke')
def rese_2001Odisea_Cclarke():
    return render_template('rese_2001Odisea_Cclarke.html')  # Archivo rese_2001Odisea_Cclarke

@app.route('/rese_FightClub_Palaniuk')
def rese_FightClub_Palaniuk():
    return render_template('rese_FightClub_Palaniuk.html')  # Archivo rese_FightClub_Palaniuk

@app.route('/rese_trenAzul_Agata')
def rese_trenAzul_Agata():
    return render_template('rese_trenAzul_Agata.html')  # Archivo rese_trenAzul_Agata

@app.route('/rese_Psicoanalista_Katzenbach')
def rese_Psicoanalista_Katzenbach():
    return render_template('rese_Psicoanalista_Katzenbach.html')  # Archivo rese_Psicoanalista_Katzenbach


@app.route('/rese_SimboloPerdido_Brown')
def rese_SimboloPerdido_Brown():
    return render_template('rese_SimboloPerdido_Brown.html')  # Archivo rese_SimboloPerdido_Brown

@app.route('/rese_ElHombreMasRicoBabilonia_Clason')
def rese_ElHombreMasRicoBabilonia_Clason():
    return render_template('rese_ElHombreMasRicoBabilonia_Clason.html')  # Archivo rese_ElHombreMasRicoBabilonia_Clason

@app.route('/rese_LaMaquinaDelTiempo_HGwells')
def rese_LaMaquinaDelTiempo_HGwells():
    return render_template('rese_LaMaquinaDelTiempo_HGwells.html')  # Archivo rese_LaMaquinaDelTiempo_HGwells


@app.route('/rese_ElHotelDeLosRecuerdos_dotatodi')
def rese_ElHotelDeLosRecuerdos_dotatodi():
    return render_template('rese_ElHotelDeLosRecuerdos_dotatodi.html')  # Archivo rese_ElHotelDeLosRecuerdos_dotatodi



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Usa el puerto de Render o 5000 por defecto
    app.run(debug=True, host='0.0.0.0', port=port)  # Cambia host a '0.0.0.0'
