from machine import Pin
import ntptime
import network
import urequests
import time
import dht
import socket

# Constants
WIFI_SSID = 'Solus'
WIFI_PASS = '94210231'
NTP_HOST = 'time.google.com'
ALARM_TIME = '06:00:00'
SET_TIMER_CMD = 'set_timer'
TIMEZONE_OFFSET = 3 * 3600  # UTC+3

# Pins
DHT_PIN = 21
SOUND_PIN = 4
LED_PIN = 2


class SensorManager:
    def __init__(self):
        self.dht = dht.DHT22(Pin(DHT_PIN))
        self.sound = Pin(SOUND_PIN, Pin.OUT)
        self.led = Pin(LED_PIN, Pin.OUT)
        
    def read_dht(self):
        try:
            self.dht.measure()
            return self.dht.temperature(), self.dht.humidity()
        except:
            return None, None
            
    def beep(self, duration=0.1):
        self.sound.on()
        time.sleep(duration)
        self.sound.off()

    def light(self, duration):
        self.led.on()
        time.sleep(duration)
        self.led.off()
        time.sleep(duration)

    def error(self):
        while True:
            self.light(0.5)


class NetworkManager:
    def __init__(self):
        self.wifi = network.WLAN(network.STA_IF)

    def connect(self):
        self.wifi.active(True)
        if not self.wifi.isconnected():
            self.wifi.connect(WIFI_SSID, WIFI_PASS)
            for _ in range(10):  # 10 second timeout
                if self.wifi.isconnected():
                    return True
                time.sleep(1)
            return False
        return True

    def sync_time(self):
        ntptime.host = NTP_HOST
        for _ in range(3):  # 3 attempts
            try:
                ntptime.settime()
                return True
            except:
                time.sleep(1)
        return False


class AlarmManager:
    def __init__(self, sensor):
        self.sensor = sensor
        
    def trigger(self):
        for _ in range(30):  # 30 seconds alarm
            self.sensor.beep(0.1)
            time.sleep(1)


def main():
    # Initialize components
    sensor = SensorManager()
    network = NetworkManager()
    alarm = AlarmManager(sensor)
    
    # Connect to WiFi
    if not network.connect():
        return
    
    sensor.beep(0.01)
    # Setup socket server
    server = socket.socket()
    server.bind(('0.0.0.0', 80))
    server.listen(1)
    server.setblocking(False)
    
    if not network.connect():
        sensor.error()

    if not network.sync_time():
        sensor.error()

    while True:
        current_time = time.localtime(time.time() + TIMEZONE_OFFSET)
        hours, mins, secs = current_time[3], current_time[4], current_time[5]

        # Handle socket connections
        try:
            conn, addr = server.accept()
            data = conn.recv(128)  # Limit to 128 bytes
            if data:
                message = data.decode().strip()
                if message == 'weather':
                    conn.send(str(sensor.read_dht()).encode())
            conn.close()
        except:
            pass

        # Check alarm
        if f"{hours:02d}:{mins:02d}:{secs:02d}" == ALARM_TIME:
            alarm.trigger()

        if f"{mins:02d}" in str(range(0, 60, 10)):
            urequests.get(url="https://calories-api.onrender.com")
            sensor.light(1)

        time.sleep(1)


if __name__ == "__main__":
    main()
