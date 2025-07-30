import os
import json
import re
import datetime
import time
import hashlib
import jwt
import sqlite3
import subprocess
from flask import Flask, jsonify, request
from flask_cors import CORS

SECRET_KEY = "SOME_SECRET_KEY"
DATABASE = "users.db"
COMPETENCE_FILE = "competence010302.json"
VERSIONS_FOLDER = "versions"
JSON_OUTPUT_FOLDER = "json_output"
DOC_OUTPUT_FOLDER = "docs"

app = Flask(__name__)
CORS(app)

os.makedirs(VERSIONS_FOLDER, exist_ok=True)
os.makedirs(JSON_OUTPUT_FOLDER, exist_ok=True)
os.makedirs(DOC_OUTPUT_FOLDER, exist_ok=True)

def hash_password(pw):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def init_db():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        role TEXT,
        subjects TEXT
    )
    ''')
    conn.commit()

    c.execute("INSERT INTO users (username, password, email, role, subjects) VALUES (?,?,?,?,?)",
              ("superadmin", hash_password("superadmin"), "super@admin.com", "superadmin", json.dumps([])))
    conn.commit()
    conn.close()

init_db()

def create_token(username, role):
    payload = {
        "username": username,
        "role": role,
        "exp": time.time() + 3600
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        return None

def get_user(username):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT username, password, email, role, subjects FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "password": row[1], "email": row[2], "role": row[3], "subjects": json.loads(row[4]) if row[4] else []}
    return None

def update_user(username, **kwargs):
    user = get_user(username)
    if not user:
        return False
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    fields = []
    values = []
    if "role" in kwargs:
        fields.append("role=?")
        values.append(kwargs["role"])
    if "subjects" in kwargs:
        fields.append("subjects=?")
        values.append(json.dumps(kwargs["subjects"]))
    if fields:
        values.append(username)
        c.execute("UPDATE users SET " + ", ".join(fields) + " WHERE username=?", values)
        conn.commit()
    conn.close()
    return True

def list_subjects():
    subjects = []
    for fname in os.listdir(JSON_OUTPUT_FOLDER):
        if fname.startswith("subject_") and fname.endswith(".json"):
            subjects.append(fname)
    return subjects

def load_subject_data(subject_file):
    path = os.path.join(JSON_OUTPUT_FOLDER, subject_file)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_subject_data(subject_file, data):
    path = os.path.join(JSON_OUTPUT_FOLDER, subject_file)
    if os.path.exists(path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        old_path = os.path.join(VERSIONS_FOLDER, f"{subject_file}_{timestamp}")
        os.rename(path, old_path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password or not email:
        return jsonify({"error": "Необходимо указать логин, пароль и email"}), 400

    if get_user(username):
        return jsonify({"error": "Пользователь уже существует"}), 400

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, email, role, subjects) VALUES (?,?,?,?,?)",
              (username, hash_password(password), email, "student", json.dumps([])))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Пользователь зарегистрирован."})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = get_user(username)
    if user and user["password"] == hash_password(password):
        token = create_token(user["username"], user["role"])
        return jsonify({"success": True, "token": token, "role": user["role"]})
    else:
        return jsonify({"error": "Неверный логин или пароль"}), 401

@app.route('/api/subjects', methods=['GET'])
def get_subjects_api():
    token = request.headers.get("Authorization")
    user_subjects = None
    if token:
        payload = verify_token(token)
        if payload:
            user = get_user(payload["username"])
            if user and user["role"] == "teacher":
                user_subjects = user["subjects"]

    subjects = list_subjects()
    if user_subjects is not None:
        subjects = [s for s in subjects if s in user_subjects]

    return jsonify(subjects)

@app.route('/api/course', methods=['GET'])
def get_course_api():
    token = request.headers.get("Authorization")
    payload = verify_token(token) if token else None
    user = get_user(payload["username"]) if payload else None

    subject_file = request.args.get("subject")
    if not subject_file:
        return jsonify({"error": "Укажите параметр subject"}), 400

    if user and user["role"] == "teacher":
        if subject_file not in user["subjects"]:
            return jsonify({"error": "У вас нет доступа к этому предмету"}), 403

    data = load_subject_data(subject_file)
    if data is None:
        return jsonify({"error": "Предмет не найден"}), 404
    return jsonify(data)

@app.route('/api/course', methods=['POST'])
def update_course_api():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Требуется авторизация"}), 401
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "Недействительный токен"}), 401
    user = get_user(payload["username"])
    if user["role"] not in ["teacher", "superadmin"]:
        return jsonify({"error": "Недостаточно прав"}), 403

    subject_file = request.args.get("subject")
    if not subject_file:
        return jsonify({"error": "Укажите параметр subject"}), 400

    if user["role"] == "teacher":
        if subject_file not in user["subjects"]:
            return jsonify({"error": "Нет доступа к этому предмету"}), 403

    data = request.json
    if not data:
        return jsonify({"error": "Нет данных"}), 400

    save_subject_data(subject_file, data)
    return jsonify({"success": True, "message": "Обновлено"})

@app.route('/api/edit_field', methods=['POST'])
def edit_field():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error":"Требуется авторизация"}),401
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"Недействительный токен"}),401
    user = get_user(payload["username"])

    if user["role"] not in ["teacher","superadmin"]:
        return jsonify({"error":"Недостаточно прав"}),403

    subject_file = request.args.get("subject")
    field = request.args.get("field")
    if not subject_file or not field:
        return jsonify({"error":"Укажите subject и field"}),400

    if user["role"] == "teacher" and subject_file not in user["subjects"]:
        return jsonify({"error":"Нет доступа"}),403

    data = load_subject_data(subject_file)
    if not data:
        return jsonify({"error":"Предмет не найден"}),404

    body = request.json
    if "value" not in body:
        return jsonify({"error":"Укажите value"}),400

    value = body["value"]
    data[field] = value

    save_subject_data(subject_file, data)
    return jsonify({"success": True, "message":"Поле обновлено"})

@app.route('/api/generate_tickets', methods=['POST'])
def generate_tickets():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error":"Требуется авторизация"}),401

    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"Недействительный токен"}),401

    # Раньше мы проверяли роль, теперь этого не делаем:
    # user = get_user(payload["username"])
    # if user["role"] not in ["teacher","superadmin"]:
    #     return jsonify({"error":"Недостаточно прав"}),403

    subject_file = request.args.get("subject")
    semester = request.args.get("semester", "3")
    count = request.args.get("count", "5")
    count = int(count)

    if not subject_file:
        return jsonify({"error":"Укажите subject"}),400

    # Не проверяем роль, просто генерируем билеты
    course_data = load_subject_data(subject_file)
    if not course_data:
        return jsonify({"error":"Предмет не найден"}),404

    exam_questions = course_data.get("ExamQuestions", [])
    import random
    for sem in exam_questions:
        if sem["Semester"] == int(semester):
            questions = sem["Questions"][:]
            if len(questions) < count:
                return jsonify({"error":"Недостаточно вопросов"}),400
            random.shuffle(questions)
            ticket = questions[:count]
            # Генерация документа не обязательна, можно просто вернуть билеты
            return jsonify({"success": True, "ticket": ticket})

    return jsonify({"error":"Вопросы для указанного семестра не найдены"}),400


@app.route('/api/generate_doc', methods=['GET'])
def generate_doc():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error":"Требуется авторизация"}),401
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"Недействительный токен"}),401

    user = get_user(payload["username"])
    doc_type = request.args.get("type")
    subject_file = request.args.get("subject")
    if not doc_type or not subject_file:
        return jsonify({"error":"Укажите type и subject"}),400

    if user["role"] not in ["teacher","superadmin"]:
        return jsonify({"error":"Недостаточно прав"}),403
    if user["role"] == "teacher" and subject_file not in user["subjects"]:
        return jsonify({"error":"Нет доступа"}),403

    course_data = load_subject_data(subject_file)
    if not course_data:
        return jsonify({"error":"Предмет не найден"}),404

    params = {}
    if 'count' in request.args:
        params['count'] = int(request.args.get('count'))

    doc_path = generate_document(subject_file, doc_type, params)
    return jsonify({"success":True,"doc_path":doc_path})

def generate_document(subject_file, doc_type, params):
    course_data = load_subject_data(subject_file)
    if not course_data:
        return None
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    tex_content = r"""
\documentclass[a4paper,12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[english,russian]{babel}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage[T2A]{fontenc}
\textwidth=17cm
\oddsidemargin=0pt
\topmargin=-2cm
\textheight=27cm

\begin{document}
"""
    tex_content += f"Дата: {date_str}\n\n"
    tex_content += f"Подпись: \\underline{{\\hspace{{3cm}}}}\n\n"

    if doc_type == "methodichka":
        tex_content += "\\section*{Методические рекомендации}\n"
        tex_content += course_data.get("MetodicalRecommendations","Нет рекомендаций")
    elif doc_type == "summary":
        tex_content += "\\section*{Сводный отчет о дисциплине}\n"
        tex_content += f"Факультет: {course_data.get('Faculty','')}\n\n"
        tex_content += f"Кафедра: {course_data.get('Chair','')}\n\n"
        tex_content += f"Название: {course_data.get('Name','')}\n\n"
    elif doc_type == "bilets":
        tex_content += "\\section*{Билеты}\n"
        ticket = params.get("ticket", [])
        i = 1
        for q in ticket:
            tex_content += f"{i}. {q}\n"
            i+=1
    else:
        tex_content += "Документ данного типа не реализован.\n"

    tex_content += "\n\\end{document}"

    doc_name = f"{doc_type}_{subject_file}_{int(time.time())}.tex"
    doc_path = os.path.join(DOC_OUTPUT_FOLDER, doc_name)
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(tex_content)

    return doc_path

@app.route('/api/users', methods=['GET'])
def list_users_api():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error":"Требуется авторизация"}),401
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"Недействительный токен"}),401
    if payload["role"] != "superadmin":
        return jsonify({"error":"Недостаточно прав"}),403

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT username, email, role, subjects FROM users")
    rows = c.fetchall()
    conn.close()
    users = []
    for r in rows:
        users.append({
            "username": r[0],
            "email": r[1],
            "role": r[2],
            "subjects": json.loads(r[3]) if r[3] else []
        })
    return jsonify(users)

@app.route('/api/update_user_role', methods=['POST'])
def update_user_role():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error":"Требуется авторизация"}),401
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"Недействительный токен"}),401
    if payload["role"] != "superadmin":
        return jsonify({"error":"Недостаточно прав"}),403

    data = request.json
    username = data.get("username")
    new_role = data.get("role")
    if not username or not new_role:
        return jsonify({"error":"Укажите username и role"}),400

    user = get_user(username)
    if not user:
        return jsonify({"error":"Пользователь не найден"}),404

    update_user(username, role=new_role)
    return jsonify({"success":True,"message":"Роль обновлена"})

@app.route('/api/assign_subjects', methods=['POST'])
def assign_subjects():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error":"Требуется авторизация"}),401
    payload = verify_token(token)
    if not payload:
        return jsonify({"error":"Недействительный токен"}),401
    if payload["role"] != "superadmin":
        return jsonify({"error":"Недостаточно прав"}),403

    data = request.json
    username = data.get("username")
    subjects = data.get("subjects", [])

    user = get_user(username)
    if not user:
        return jsonify({"error":"Пользователь не найден"}),404

    all_subj = set(list_subjects())
    for s in subjects:
        if s not in all_subj:
            return jsonify({"error":f"Предмет {s} не найден"}),400

    update_user(username, subjects=subjects)
    return jsonify({"success":True,"message":"Предметы назначены"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
