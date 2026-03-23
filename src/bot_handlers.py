from telegram import Update
from telegram.ext import ContextTypes
from ai_agent import get_ai_response
from database import SessionLocal, Transaccion, Recordatorio, SensorAlert
from datetime import datetime
from sqlalchemy import func

# Memoria temporal
user_memory = {} 

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy JARVIS, tu asistente personal "
        "y estoy en línea.\n\n"
        "Usa /ayuda para ver todos mis comandos, o háblame con total naturalidad."
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🧠 *Asistencia Natural e IA:*\n"
        "JARVIS tiene MEMORIA y acceso a tus finanzas y alarmas.\n"
        "Dile: 'Recuérdame en 2 minutos que apague el horno' o 'Gasté 500 en pan'.\n\n"
        "💸 *Comandos Manuales Rápidos:*\n"
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
        nuevo = Transaccion(tipo="gasto", monto=monto, descripcion=descripcion)
        db.add(nuevo)
        db.commit()
        db.close()
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
        nuevo = Transaccion(tipo="ingreso", monto=monto, descripcion=descripcion)
        db.add(nuevo)
        db.commit()
        db.close()
        await update.message.reply_text(f"💰 Ingreso manual: **${monto:,.2f}** ({descripcion}).", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ El monto necesita ser un número.")

async def resumen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    gastos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "gasto").scalar() or 0.0
    ingresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "ingreso").scalar() or 0.0
    db.close()
    balance = ingresos - gastos
    resumen_text = (
        f"📊 *Balance Financiero*\n"
        f"-------------------------------\n"
        f"Ingresos: ${ingresos:,.2f}\n"
        f"Gastos:   ${gastos:,.2f}\n"
        f"-------------------------------\n"
        f"Saldo:    *${balance:,.2f}*"
    )
    await update.message.reply_text(resumen_text, parse_mode='Markdown')

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador principal de la IA con memoria e interacción libre"""
    chat_id = update.effective_chat.id
    user_text = update.message.text
    
    if chat_id not in user_memory:
        user_memory[chat_id] = []
        
    user_memory[chat_id].append({"role": "user", "content": user_text})
    if len(user_memory[chat_id]) > 15:
        user_memory[chat_id] = user_memory[chat_id][-15:]
        
    status_msg = await update.message.reply_text("Analizando...")
    
    try:
        response, updated_history = get_ai_response(user_memory[chat_id], str(chat_id))
        user_memory[chat_id] = updated_history
        await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=response)
    except Exception as e:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=status_msg.message_id, text=f"Error: {str(e)}")

# Tarea programada (Cron/JobQueue)
async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Verifica si hay recordatorios pendientes y los envía"""
    db = SessionLocal()
    ahora = datetime.now()
    
    pendientes = db.query(Recordatorio).filter(
        Recordatorio.enviado == False, 
        Recordatorio.fecha_aviso <= ahora
    ).all()
    
    for r in pendientes:
        try:
            await context.bot.send_message(
                chat_id=r.chat_id, 
                text=f"⏰ *RECORDATORIO DE JARVIS:*\n\n{r.mensaje}",
                parse_mode='Markdown'
            )
            r.enviado = True
        except Exception as e:
            print(f"Error enviando recordatorio {r.id}: {e}")
            
    if pendientes:
        db.commit()
    db.close()

# Tarea programada (Cron/JobQueue) para Sensores
async def check_sensores(context: ContextTypes.DEFAULT_TYPE):
    """Verifica si hay alertas de hardware sin leer y avisa al dueño."""
    db = SessionLocal()
    alertas = db.query(SensorAlert).filter(SensorAlert.leido == False).all()
    
    # Broadcast a cualquier chat_id que haya interactuado con el bot
    if alertas and user_memory.keys():
        for alerta in alertas:
            alerta.leido = True
            for chat_id in user_memory.keys():
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🚨 *ALERTA IOT - Sensor: {alerta.sensor_id}*\n⚠️ {alerta.mensaje}",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Error enviando alerta IoT al chat {chat_id}: {e}")
        db.commit()
    db.close()
