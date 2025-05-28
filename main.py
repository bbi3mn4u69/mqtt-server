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
CONTROL_TOPIC = f"{BASE_TOPIC}/control"  # Topic for receiving control commands

def on_message(client, userdata, message):
    """Handle incoming MQTT messages for control commands"""
    try:
        command = message.payload.decode('utf-8').strip()
        topic = message.topic
        
        # Extract the device and action from the topic
        # Example: garden/sensors/control/pump/on
        parts = topic.split('/')
        if len(parts) >= 2:
            device = parts[-2]  # e.g., 'pump'
            action = parts[-1]  # e.g., 'on'
            
            # Format command for Arduino
            # Example: "PUMP:ON" or "FAN:OFF"
            arduino_command = f"{device.upper()}:{action.upper()}\n"
            ser.write(arduino_command.encode('utf-8'))
            print(f"Sent command to Arduino: {arduino_command.strip()}")
            
    except Exception as e:
        print(f"Error processing command: {e}")

def main():
    global ser
    # 1) Open serial port
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)  # let Arduino reset

    # 2) Connect to MQTT broker
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    
    # Subscribe to control topics
    client.subscribe(f"{CONTROL_TOPIC}/#")  # Subscribe to all control subtopics
    client.loop_start()

    print(f"Bridging {SERIAL_PORT}@{BAUD_RATE} → MQTT {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Listening for control commands on: {CONTROL_TOPIC}/#")
    
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
