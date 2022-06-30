import paho.mqtt.client as mqtt
import time

mqttBroker = "test.mosquitto.org"
topic_list = ["Test/send text"]

with open("Test.txt", 'r') as f:
    line_list = f.readlines()
    content = ""
    for line in line_list:
        line = line.replace("\n","")
        content = content + line + "&"

encode_content = content.encode('utf-8')


client = mqtt.Client("Send Text")

client.connect(mqttBroker)

client.loop_start()


client.publish(topic_list[0], encode_content)
time.sleep(1)

