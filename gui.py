import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
import random
import datetime

def show_window(value_generator, interval=1000):
    matplotlib.use('Qt5Agg')

    times = []
    values = []

    # Создаём фигуру
    fig, ax = plt.subplots()
    ax.set_ylim(0, 20)
    ax.set_xlabel("Время")
    ax.set_ylabel("Значение")
    line, = ax.plot([], [], marker='o', color='blue')

    # Функция обновления
    def update(frame):
        now = datetime.datetime.now().strftime("%H:%M")
        # value = random.uniform(0, 20)
        value = value_generator()
        times.append(now)
        values.append(value)

        # ограничиваем количество точек на экране
        # if len(times) > 20:
        #     times.pop(0)
        #     values.pop(0)

        ax.clear()
        ax.set_ylim(0, 20)
        ax.set_xlabel("Время")
        ax.set_ylabel("Скорость")
        ax.plot(times, values, marker='o', color='blue')
        ax.tick_params(axis='x', rotation=45)

        return line,

    ani = animation.FuncAnimation(fig, update, interval=interval)
    plt.tight_layout()
    plt.show()
    return ani, plt
