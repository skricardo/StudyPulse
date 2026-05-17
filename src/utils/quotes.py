"""
StudyPulse — Motivational Quotes
Fetches quotes from API with local fallback.
"""

import random
import threading

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ─── Local fallback quotes ────────────────────────────────────────
FALLBACK_QUOTES = [
    {"text": "O segredo de progredir é começar.", "author": "Mark Twain"},
    {"text": "A educação é a arma mais poderosa que você pode usar para mudar o mundo.", "author": "Nelson Mandela"},
    {"text": "Nunca é tarde demais para ser aquilo que sempre desejou ser.", "author": "George Eliot"},
    {"text": "O sucesso é a soma de pequenos esforços repetidos dia após dia.", "author": "Robert Collier"},
    {"text": "A persistência é o caminho do êxito.", "author": "Charles Chaplin"},
    {"text": "Estudar é polir a pedra bruta do talento.", "author": "Provérbio"},
    {"text": "A mente que se abre a uma nova ideia jamais voltará ao seu tamanho original.", "author": "Albert Einstein"},
    {"text": "O conhecimento é o único tesouro que quanto mais se gasta, mais se tem.", "author": "Provérbio Árabe"},
    {"text": "Você não precisa ser grande para começar, mas precisa começar para ser grande.", "author": "Zig Ziglar"},
    {"text": "Cada dia é uma chance de aprender algo novo.", "author": "Desconhecido"},
    {"text": "Disciplina é a ponte entre metas e realizações.", "author": "Jim Rohn"},
    {"text": "A única maneira de fazer um excelente trabalho é amar o que você faz.", "author": "Steve Jobs"},
    {"text": "O futuro pertence àqueles que acreditam na beleza de seus sonhos.", "author": "Eleanor Roosevelt"},
    {"text": "Não espere por uma crise para descobrir o que é importante na sua vida.", "author": "Platão"},
    {"text": "Quanto mais eu estudo, mais eu descubro que não sei.", "author": "Sócrates"},
]

_cached_quote = {"text": "", "author": ""}


def get_random_quote(callback=None):
    """Get a motivational quote. If callback is provided, fetches async."""
    if callback:
        thread = threading.Thread(target=_fetch_async, args=(callback,), daemon=True)
        thread.start()
        return _get_fallback()
    return _get_fallback()


def _fetch_async(callback):
    """Fetch quote from API in background thread."""
    if not HAS_REQUESTS:
        callback(_get_fallback())
        return

    try:
        resp = requests.get(
            "https://api.quotable.io/random",
            params={"tags": "education|motivational|wisdom"},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            quote = {"text": data.get("content", ""), "author": data.get("author", "")}
            if quote["text"]:
                callback(quote)
                return
    except Exception:
        pass

    # Fallback on any error
    callback(_get_fallback())


def _get_fallback() -> dict:
    """Return a random local quote."""
    return random.choice(FALLBACK_QUOTES)
