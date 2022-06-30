import cv2
import os

directory = 'C:/Users/zzh84/PycharmProjects/BooqedQubic/HumanTopViewDatabase/OriginalData/'

for file in os.listdir(directory):
    image_file = directory + file
    img = cv2.imread(image_file, cv2.IMREAD_UNCHANGED)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (256, 256))

    cv2.imwrite(directory + "Resized_{}".format(file), img)