# serial_to_mqtt.py

import os
import serial
import time
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()  # expects SERIAL_PORT, BAUD_RATE, MQTT_*

# Serial settings
SERIAL_PORT = os.getenv("SERIAL_PORT")        # e.g. "/dev/tty.usbmodem14101"
BAUD_RATE   = int(os.getenv("BAUD_RATE", 9600))

# MQTT settings
MQTT_BROKER = os.getenv("MQTT_BROKER_URL", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_BROKER_PORT", "1883"))
BASE_TOPIC  = os.getenv("MQTT_BASE_TOPIC", "garden/sensors")

def main():
    # 1) Open serial port
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)  # let Arduino reset

    # 2) Connect to MQTT broker
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    print(f"Bridging {SERIAL_PORT}@{BAUD_RATE} → MQTT {MQTT_BROKER}:{MQTT_PORT}")
    
    try:
        while True:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue

            # Expect lines like "TEMP:25.3" or "SOIL:512"
            if ":" in line:
                key, val = line.split(":", 1)
                topic = f"{BASE_TOPIC}/{key.lower()}"
                client.publish(topic, val)
                print(f"→ {topic} = {val}")

    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        ser.close()

if __name__ == "__main__":
    main()
