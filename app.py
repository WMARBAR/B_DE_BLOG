from flask import Flask, render_template
import os
from flask import request, jsonify
import json
app = Flask(__name__)

def cargar_json():
    archivo = 'calificaciones.json'
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            return json.load(f)
    return {}

def calcular_promedio(calificaciones, historia):
    votos_por_ip = calificaciones.get(historia, {})
    votos = list(votos_por_ip.values())
    if votos:
        return round(sum(votos) / len(votos), 2)
    return 0


@app.route('/guardar_calificacion', methods=['POST'])
def guardar_calificacion():
    data = request.get_json()
    historia = data.get('historia')
    calificacion = int(data.get('calificacion'))
    ip = request.remote_addr

    archivo = 'calificaciones.json'

    # Cargar calificaciones existentes o crear nuevo diccionario
    if os.path.exists(archivo):
        with open(archivo, 'r') as f:
            calificaciones = json.load(f)
    else:
        calificaciones = {}

    # Si no existe la historia, se crea
    if historia not in calificaciones:
        calificaciones[historia] = {}

    # Actualizar o insertar la calificación por IP
    calificaciones[historia][ip] = calificacion

    # Guardar el archivo actualizado
    with open(archivo, 'w') as f:
        json.dump(calificaciones, f, indent=4)

    return jsonify({"message": f"¡Gracias! Has calificado con {calificacion} estrella(s)."})



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/historias')
def historias():
    return render_template('historias.html')

@app.route('/H_ElDiaQueElSol')
def H_ElDiaQueElSol():
    calificaciones = cargar_json()  # Función que lee el JSON
    historia = '/H_ElDiaQueElSol'
    promedio = calcular_promedio(calificaciones, historia)
    return render_template('H_ElDiaQueElSol.html', promedio=promedio)

@app.route('/H_eLEco')
def H_eLEco():
    calificaciones = cargar_json()  # Función que lee el JSON
    historia = '/H_eLEco'
    promedio = calcular_promedio(calificaciones, historia)
    return render_template('H_eLEco.html', promedio=promedio)

@app.route('/H_cyberRevuelta')
def H_cyberRevuelta():
    calificaciones = cargar_json()  # Función que lee el JSON
    historia = '/H_cyberRevuelta'
    promedio = calcular_promedio(calificaciones, historia)
    return render_template('H_cyberRevuelta.html', promedio=promedio)  # Archivo H_cyberRevuelta.html


@app.route('/H_ElAmantePerdido')
def H_ElAmantePerdido():
    calificaciones = cargar_json()  # Función que lee el JSON
    historia = '/H_ElAmantePerdido'
    promedio = calcular_promedio(calificaciones, historia)
    return render_template('H_ElAmantePerdido.html', promedio=promedio)  # Archivo H_ElAmantePerdido.html

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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Usa el puerto de Render o 5000 por defecto
    app.run(debug=True, host='0.0.0.0', port=port)  # Cambia host a '0.0.0.0'
