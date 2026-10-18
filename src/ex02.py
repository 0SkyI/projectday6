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
    # TODO
    pass


class Median:
    """Своя агрегатная функция MEDIAN для SQLite.

    SQLite создаёт объект этого класса на каждую группу,
    вызывает step() для каждой строки группы, а в конце — finalize().
    Пример попроще с тем же устройством — в materials/sql_start_rus.md.
    """

    def __init__(self):
        self.values = []

    def step(self, value):
        # TODO: сохрани значение (пропуски None не учитывай)
        pass

    def finalize(self):
        # TODO: верни медиану собранных значений (или None, если их нет)
        pass


def main():
    con = connect()
    con.create_function("unicode_lower", 1, unicode_lower)
    con.create_aggregate("MEDIAN", 1, Median)

    print("1. Строк в справочнике и людей")
    # TODO: COUNT(*) и COUNT(DISTINCT login) в одном запросе, таблица agents

    print("1a. Какая строка лишняя")
    # TODO: GROUP BY по всем полям справочника + HAVING

    print("2. Смены, где меньше 6 человек")
    # TODO: GROUP BY + HAVING; считай людей, а не строки

    print("3. Каналы в сырой выгрузке: lower()")
    # TODO: таблица tickets, GROUP BY lower(channel), ORDER BY 1

    print("3a. Каналы в сырой выгрузке: unicode_lower()")
    # TODO: то же со своей функцией

    print("4. Время обработки до апреля: среднее и медиана")
    # TODO: таблица clean, WHERE period = 'до'; ROUND(AVG(handle_min), 1) и MEDIAN(handle_min) в одном запросе
    # Почему они так расходятся и какое число ты назовёшь руководителю:
    # ...

    print("5. Медиана: SQL и Python")
    # TODO: та же медиана своей MEDIAN и через statistics.median по значениям из запроса — в одной строке


if __name__ == "__main__":
    main()
