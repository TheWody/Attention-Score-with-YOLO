"""
FER-2013 veri seti ile YOLO modelini fine-tune etmek için script.

Kullanım:
1. FER-2013 veri setini indirin: https://www.kaggle.com/datasets/msambare/fer2013
2. Bu scripti çalıştırın: python yolo_trainer.py --data_path /path/to/fer2013
"""

import os
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
import shutil
import argparse
from ultralytics import YOLO

# FER-2013 duygu etiketleri
EMOTION_LABELS = {
    0: 'angry',
    1: 'disgust',
    2: 'fear',
    3: 'happy',
    4: 'sad',
    5: 'surprise',
    6: 'neutral'
}

class FER2013ToYOLO:
    def __init__(self, fer_data_path: str, output_path: str):
        self.fer_data_path = Path(fer_data_path)
        self.output_path = Path(output_path)
        self.image_size = 48  # FER-2013 orijinal boyut

    def convert_dataset(self):
        """FER-2013 CSV'yi YOLO formatına dönüştürür."""
        print("Veri seti dönüştürülüyor...")

        # Klasör yapısı oluştur
        for split in ['train', 'val']:
            (self.output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
            (self.output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)

        # CSV dosyasını oku
        csv_path = self.fer_data_path / 'fer2013.csv'
        if not csv_path.exists():
            # Alternatif: klasör yapısından oku
            self._convert_from_folders()
            return

        df = pd.read_csv(csv_path)

        for idx, row in df.iterrows():
            pixels = np.array(row['pixels'].split(), dtype=np.uint8)
            image = pixels.reshape(48, 48)

            # Görüntüyü büyüt (YOLO için daha iyi)
            image = cv2.resize(image, (224, 224))

            emotion = row['emotion']
            usage = 'train' if row['Usage'] != 'PublicTest' else 'val'

            # Görüntüyü kaydet
            img_filename = f"{idx:05d}.jpg"
            img_path = self.output_path / 'images' / usage / img_filename
            cv2.imwrite(str(img_path), image)

            # YOLO etiketi oluştur (tüm yüz = bbox)
            # Format: class x_center y_center width height (normalized)
            label_filename = f"{idx:05d}.txt"
            label_path = self.output_path / 'labels' / usage / label_filename

            with open(label_path, 'w') as f:
                # Tüm görüntü yüz olduğu için: 0.5 0.5 1.0 1.0
                f.write(f"{emotion} 0.5 0.5 1.0 1.0\n")

            if idx % 1000 == 0:
                print(f"İşlenen: {idx}/{len(df)}")

        self._create_yaml_config()
        print("Dönüştürme tamamlandı!")

    def _convert_from_folders(self):
        """Klasör yapısından dönüştürür (train/angry, train/happy, vb.)"""
        print("Klasör yapısından dönüştürülüyor...")

        idx = 0
        for split in ['train', 'test']:
            target_split = 'train' if split == 'train' else 'val'
            split_path = self.fer_data_path / split

            if not split_path.exists():
                continue

            for emotion_name in os.listdir(split_path):
                emotion_path = split_path / emotion_name
                if not emotion_path.is_dir():
                    continue

                # Duygu indeksini bul
                emotion_idx = None
                for eid, ename in EMOTION_LABELS.items():
                    if ename == emotion_name.lower():
                        emotion_idx = eid
                        break

                if emotion_idx is None:
                    continue

                for img_file in emotion_path.glob('*.jpg'):
                    image = cv2.imread(str(img_file), cv2.IMREAD_GRAYSCALE)
                    if image is None:
                        continue

                    image = cv2.resize(image, (224, 224))

                    img_filename = f"{idx:05d}.jpg"
                    img_path = self.output_path / 'images' / target_split / img_filename
                    cv2.imwrite(str(img_path), image)

                    label_filename = f"{idx:05d}.txt"
                    label_path = self.output_path / 'labels' / target_split / label_filename

                    with open(label_path, 'w') as f:
                        f.write(f"{emotion_idx} 0.5 0.5 1.0 1.0\n")

                    idx += 1

                    if idx % 1000 == 0:
                        print(f"İşlenen: {idx}")

        self._create_yaml_config()
        print("Dönüştürme tamamlandı!")

    def _create_yaml_config(self):
        """YOLO eğitimi için YAML config dosyası oluşturur."""
        yaml_content = f"""
path: {self.output_path.absolute()}
train: images/train
val: images/val

names:
  0: angry
  1: disgust
  2: fear
  3: happy
  4: sad
  5: surprise
  6: neutral
"""
        yaml_path = self.output_path / 'fer2013.yaml'
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        print(f"YAML config kaydedildi: {yaml_path}")


def train_yolo_fer(data_yaml: str, epochs: int = 100, batch_size: int = 16):
    """YOLO modelini FER-2013 ile eğitir."""

    # Önceden eğitilmiş YOLO modelini yükle
    model = YOLO('yolov8n.pt')  # nano model, hızlı eğitim için

    # Modeli eğit
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=224,
        project='runs/fer_training',
        name='yolo_fer_finetuned',
        patience=20,
        save=True,
        plots=True
    )

    # En iyi modeli kaydet
    best_model_path = Path('runs/fer_training/yolo_fer_finetuned/weights/best.pt')
    target_path = Path('models/yolo_fer_finetuned.pt')
    target_path.parent.mkdir(exist_ok=True)

    if best_model_path.exists():
        shutil.copy(best_model_path, target_path)
        print(f"Model kaydedildi: {target_path}")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FER-2013 ile YOLO eğitimi')
    parser.add_argument('--data_path', type=str, required=True, help='FER-2013 veri seti yolu')
    parser.add_argument('--output_path', type=str, default='datasets/fer2013_yolo', help='Çıktı yolu')
    parser.add_argument('--epochs', type=int, default=100, help='Eğitim epoch sayısı')
    parser.add_argument('--batch_size', type=int, default=16, help='Batch boyutu')
    parser.add_argument('--convert_only', action='store_true', help='Sadece dönüştür, eğitme')

    args = parser.parse_args()

    # Veri setini dönüştür
    converter = FER2013ToYOLO(args.data_path, args.output_path)
    converter.convert_dataset()

    if not args.convert_only:
        # Modeli eğit
        yaml_path = Path(args.output_path) / 'fer2013.yaml'
        train_yolo_fer(str(yaml_path), args.epochs, args.batch_size)

