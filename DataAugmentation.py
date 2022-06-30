from keras.preprocessing.image import *
import tensorflow as tf
import os

directory = 'C:/Users/zzh84/PycharmProjects/BooqedQubic/HumanTopViewDatabase/'
original_directory = 'C:/Users/zzh84/PycharmProjects/BooqedQubic/HumanTopViewDatabase/OriginalData/'
idg = ImageDataGenerator(rescale=1 / 255,
                         horizontal_flip=True,
                         rotation_range=30,
                         width_shift_range=0.3,
                         height_shift_range=0.3,
                         brightness_range=[0.2, 1.0],
                         zoom_range=[0.5, 1.0]
                         )

for num in range(1,11):
    file_name = original_directory + "Resized_img_{}.jpg".format(num)

    image = tf.keras.preprocessing.image.load_img(file_name)
    input_arr = tf.keras.utils.img_to_array(image)
    # reshaping the image to a 4D array to be used with keras flow function.
    input_arr = input_arr.reshape((1,) + input_arr.shape)

    i = 0
    for batch in idg.flow(input_arr, batch_size=1,
                          save_to_dir=directory + "AugmentedData/", save_prefix='HumanTop', save_format='jpg'):
        i += 1
        if i > 100:
            break  # need to break the loop otherwise it will run infinite times
