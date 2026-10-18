"""Задание 6. График для аналитической записки.

Запуск из корня репозитория:  python3 src/ex06_chart.py
Результат: картинка src/ex06_chart.png, которую ты вставишь в записку.

Рисовать ничего не нужно — только решить, ЧТО показать:
  1. впиши запросы в SERIES — каждый возвращает строки (подпись, число);
     если запросов два, у них должны быть одинаковые подписи — будут столбики парами;
  2. придумай заголовок, который говорит вывод, а не тему;
  3. подпиши ось.
Если matplotlib не установлен:  pip3 install --user matplotlib
"""

import matplotlib.pyplot as plt

from db import connect
from run_sql import register_own_functions

TITLE = "TODO: заголовок — вывод одной фразой"
YLABEL = "TODO: что по оси и в каких единицах"

SERIES = [
    # ("название ряда для легенды", """SQL-запрос: SELECT подпись, число FROM ... GROUP BY ..."""),
    ("TODO", """
        SELECT blok, COUNT(*) FROM razmetka GROUP BY blok
    """),
]

con = connect()
register_own_functions(con)

labels = None
top = 0
fig, ax = plt.subplots(figsize=(8, 4.5))
width = 0.8 / len(SERIES)
for k, (name, query) in enumerate(SERIES):
    rows = con.execute(query).fetchall()
    if labels is None:
        labels = [str(r[0]) for r in rows]
    values = {str(r[0]): r[1] for r in rows}
    xs = [i - 0.4 + width * (k + 0.5) for i in range(len(labels))]
    ys = [values.get(label) or 0 for label in labels]
    ax.bar(xs, ys, width=width, label=name)
    top = max([top] + ys)
    for x, y in zip(xs, ys):
        ax.text(x, y, f"{y:g}", ha="center", va="bottom", fontsize=9)
ax.set_xticks(range(len(labels)), labels)
ax.set_title(TITLE)
ax.set_ylabel(YLABEL)
ax.set_ylim(0, top * 1.25 if top else 1)
if len(SERIES) > 1:
    ax.legend(loc="upper right", ncol=len(SERIES))
fig.tight_layout()
fig.savefig("src/ex06_chart.png", dpi=150)
print("Сохранено: src/ex06_chart.png")
