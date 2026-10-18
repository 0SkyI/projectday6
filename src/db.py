"""Готовая база для заданий: сырые таблицы, очищенная таблица clean и разметка.

НЕ МЕНЯЙ этот файл: проверяющий запускает твои запросы на этой же базе,
и числа совпадут, только если база собрана одинаково.

Что появляется в базе после connect():

  agents     — справочник сотрудников, как в data/agents.csv, все поля текстом;
  tickets    — выгрузка обращений, как в data/tickets.csv, все поля текстом,
               пустая ячейка = пустая строка ''. Грязь на месте: дубли, форматы дат и прочее;
  clean      — те же обращения после чистки, которую сделал коллега-аналитик
               (что именно он сделал — выясняешь в задании 3). Поля:
                 id, num             — номер обращения текстом и числом
                 created             — дата создания в одном формате ГГГГ-ММ-ДД чч:мм:сс
                 period              — 'до' или 'после' 1 апреля 2025
                 month               — месяц, ГГГГ-ММ
                 client_id           — клиент
                 channel             — канал: чат, почта, форма, телефон
                 written             — 1 для письменных каналов (чат, почта, форма), 0 для телефона
                 topic               — тема
                 priority            — приоритет числом 1/2/3
                 bot_result          — 'закрыл', 'передал' или 'нет' (бот не участвовал)
                 agent_id            — сотрудник или NULL
                 handle_min          — время обработки сотрудником, минуты, или NULL
                 first_reply_min     — минуты от создания до первого ответа
                 resolve_hours       — часы от создания до закрытия, NULL если не закрыто
                 status              — статус
                 reopened            — 1, если клиент переоткрывал обращение
                 csat                — оценка 1–5 или NULL
                 came_back           — 1, если тот же клиент обратился снова с той же темой
                                       в течение 7 дней (возврат); если тема неизвестна — 0
                 next_bot_result     — что бот сделал с этим возвратом: 'закрыл', 'передал', 'нет',
                                       NULL — если возврата не было;
  razmetka_rule — твоя таблица-решение из src/razmetka.csv (задание 4);
  razmetka   — clean плюс поле blok: 'первая', 'серая', 'вторая' или 'не размечено'.

Как использовать в своём скрипте (скрипт лежит в src/, запуск из корня репозитория):

    from db import connect
    con = connect()
    print(con.execute("SELECT COUNT(*) FROM clean").fetchone())
"""

import csv
import sqlite3
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
DATA_DIR = SRC_DIR.parent / "data"
RULE_FILE = SRC_DIR / "razmetka.csv"
BLOKS = ("первая", "серая", "вторая")

SCHEMA = {
    "agents": """
        CREATE TABLE agents (
            id        TEXT,  -- номер сотрудника в справочнике
            login     TEXT,
            team      TEXT,  -- смена первой линии
            hired_at  TEXT   -- дата найма
        )""",
    "tickets": """
        CREATE TABLE tickets (
            id              TEXT,  -- номер обращения
            created_at      TEXT,  -- когда обращение создано
            client_id       TEXT,  -- кто обратился
            channel         TEXT,  -- канал: чат, почта, форма, телефон
            topic           TEXT,  -- тема
            priority        TEXT,  -- приоритет 1/2/3
            bot_result      TEXT,  -- что сделал бот: закрыл / передал / пусто
            agent_id        TEXT,  -- сотрудник, который вёл обращение
            first_reply_at  TEXT,  -- первый ответ клиенту
            resolved_at     TEXT,  -- когда закрыли
            handle_min      TEXT,  -- минуты работы сотрудника над обращением
            status          TEXT,
            reopened        TEXT,  -- открывали ли обращение повторно
            csat            TEXT   -- оценка клиента после обращения
        )""",
}

