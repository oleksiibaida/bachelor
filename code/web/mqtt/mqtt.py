import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker, port):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe("your/sensor/topic")

    def on_message(self, client, userdata, msg):
        print(f"Message received: {msg.payload.decode()}")
        

# Initialize the MQTT client in your app
mqtt_client = MQTTClient("mqtt_broker_address", 1883)