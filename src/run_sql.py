"""Прогон SQL-запросов из твоих .md-файлов — для тебя и для проверяющего.

НЕ МЕНЯЙ этот файл.

Запуск из корня репозитория:

    python3 src/run_sql.py src/ex03.md
        # все блоки ```sql из файла, по порядку, с результатами

    python3 src/run_sql.py src/ex04.md src/ex05.md
        # несколько файлов: все, кроме последнего, выполняются молча (создают VIEW),
        # результаты печатаются только для последнего

    python3 src/run_sql.py src/ex04.md src/ex05.md "Сценарии"
        # показать только блоки последнего файла под заголовком, где есть этот текст

    python3 src/run_sql.py src/ex04.md -e "SELECT blok, COUNT(*) FROM razmetka GROUP BY blok"
        # выполнить файлы молча, потом один свой запрос

Как это работает:
  - база собирается скриптом src/db.py (данные как есть, без чистки);
  - блоки ```sql выполняются сверху вниз в ОДНОЙ базе: представление (VIEW) или таблица,
    созданные в раннем блоке или файле, доступны во всех следующих;
  - если в src/ex02.py есть функция unicode_lower и класс Median,
    они регистрируются в базе как unicode_lower() и MEDIAN();
  - рядом с результатом печатается заголовок вопроса и твоя строка «**Ответ:**»,
    чтобы сразу было видно, совпадает ли число.
"""

import sqlite3
import sys

from db import connect

MAX_ROWS = 30


def register_own_functions(con):
    """Подключает unicode_lower и MEDIAN из ex02.py, если они там уже написаны."""
    try:
        import ex02
    except Exception as e:  # файл с ошибкой не должен ломать прогон
        print(f"[!] ex02.py не импортируется ({e}); unicode_lower и MEDIAN недоступны\n")
        return
    if hasattr(ex02, "unicode_lower"):
        con.create_function("unicode_lower", 1, ex02.unicode_lower)
    else:
        print("[!] в ex02.py нет функции unicode_lower\n")
    if hasattr(ex02, "Median"):
        con.create_aggregate("MEDIAN", 1, ex02.Median)
    else:
        print("[!] в ex02.py нет класса Median\n")


def is_blank(sql):
    """True, если в тексте нет ничего, кроме пустых строк и комментариев --."""
    return all(not ln.strip() or ln.strip().startswith("--") for ln in sql.splitlines())


def split_statements(sql):
    """Делит текст блока на отдельные запросы по ';' (точка с запятой внутри кавычек не режет)."""
    statements, buf = [], ""
    for ch in sql:
        buf += ch
        if ch == ";" and sqlite3.complete_statement(buf):
            if not is_blank(buf):
                statements.append(buf.strip())
            buf = ""
    if not is_blank(buf):
        statements.append(buf.strip())
    return statements


def run_statement(con, stmt):
    try:
        cur = con.execute(stmt)
    except sqlite3.Error as e:
        print(f"    ОШИБКА: {e}")
        return
    if cur.description is None:
        print("    ok")
        return
    rows = cur.fetchall()
    for row in rows[:MAX_ROWS]:
        print("   ", row)
    if len(rows) > MAX_ROWS:
        print(f"    … ещё {len(rows) - MAX_ROWS} строк")
    if not rows:
        print("    (пусто)")


def blocks_from_markdown(path):
    """Возвращает список (заголовок, строка ответа, текст sql) по порядку."""
    heading, answer = "", ""
    in_sql, buf, result = False, [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if in_sql:
                if stripped.startswith("```"):
                    result.append((heading, answer, "".join(buf)))
                    in_sql, buf = False, []
                else:
                    buf.append(line)
            elif stripped.lower().startswith("```sql"):
                in_sql = True
            elif stripped.startswith("#"):
                heading, answer = stripped.lstrip("#").strip(), ""
            elif stripped.startswith("**Ответ:**"):
                answer = stripped
    if in_sql:
        print(f"[!] {heading}: блок ```sql не закрыт — выполняю его до конца файла\n")
        result.append((heading, answer, "".join(buf)))
    return result


def run_quietly(con, path):
    """Выполняет блоки файла без вывода результатов — только ошибки."""
    for heading, _, sql in blocks_from_markdown(path):
        for stmt in split_statements(sql):
            try:
                con.execute(stmt).fetchall()
            except sqlite3.Error as e:
                print(f"[!] {heading}: {e}")


def run_verbose(con, blocks, only):
    """Выполняет блоки и печатает результаты (только под подходящими заголовками, если задан фильтр)."""
    last_heading = None
    for heading, answer, sql in blocks:
        if is_blank(sql):
            if only and only in heading.lower():
                print(f"{heading}: блок ```sql пустой")
            continue
        if only and only not in heading.lower():
            # блок не показываем, но выполняем: он может создавать VIEW для следующих
            for stmt in split_statements(sql):
                try:
                    con.execute(stmt).fetchall()
                except sqlite3.Error as e:
                    print(f"[!] {heading}: {e}")
            continue
        if heading != last_heading:
            print("=" * 70)
            print(heading)
            if answer:
                print(answer)
            last_heading = heading
        for stmt in split_statements(sql):
            print("-" * 70)
            print("   ", stmt.replace("\n", "\n    "))
            print("  →")
            run_statement(con, stmt)


def main(argv):
    args = argv[1:]
    query = None
    if "-e" in args:
        i = args.index("-e")
        if i + 1 >= len(args):
            print(__doc__)
            return 1
        query = args[i + 1]
        args = args[:i] + args[i + 2:]
    files = [a for a in args if a.lower().endswith(".md")]
    rest = [a for a in args if not a.lower().endswith(".md")]
    if len(rest) > 1 or (query is None and not files):
        print(__doc__)
        return 1
    only = rest[0].lower() if rest else None

    con = connect()
    register_own_functions(con)

    if query is not None:
        for path in files:
            run_quietly(con, path)
        for stmt in split_statements(query):
            run_statement(con, stmt)
        return 0

    for path in files[:-1]:
        run_quietly(con, path)
    blocks = blocks_from_markdown(files[-1])
    if not blocks:
        print("В файле нет блоков ```sql")
        return 1
    if all(is_blank(sql) for _, _, sql in blocks):
        print("Все блоки ```sql пока пустые — впиши запросы.")
        return 0
    if only and not any(only in h.lower() for h, _, _ in blocks):
        print(f"Нет заголовка, в котором есть «{rest[0]}»")
        return 1
    run_verbose(con, blocks, only)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
