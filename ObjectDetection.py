import cv2
import numpy as np

def get_object(base_image, current_frame, real_frame):

    # Calculating the difference and image thresholding
    delta = cv2.absdiff(base_image, current_frame)
    threshold = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]

    # Finding all the contours
    (contours, _) = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Drawing rectangles bounding the contours
    if len(contours) > 0:
        areas = [cv2.contourArea(contour) for contour in contours]
        max_index = np.argmax(areas)
        cnt = contours[max_index]
        if cv2.contourArea(cnt) < 200:
            pass
        else:
            (x, y, w, h) = cv2.boundingRect(cnt)
            cv2.rectangle(real_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return True
    else:
        return False