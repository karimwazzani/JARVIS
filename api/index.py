import os
import sys
from flask import Flask, request

# Asegurar path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    return "<h1>JARVIS está en línea</h1><p>Si ves esto, el servidor funciona. Falta configurar el Webhook.</p>", 200

@app.route('/api/webhook', methods=['POST'])
def webhook():
    return "OK", 200

# Exponer la app para Vercel
app_obj = app
