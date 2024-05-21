import numpy as np
import torch
from ultralytics import YOLO
import time

class DetectorAPI:
    def __init__(self, model_path='runs/detect/train2/weights/best.pt'):
        # Загрузка модели YOLOv8
        self.model = YOLO(model_path)

    def processFrame(self, image):
        # Преобразуем изображение в формат, ожидаемый моделью
        start_time = time.time()
        results = self.model(image)
        end_time = time.time()

        print("Elapsed Time:", end_time - start_time)
        # Извлечение результатов
        boxes = results[0].boxes.xyxy.cpu().numpy()  # Координаты ограничивающих рамок
        scores = results[0].boxes.conf.cpu().numpy()  # Оценки достоверности
        classes = results[0].boxes.cls.cpu().numpy()  # Классы объектов

        im_height, im_width, _ = image.shape
        boxes_list = [(int(box[1]), int(box[0]), int(box[3]), int(box[2])) for box in boxes]

        return boxes_list, scores.tolist(), classes.tolist(), len(boxes)

    def close(self):
        pass  # Нет необходимости закрывать ресурсы вручную для YOLOv8

# Пример использования
if __name__ == '__main__':
    import cv2

    detector = DetectorAPI(model_path='runs/detect/train2/weights/best.pt')
    cap = cv2.VideoCapture('Videoes/12124.mp4')

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        boxes, scores, classes, num = detector.processFrame(frame)

        # Отображение результатов на изображении
        for (ymin, xmin, ymax, xmax), score, cls in zip(boxes, scores, classes):
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            label = f'Class: {int(cls)}, Score: {score:.2f}'
            cv2.putText(frame, label, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    detector.close()
