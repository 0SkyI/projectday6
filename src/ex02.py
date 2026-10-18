"""Задание 2. Сколько людей и сколько времени.

Запуск из корня репозитория:  python3 src/ex02.py

Функция unicode_lower и класс Median должны остаться на верхнем уровне файла:
src/run_sql.py подключает их к базе, и в заданиях 3–7 ты сможешь писать
в запросах unicode_lower(...) и MEDIAN(...).
"""

import statistics

from db import connect


def unicode_lower(text):
    """Нижний регистр для любого текста, включая кириллицу.

    SQLite передаёт сюда значение поля. Если в поле NULL, придёт None —
    функция не должна на нём падать.
    """
    if text is None:
        return None
    return text.lower()


class Median:
    """Своя агрегатная функция MEDIAN для SQLite.

    SQLite создаёт объект этого класса на каждую группу,
    вызывает step() для каждой строки группы, а в конце — finalize().
    Пример попроще с тем же устройством — в materials/sql_start_rus.md.
    """

    def __init__(self):
        self.values = []

    def step(self, value):
        if value is not None:
            self.values.append(value)

    def finalize(self):
        if not self.values:
            return None
        return statistics.median(self.values)


def main():
    con = connect()
    cur = con.cursor()
    con.create_function("unicode_lower", 1, unicode_lower)
    con.create_aggregate("MEDIAN", 1, Median)

    print("1. Строк в справочнике и людей")
    # Разница в одну строку: кто-то записан в справочник дважды.
    print(cur.execute(
        "SELECT COUNT(*), COUNT(DISTINCT login) FROM agents"
    ).fetchone())

    print("1a. Какая строка лишняя")
    # Группа из одинаковых строк — это дубль; HAVING оставляет только те, где строк больше одной.
    for row in cur.execute("""
        SELECT id, login, team, hired_at, COUNT(*)
        FROM agents
        GROUP BY id, login, team, hired_at
        HAVING COUNT(*) > 1
    """):
        print(row)

    print("2. Смены, где меньше 6 человек")
    # DISTINCT внутри COUNT: считаем людей, а не строки — иначе дневная смена с дублем скрылась бы.
    for row in cur.execute("""
        SELECT team, COUNT(DISTINCT login)
        FROM agents
        GROUP BY team
        HAVING COUNT(DISTINCT login) < 6
    """):
        print(row)

    print("3. Каналы в сырой выгрузке: lower()")
    # Встроенная lower() в стандартной сборке SQLite трогает только латиницу:
    # 'Чат' для неё остаётся 'Чат' и уходит отдельной группой от 'чат'.
    for row in cur.execute("""
        SELECT lower(channel), COUNT(*)
        FROM tickets
        GROUP BY lower(channel)
        ORDER BY 1
    """):
        print(row)

    print("3a. Каналы в сырой выгрузке: unicode_lower()")
    # Та же группировка через свою функцию: Python-ный .lower() знает кириллицу,
    # и оба варианта «чат» сливаются в одну группу.
    for row in cur.execute("""
        SELECT unicode_lower(channel), COUNT(*)
        FROM tickets
        GROUP BY unicode_lower(channel)
        ORDER BY 1
    """):
        print(row)

    print("4. Время обработки до апреля: среднее и медиана")
    # Среднее (29.7) почти вдвое выше медианы (16): единицы очень долгих обращений
    # тянут его вверх. Руководителю назову медиану — типичное обращение живут 16 минут.
    print(cur.execute("""
        SELECT ROUND(AVG(handle_min), 1), MEDIAN(handle_min)
        FROM clean
        WHERE period = 'до'
    """).fetchone())

    print("5. Медиана: SQL и Python")
    # Сверяю свой инструмент: то же самое считает statistics.median по тем же значениям.
    values = [row[0] for row in cur.execute(
        "SELECT handle_min FROM clean WHERE period = 'до' AND handle_min IS NOT NULL"
    )]
    sql_median = cur.execute(
        "SELECT MEDIAN(handle_min) FROM clean WHERE period = 'до'"
    ).fetchone()[0]
    print(sql_median, statistics.median(values))


if __name__ == "__main__":
    main()
