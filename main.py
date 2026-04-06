import io, uvicorn, requests
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from PIL import Image
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from passlib.context import CryptContext

app = FastAPI()
#configuración para seguridad de contraseñas -- importante usar un algoritmo robusto como bcrypt o pbkdf2_sha256
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)

#--- CONFIGURACIÓN ---
API_KEY = ""  #reemplaza con tu API Key de Google GenAI
client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-2.5-flash"
SPREADSHEET_ID = '' #Reemplaza con nueva ID de hoja de cálculo
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_service():
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES) #Reemplaza con la ruta a tu archivo de credenciales JSON
    return build('sheets', 'v4', credentials=creds)

def init_user_db(service):
    """Asegura que exista la hoja de usuarios"""
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = [s['properties']['title'] for s in meta.get('sheets', [])]
    if 'Users_DB' not in sheets:
        body = {'requests': [{'addSheet': {'properties': {'title': 'Users_DB'}}}]}
        service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range="Users_DB!A1:B1",
            valueInputOption="RAW", body={'values': [["USERNAME", "PASSWORD"]]}
        ).execute()

# --- ENDPOINTS DE AUTENTICACIÓN ---
@app.post("/api/register")
async def register(data: dict):
    username = data.get("username").strip().lower()
    password = data.get("password")
    if not username or not password: raise HTTPException(status_code=400, detail="Datos incompletos")
    
    service = get_service()
    init_user_db(service)
    
    #Verificar duplicados
    res = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="Users_DB!A:A").execute()
    users = [row[0] for row in res.get('values', [])]
    if username in users: raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    #Guardar Usuario
    hashed_pw = pwd_context.hash(password)
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID, range="Users_DB!A:B",
        valueInputOption="RAW", body={'values': [[username, hashed_pw]]}).execute()
    
    #Crear su hoja personal
    sheet_name = f"Colección_{username}"
    body = {'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}
    service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    headers = [["ID", "NOMBRE", "TIPO", "ALTURA", "PESO", "HP", "ATK", "DEF", "SPD", "SKILLS", "MOVES", "USER"]]
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A1:L1",
        valueInputOption="RAW", body={'values': headers}).execute()
    
    return {"status": "success", "user": username}

@app.post("/api/login")
async def login(data: dict):
    username = data.get("username").strip().lower()
    password = data.get("password")
    
    service = get_service()
    res = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="Users_DB!A:B").execute()
    rows = res.get('values', [])
    
    for row in rows[1:]:
        if row[0] == username:
            if pwd_context.verify(password, row[1]):
                return {"status": "success", "user": username}
            break
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

#--- ENDPOINTS DE FUNCIONALIDAD ---

@app.post("/api/ai-identify")
async def ai_identify(file: UploadFile = File(...)):
    try:
        content = await file.read()
        img = Image.open(io.BytesIO(content))
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=["Identify this pokemon. Return ONLY the name in one word, lowercase.", img])
        clean_name = "".join(e for e in response.text.strip().lower() if e.isalnum())
        return {"name": clean_name}
    except Exception: raise HTTPException(status_code=500)

@app.get("/api/pokemon/{name}")
async def get_pokemon(name: str):
    res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name.lower().strip()}")
    if res.status_code != 200: raise HTTPException(status_code=404)
    return res.json()

@app.post("/api/favorites")
async def save_favorite(payload: dict):
    try:
        service = get_service()
        data = payload['full_data']
        username = payload['user'].strip().lower()
        sheet_name = f"Colección_{username}"
        
        s = {st['stat']['name']: st['base_stat'] for st in data.get('stats', [])}
        moves = ", ".join([m['move']['name'] for m in data.get('moves', [])[:4]])
        
        row = [
            str(data.get('id')), str(data.get('name')).upper(), 
            ", ".join([t['type']['name'] for t in data.get('types', [])]),
            data.get('height', 0)/10, data.get('weight', 0)/10,
            s.get('hp', 0), s.get('attack', 0), s.get('defense', 0), s.get('speed', 0),
            ", ".join([a['ability']['name'] for a in data.get('abilities', [])]),
            moves, username]
        
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:L",
            valueInputOption="RAW", body={'values': [row]}).execute()
        return {"status": "success"}
    except Exception: raise HTTPException(status_code=500)

@app.get("/api/collection")
async def get_collection(user: str):
    try:
        service = get_service()
        sheet_name = f"Colección_{user.lower()}"
        res = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A:L").execute()
        rows = res.get('values', [])
        if not rows: return []
        
        return [{
            "id": r[0], "name": r[1], "types": r[2], "h": r[3], "w": r[4],
            "hp": r[5], "at": r[6], "df": r[7], "sp": r[8], "skills": r[9],
            "moves": r[10], "user": r[11]
        } for r in rows[1:] if len(r) > 1]
    except Exception: return []

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)