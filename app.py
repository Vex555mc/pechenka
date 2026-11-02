import mss
import cv2
import numpy as np
from ultralytics import YOLO
import time
import pyautogui
from pynput import keyboard
import threading

# ==================== НАСТРОЙКИ ====================
MODEL_PATH = 'runs/detect/cookie_detector/weights/best.pt'

GAME_CLASS = 'game'        # имя класса печеньки — точно как в разметке X-AnyLabeling
UPGRADE_CLASS = 'upgrade'  # имя класса улучшений — точно как в разметке

CONF_THRESHOLD = 0.7       # порог уверенности детекции

COOKIE_CLICKS = 20         # сколько кликов по печеньке за один проход
CLICK_INTERVAL = 0.01      # пауза между кликами по печеньке

UPGRADE_CHECK_EVERY = 3.0  # раз в сколько секунд пытаться покупать улучшения
UPGRADE_CLICK_PAUSE = 0.15 # пауза после клика по улучшению (игра должна успеть обработать)
# ===================================================

pyautogui.PAUSE = 0  # отключаем встроенные задержки pyautogui

# --- Загрузка модели и сопоставление имён классов с id ---
model = YOLO(MODEL_PATH)
print("Классы, известные модели:", model.names)

try:
    GAME_ID = next(cid for cid, name in model.names.items() if name == GAME_CLASS)
    UPGRADE_ID = next(cid for cid, name in model.names.items() if name == UPGRADE_CLASS)
except StopIteration:
    raise SystemExit(
        f"В модели нет классов '{GAME_CLASS}' и/или '{UPGRADE_CLASS}'.\n"
        f"Проверь имена классов в разметке / переобучи модель на 2 класса."
    )

sct = mss.mss()
monitor = sct.monitors[1]

# --- Пауза по пробелу ---
pause_event = threading.Event()
pause_event.set()          # при запуске бот активен
stop_event = threading.Event()
last_toggle = 0.0          # защита от автоповтора пробела при удержании

def on_press(key):
    global last_toggle
    if key == keyboard.Key.esc:
        stop_event.set()
        print("\n[СТОП] Выход по Esc.")
        return
    if key == keyboard.Key.space:
        if time.time() - last_toggle < 0.3:  # игнорируем автоповтор
            return
        last_toggle = time.time()
        if pause_event.is_set():
            pause_event.clear()
            print("\n[ПАУЗА] Бот приостановлен. Нажмите ПРОБЕЛ для продолжения.")
        else:
            pause_event.set()
            print("\n[ВОЗОБНОВЛЕНИЕ] Бот снова работает.")

listener = keyboard.Listener(on_press=on_press)
listener.daemon = True
listener.start()

def wait_if_paused():
    """Блокирует поток, пока включена пауза."""
    while not pause_event.is_set() and not stop_event.is_set():
        time.sleep(0.05)

def grab_screen():
    """Захват экрана -> BGR numpy array."""
    img = sct.grab(monitor)
    frame = np.array(img)
    return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

def detect(frame):
    """Одна инференция -> (список печенек, список улучшений)."""
    results = model(frame, verbose=False)
    cookies, upgrades = [], []

    for box in results[0].boxes:
        conf = float(box.conf[0])
        if conf < CONF_THRESHOLD:
            continue

        cls_id = int(box.cls[0])
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        area = float((x2 - x1) * (y2 - y1))

        if cls_id == GAME_ID:
            cookies.append({'conf': conf, 'center': (cx, cy), 'area': area})
        elif cls_id == UPGRADE_ID:
            upgrades.append({'conf': conf, 'center': (cx, cy), 'y': float(y1)})

    return cookies, upgrades

def buy_upgrades(upgrades):
    """
    Кликает по улучшениям СВЕРХУ ВНИЗ (в Cookie Clicker сверху — лучшие).
    Клик по недоступному улучшению безвреден — игра его просто проигнорирует.
    """
    for up in sorted(upgrades, key=lambda u: u['y']):
        wait_if_paused()
        if stop_event.is_set():
            return
        x, y = up['center']
        pyautogui.click(x, y)
        time.sleep(UPGRADE_CLICK_PAUSE)
        print(f"[АПГРЕЙД] Клик по улучшению ({x}, {y}), conf={up['conf']:.2f}")

def click_cookies(cookies):
    """Самую большую печеньку кликаем много раз, остальные (напр. золотые) — по разу."""
    for i, cookie in enumerate(sorted(cookies, key=lambda c: c['area'], reverse=True)):
        clicks = COOKIE_CLICKS if i == 0 else 1
        x, y = cookie['center']
        for _ in range(clicks):
            wait_if_paused()
            if stop_event.is_set():
                return
            pyautogui.click(x, y)
            time.sleep(CLICK_INTERVAL)
        print(f"[ПЕЧЕНЬКА] {clicks} кликов по ({x}, {y}), conf={cookie['conf']:.2f}")

if __name__ == "__main__":
    print("Бот запущен. ПРОБЕЛ — пауза/продолжение, Esc или Ctrl+C — выход.")
    last_upgrade_check = 0.0

    try:
        while not stop_event.is_set():
            wait_if_paused()
            if stop_event.is_set():
                break

            frame = grab_screen()
            cookies, upgrades = detect(frame)

            # 1) Улучшения покупаем не чаще, чем раз в UPGRADE_CHECK_EVERY секунд
            now = time.time()
            if upgrades and now - last_upgrade_check >= UPGRADE_CHECK_EVERY:
                buy_upgrades(upgrades)
                last_upgrade_check = time.time()

            # 2) Кликаем печеньку (её координаты остаются валидными — она не двигается)
            if cookies:
                click_cookies(cookies)
            else:
                time.sleep(0.2)  # ничего не нашли — ждём, чтобы не грузить CPU

    except pyautogui.FailSafeException:
        print("\nАварийная остановка: курсор был в левом верхнем углу экрана.")
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем (Ctrl+C).")
    finally:
        listener.stop()
        print("Работа завершена.")