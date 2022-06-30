import paho.mqtt.client as mqtt

mqttBroker = "test.mosquitto.org"
topic_list = ["Test/send text"]
client = mqtt.Client("Receive Text")


def on_message(client, userdata, message):
    ID_list = message.payload.decode("utf-8")
    IDs = ID_list.split("&")[:-1]
    with open("Received_Log.txt", 'w') as f:
        for ID in IDs:
            f.write("{}\n".format(ID))



client.connect(mqttBroker)

client.loop_start()

while True:
    client.subscribe(topic_list[0])
    client.on_message = on_message
