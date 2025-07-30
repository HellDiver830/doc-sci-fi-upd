import eel
import requests
import json

eel.init('design')

API_URL = "http://185.174.137.123:8000"
token = None
role = None

@eel.expose
def login(username, password):
    global token, role
    r = requests.post(f"{API_URL}/api/login", json={"username": username, "password": password})
    if r.status_code == 200:
        res = r.json()
        token = res["token"]
        role = res["role"]
        return {"success": True, "role": role}
    else:
        return {"success": False, "error": r.json().get("error")}

@eel.expose
def register(username, password, email):
    r = requests.post(f"{API_URL}/api/register", json={"username": username, "password": password, "email": email})
    return r.json()

@eel.expose
def list_subjects():
    headers = {}
    if token:
        headers["Authorization"] = token
    r = requests.get(f"{API_URL}/api/subjects", headers=headers)
    return r.json()

@eel.expose
def get_course(subject):
    headers = {}
    if token:
        headers["Authorization"] = token
    r = requests.get(f"{API_URL}/api/course?subject={subject}", headers=headers)
    return r.json()

@eel.expose
def update_course(subject, data):
    global token
    if not token:
        return {"error":"Требуется авторизация"}
    headers = {"Authorization": token, "Content-Type":"application/json"}
    r = requests.post(f"{API_URL}/api/course?subject={subject}", headers=headers, json=data)
    return r.json()

@eel.expose
def generate_tickets(subject, semester, count):
    global token
    if not token:
        return {"error":"Требуется авторизация"}
    headers = {"Authorization": token, "Content-Type":"application/json"}
    r = requests.post(f"{API_URL}/api/generate_tickets?subject={subject}&semester={semester}&count={count}", headers=headers, json={})
    return r.json()

@eel.expose
def get_users():
    global token
    if not token:
        return {"error":"Требуется авторизация"}
    headers = {"Authorization": token}
    r = requests.get(f"{API_URL}/api/users", headers=headers)
    return r.json()

@eel.expose
def update_user_role(username, new_role):
    global token
    if not token:
        return {"error":"Требуется авторизация"}
    headers = {"Authorization": token, "Content-Type":"application/json"}
    r = requests.post(f"{API_URL}/api/update_user_role", headers=headers, json={"username":username,"role":new_role})
    return r.json()

@eel.expose
def assign_subjects(username, subjects):
    global token
    if not token:
        return {"error":"Требуется авторизация"}
    headers = {"Authorization": token, "Content-Type":"application/json"}
    r = requests.post(f"{API_URL}/api/assign_subjects", headers=headers, json={"username":username,"subjects":subjects})
    return r.json()

@eel.expose
def edit_field(subject, field, value):
    global token
    if not token:
        return {"error":"Требуется авторизация"}
    headers = {"Authorization": token, "Content-Type":"application/json"}
    r = requests.post(f"{API_URL}/api/edit_field?subject={subject}&field={field}", headers=headers, json={"value":value})
    return r.json()

@eel.expose
def generate_doc(subject, doc_type, count=None):
    global token
    if not token:
        return {"error":"Требуется авторизация"}
    headers = {"Authorization": token}
    url = f"{API_URL}/api/generate_doc?subject={subject}&type={doc_type}"
    if count is not None:
        url += f"&count={count}"
    r = requests.get(url, headers=headers)
    return r.json()

eel.start('index.html', size=(1200,800))
