import os
import math
from telegram import Update
from telegram.ext import ContextTypes
from src.ai_agent import get_ai_response, transcribir_audio, ejecutar_funcion, generar_audio_respuesta
from src.database import SessionLocal, Transaccion, Recordatorio, SensorAlert, Tarea, PreferenciaUsuario, HabitoYPatron, LogEvento, PropuestaAutomatizacion, Conversacion
from src.external_services import get_btc_price, get_weather, get_top_news
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import func

# Memoria temporal
user_memory = {} 
last_interaction = {}

def registrar_evento(chat_id: str, evento: str):
    try:
        db = SessionLocal()
        db.add(LogEvento(chat_id=str(chat_id), evento=evento))
        db.commit()
    except: pass
    finally:
        db.close()

def registrar_mensaje(chat_id: str, rol: str, contenido: str):
    try:
        db = SessionLocal()
        db.add(Conversacion(chat_id=str(chat_id), rol=rol, contenido=contenido))
        db.commit()
    except: pass
    finally:
        db.close()

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy JARVIS, tu asistente analítico.\n\n"
        "Puedes hablarme, enviarme audios o usar comandos manuales. Usa /ayuda para más info."
    )

async def enviar_respuesta_jarvis(update: Update, response: str, es_voz: bool = False):
    import re, os
    match_graf = re.search(r"\[GRAFICO_GENERADO:(.*?)\]", response)
    match_fot = re.search(r"\[FOTO_CAMARA:(.*?)\]", response)
    
    if match_graf or match_fot:
        match = match_graf if match_graf else match_fot
        file_path = match.group(1)
        texto_limpio = response.replace(match.group(0), "").strip()
        
        # El usuario solicitó explícitamente no recibir muletillas de texto junto a la foto
        # if texto_limpio:
        #     await update.message.reply_text(text=texto_limpio, parse_mode='Markdown')
            
        if os.path.exists(file_path):
            with open(file_path, 'rb') as photo:
                await update.message.reply_photo(photo=photo)
            try:
                os.remove(file_path)
            except: pass
        else:
            await update.message.reply_text(text="⚠️ JARVIS: No se encontró el archivo visual en el almacenamiento local.", parse_mode='Markdown')
        return

    # Si es voz, generamos el TTS
    if es_voz:
        audio_path = await generar_audio_respuesta(response, str(update.effective_chat.id))
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, 'rb') as voice_file:
                await update.message.reply_voice(voice=voice_file)
            try:
                os.remove(audio_path)
            except: pass
            return

    # Fallback to text (or user sent text)
    await update.message.reply_text(text=response, parse_mode='Markdown')
    
async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    last_interaction[chat_id] = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None)
    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude
        
        db = SessionLocal()
        home_lat = db.query(PreferenciaUsuario).filter_by(chat_id=str(chat_id), clave="home_lat").first()
        home_lon = db.query(PreferenciaUsuario).filter_by(chat_id=str(chat_id), clave="home_lon").first()
        
        proximidad_msg = ""
        if home_lat and home_lon:
            # Distancia aproximada (muy simplificada para radio de ~1km)
            dist = math.sqrt((lat - float(home_lat.valor))**2 + (lon - float(home_lon.valor))**2)
            if dist < 0.005: # Aprox 500 metros
                proximidad_msg = "\n📍 *JARVIS:* Detecto que está cerca de casa, Señor. ¿Desea que active el Modo Hogar?"
                registrar_evento(str(chat_id), "Usuario detectado cerca de Casa")
        
        registrar_evento(str(chat_id), f"Compartió ubicación: {lat}, {lon}")
        db.close()
        
        await update.message.reply_text(f"Ubicación recibida por JARVIS.{proximidad_msg}", parse_mode='Markdown')

