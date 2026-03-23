import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from database import SessionLocal, Transaccion, Recordatorio
from sqlalchemy import func

tools = [
     {
        "type": "function",
        "function": {
            "name": "registrar_transaccion",
            "description": "Registra un nuevo gasto o ingreso en la base de datos de finanzas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["gasto", "ingreso"]},
                    "monto": {"type": "number"},
                    "descripcion": {"type": "string"}
                },
                "required": ["tipo", "monto", "descripcion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_resumen",
            "description": "Obtiene el total de ingresos, gastos y el balance actual (saldo).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_ultimos_movimientos",
            "description": "Consulta las últimas transacciones registradas. Útil para buscar el ID de una transacción para borrarla o editarla.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limite": {"type": "integer"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "eliminar_transaccion",
            "description": "Elimina permanentemente una transacción de la base de datos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"}
                },
                "required": ["id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "editar_transaccion",
            "description": "Modifica una transacción existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "monto": {"type": "number"},
                    "descripcion": {"type": "string"},
                    "tipo": {"type": "string", "enum": ["gasto", "ingreso"]}
                },
                "required": ["id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_recordatorio",
            "description": "Crea una alerta o recordatorio programado para el usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "description": "El ID de Telegram del usuario (está provisto en el prompt de sistema)."},
                    "mensaje": {"type": "string", "description": "Lo que JARVIS debe recordarle al usuario."},
                    "fecha_aviso": {"type": "string", "description": "La fecha y hora exacta para avisar en formato 'YYYY-MM-DD HH:MM:00'."}
                },
                "required": ["chat_id", "mensaje", "fecha_aviso"]
            }
        }
    }
]

def ejecutar_funcion(nombre: str, argumentos: dict) -> str:
    db = SessionLocal()
    try:
        # transacciones
        if nombre == "registrar_transaccion":
            nuevo = Transaccion(tipo=argumentos["tipo"], monto=argumentos["monto"], descripcion=argumentos["descripcion"])
            db.add(nuevo)
            db.commit()
            return f"Transacción registrada con éxito: {argumentos['tipo']} de ${argumentos['monto']} en {argumentos['descripcion']}."
            
        elif nombre == "consultar_resumen":
            gastos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "gasto").scalar() or 0.0
            ingresos = db.query(func.sum(Transaccion.monto)).filter(Transaccion.tipo == "ingreso").scalar() or 0.0
            balance = ingresos - gastos
            return json.dumps({"ingresos": ingresos, "gastos": gastos, "balance": balance})
            
        elif nombre == "consultar_ultimos_movimientos":
            limite = argumentos.get("limite", 5)
            movimientos = db.query(Transaccion).order_by(Transaccion.id.desc()).limit(limite).all()
            if not movimientos:
                return "No hay transacciones guardadas."
            res = [{"id": m.id, "tipo": m.tipo, "monto": m.monto, "desc": m.descripcion} for m in movimientos]
            return json.dumps(res)
            
        elif nombre == "eliminar_transaccion":
            id_trans = argumentos["id"]
            t = db.query(Transaccion).filter(Transaccion.id == id_trans).first()
            if not t: return f"ID {id_trans} no encontrado."
            db.delete(t)
            db.commit()
            return f"ID {id_trans} eliminada exitosamente."
            
        elif nombre == "editar_transaccion":
            id_trans = argumentos["id"]
            t = db.query(Transaccion).filter(Transaccion.id == id_trans).first()
            if not t: return f"ID {id_trans} no encontrado."
            if "monto" in argumentos and argumentos["monto"] is not None: t.monto = argumentos["monto"]
            if "descripcion" in argumentos and argumentos["descripcion"] is not None: t.descripcion = argumentos["descripcion"]
            if "tipo" in argumentos and argumentos["tipo"] is not None: t.tipo = argumentos["tipo"]
            db.commit()
            return f"Transacción ID {id_trans} editada."
            
        # recordatorios
        elif nombre == "crear_recordatorio":
            fecha_str = argumentos["fecha_aviso"]
            fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            nuevo = Recordatorio(
                chat_id=str(argumentos["chat_id"]),
                mensaje=argumentos["mensaje"],
                fecha_aviso=fecha_obj
            )
            db.add(nuevo)
            db.commit()
            return f"Recordatorio programado exitosamente para el {fecha_str}."

        return "Función no reconocida."
    except Exception as e:
        return f"Error en DB: {e}"
    finally:
        db.close()

def get_ai_response(historial: list, chat_id: str) -> (str, list):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "tu_openai_api_key_aqui":
        return "ERROR: API KEY inexistente.", historial

    client = OpenAI(api_key=api_key)
    
    now = datetime.now()
    fecha = now.strftime("%A, %d de %B de %Y")
    hora = now.strftime("%H:%M:%S")

    system_prompt = (
        "Eres JARVIS, un inteligente asistente personal. "
        f"HOY ES {fecha} y la hora local en Argentina es {hora}. "
        f"INFORMACIÓN DEL USUARIO: Su 'chat_id' de Telegram es '{chat_id}'. Úsalo SIEMPRE COMO STRING que crees un recordatorio.\n"
        "REGLAS:\n"
        "1. Tienes MEMORIA del chat.\n"
        "2. Usa 'registrar_transaccion' o 'consultar_resumen' para finanzas.\n"
        "3. Usa 'consultar_ultimos_movimientos' y luego 'editar_transaccion' o 'eliminar_transaccion' para corregir errores.\n"
        "4. Usa 'crear_recordatorio' si el usuario te pide que le avises o le recuerdes algo más tarde, en unos minutos o mañana. Usa el chat_id provisto y calcula la fecha_aviso exacta basándote en la fecha y hora proporcionada en el contexto.\n"
        "Aclárale al usuario a qué hora exacta programaste la alerta."
    )
    
    messages = [{"role": "system", "content": system_prompt}] + historial
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=tools, tool_choice="auto", max_tokens=800
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)
        
        while getattr(response_message, 'tool_calls', None):
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                function_response = ejecutar_funcion(function_name, function_args)
                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": str(function_response)})
            
            second_response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools, tool_choice="auto")
            response_message = second_response.choices[0].message
            messages.append(response_message)
            
        final_text = messages[-1].content
        historial.append({"role": "assistant", "content": final_text})
        return final_text, historial

    except Exception as e:
        print(f"Error AI Agent: {e}")
        return "Error en mi núcleo OpenAI.", historial
