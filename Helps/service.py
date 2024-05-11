from flask import Flask, request, jsonify
import cv2
import numpy as np
import time

app = Flask(__name__)

# Загрузка предварительно обученной модели (например, YOLO)
net = cv2.dnn.readNet("detection/yolov3.weights", "detection/yolov3.cfg")
classes = []
with open("../detection/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]


frame_skip = 2  # Обрабатывать каждый второй кадр
frame_count = 0

def process_frame(frame, width, height):
    # global frame_count
    # frame_count += 1
    # if frame_count % frame_skip != 0:
    #     return frame  # Пропускаем кадры
    #
    # # Уменьшение размера кадра
    # frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)


    blob = cv2.dnn.blobFromImage(frame, 0.00392, (width, height), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)


    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return frame

@app.route('/process', methods=['POST'])
def process_video():
    file = request.files['file']
    width = int(request.form['width'])
    height = int(request.form['height'])
    npimg = np.fromfile(file, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    processed_frame = process_frame(frame, width, height)
    _, buffer = cv2.imencode('.jpg', processed_frame)
    response = buffer.tobytes()
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
