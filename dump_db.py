import os
import subprocess
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB")

DUMP_FOLDER = os.path.join(os.path.dirname(__file__), "dumps")
os.makedirs(DUMP_FOLDER, exist_ok=True)

def dump_database():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dump_file = os.path.join(DUMP_FOLDER, f"{POSTGRES_DB}_{timestamp}.sql")

    # Встановлюємо змінну середовища для пароля
    env = os.environ.copy()
    env["PGPASSWORD"] = POSTGRES_PASSWORD

    command = [
        "pg_dump",
        "-h", POSTGRES_HOST,
        "-p", str(POSTGRES_PORT),
        "-U", POSTGRES_USER,
        "-F", "c",             # custom format (можна замінити на plain)
        "-f", dump_file,
        POSTGRES_DB
    ]

    try:
        subprocess.run(command, check=True, env=env)
        print(f"✅ Дамп створено: {dump_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Помилка при створенні дампу: {e}")