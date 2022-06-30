import tkinter as tk
from datetime import datetime
import paho.mqtt.client as mqtt
import os


class MainWindow():
    def __init__(self, window):
        self.window = window

        self.folder_directory = "C:/Users/zzh84/OneDrive/Documents/GitHub/Booqed/" # Directory to save received imgs

        self.mqttBroker = "test.mosquitto.org" # mqtt broker address

        self.client = mqtt.Client("Client_Message")

        self.file_name = "" # received imgs' file name (to keep consistency of name)

        self.ID = "Not Connected"               # Pod ID
        self.Pod_Status = "Not Connected"       # Received Pod's status
        self.Obj_Status = "Not Connected"       # Received Pod's object detection result
        self.Mot_Status = "Not Connected"       # Received Pod's motion detection result

        # Pre-define the text and color in UI
        self.Obj_txt = None
        self.Mot_txt = None
        self.Obj_txt_color = "black"
        self.Mot_txt_color = "black"

        # Create canvas for image
        self.set_up_window(window)

    # Callback function when the "Connect to Pod" button has been pressed
    def connect_to_pod(self):
        self.client.disconnect()
        self.client.loop_stop()

        time = str(datetime.now())[:-7]
        if len(self.ID_Input.get("1.0", "end-1c")) != 0:
            try:
                self.temp_ID = int(self.ID_Input.get("1.0", "end-1c"))
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Trying to connect to Pod ({})...\n".format(time, self.temp_ID))
                self.log_box.config(state="disabled")

                self.topic_list = ["Qubic/Connect to Qubic/{}".format(self.temp_ID),
                                   "Qubic/Connection State/{}".format(self.temp_ID),
                                   "Qubic/Get Pod Status/{}".format(self.temp_ID),
                                   "Qubic/Pod Status/{}".format(self.temp_ID),
                                   "Qubic/Get Image/{}".format(self.temp_ID),
                                   "Qubic/File Names/{}".format(self.temp_ID),
                                   "Qubic/Requested Images/{}".format(self.temp_ID),
                                   "Qubic/Get Difference/{}".format(self.temp_ID),
                                   "Qubic/Differences/{}".format(self.temp_ID),
                                   "Qubic/Get Un-sent Images/{}".format(self.temp_ID),
                                   "Qubic/Sync Database/{}".format(self.temp_ID)]

                self.client.on_connect = self.on_connect
                self.client.on_message = self.on_message

                self.client.connect(self.mqttBroker)

                self.client.loop_start()

                MQTT_TOPIC = "Qubic/Connect to Qubic/{}".format(self.temp_ID)
                self.client.publish(MQTT_TOPIC, self.temp_ID)
            except:
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Pod ID must be number...\n".format(time))
                self.log_box.config(state="disabled")

        else:
            self.log_box.config(state="normal")
            self.log_box.insert("end", "{} - Enter the Pod ID first...\n".format(time, self.ID))
            self.log_box.config(state="disabled")

    # Callback function when the "Get Pod Status" button has been pressed
    def get_qubic_status(self):
        time = str(datetime.now())[:-7]
        MQTT_TOPIC = "Qubic/Get Pod Status/{}".format(self.ID)
        self.client.publish(MQTT_TOPIC, 1)
        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Pod's status request has been sent to Pod ({})\n".format(time, self.ID))
        self.log_box.config(state="disabled")

    # Callback function when the "Get Captured Image" button has been pressed
    def get_capture_image(self):
        time = str(datetime.now())[:-7]
        MQTT_TOPIC = "Qubic/Get Image/{}".format(self.ID)
        self.client.publish(MQTT_TOPIC, 1)
        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Pod's image request has been sent to Pod ({})\n".format(time, self.ID))
        self.log_box.config(state="disabled")

    # Function to convert received .txt file to byte array
    def get_decode_text(self):
        try:
            with open("Pod({}) - Received_Images.txt".format(self.ID), 'r') as f:
                line_list = f.readlines()
                content = ""
                for line in line_list:
                    line = line.replace("\n", "")
                    content = content + line + "&"

            self.encode_content = content.encode('utf-8')
        except:
            self.encode_content = ""

    # Callback function when the "Get Data Differences" button has been pressed
    def get_differences(self):
        time = str(datetime.now())[:-7]
        MQTT_TOPIC = "Qubic/Get Difference/{}".format(self.ID)
        self.get_decode_text()
        self.client.publish(MQTT_TOPIC, self.encode_content)
        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Database comparison request has been sent to Pod ({})\n".format(time, self.ID))
        self.log_box.config(state="disabled")

    # Callback function when the "Re-send Data" button has been pressed
    def get_resent_data(self):
        time = str(datetime.now())[:-7]
        MQTT_TOPIC = "Qubic/Get Un-sent Images/{}".format(self.ID)
        self.client.publish(MQTT_TOPIC, 1)
        self.log_box.config(state="normal")
        self.log_box.insert("end", "{} - Database sync request has been sent to Pod ({})\n".format(time, self.ID))
        self.log_box.config(state="disabled")

    # Function to insert image log to .txt file
    def create_img_log(self):
        try:
            img_log_file = open("Pod({}) - Received_Images.txt".format(self.ID), "x")
            img_log_file.close()
        except:
            pass

    # Mqtt on_message function, based on different sub topic to perform different functions
    def on_message(self, client, userdata, message):

        # When the connection message received from Pod
        if message.topic == "Qubic/Connection State/{}".format(self.temp_ID):
            if message != None:
                time = str(datetime.now())[:-7]
                self.ID = int(message.payload.decode("utf-8"))
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Connected to Pod ({})...\n".format(time, self.ID))
                self.log_box.config(state="disabled")

                self.connect_pod.config(state="disabled")

                self.title_ID.config(text="POD ID - {}".format(self.ID))
                self.get_status.config(state="normal")
                self.get_img.config(state="normal")
                self.get_calibrate_data.config(state="normal")

                self.create_img_log()

        # When the Pod's Status message received from Pod
        if message.topic == "Qubic/Pod Status/{}".format(self.ID):
            message_list = str(message.payload.decode("utf-8")).split("|")
            self.ID = message_list[0]
            self.Obj_Status = message_list[1]
            self.Mot_Status = message_list[2]
            self.Pod_Status = message_list[3]

            if self.Obj_Status == "True":
                self.Obj_txt = "Objet Detected"
                self.Obj_txt_color = "red"
            else:
                self.Obj_txt = "No Object Detected"
                self.Obj_txt_color = "green"

            if self.Mot_Status == "True":
                self.Mot_txt = "Motion Detected"
                self.Mot_txt_color = "red"
            else:
                self.Mot_txt = "No Motion Detected"
                self.Mot_txt_color = "green"

            if self.Pod_Status == "Occupied":
                self.Pod_txt_color = "red"
            else:
                self.Pod_txt_color = "green"

            self.Pod.config(text=self.Pod_Status, fg=self.Pod_txt_color)
            self.Obj.config(text=self.Obj_txt, fg=self.Obj_txt_color)
            self.Mot.config(text=self.Mot_txt, fg=self.Mot_txt_color)

            self.log_box.config(state="normal")
            self.log_box.insert("end",
                                "{} - Pod's status have received from Pod ({})\n".format(str(datetime.now())[:-7],
                                                                                         self.ID))
            self.log_box.config(state="disabled")

        # When the img's file name message received from Pod
        if message.topic == "Qubic/File Names/{}".format(self.ID):
            self.file_name = str(message.payload.decode("utf-8"))

        # When the requested img message received from Pod
        if message.topic == "Qubic/Requested Images/{}".format(self.ID):
            # more callbacks, etc
            # Create a file with write byte permission
            format = ".jpg"

            capture_time_str = self.file_name
            capture_time = datetime.strptime(capture_time_str, '%H_%M_%S')
            date_folder = str(datetime.now().date())

            if capture_time.minute < 30:
                Hour = str(capture_time.hour)
                next_hour = Hour
                Min = '00'
                next_min = '30'
            else:
                Hour = str(capture_time.hour)
                next_hour = str(int(capture_time.hour) + 1)
                Min = '30'
                next_min = '00'

            time_period = "{}_{} - {}_{}".format(Hour, Min, next_hour, next_min)


            path = self.folder_directory + "Received_images/{}/{}/{}".format(self.ID, date_folder, time_period)

            if not os.path.exists(path):
                os.makedirs(path)

            directory = self.folder_directory + "Received_images/{}/{}/{}/".format(self.ID, date_folder, time_period)

            f = open(directory + self.file_name + format, "wb")
            f.write(message.payload)

            self.log_box.config(state="normal")
            self.log_box.insert("end", "{} - Image ({}) received from Pod ({})\n".format(str(datetime.now())[:-7],
                                                                                         self.file_name, self.ID))
            self.log_box.config(state="disabled")

            f.close()

            img_log_file = open("Pod({}) - Received_Images.txt".format(self.ID), "a")
            img_log_file.write("{}|{}|{}|{}\n".format(self.ID, date_folder, time_period, self.file_name))
            img_log_file.close()

        # When the data difference message received from Pod
        if message.topic == "Qubic/Differences/{}".format(self.ID):
            time = str(datetime.now())[:-7]
            difference = int(message.payload.decode("utf-8"))

            if difference == 0:
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - No images need to be synced...\n".format(time))
                self.log_box.config(state="disabled")

                self.calibrate.config(state="disabled")
            else:
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - {} image(s) need to be synced...\n".format(time, difference))
                self.log_box.config(state="disabled")

                self.calibrate.config(state="normal")

        # When the different data have been re-sent successfully message received from Pod
        if message.topic == "Qubic/Sync Database/{}".format(self.ID):
            time = str(datetime.now())[:-7]
            result = int(message.payload.decode("utf-8"))
            if result == 1:
                self.log_box.config(state="normal")
                self.log_box.insert("end", "{} - Database sync has done...\n".format(time))
                self.log_box.config(state="disabled")

                self.calibrate.config(state="disabled")

    # MQTT on_connect function to sub all the required topics from broker
    def on_connect(self, client, userdata, flags, rc):
        for i in self.topic_list:
            client.subscribe(i)

    # Callback funtion when the "Connect to MQTT broker" button has been pressed in the drop-down
    # menu
    def Start_MQTT(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        time = str(datetime.now())[:-7]
        self.log_box.insert("end", "{} - Creating new client instance...\n".format(time))

        self.log_box.insert("end", "{} - Connected to MQTT broker...\n".format(time).format(time))
        self.log_box.config(state="disabled")

        self.title_ID.config(text="POD - Not Connected")
        self.Pod.config(text="Not Connected", fg='black')
        self.Obj.config(text="Not Connected", fg='black')
        self.Mot.config(text="Not Connected", fg='black')

        self.get_img.config(state="disabled")
        self.get_status.config(state="disabled")
        self.get_calibrate_data.config(state="disabled")
        self.calibrate.config(state="disabled")

        self.connect_pod.config(state="normal")
        self.ID_Input.delete("1.0", "end")
        self.ID_Input.config(state="normal")

    # Function to create all the GUI elements in the client application
    def set_up_window(self, window):

        window.title("Qubic Monitoring Client")
        window.iconbitmap("Icons/icon.ico")

        # Menu for the navigation

        menubar = tk.Menu(window)
        window.config(menu=menubar)

        connectMenu = tk.Menu(menubar, tearoff=0)
        connectMenu.add_command(label="Connect to MQTT broker", command=self.Start_MQTT)
        menubar.add_cascade(label="Connect", menu=connectMenu)

        # Title Label

        title = "POD ID - {}".format(self.ID)
        self.title_ID = tk.Label(window, text=title, font="Helvetica 20 bold", bg="yellow", fg="blue", height=2,
                                 width=40)
        self.title_ID.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        # Labels for the Pod Status
        l1 = tk.Label(window, text="Qubic Status:", font="Helvetica 16 bold", width=20, anchor="w")
        l2 = tk.Label(window, text="Object Detection:", font="Helvetica 16 bold", width=20, anchor="w")
        l3 = tk.Label(window, text="Motion Detection:", font="Helvetica 16 bold", width=20, anchor="w")

        l1.grid(row=1, column=0, padx=5, pady=5, stick="e")
        l2.grid(row=2, column=0, padx=5, pady=5, stick="e")
        l3.grid(row=3, column=0, padx=5, pady=5, stick="e")

        self.Pod = tk.Label(window, text=self.Pod_Status, font="Helvetica 16 bold", width=20, anchor="w")
        self.Pod.grid(row=1, column=1, stick="e")

        self.Obj = tk.Label(window, text=self.Obj_Status, font="Helvetica 16 bold", width=20, anchor="w")
        self.Obj.grid(row=2, column=1, stick="e")

        self.Mot = tk.Label(window, text=self.Mot_Status, font="Helvetica 16 bold", width=20, anchor="w")
        self.Mot.grid(row=3, column=1, stick="e")

        self.get_img = tk.Button(window, text="Get Capture Image", command=self.get_capture_image,
                                  font="Helvetica 16 bold", width=18, state="disabled")
        self.get_img.grid(row=4, column=1, padx=5, pady=5)

        self.get_status = tk.Button(window, text="Get Pod Status", command=self.get_qubic_status,
                                     font="Helvetica 16 bold", width=18, state="disabled")
        self.get_status.grid(row=4, column=0, padx=5, pady=5)

        self.get_calibrate_data = tk.Button(window, text="Get Data Differences", command=self.get_differences,
                                            font="Helvetica 16 bold", width=18, state="disabled")
        self.get_calibrate_data.grid(row=5, column=0, padx=5, pady=5)

        self.calibrate = tk.Button(window, text="Re-send Data", command=self.get_resent_data,
                                   font="Helvetica 16 bold", width=18, state="disabled")
        self.calibrate.grid(row=5, column=1, padx=5, pady=5)

        self.connect_pod = tk.Button(window, text="Connect to Pod", command=self.connect_to_pod,
                                   font="Helvetica 16 bold", bg="#75ffda", width=18, state="disabled")
        self.connect_pod.grid(row=6, column=0, columnspan=1, padx=5, pady=5)

        # Create ID input box
        self.ID_Input = tk.Text(window, wrap="word", height=1, width=25)
        self.ID_Input.grid(row=6, column=1, padx=5, pady=5)
        self.ID_Input.config(font="Ubuntu 20", state="disabled")

        # Create log widget
        self.log_box = tk.Text(window, wrap="word", width=80, height=40)
        self.log_box.grid(row=7, column=0, columnspan=2, padx=10, pady=10)
        self.log_box.config(font="Ubuntu 12 italic", state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    main_window = MainWindow(root)
    root.mainloop()
