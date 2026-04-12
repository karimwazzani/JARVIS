import os
import json
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from src.database import SessionLocal, Transaccion, Recordatorio, Memoria, Tarea, PreferenciaUsuario, HabitoYPatron, PropuestaAutomatizacion
from sqlalchemy import func
from src.multimedia import generar_grafico_balance, spotify_control

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
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_memoria",
            "description": "Guarda información permanente sobre el usuario, preferencias, u otros datos a largo plazo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {"type": "string", "description": "Ej: 'Personal', 'Hogar', 'Vehículo', 'Trabajo'"},
                    "dato": {"type": "string", "description": "El dato clave a recordar."}
                },
                "required": ["categoria", "dato"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_memoria",
            "description": "Busca en la base de datos de memoria a largo plazo usando una palabra clave para recordar algo del pasado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string", "description": "Palabra clave a buscar en la memoria."}
                },
                "required": ["consulta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gestionar_luces",
            "description": "Controla las luces de la casa. Exige saber exactamente la habitación y la acción a realizar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "enum": ["encender", "apagar", "atenuar"]},
                    "habitacion": {"type": "string", "description": "Lugar específico, ej. 'todas', 'sala', 'dormitorio principal'."}
                },
                "required": ["accion", "habitacion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_tarea",
            "description": "Crea una nueva tarea o meta para hacerle seguimiento.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string"},
                    "titulo": {"type": "string", "description": "Breve nombre de la tarea."},
                    "descripcion": {"type": "string"}
                },
                "required": ["chat_id", "titulo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "completar_tarea",
            "description": "Marca una tarea existente como completada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tarea_id": {"type": "integer"}
                },
                "required": ["tarea_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_tareas",
            "description": "Consulta la lista de tareas (pendientes o completadas) del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string"},
                    "estado": {"type": "string", "enum": ["pendiente", "completada", "todas"], "description": "Filtro de búsqueda"}
                },
                "required": ["chat_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "configurar_preferencia",
            "description": "Guarda o actualiza una preferencia de sistema o alerta para el usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string"},
                    "clave": {"type": "string", "description": "Ej: 'silencio_nocturno', 'frecuencia_reportes'."},
                    "valor": {"type": "string"}
                },
                "required": ["chat_id", "clave", "valor"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "aprender_habito",
            "description": "Registra un comportamiento repetitivo o patrón del usuario para el aprendizaje continuo de JARVIS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string"},
                    "descripcion": {"type": "string", "description": "Ej: 'Siempre prende las luces a las 19:00'."}
                },
                "required": ["chat_id", "descripcion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_grafico_finanzas",
            "description": "Genera una imagen gráfica del balance general del usuario. Retorna una marca que le dice al bot de Telegram que envíe la imagen.",
            "parameters": {"type": "object", "properties": {"chat_id": {"type": "string"}}, "required": ["chat_id"]}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_multimedia",
            "description": "Control de música y ambientación (Spotify, Modos especiales).",
            "parameters": {
                "type": "object",
                "properties": {
                    "accion": {"type": "string", "enum": ["reproducir_cancion", "pausa", "modo_relajacion"]},
                    "query": {"type": "string", "description": "Nombre de canción o playlist si aplica."}
                },
                "required": ["accion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gestionar_propuesta_automatizacion",
            "description": "Acepta o rechaza una propuesta de aprendizaje continuo hecha previamente por el sistema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string"},
                    "decision": {"type": "string", "enum": ["aprobar", "rechazar"]}
                },
                "required": ["chat_id", "decision"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tomar_foto_vigilancia",
            "description": "Se conecta a la cámara de seguridad local IP (Tapo C200 o genérica) por protocolo RTSP y toma una fotografía instantánea del entorno físico del usuario.",
            "parameters": {"type": "object", "properties": {"chat_id": {"type": "string"}}, "required": ["chat_id"]}
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

        # memoria local de largo plazo
        elif nombre == "guardar_memoria":
            nuevo = Memoria(categoria=argumentos["categoria"], dato=argumentos["dato"])
            db.add(nuevo)
            db.commit()
            return f"Dato permanentemente guardado en categoría '{argumentos['categoria']}'."
            
        elif nombre == "buscar_memoria":
            from sqlalchemy import or_
            consulta = argumentos["consulta"].lower()
            terminos = [p for p in consulta.split() if len(p) > 2]
            query = db.query(Memoria)
            
            if terminos:
                condiciones = []
                for p in terminos:
                    condiciones.append(Memoria.categoria.ilike(f"%{p}%"))
                    condiciones.append(Memoria.dato.ilike(f"%{p}%"))
                query = query.filter(or_(*condiciones))
                
            resultados = query.limit(15).all()
            
            if not resultados:
                # Red de seguridad: si el LLM se equivoca de sinónimo (ej: autos vs vehículos)
                ultimos = db.query(Memoria).order_by(Memoria.id.desc()).limit(10).all()
                if not ultimos:
                    return "Tu memoria a largo plazo está vacía."
                res = [f"[{m.categoria}] {m.dato}" for m in ultimos]
                return f"No hallé coincidencia exacta para '{consulta}'. Como respaldo RAG, te ofrezco los últimos datos recordados:\n" + "\n".join(res)
                
            res = [f"[{m.categoria}] {m.dato}" for m in resultados]
            return "Extracción RAG exitosa. Datos:\n" + "\n".join(res)
            
        elif nombre == "gestionar_luces":
            return f"He procedido a {argumentos['accion']} las luces de {argumentos['habitacion']}."
            
        elif nombre == "crear_tarea":
            nueva_tarea = Tarea(chat_id=argumentos["chat_id"], titulo=argumentos["titulo"], descripcion=argumentos.get("descripcion", ""))
            db.add(nueva_tarea)
            db.commit()
            return f"Tarea '{argumentos['titulo']}' creada con éxito."
            
        elif nombre == "completar_tarea":
            t = db.query(Tarea).filter(Tarea.id == argumentos["tarea_id"]).first()
            if not t: return "No encontré esa tarea."
            t.estado = "completada"
            t.fecha_completada = datetime.now()
            db.commit()
            return f"Genial, tarea '{t.titulo}' marcada como completada."
            
        elif nombre == "consultar_tareas":
            estado = argumentos.get("estado", "todas")
            query = db.query(Tarea).filter(Tarea.chat_id == argumentos["chat_id"])
            if estado in ["pendiente", "completada"]:
                query = query.filter(Tarea.estado == estado)
            tareas_bd = query.all()
            if not tareas_bd: return f"No hay tareas registradas con estado '{estado}'."
            res = [f"ID {t.id} - [{t.estado.upper()}] {t.titulo}: {t.descripcion}" for t in tareas_bd]
            return "Tareas del usuario:\n" + "\n".join(res)
            
        elif nombre == "configurar_preferencia":
            pref = db.query(PreferenciaUsuario).filter(PreferenciaUsuario.chat_id == argumentos["chat_id"], PreferenciaUsuario.clave == argumentos["clave"]).first()
            if pref:
                pref.valor = argumentos["valor"]
            else:
                pref = PreferenciaUsuario(chat_id=argumentos["chat_id"], clave=argumentos["clave"], valor=argumentos["valor"])
                db.add(pref)
            db.commit()
            return f"Preferencia '{argumentos['clave']}' guardada como '{argumentos['valor']}'."
            
        elif nombre == "aprender_habito":
            habito = HabitoYPatron(chat_id=argumentos["chat_id"], descripcion=argumentos["descripcion"])
            db.add(habito)
            db.commit()
            return f"He aprendido este nuevo comportamiento: {argumentos['descripcion']}"
            
        elif nombre == "gestionar_propuesta_automatizacion":
            decision = argumentos["decision"]
            propuesta = db.query(PropuestaAutomatizacion).filter(PropuestaAutomatizacion.chat_id == str(argumentos["chat_id"]), PropuestaAutomatizacion.estado == "pendiente").first()
            if propuesta:
                propuesta.estado = "aprobada" if decision == "aprobar" else "rechazada"
                db.commit()
                return f"Propuesta '{propuesta.descripcion}' ha sido {propuesta.estado}."
            return "No encontré ninguna propuesta pendiente de aprendizaje continuo para gestionar."
            
        elif nombre == "generar_grafico_finanzas":
            ruta_imagen = generar_grafico_balance(argumentos["chat_id"])
            if not ruta_imagen: return "No tenés transacciones registradas para hacer un gráfico."
            return f"[GRAFICO_GENERADO:{ruta_imagen}] He generado el gráfico correspondiente."
            
        elif nombre == "tomar_foto_vigilancia":
            import os
            from multimedia import tapo_snapshot
            user = os.getenv("TAPO_USER")
            pwd = os.getenv("TAPO_PASSWORD")
            ip = os.getenv("TAPO_IP")
            if not user or not pwd or not ip:
                return "Error: Faltan credenciales ocultas TAPO_USER, TAPO_PASSWORD o TAPO_IP en el archivo secreto local .env."
                
            ruta = tapo_snapshot(ip, user, pwd, argumentos["chat_id"])
            if "Error" in ruta: return ruta
            return f"[FOTO_CAMARA:{ruta}] Conecté al dispositivo por red local usando latencia < 0.5s. Aquí está tu instantánea solicitada."
            
        elif nombre == "control_multimedia":
            res = spotify_control(argumentos["accion"], argumentos.get("query", ""))
            return res

        return "Función no reconocida."
    except Exception as e:
        return f"Error en DB: {e}"
    finally:
        db.close()

def transcribir_audio(file_path: str) -> str:
    """Envía un archivo local a OpenAI Whisper para su transcripción."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    return transcription.text

def get_ai_response(historial: list, chat_id: str) -> tuple[str, list]:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "tu_openai_api_key_aqui":
        return "ERROR: API KEY inexistente.", historial

    client = OpenAI(api_key=api_key)
    
    # Cargar preferencias
    db = SessionLocal()
    preferenciasText = ""
    try:
        prefs = db.query(PreferenciaUsuario).filter(PreferenciaUsuario.chat_id == str(chat_id)).all()
        if prefs:
            preferenciasText = "Tus preferencias configuradas actualmente son: " + ", ".join([f"{p.clave}={p.valor}" for p in prefs])
    except Exception:
        pass
    finally:
        db.close()
    
    now = datetime.now()
    fecha = now.strftime("%A, %d de %B de %Y")
    hora = now.strftime("%H:%M:%S")

    system_prompt = (
        "Eres JARVIS, un asistente inteligente ultra-proactivo y personal. "
        f"HOY ES {fecha} y la hora local es {hora}. "
        f"Tu chat_id oficial es '{chat_id}'. Úsalo siempre como STRING.\n"
        f"{preferenciasText}\n"
        "REGLAS OBLIGATORIAS:\n"
        "1. Tienes acceso a herramientas SQL en tiempo real.\n"
        "2. Usa herramientas financieras si el usuario pide manejar gastos/ingresos.\n"
        "3. EXIGE saber detalles explícitos si un comando es ambiguo.\n"
        "4. Si el usuario te indica un gusto rutinario ('no me avises de noche'), usa 'configurar_preferencia'.\n"
        "5. MODO MEMORIA PASIVA: ¡Usa 'guardar_memoria' proactivamente TODO EL TIEMPO si el usuario te menciona gustos, parientes, posesiones, o datos curiosos de sí mismo!\n"
        "6. MODO BÚSQUEDA RAG: Si el usuario asume que deberías recordar algo, o te hace una pregunta personal ('¿Cuál es mi auto?'), ¡usa obligatoriamente 'buscar_memoria' primero antes de contestarle que no sabes!\n"
        "7. Administra tareas usando 'crear_tarea', 'consultar_tareas' y 'completar_tarea'. Si el usuario te pregunta por un tema (ej: autos), usa 'buscar_memoria' y 'consultar_tareas' para cruzar la información inteligentemente.\n"
        "8. Usa 'gestionar_propuesta_automatizacion' si el usuario te lo pide."
    )
    
    messages = [{"role": "system", "content": system_prompt}] + historial
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=messages, tools=tools, tool_choice="auto", max_tokens=800
        )
        
        response_message = response.choices[0].message
        messages.append(response_message)
        
        media_buffer = []
        while getattr(response_message, 'tool_calls', None):
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                function_response = ejecutar_funcion(function_name, function_args)
                
                # Rescate infalible de UI Markers
                if isinstance(function_response, str):
                    if "[FOTO_CAMARA:" in function_response:
                        r = function_response.split("[FOTO_CAMARA:")[1].split("]")[0]
                        media_buffer.append(f"[FOTO_CAMARA:{r}]")
                    elif "[GRAFICO_GENERADO:" in function_response:
                        r = function_response.split("[GRAFICO_GENERADO:")[1].split("]")[0]
                        media_buffer.append(f"[GRAFICO_GENERADO:{r}]")
                        
                messages.append({"tool_call_id": tool_call.id, "role": "tool", "name": function_name, "content": str(function_response)})
            
            second_response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools, tool_choice="auto")
            response_message = second_response.choices[0].message
            messages.append(response_message)
            
        final_text = getattr(messages[-1], "content", "") if hasattr(messages[-1], "content") else messages[-1].get("content", "")
        if media_buffer:
            final_text += "\n" + "\n".join(media_buffer)
            
        historial.append({"role": "assistant", "content": final_text})
        return final_text, historial

    except Exception as e:
        print(f"Error AI Agent: {e}")
        return "Error en mi núcleo OpenAI.", historial
