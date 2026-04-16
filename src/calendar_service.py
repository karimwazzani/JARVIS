import os
import datetime
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def get_calendar_service():
    creds = None
    # El archivo token.pickle almacena los tokens de acceso del usuario
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # Si no hay credenciales válidas, dejamos que el usuario inicie sesión (o fallamos elegantemente)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("⚠️ [CALENDAR] No se encontró credentials.json. Saltando integración.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guardar las credenciales para la próxima vez
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def get_next_events(n=5):
    service = get_calendar_service()
    if not service:
        return []
    
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=n, singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    
    formatted_events = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        # Parsear fecha
        try:
            dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
        except:
            # Fallback para fechas todo-el-dia
            dt = datetime.datetime.strptime(start, '%Y-%m-%d')
            
        formatted_events.append({
            'summary': event.get('summary', '(Sin título)'),
            'start': dt,
            'location': event.get('location', '')
        })
    return formatted_events
