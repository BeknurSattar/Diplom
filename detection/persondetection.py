import time
from ultralytics import YOLO

class DetectorAPI:
    def __init__(self, model_path):
        # Загрузка модели
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