import mss
import time
from datetime import datetime
import os

# Папка для сохранения скриншотов
save_dir = "screenshots"
os.makedirs(save_dir, exist_ok=True)

print("Начинаю делать скриншоты каждые 5 секунд…")
print("Нажмите Ctrl+C для остановки\n")

count = 0

with mss.mss() as sct:
    try:
        while True:
            # Делаем скриншот всего экрана
            screenshot = sct.shot(output=f"{save_dir}/screenshot_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.png")
            count += 1
            print(f"[{count}] Сохранено: {screenshot}")

            # Ждём 5 секунд
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\nОстановлено. Всего сделано скриншотов: {count}")

