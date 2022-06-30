import tkinter as tk
from PIL import Image, ImageTk
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import paho.mqtt.client as mqtt
from datetime import datetime
import os
from time import *

# Camera's frame dimension
camera_width = 640
camera_height = 480

# Frequncy to capture frame (Frame per Second)
FPS = 60

avg = None


class MainWindow():
    def __init__(self, window, cap, Pod_ID):
        self.ID = Pod_ID            # Static Pod ID
        self.window = window

        # Directory to save captured img locally
        self.folder_directory = "C:/Users/zzh84/OneDrive/Documents/GitHub/Booqed/"

        self.mqttBroker = "test.mosquitto.org" # mqtt broker address
        self.client = mqtt.Client("Qubic_{}".format(self.ID))

        self.server_status = False
        self.topic_list = ["Qubic/Connect to Qubic/{}".format(Pod_ID),
                           "Qubic/Connection State/{}".format(Pod_ID),
                           "Qubic/Get Pod Status/{}".format(Pod_ID),
                           "Qubic/Pod Status/{}".format(Pod_ID),
                           "Qubic/Get Image/{}".format(Pod_ID),
                           "Qubic/File Names/{}".format(Pod_ID),
                           "Qubic/Requested Images/{}".format(Pod_ID),
                           "Qubic/Get Difference/{}".format(Pod_ID),
                           "Qubic/Differences/{}".format(Pod_ID),
                           "Qubic/Get Un-sent Images/{}".format(Pod_ID),
                           "Qubic/Sync Database/{}".format(Pod_ID)]

        self.file_name = ""         # Captured imgs' file name (to keep consistency of name)
        self.img_log_file_name = "Pod({}) - Captured_Images.txt".format(Pod_ID) # .txt file for the captured img log
        self.received_log_file_name = "Received_Log.txt" # file name for the received log from client, for comparison

        self.differences = []

        self.Pod_Status = None      # Current Pod's status
        self.Obj_Status = None      # Current Pod's object detection result
        self.Mot_Status = None      # Current Pod's motion detection result

        self.check_in_time = datetime.now()
        self.check_out_time = datetime.now()

        self.in_switch = False
        self.out_switch = False

        self.cap = cap
        self.interval = int(1000 / FPS)  # Interval in ms to get the latest frame

        # Create canvas for image
        self.set_up_window(window)

        self.real_frame = None

        self.create_img_log()
        # Update image on canvas
        self.get_base_image()
        self.update_image()

    # Function create local img log file when the Pod starts to work
    def create_img_log(self):
        try:
            img_log_file = open(self.img_log_file_name, "x")
            img_log_file.close()
        except:
            pass

    # Function to get the reference img for the object detection algorithm
    def get_base_image(self):
        self.base_image_unchanged = self.cap.read()[1]
        self.base_image = cv2.cvtColor(self.base_image_unchanged, cv2.COLOR_BGR2GRAY)
        self.base_image = cv2.GaussianBlur(self.base_image, (25, 25), 0)

    # Function to convert cv2 captured BGR img to RGB img
    def convert2tk(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # to RGB
        img = Image.fromarray(img)  # to PIL format
        img = ImageTk.PhotoImage(img)  # to ImageTk format
        return img

    # Function to get image from camera and add GaussianBlur on it
    def get_current_frame(self, real_frame):
        self.current_frame = cv2.cvtColor(real_frame, cv2.COLOR_BGR2GRAY)
        self.current_frame = cv2.GaussianBlur(self.current_frame, (25, 25), 0)

    # Callback function when the "Start to check-in" button is pressed
    def CheckInCallBack(self):
        time = str(datetime.now())[:-7]
        self.in_switch = True
        self.check_in_time = datetime.now()
        self.get_base_image()

        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Check-in process start...\n".format(time))
        self.log_box.config(state="disabled")
        self.check_in.config(state="disabled")

    # Callback function when the "Start to check-out" button is pressed
    def CheckOutCallBack(self):
        time = str(datetime.now())[:-7]
        self.out_switch = True
        self.check_out_time = datetime.now()

        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Check-out process start...\n".format(time))
        self.log_box.config(state="disabled")
        self.check_out.config(state="disabled")

    # Function to format the Pod's status to the required format and send them via MQTT
    def send_pod_status(self):
        time = str(datetime.now())[:-7]
        msgs = "{}|{}|{}|{}".format(self.ID, self.Obj_Status, self.Mot_Status, self.Pod_Status)

        self.client.publish("Qubic/Pod Status/{}".format(self.ID), msgs)

        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Pod's Status have successfully sent to broker...\n".format(time))
        self.log_box.config(state="disabled")

    # Function to convert decoded string to txt file
    def encode_content2text(self, encode_content):
        lines = encode_content.split("&")[:-1]
        with open("Received_Log.txt", 'w') as f:
            for line in lines:
                f.write("{}\n".format(line))

    # Function to compare to text files and return the differences between them
    def get_differences(self):
        time = str(datetime.now())[:-7]

        try:
            with open(self.img_log_file_name, 'r') as f:
                try:
                    sent_lines = f.readlines()
                    f.close()
                except:
                    sent_lines = []
        except:
            sent_lines = []

        try:
            with open(self.received_log_file_name, 'r') as f:
                try:
                    received_lines = f.readlines()
                    f.close()
                except:
                    received_lines = []
        except:
            received_lines = []

        sent_lines_copy = sent_lines.copy()
        for item in sent_lines:
            if item in received_lines:
                sent_lines_copy.remove(item)

        self.differences = sent_lines_copy
        return len(self.differences)

    # Function to re-send the different imgs to client via MQTT
    def send_calibrated_img(self, img, file_name, ID):
        time = str(datetime.now())[:-7]
        MQTT_TOPIC = "Qubic/Requested Images/{}".format(self.ID)
        f = open(img, "rb")
        fileContent = f.read()
        byteArr = bytearray(fileContent)

        self.client.publish(MQTT_TOPIC, byteArr, 0)

        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Calibrated image ({}) from Pod ({}) re-sent to broker\n".format(
            str(datetime.now())[:-7],
            file_name, ID))
        self.log_box.config(state="disabled")

    # Function to sync all the un-processed data
    def sync_data(self):
        files_dirs = []
        for item in self.differences:
            info = item[:-1].split("|")
            Pod_ID = info[0]
            Date = info[1]
            Time_Period = info[2]
            file_name = info[3]
            format = ".jpg"
            file_dir = (self.folder_directory + "Check_in_out_images/{}/{}/{}/{}{}".format(
                Pod_ID, Date, Time_Period, file_name, format))
            self.send_img_file_name(file_name)
            sleep(0.5)
            self.send_calibrated_img(file_dir, file_name, Pod_ID)
            sleep(0.5)

    # Function to send img via MQTT (convert img to byte array)
    def send_captured_img(self, img, MQTT_TOPIC):
        time = str(datetime.now())[:-7]
        f = open(img, "rb")
        fileContent = f.read()
        byteArr = bytearray(fileContent)

        self.client.publish(MQTT_TOPIC, byteArr, 0)

        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Image ({}) from Pod ({}) sent to broker\n".format(str(datetime.now())[:-7],
                                                                                           self.file_name,
                                                                                           self.ID))
        self.log_box.config(state="disabled")

    def send_img_file_name(self, filename):
        MQTT_PATH = "Qubic/File Names/{}".format(self.ID)
        self.client.publish(MQTT_PATH, filename)

    # Function to save captured img to local directory
    def save_local_image(self):
        time = str(datetime.now())[:-7]
        current_time = datetime.now()
        date_folder = str(current_time.date())
        if current_time.minute < 30:
            Hour = str(current_time.hour)
            next_hour = Hour
            Min = '00'
            next_min = '30'
        else:
            Hour = str(current_time.hour)
            next_hour = str(int(current_time.hour) + 1)
            Min = '30'
            next_min = '00'

        time_period = "{}_{} - {}_{}".format(Hour, Min, next_hour, next_min)
        self.file_name = str(current_time.time())[:-7].replace(":", "_")
        self.send_img_file_name(self.file_name)

        format = ".jpg"
        path = self.folder_directory + "Check_in_out_images/{}/{}/{}".format(self.ID, date_folder, time_period)
        # Data Log
        img_log_file = open(self.img_log_file_name, "a")
        img_log_file.write("{}|{}|{}|{}\n".format(self.ID, date_folder, time_period, self.file_name))
        img_log_file.close()

        if not os.path.exists(path):
            os.makedirs(path)

        directory = self.folder_directory + "Check_in_out_images/{}/{}/{}/".format(self.ID, date_folder, time_period)
        cv2.imwrite(directory + self.file_name + format, self.real_frame)

        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Image ({}) from Pod ({}) has been saved to local...\n".format(time,
                                                                                                       self.file_name,
                                                                                                       self.ID))
        self.log_box.config(state="disabled")

        if self.Obj_Status == True:
            self.file_name = str(current_time.time())[:-7].replace(":", "_") + "_Reference"
            cv2.imwrite(directory + self.file_name + format, self.base_image_unchanged)

    # Action to capture the camera's current frame
    def capture_image(self, MQTT_TOPIC):
        current_time = datetime.now()
        date_folder = str(current_time.date())
        if current_time.minute < 30:
            Hour = str(current_time.hour)
            next_hour = Hour
            Min = '00'
            next_min = '30'
        else:
            Hour = str(current_time.hour)
            next_hour = str(int(current_time.hour) + 1)
            Min = '30'
            next_min = '00'

        time_period = "{}_{} - {}_{}".format(Hour, Min, next_hour, next_min)
        self.file_name = str(current_time.time())[:-7].replace(":", "_")
        self.send_img_file_name(self.file_name)

        format = ".jpg"
        path = self.folder_directory + "Check_in_out_images/{}/{}/{}".format(self.ID, date_folder, time_period)

        # Data Log
        img_log_file = open(self.img_log_file_name, "a")
        img_log_file.write("{}|{}|{}|{}\n".format(self.ID, date_folder, time_period, self.file_name))
        img_log_file.close()

        if not os.path.exists(path):
            os.makedirs(path)

        directory = self.folder_directory + "Check_in_out_images/{}/{}/{}/".format(self.ID, date_folder, time_period)
        cv2.imwrite(directory + self.file_name + format, self.real_frame)

        self.send_captured_img(directory + self.file_name + format, MQTT_TOPIC)

        if self.Obj_Status == True:
            self.file_name = str(current_time.time())[:-7].replace(":", "_") + "_Reference"
            cv2.imwrite(directory + self.file_name + format, self.base_image_unchanged)

    # Function to detect the object in the current frame by comparing the current frame with the pre-defined
    # reference frame
    def get_object(self):
        # Calculating the difference and image thresholding
        delta = cv2.absdiff(self.base_image, self.current_frame)
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
                cv2.rectangle(self.real_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            self.Obj_Status = True
            self.Obj_txt = "Object Detected"
            self.Obj_txt_color = "red"
        else:
            self.Obj_Status = False
            self.Obj_txt = "No Object Detected"
            self.Obj_txt_color = "green"

    # Function to detect the motion in the current frame by comparing the current frame with the average frames
    def get_motion(self):
        global avg
        if avg is None:
            avg = self.current_frame.copy().astype("float")

        cv2.accumulateWeighted(self.current_frame, avg, 0.01)

        # Calculating the difference and image thresholding
        delta = cv2.absdiff(self.current_frame, cv2.convertScaleAbs(avg))
        threshold = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]

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
                cv2.rectangle(self.real_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            self.Mot_Status = True
            self.Mot_txt = "Motion Detected"
            self.Mot_txt_color = "red"
        else:
            self.Mot_Status = False
            self.Mot_txt = "No Motion Detected"
            self.Mot_txt_color = "green"

    # Function to determine the Pod's status by analysing the collected obj and mot detection results
    def get_pod_status(self):

        if self.Mot_Status and self.Obj_Status:
            self.Pod_Status = "Occupied"
            self.Pod_txt_color = "red"

        if (not self.Mot_Status) and (not self.Obj_Status):
            self.Pod_Status = "Empty"
            self.Pod_txt_color = "Green"

        if self.Obj_Status == True and self.out_switch == True:
            self.Pod_Status == "Occupied"
            self.Pod_txt_color = "red"

        if self.Mot_Status:
            self.check_out_time = datetime.now()

        if not self.Obj_Status:
            self.check_in_time = datetime.now()

        current_time = datetime.now()
        in_difference = current_time - self.check_in_time
        out_difference = current_time - self.check_out_time

        if in_difference.seconds >= 15 and self.in_switch == True:
            time = str(datetime.now())[:-7]
            self.in_switch = False
            self.log_box.config(state="normal")
            self.log_box.insert("end", "{} - User has done the check-in...\n".format(time))
            self.log_box.config(state="disabled")
            self.check_in.config(state="normal")

        if out_difference.seconds >= 15 and self.out_switch == True:
            time = str(datetime.now())[:-7]
            self.out_switch = False
            self.log_box.config(state="normal")
            self.log_box.insert("end", "{} - User has done the check-out...\n".format(time))
            self.log_box.config(state="disabled")
            self.check_out.config(state="normal")

    # Function to detect QR code to initialize the check-in process
    def check_QR_code(self):
        gray = cv2.cvtColor(self.real_frame, cv2.COLOR_BGR2GRAY)
        try:
            qr_info_list = decode(gray)
            for code in qr_info_list:
                qr_info = code.data.decode('utf-8')
                pts = []
                for i in range(len(code.polygon)):
                    pts.append([code.polygon[i][0], code.polygon[i][1]])
                pts = np.array(pts, np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(self.real_frame, [pts], True, (255, 0, 0), 2)
                try:
                    qr_ID = int(qr_info.split("_")[0])
                    start_time = qr_info.split("-")[1]
                    end_time = qr_info.split("-")[1]

                    if qr_ID == self.ID and self.in_switch == False:
                        self.CheckInCallBack()
                except:
                    pass
        except:
            pass

    # Callback function when the connect button is pressed in the drop-down menu
    # to connect to MQTT broker
    def Connect2Mqtt(self):
        time = str(datetime.now())[:-7]
        try:
            if not self.server_status:

                self.client.on_connect = self.on_connect
                self.client.on_message = self.on_message

                self.client.connect(self.mqttBroker)

                self.client.loop_start()

                self.log_box.config(state="normal")
                self.log_box.delete("1.0", "end")
                self.log_box.insert("end", "{} - Connected to MQTT broker...\n".format(time))
                self.log_box.config(state="disabled")

                self.server_status = True
            else:
                self.client.on_connect = self.on_connect
                self.client.on_message = self.on_message

                self.client.connect(self.mqttBroker)

                self.client.loop_start()

                self.server_status = True

                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Reconnected to MQTT broker...\n".format(time))
                self.log_box.config(state="disabled")

        except:
            self.log_box.config(state="normal")
            self.log_box.insert("end", "Unable to connect to MQTT server...\n")
            self.log_box.config(state="disabled")

    # Callback function when the disconnet button is pressed in the drop-down menu
    # to disconnect from client
    def Disconnect2Mqtt(self):
        time = str(datetime.now())[:-7]
        if self.server_status:
            self.client.disconnect()
            self.client.loop_stop()
            self.server_status = False

            self.log_box.config(state="normal")
            self.log_box.insert("end", "{} - Disconnected from MQTT broker...\n".format(time))
            self.log_box.config(state="disabled")

        else:
            self.log_box.config(state="normal")
            self.log_box.insert("end", "{} - Already disconnected from MQTT broker...\n".format(time))
            self.log_box.config(state="disabled")

    # Mqtt on_message function, based on different sub topic to perform different functions
    def on_message(self, client, userdata, message):

        if message.topic == "Qubic/Connect to Qubic/{}".format(self.ID):
            temp_ID = int(message.payload.decode("utf-8"))
            if temp_ID == self.ID:
                time = str(datetime.now())[:-7]
                MQTT_TOPIC = "Qubic/Connection State/{}".format(self.ID)
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Get connection request from client...\n".format(time))
                self.log_box.config(state="disabled")
                self.client.publish(MQTT_TOPIC, self.ID)

        if message.topic == "Qubic/Get Pod Status/{}".format(self.ID):
            if int(message.payload.decode("utf-8")) == 1:
                time = str(datetime.now())[:-7]
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Get pod status request from client...\n".format(time))
                self.log_box.config(state="disabled")
                self.send_pod_status()

        if message.topic == "Qubic/Get Image/{}".format(self.ID):
            if int(message.payload.decode("utf-8")) == 1:
                time = str(datetime.now())[:-7]
                MQTT_TOPIC = "Qubic/Requested Images/{}".format(self.ID)
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Get pod image request from client...\n".format(time))
                self.log_box.config(state="disabled")
                self.capture_image(MQTT_TOPIC)

        if message.topic == "Qubic/Get Difference/{}".format(self.ID):
            if message.payload.decode("utf-8") != "\n":
                time = str(datetime.now())[:-7]
                MQTT_TOPIC = "Qubic/Differences/{}".format(self.ID)
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Get database comparison request from client...\n".format(time))
                self.log_box.config(state="disabled")

                self.encode_content2text(message.payload.decode("utf-8"))
                difference = self.get_differences()

                self.client.publish(MQTT_TOPIC, difference)

                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Database comparison result has been sent to client...\n".format(time))
                self.log_box.config(state="disabled")
            else:
                time = str(datetime.now())[:-7]
                MQTT_TOPIC = "Qubic/Differences/{}".format(self.ID)
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Get database comparison request from client...\n".format(time))
                self.log_box.config(state="disabled")

                with open("Received_Log.txt", 'w') as f:
                    f.write("")

                self.client.publish(MQTT_TOPIC, 0)

                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Database comparison result has been sent to client...\n".format(time))
                self.log_box.config(state="disabled")

        if message.topic == "Qubic/Get Un-sent Images/{}".format(self.ID):
            if int(message.payload.decode("utf-8")) == 1:
                time = str(datetime.now())[:-7]
                MQTT_TOPIC = "Qubic/Sync Database/{}".format(self.ID)
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Get database sync request from client...\n".format(time))
                self.log_box.config(state="disabled")

                self.sync_data()
                self.client.publish(MQTT_TOPIC, 1)

                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Sync data has been sent to client...\n".format(time))
                self.log_box.config(state="disabled")

    # MQTT on_connect function to sub all the required topics from broker
    def on_connect(self, client, userdata, flags, rc):
        for i in self.topic_list:
            client.subscribe(i)

    # Function to update img
    def update_image(self):
        # Get the latest frame and convert image format
        self.real_frame = self.cap.read()[1]
        self.get_current_frame(self.real_frame)
        self.get_object()
        self.get_motion()
        self.check_QR_code()

        self.tk_img = self.convert2tk(self.real_frame)

        # Update Pod
        self.get_pod_status()
        self.Pod.config(text=self.Pod_Status, fg=self.Pod_txt_color)
        self.Obj.config(text=self.Obj_txt, fg=self.Obj_txt_color)
        self.Mot.config(text=self.Mot_txt, fg=self.Mot_txt_color)

        # Update image
        self.canvas_ori.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

        # Repeat every 'interval' ms
        self.window.after(self.interval, self.update_image)

    # Function to create all the GUI elements in the Pod application
    def set_up_window(self, window):

        window.title("Qubic {}".format(self.ID))
        window.iconbitmap("Icons/icon.ico")

        # Menu for the navigation
        menubar = tk.Menu(window)
        window.config(menu=menubar)

        connectMenu = tk.Menu(menubar, tearoff=0)
        connectMenu.add_command(label="Connect to MQTT broker", command=self.Connect2Mqtt)
        connectMenu.add_command(label="Disconnect to MQTT broker", command=self.Disconnect2Mqtt)
        menubar.add_cascade(label="Connect", menu=connectMenu)

        # Title Label
        title = "POD ID - {}".format(self.ID)
        title_ID = tk.Label(window, text=title, font="Helvetica 20 bold", bg="#42a4f5", fg="white", height=2,
                            width=50)
        title_ID.grid(row=0, column=1, columnspan=2, padx=5, pady=5)

        # Labels for the Pod Status
        l1 = tk.Label(window, text="Qubic Status:", font="Helvetica 16 bold", width=15, anchor="w")
        l2 = tk.Label(window, text="Object Detection:", font="Helvetica 16 bold", width=15, anchor="w")
        l3 = tk.Label(window, text="Motion Detection:", font="Helvetica 16 bold", width=15, anchor="w")

        l1.grid(row=1, column=1, stick="w")
        l2.grid(row=3, column=1, stick="w")
        l3.grid(row=4, column=1, stick="w")

        self.Pod = tk.Label(window, text=self.Pod_Status, font="Helvetica 16 bold", width=15, anchor="w")
        self.Pod.grid(row=1, column=2, stick="w", padx=5)

        self.Obj = tk.Label(window, text=self.Obj_Status, font="Helvetica 16 bold", width=15, anchor="w")
        self.Obj.grid(row=3, column=2, stick="w", padx=5)

        self.Mot = tk.Label(window, text=self.Mot_Status, font="Helvetica 16 bold", width=15, anchor="w")
        self.Mot.grid(row=4, column=2, stick="w", padx=5)

        # Buttons
        self.check_in = tk.Button(window, text="Start to Check In", command=self.CheckInCallBack,
                                  font="Helvetica 16 bold", width=15, bg='green', fg='white')
        self.check_in.grid(row=5, column=1, padx=5, pady=5, stick="w")

        self.check_out = tk.Button(window, text="Start to Check Out", command=self.CheckOutCallBack,
                                   font="Helvetica 16 bold", width=15, bg='red', fg='white')
        self.check_out.grid(row=6, column=1, padx=5, pady=5, stick="w")

        self.take_img = tk.Button(window, text="Capture Image", command=self.save_local_image,
                                  font="Helvetica 16 bold", width=15)
        self.take_img.grid(row=7, column=1, padx=5, pady=5, stick="w")

        # Create data log box
        self.log_box = tk.Text(root, wrap="word", width=70)
        self.log_box.grid(row=5, column=2, rowspan=6, padx=10, pady=10)
        self.log_box.config(font="Ubuntu 12 italic", state="disabled")

        # Image Canvas
        self.canvas_ori = tk.Canvas(self.window, width=camera_width, height=camera_height)
        self.canvas_ori.grid(row=0, column=0, rowspan=12, padx=5, pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    main_window = MainWindow(root, cv2.VideoCapture(1), 2555)
    root.mainloop()
