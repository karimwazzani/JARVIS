import os
import sys
import traceback

from dotenv import load_dotenv
from flask import Flask, request as flask_request
# Asegurar path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from src.security import is_chat_authorized

app = Flask(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
_db_initialized = False


def tg_send(chat_id, text, parse_mode=None):
    import requests

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = TELEGRAM_API.format(token=token, method="sendMessage")
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        requests.post(url, json=payload, timeout=8)
    except Exception as exc:
        print(f"ERROR tg_send: {exc}", flush=True)


def tg_send_action(chat_id, action="typing"):
    import requests

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = TELEGRAM_API.format(token=token, method="sendChatAction")
    try:
        requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=5)
    except Exception:
        pass


def ensure_db():
    global _db_initialized
    if not _db_initialized:
        from src.database import init_db

        print("DEBUG: Inicializando base de datos...", flush=True)
        init_db()
        _db_initialized = True
        print("DEBUG: Base de datos lista.", flush=True)


def registrar_evento(chat_id: str, evento: str) -> None:
    from src.database import LogEvento, SessionLocal

    try:
        db = SessionLocal()
        db.add(LogEvento(chat_id=str(chat_id), evento=evento))
        db.commit()
    except Exception as exc:
        print(f"WARN: No se pudo registrar evento: {exc}", flush=True)
    finally:
        db.close()


def process_text_message(chat_id, text):
    ensure_db()

    from src.core.orchestrator import run_jarvis_turn
    from src.database import fetch_conversation_history, store_conversation_message

    store_conversation_message(str(chat_id), "user", text)
    history = fetch_conversation_history(str(chat_id), limit=20)
    response_text, _ = run_jarvis_turn(history, str(chat_id))
    store_conversation_message(str(chat_id), "assistant", response_text)
    return response_text


def handle_chat_turn(chat_id, text):
    print(f"DEBUG: Chat={chat_id}, Texto='{text[:80]}'", flush=True)
    registrar_evento(str(chat_id), f"Texto: {text}")
    response = process_text_message(chat_id, text)
    return response


def handle_finance_command(chat_id, text):
    from src.database import create_finance_transaction, fetch_finance_summary

    try:
        if text == "/resumen":
            summary = fetch_finance_summary()
            tg_send(
                chat_id,
                f"Balance\nIngresos: ${summary['ingresos']:,.2f}\nGastos: ${summary['gastos']:,.2f}\nSaldo: ${summary['saldo']:,.2f}",
            )
            return True

        if text.startswith("/gasto"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                tg_send(chat_id, "Uso: /gasto [monto] [descripcion]")
                return True
            monto = float(parts[1])
            desc = parts[2]
            create_finance_transaction("gasto", monto, desc)
            tg_send(chat_id, f"Gasto registrado: ${monto:,.2f} ({desc})")
            return True

        if text.startswith("/ingreso"):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                tg_send(chat_id, "Uso: /ingreso [monto] [descripcion]")
                return True
            monto = float(parts[1])
            desc = parts[2]
            create_finance_transaction("ingreso", monto, desc)
            tg_send(chat_id, f"Ingreso registrado: ${monto:,.2f} ({desc})")
            return True
    except ValueError:
        tg_send(chat_id, "El monto tiene que ser un numero.")
        return True

    return False


@app.route("/", methods=["GET", "POST"])
def webhook():
    if flask_request.method == "GET":
        return "<h1>JARVIS Online</h1><p>Sistema operativo.</p>", 200

    try:
        update = flask_request.get_json(force=True)
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = (message.get("text") or "").strip()

        if not chat_id:
            return "OK", 200

        if not is_chat_authorized(chat_id):
            tg_send(chat_id, "Acceso no autorizado.")
            return "OK", 200

        if text.lower() == "ping":
            tg_send(chat_id, "PONG! JARVIS conectado.")
            return "OK", 200

        if text == "/start":
            tg_send(
                chat_id,
                "Hola. Soy JARVIS.\n\n"
                "Ya estoy online en Render y ahora corro con orquestador, memoria y rutas por agente.\n"
                "Usa /ayuda para ver los comandos base.",
            )
            return "OK", 200

        if text == "/ayuda":
            tg_send(
                chat_id,
                "Comandos base:\n"
                "/gasto 1500 cafe\n"
                "/ingreso 50000 sueldo\n"
                "/resumen\n\n"
                "Y si no, hablame normal. Ahora yo decido que agente entra.",
            )
            return "OK", 200

        if handle_finance_command(chat_id, text):
            return "OK", 200

        if text and not text.startswith("/"):
            tg_send_action(chat_id, "typing")
            try:
                response = handle_chat_turn(chat_id, text)
                tg_send(chat_id, response)
            except Exception as exc:
                print(f"ERROR procesando texto:\n{traceback.format_exc()}", flush=True)
                tg_send(chat_id, f"Error interno: {str(exc)[:200]}")
            return "OK", 200

        return "OK", 200
    except Exception:
        print(f"ERROR FATAL EN WEBHOOK:\n{traceback.format_exc()}", flush=True)
        return "OK", 200


@app.route("/api/chat", methods=["POST"])
def web_chat():
    try:
        payload = flask_request.get_json(force=True) or {}
        chat_id = str(payload.get("chatId") or "web-panel")
        text = str(payload.get("message") or "").strip()

        if not text:
            return {"ok": False, "error": "Message is required."}, 400

        response = handle_chat_turn(chat_id, text)
        return {"ok": True, "chatId": chat_id, "message": text, "response": response}, 200
    except Exception as exc:
        print(f"ERROR WEB CHAT:\n{traceback.format_exc()}", flush=True)
        return {"ok": False, "error": str(exc)[:200]}, 500
