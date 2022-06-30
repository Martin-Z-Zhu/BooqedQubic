import cv2
from pyzbar.pyzbar import decode
import numpy as np

width = 800
height = 600

cap = cv2.VideoCapture(1)
cap.set(3, width)
cap.set(4, height)

while True:
    frame = cap.read()[1]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    try:
        data = decode(gray)
        for code in data:
            print(code.data.decode('utf-8'))
            pts = []
            for i in range(len(code.polygon)):
                pts.append([code.polygon[i][0], code.polygon[i][1]])
            pts = np.array(pts, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.rectangle(frame, (code.rect[0], code.rect[1]), (code.rect[0] + code.rect[2], code.rect[1] + code.rect[3]),
                          (255, 0, 0), 2)
            cv2.polylines(frame, [pts], True, (0, 0, 255), 2)
    except:
        pass

    cv2.imshow("Stream", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