async def sethome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not update.message.reply_to_message or not update.message.reply_to_message.location:
        await update.message.reply_text("Señor, debe responder a un mensaje de ubicación con /sethome para establecer su base.")
        return
    
    loc = update.message.reply_to_message.location
    db = SessionLocal()
    # Guardar lat
    plat = db.query(PreferenciaUsuario).filter_by(chat_id=str(chat_id), clave="home_lat").first()
    if plat: plat.valor = str(loc.latitude)
    else: db.add(PreferenciaUsuario(chat_id=str(chat_id), clave="home_lat", valor=str(loc.latitude)))
    
    # Guardar lon
    plon = db.query(PreferenciaUsuario).filter_by(chat_id=str(chat_id), clave="home_lon").first()
    if plon: plon.valor = str(loc.longitude)
    else: db.add(PreferenciaUsuario(chat_id=str(chat_id), clave="home_lon", valor=str(loc.longitude)))
    
    db.commit()
    db.close()
    await update.message.reply_text("📍 *Base establecida.* JARVIS ahora conoce la ubicación de su residencia.", parse_mode='Markdown')

async def modo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not context.args:
        await update.message.reply_text("Dígame el modo, Señor. Ejemplo: `/modo Centinela` o `/modo Relax`.", parse_mode='Markdown')
        return
    
    nuevo_modo = " ".join(context.args)
    db = SessionLocal()
    # Usamos 'general' para sincronizar con el Dashboard
    pref = db.query(PreferenciaUsuario).filter_by(clave="modo_sistema").first()
    if pref: 
        pref.valor = nuevo_modo
        pref.chat_id = "general" # Asegurar consistencia
    else: 
        db.add(PreferenciaUsuario(chat_id="general", clave="modo_sistema", valor=nuevo_modo))
    
    db.add(LogEvento(chat_id=str(chat_id), evento=f"Cambio de modo a: {nuevo_modo}"))
    db.commit()
    db.close()
    await update.message.reply_text(f"⚙️ *SISTEMA:* Iniciando {nuevo_modo}. Ajustando protocolos...", parse_mode='Markdown')

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🧠 *Notas de Voz y Texto (IA):*\n"
        "Solo presiona el micrófono de Telegram y dime qué necesitas (o escríbelo).\n\n"
        "💸 *Comandos Manuales:*\n"
        "• `/gasto 1500 café`\n"
        "• `/ingreso 50000 sueldo`\n"
        "• `/resumen`"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def gasto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Uso: /gasto [monto] [descripción]")
            return
        monto = float(context.args[0])
        descripcion = " ".join(context.args[1:])
        db = SessionLocal()
        db.add(Transaccion(tipo="gasto", monto=monto, descripcion=descripcion))
        db.commit()
        db.close()
        registrar_evento(str(update.effective_chat.id), f"Registró gasto: {monto} en {descripcion}")
        await update.message.reply_text(f"💸 Gasto manual: **${monto:,.2f}** ({descripcion}).", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ El monto necesita ser un número.")

async def ingreso_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ Uso: /ingreso [monto] [descripción]")
            return
        monto = float(context.args[0])
        descripcion = " ".join(context.args[1:])
        db = SessionLocal()
        db.add(Transaccion(tipo="ingreso", monto=monto, descripcion=descripcion))
        db.commit()
        db.close()
        registrar_evento(str(update.effective_chat.id), f"Registró ingreso: {monto} en {descripcion}")
        await update.message.reply_text(f"💰 Ingreso manual: **${monto:,.2f}** ({descripcion}).", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ El monto necesita ser un número.")

async def resumen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    gastos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "gasto").scalar() or 0.0
    ingresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "ingreso").scalar() or 0.0
    db.close()
    registrar_evento(str(update.effective_chat.id), "Solicitó resumen financiero")
    await update.message.reply_text(f"📊 *Balance*\nIngresos: ${ingresos:,.2f}\nGastos: ${gastos:,.2f}\nSaldo: *${ingresos - gastos:,.2f}*", parse_mode='Markdown')

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = update.message.text
    last_interaction[chat_id] = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None)
    registrar_evento(str(chat_id), f"Texto: {user_text}")
    registrar_mensaje(str(chat_id), "user", user_text)
    if chat_id not in user_memory: user_memory[chat_id] = []
    user_memory[chat_id].append({"role": "user", "content": user_text})
    if len(user_memory[chat_id]) > 40: user_memory[chat_id] = user_memory[chat_id][-40:]
        
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        response, updated_history = get_ai_response(user_memory[chat_id], str(chat_id))
        user_memory[chat_id] = updated_history
        registrar_mensaje(str(chat_id), "assistant", response)
        await enviar_respuesta_jarvis(update, response, es_voz=False)
    except Exception as e:
        await update.message.reply_text(text=f"Error: {str(e)}")

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para notas de Voz (Vía Whisper)"""
    chat_id = update.effective_chat.id
    last_interaction[chat_id] = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None)
    
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        
        file = await context.bot.get_file(update.message.voice.file_id)
        file_path = f"voz_{chat_id}.ogg"
        await file.download_to_drive(file_path)
        
        texto_transcrito = transcribir_audio(file_path)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        registrar_evento(str(chat_id), f"Voz (transcrito): {texto_transcrito}")
        registrar_mensaje(str(chat_id), "user", f"[VOZ] {texto_transcrito}")
        if chat_id not in user_memory: user_memory[chat_id] = []
        user_memory[chat_id].append({"role": "user", "content": texto_transcrito})
        if len(user_memory[chat_id]) > 40: user_memory[chat_id] = user_memory[chat_id][-40:]
            
        response, updated_history = get_ai_response(user_memory[chat_id], str(chat_id))
        user_memory[chat_id] = updated_history
        registrar_mensaje(str(chat_id), "assistant", response)
        await enviar_respuesta_jarvis(update, response, es_voz=True)
        
    except Exception as e:
        await update.message.reply_text(text=f"Error en audio: {str(e)}")

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    ahora = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None)
    pendientes = db.query(Recordatorio).filter(Recordatorio.enviado == False, Recordatorio.fecha_aviso <= ahora).all()
    for r in pendientes:
        try:
            await context.bot.send_message(chat_id=r.chat_id, text=f"⏰ *RECORDATORIO DE JARVIS:*\n\n{r.mensaje}", parse_mode='Markdown')
            r.enviado = True
        except: pass
    if pendientes: db.commit()
    db.close()

async def check_sensores(context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    alertas = db.query(SensorAlert).filter(SensorAlert.leido == False).all()
    if alertas and user_memory.keys():
        for alerta in alertas:
            alerta.leido = True
            
            if alerta.sensor_id == "PIR_Centinela_Habitacion":
                # Alerta Ojo de Halcón - Avisar a Tapo C200
                import os
                tapo_user = os.getenv("TAPO_USER")
                tapo_pass = os.getenv("TAPO_PASSWORD")
                tapo_ip = os.getenv("TAPO_IP")
                
                if tapo_user and tapo_pass and tapo_ip:
                    # Opcionalmente se podría forzar un snapshot RTSP o rotar el PTZ
                    for chat_id in user_memory.keys():
                        try:
                            await context.bot.send_message(
                                chat_id=chat_id, 
                                text=f"🚨 *MODO CENTINELA ACTIVADO*\n{alerta.mensaje}\n_(Iniciando rotación de cámara PTZ TP-Link Tapo hacia la zona de intrusión)_", 
                                parse_mode='Markdown'
                            )
                        except: pass
                else:
                    for chat_id in user_memory.keys():
                        try:
                            await context.bot.send_message(
                                chat_id=chat_id, 
                                text=f"🚨 *MODO CENTINELA ACTIVADO*\n{alerta.mensaje}\n_(Aviso: Configura las credenciales TAPO_USER, TAPO_PASSWORD e IP en tu archivo .env para procesar rotación automática)_", 
                                parse_mode='Markdown'
                            )
                        except: pass
            else:
                for chat_id in user_memory.keys():
                    try: 
                        await context.bot.send_message(chat_id=chat_id, text=f"🚨 *ALERTA IOT - Sensor: {alerta.sensor_id}*\n⚠️ {alerta.mensaje}", parse_mode='Markdown')
                    except: pass
        db.commit()
    db.close()

async def check_bienestar(context: ContextTypes.DEFAULT_TYPE):
    ahora = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None)
    for chat_id, ultima_vez in last_interaction.items():
        if (ahora - ultima_vez).total_seconds() > 4 * 3600: # 4 horas
            if 8 <= ahora.hour <= 22:
                try:
                    await context.bot.send_message(chat_id=chat_id, text="🧘‍♂️ JARVIS Bienestar: Pasaron 4 horas desde tu última interacción. ¡Recordá tomar un breve descanso!")
                except: pass
                last_interaction[chat_id] = ahora

async def reporte_semanal(context: ContextTypes.DEFAULT_TYPE):
    """Envía un reporte semanal de tareas y hábitos registrados."""
    db = SessionLocal()
    for chat_id in user_memory.keys():
        try:
            total = db.query(Tarea).filter(Tarea.chat_id == str(chat_id)).count()
            completadas = db.query(Tarea).filter(Tarea.chat_id == str(chat_id), Tarea.estado == "completada").count()
            if total > 0:
                porcentaje = (completadas / total) * 100
                msg = f"📈 *Resumen de Actividades*\nCompletaste el {porcentaje:.0f}% de tus tareas recientes ({completadas}/{total})."
                if porcentaje == 100: msg += "\n¡Excelente trabajo! Seguí así."
                elif porcentaje > 50: msg += "\n¡Vas muy bien!"
                else: msg += "\nEs un buen momento para enfocarte en tus pendientes, ¡tú puedes!"
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        except: pass
    db.close()

async def analisis_predictivo(context: ContextTypes.DEFAULT_TYPE):
    """Módulo de Análisis Predictivo y Detección de Patrones"""
    db = SessionLocal()
    ahora = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).replace(tzinfo=None)
    
    for chat_id in user_memory.keys():
        try:
            # 1. Inactividad financiera
            ultima_transaccion = db.query(Transaccion).filter(Transaccion.tipo == "gasto").order_by(Transaccion.fecha.desc()).first()
            if ultima_transaccion and (ahora - ultima_transaccion.fecha).days >= 2:
                try: 
                    await context.bot.send_message(chat_id=chat_id, text="💡 *JARVIS Finanzas:* Llevás más de 2 días sin registrar gastos; no olvides actualizar tu flujo financiero.", parse_mode='Markdown')
                except: pass
                
            # 2. Sugerencias basadas en patrones
            patrones = db.query(HabitoYPatron).filter(HabitoYPatron.chat_id == str(chat_id)).all()
            if patrones:
                p = patrones[-1]
                try:
                    await context.bot.send_message(chat_id=chat_id, text=f"🧠 *JARVIS Predictivo:* Basado en tus hábitos o comportamientos detectados:\n_{p.descripcion}_", parse_mode='Markdown')
                except: pass
        except: pass
    db.close()

async def proactive_morning_briefing(context: ContextTypes.DEFAULT_TYPE):
    """Envía un resumen matutino proactivo optimizado para baja latencia (sin tool calls)."""
    db = SessionLocal()
    try:
        # Pre-fetch de datos externos para ahorrar round-trips de IA
        clima = get_weather("Buenos Aires")
        btc = get_btc_price()
        noticias = "\n- ".join(get_top_news())
        
        chat_ids = db.query(LogEvento.chat_id).distinct().all()
        for row in chat_ids:
            chat_id = row[0]
            
            # Consultar agenda localmente para inyectarla directo
            agenda_raw = ejecutar_funcion("consultar_agenda", {"chat_id": str(chat_id)})
            
            prompt = (
                f"SISTEMA: Reporte Matutino de Baja Latencia.\n"
                f"DATOS RECIENTES:\n- Clima: {clima}\n- BTC: {btc}\n- Noticias: {noticias}\n- {agenda_raw}\n\n"
                "Genera un saludo matutino elegante, breve y motivador basado en estos datos. "
                "No uses herramientas, redacta la respuesta directamente para ahorrar tokens."
            )
            
            temp_history = [{"role": "user", "content": prompt}]
            response, _ = get_ai_response(temp_history, str(chat_id))
            
            audio_path = await generar_audio_respuesta(response, chat_id)
            if audio_path and os.path.exists(audio_path):
                with open(audio_path, 'rb') as audio_file:
                    await context.bot.send_voice(
                        chat_id=chat_id, 
                        voice=audio_file, 
                        caption="☀️ *JARVIS: REPORTE MATUTINO*\n_(Audio generado proactivamente)_", 
                        parse_mode='Markdown'
                    )
                try:
                    os.remove(audio_path)
                except: pass
            else:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=f"☀️ *JARVIS: REPORTE MATUTINO*\n\n{response}", 
                    parse_mode='Markdown'
                )
    except Exception as e:
        print(f"Error en briefing matutino: {e}")
    finally:
        db.close()