CLEAN_SQL = """
CREATE TEMP TABLE base AS
SELECT
    id,
    CAST(substr(id, 2) AS INTEGER) AS num,
    CASE WHEN created_at LIKE '__.__.____ __:__'
         THEN substr(created_at, 7, 4) || '-' || substr(created_at, 4, 2) || '-' || substr(created_at, 1, 2)
              || ' ' || substr(created_at, 12, 5) || ':00'
         ELSE created_at END AS created,
    client_id,
    CASE WHEN channel = 'Чат' THEN 'чат' ELSE channel END AS channel,
    CASE WHEN topic = '' THEN 'без темы' ELSE topic END AS topic,
    CAST(priority AS INTEGER) AS priority,
    CASE WHEN bot_result = '' THEN 'нет' ELSE bot_result END AS bot_result,
    NULLIF(agent_id, '') AS agent_id,
    CAST(NULLIF(handle_min, '') AS INTEGER) AS handle_min,
    NULLIF(first_reply_at, '') AS first_reply_at,
    NULLIF(resolved_at, '') AS resolved_at,
    status,
    CAST(reopened AS INTEGER) AS reopened,
    CAST(NULLIF(csat, '') AS INTEGER) AS csat
FROM (SELECT DISTINCT * FROM tickets);

CREATE INDEX temp.base_client ON base(client_id, topic, created);

CREATE TABLE clean AS
SELECT
    a.id, a.num, a.created,
    CASE WHEN a.created >= '2025-04-01' THEN 'после' ELSE 'до' END AS period,
    substr(a.created, 1, 7) AS month,
    a.client_id, a.channel,
    CASE WHEN a.channel = 'телефон' THEN 0 ELSE 1 END AS written,
    a.topic, a.priority, a.bot_result, a.agent_id, a.handle_min,
    ROUND((julianday(a.first_reply_at) - julianday(a.created)) * 1440, 1) AS first_reply_min,
    ROUND((julianday(a.resolved_at) - julianday(a.created)) * 24, 1) AS resolve_hours,
    a.status, a.reopened, a.csat,
    EXISTS (SELECT 1 FROM base b
            WHERE b.client_id = a.client_id AND b.topic = a.topic
              AND a.topic NOT IN ('без темы', 'NULL')
              AND b.created > a.created
              AND julianday(b.created) - julianday(a.created) <= 7) AS came_back,
    (SELECT b.bot_result FROM base b
     WHERE b.client_id = a.client_id AND b.topic = a.topic
       AND a.topic NOT IN ('без темы', 'NULL')
       AND b.created > a.created
       AND julianday(b.created) - julianday(a.created) <= 7
     ORDER BY b.created LIMIT 1) AS next_bot_result
FROM base a
ORDER BY a.num;

DROP TABLE temp.base;
"""


def _load(con, table):
    con.execute(SCHEMA[table])
    with open(DATA_DIR / f"{table}.csv", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        marks = ", ".join("?" for _ in header)
        con.executemany(f"INSERT INTO {table} VALUES ({marks})", reader)


def _load_rule(con):
    """Загружает таблицу-решение src/razmetka.csv, если она есть."""
    con.execute("CREATE TABLE razmetka_rule (topic TEXT, priority INTEGER, blok TEXT)")
    if not RULE_FILE.exists():
        return
    rule = {}
    with open(RULE_FILE, encoding="utf-8", newline="") as f:
        for n, row in enumerate(csv.DictReader(f), start=2):
            topic = (row.get("topic") or "").strip()
            blok = (row.get("blok") or "").strip().lower()
            try:
                priority = int((row.get("priority") or "").strip())
            except ValueError:
                print(f"[!] razmetka.csv, строка {n}: приоритет должен быть 1, 2 или 3")
                continue
            if blok and blok not in BLOKS:
                print(f"[!] razmetka.csv, строка {n}: blok «{blok}» — допустимо только первая, серая, вторая")
                continue
            if (topic, priority) in rule:
                print(f"[!] razmetka.csv, строка {n}: «{topic}», приоритет {priority} уже размечен выше — строка пропущена")
                continue
            rule[(topic, priority)] = blok
    con.executemany("INSERT INTO razmetka_rule VALUES (?, ?, ?)",
                    [(t, p, b) for (t, p), b in rule.items()])


def connect(path=":memory:"):
    """Возвращает соединение с базой, где уже лежат agents, tickets, clean и razmetka."""
    con = sqlite3.connect(path)
    for table in ("agents", "tickets", "clean", "razmetka_rule"):
        con.execute(f"DROP TABLE IF EXISTS {table}")
    con.execute("DROP VIEW IF EXISTS razmetka")
    for table in SCHEMA:
        _load(con, table)
    con.executescript(CLEAN_SQL)
    _load_rule(con)
    con.execute("""
        CREATE VIEW razmetka AS
        SELECT c.*, COALESCE(NULLIF(r.blok, ''), 'не размечено') AS blok
        FROM clean c
        LEFT JOIN razmetka_rule r ON r.topic = c.topic AND r.priority = c.priority
    """)
    con.commit()
    return con


if __name__ == "__main__":
    con = connect()
    for table in ("agents", "tickets", "clean", "razmetka"):
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {n} строк")
