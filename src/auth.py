"""
StudyPulse — Auth Module
Gerencia hash de senha e sessão persistente local.
"""
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from src import db
SESSION_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), ".session"
)
SESSION_DURATION_DAYS = 30

SECURITY_QUESTIONS = [
    "Qual o nome do seu primeiro animal de estimação?",
    "Qual o nome da sua escola primária?",
    "Qual é o nome de solteira da sua mãe?",
    "Qual foi o seu primeiro emprego?",
    "Qual é o nome da sua cidade natal?",
    "Qual o modelo do seu primeiro carro?",
    "Qual é o seu filme favorito?",
    "Qual é o apelido da sua infância?",
]

# ─── Password ─────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Gera hash seguro da senha com PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=260_000,
    )
    return f"{salt}${key.hex()}"
def verify_password(password: str, stored_hash: str) -> bool:
    """Verifica se a senha bate com o hash armazenado."""
    try:
        salt, key_hex = stored_hash.split("$")
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=260_000,
        )
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False
# ─── Session ──────────────────────────────────────────────────────
def save_session(token: str, user_id: int, display_name: str, username: str = ""):
    """Salva a sessão local em .session."""
    data = {
        "token": token,
        "user_id": user_id,
        "display_name": display_name,
        "username": username,
    }
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
def load_session() -> dict | None:
    """
    Lê o .session, define o banco do usuário e valida o token.
    Retorna os dados do usuário ou None se inválido/expirado.
    """
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        token = data.get("token")
        username = data.get("username", "")
        if not token:
            return None
        if username:
            db.set_user_db(username)
            db.init_db()
        session = db.get_session_by_token(token)
        return session
    except Exception:
        return None
def clear_session():
    """Remove a sessão local (logout)."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
def login(username: str, password: str) -> dict | None:
    """
    Tenta autenticar o usuário.
    Retorna dict com {token, user_id, display_name} ou None se falhar.
    """
    db.set_user_db(username)
    db.init_db()
    user = db.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now() + timedelta(days=SESSION_DURATION_DAYS)
    ).strftime("%Y-%m-%d %H:%M:%S")
    db.create_session(user["id"], token, expires_at)
    save_session(token, user["id"], user["display_name"], username)
    return {
        "token": token,
        "user_id": user["id"],
        "display_name": user["display_name"],
    }
def register(username: str, password: str, display_name: str,
             security_question: str = "", security_answer: str = "") -> dict | None:
    """
    Cria uma nova conta e já loga o usuário.
    Retorna dict com {token, user_id, display_name} ou None se username já existe.
    """
    db.set_user_db(username)
    db.init_db()
    password_hash = hash_password(password)
    answer_hash = hash_answer(security_answer) if security_answer else ""
    user_id = db.create_user(username, password_hash, display_name,
                             security_question, answer_hash)
    if user_id is None:
        return None  # Username já existe
    token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.now() + timedelta(days=SESSION_DURATION_DAYS)
    ).strftime("%Y-%m-%d %H:%M:%S")
    db.create_session(user_id, token, expires_at)
    save_session(token, user_id, display_name, username)
    return {
        "token": token,
        "user_id": user_id,
        "display_name": display_name,
    }

# ─── Recuperação de Senha ──────────────────────────────────────────
def hash_answer(answer: str) -> str:
    """Gera hash da resposta secreta (case-insensitive: normaliza para minúsculas)."""
    return hash_password(answer.strip().lower())
def verify_security_answer(username: str, answer: str) -> bool:
    """Verifica se a resposta secreta bate com o hash armazenado."""
    user = db.get_user_by_username(username)
    if not user or not user.get("security_answer_hash"):
        return False
    return verify_password(answer.strip().lower(), user["security_answer_hash"])
def reset_password(username: str, answer: str, new_password: str) -> bool:
    """
    Redefine a senha do usuário após validar a resposta secreta.
    Retorna True se bem-sucedido, False caso contrário.
    """
    user = db.get_user_by_username(username)
    if not user:
        return False
    if not verify_security_answer(username, answer):
        return False
    new_hash = hash_password(new_password)
    db.update_user_password(user["id"], new_hash)
    return True

def set_security_question(user_id: int, current_password: str,
                          question: str, answer: str) -> bool:
    """
    Define ou atualiza a pergunta secreta do usuário.
    Exige a senha atual para confirmar identidade.
    Retorna True se bem-sucedido, False se a senha atual estiver errada.
    """
    user_row = db.get_connection().execute(
        "SELECT password_hash FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not user_row:
        return False
    if not verify_password(current_password, user_row["password_hash"]):
        return False
    answer_hash = hash_answer(answer)
    db.update_user_security_question(user_id, question, answer_hash)
    return True