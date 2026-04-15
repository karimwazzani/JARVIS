import os
import json
from datetime import datetime, timedelta
from telegram.ext import ContextTypes
from openai import OpenAI
from dotenv import load_dotenv
from src.database import SessionLocal, LogEvento, PropuestaAutomatizacion

async def run_learning_engine(context: ContextTypes.DEFAULT_TYPE):
    """
    Minería de datos sobre el LogEvento del usuario usando OpenAI.
    Se ejecuta programadamente para descubrir patrones y hacer propuestas.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "tu_openai_api_key_aqui":
        return

    client = OpenAI(api_key=api_key)
    db = SessionLocal()
    
    from zoneinfo import ZoneInfo
    # Agrupar los usuarios activos en la última semana
    semana_pasada = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None) - timedelta(days=7)
    usuarios_chats = db.query(LogEvento.chat_id).filter(LogEvento.fecha >= semana_pasada).distinct().all()
    
    for row in usuarios_chats:
        chat_id = row[0]
        # Recuperar hasta 200 eventos recientes del usuario
        logs = db.query(LogEvento).filter(LogEvento.chat_id == chat_id).order_by(LogEvento.fecha.desc()).limit(200).all()
        if len(logs) < 10:
            continue
            
        # Formatear logs para el LLM
        lista_eventos = []
        for l in reversed(logs):
            fecha_corta = l.fecha.strftime("%A %H:%M:%S")
            lista_eventos.append(f"[{fecha_corta}] {l.evento}")
        
        texto_logs = "\n".join(lista_eventos)
        
        prompt = (
            "Eres el Motor de Aprendizaje Continuo de JARVIS.\n"
            "Analiza los siguientes logs de eventos ordenados cronológicamente y detecta si el usuario tiene un patrón o rutina repetitiva. "
            "Si encuentras al menos un patrón claro, responde EXCLUSIVAMENTE con un JSON válido usando el siguiente formato exacto:\n"
            "{\"patron_encontrado\": true, \"descripcion_sugerencia\": \"Noté que de lunes a viernes a las 08:00 siempre registrás un gasto de café. ¿Te lo automatizo?\", \"accion_tecnica\": \"registrar_gasto:cafe\"}\n"
            "Si no hay un patrón claro o no estás seguro, responde:\n"
            "{\"patron_encontrado\": false}\n"
            "No respondas absolutamente nada más que el JSON válido.\n\n"
            f"LOGS:\n{texto_logs}"
        )
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            respuesta_json = response.choices[0].message.content
            # Limpiar posible markdown del LLM (```json)
            respuesta_json = respuesta_json.replace("```json", "").replace("```", "").strip()
            datos = json.loads(respuesta_json)
            
            if datos.get("patron_encontrado"):
                desc = datos.get("descripcion_sugerencia")
                accion = datos.get("accion_tecnica")
                
                # Checkear si ya existe la propuesta para no spamear
                existente = db.query(PropuestaAutomatizacion).filter(PropuestaAutomatizacion.chat_id == chat_id, PropuestaAutomatizacion.descripcion == desc).first()
                if not existente:
                    nueva_propuesta = PropuestaAutomatizacion(chat_id=chat_id, descripcion=desc, accion_tecnica=accion)
                    db.add(nueva_propuesta)
                    db.commit()
                    
                    # Notificar al momento
                    await context.bot.send_message(
                        chat_id=chat_id, 
                        text=f"🤖 *Aprendizaje Continuo JARVIS:*\n\n{desc}\n\n_(Para aceptar esta sugerencia, decime 'Sí, acepto tu propuesta JARVIS' y yo mismo configuraré la regla)._", 
                        parse_mode='Markdown'
                    )
        except Exception as e:
            print(f"Error procesando learning engine para {chat_id}: {e}")
            pass

    db.close()
