import os
import shutil
import random

# === НАСТРОЙКИ ===
BASE_DIR = r"/home/user/Рабочий стол/pechenka/itog"  # путь к проекту

# Исходные папки (лежат внутри itog)
ITOG_DIR = os.path.join(BASE_DIR, "itog")
SRC_IMAGES = os.path.join(ITOG_DIR, "images")
SRC_LABELS = os.path.join(ITOG_DIR, "labels")

# Итоговая папка dataset
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
DST_IMAGES_TRAIN = os.path.join(DATASET_DIR, "images", "train")
DST_IMAGES_VAL = os.path.join(DATASET_DIR, "images", "val")
DST_LABELS_TRAIN = os.path.join(DATASET_DIR, "labels", "train")
DST_LABELS_VAL = os.path.join(DATASET_DIR, "labels", "val")

TRAIN_RATIO = 0.8  # 80% train, 20% val

# === СОЗДАНИЕ ПАПКОК ===
for folder in [DST_IMAGES_TRAIN, DST_IMAGES_VAL, DST_LABELS_TRAIN, DST_LABELS_VAL]:
    os.makedirs(folder, exist_ok=True)
    print(f"✓ Создана папка: {folder}")

# === СБОР СПИСКА ФАЙЛОВ ===
image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
all_images = [
    f for f in os.listdir(SRC_IMAGES)
    if os.path.isfile(os.path.join(SRC_IMAGES, f))
    and os.path.splitext(f.lower())[1] in image_extensions
]

print(f"\n📁 Найдено изображений в itog/images/: {len(all_images)}")

# Перемешиваем
random.seed(42)
random.shuffle(all_images)

# Разделяем 80/20
split_idx = int(len(all_images) * TRAIN_RATIO)
train_images = all_images[:split_idx]
val_images = all_images[split_idx:]

print(f"📊 Train: {len(train_images)} файлов ({TRAIN_RATIO*100:.0f}%)")
print(f"📊 Val:   {len(val_images)} файлов ({(1-TRAIN_RATIO)*100:.0f}%)")

# === ФУНКЦИЯ КОПИРОВАНИЯ ===
def copy_files(file_list, img_dest, lbl_dest):
    moved = 0
    skipped = 0
    for img_name in file_list:
        img_src = os.path.join(SRC_IMAGES, img_name)
        label_name = os.path.splitext(img_name)[0] + ".txt"
        lbl_src = os.path.join(SRC_LABELS, label_name)

        # Копируем картинку
        img_dst = os.path.join(img_dest, img_name)
        shutil.copy2(img_src, img_dst)

        # Копируем label (если существует)
        if os.path.exists(lbl_src):
            lbl_dst = os.path.join(lbl_dest, label_name)
            shutil.copy2(lbl_src, lbl_dst)
            moved += 1
        else:
            print(f"  ⚠️  Label не найден для {img_name}")
            skipped += 1

    return moved, skipped

# === КОПИРОВАНИЕ ===
print("\n🔄 Копирование файлов в dataset/...")

train_moved, train_skip = copy_files(train_images, DST_IMAGES_TRAIN, DST_LABELS_TRAIN)
val_moved, val_skip = copy_files(val_images, DST_IMAGES_VAL, DST_LABELS_VAL)

# === ИТОГ ===
print("\n✅ ГОТОВО!")
print(f"   Train: скопировано {train_moved} пар, пропущено {train_skip}")
print(f"   Val:   скопировано {val_moved} пар, пропущено {val_skip}")

# Проверка структуры
print("\n📂 Итоговая структура dataset/:")
for folder in [DST_IMAGES_TRAIN, DST_IMAGES_VAL, DST_LABELS_TRAIN, DST_LABELS_VAL]:
    count = len(os.listdir(folder))
    rel = os.path.relpath(folder, DATASET_DIR)
    print(f"   {rel}/ → {count} файлов")
