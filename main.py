import dht
import framebuf
import network
import ntptime

from config import wifi_config
from machine import Pin, SoftI2C, RTC
from ssd1306 import SSD1306_I2C
from time import sleep

# Network
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.scan()
sta_if.connect(wifi_config['ssid'], wifi_config['password'])
while not sta_if.isconnected():
    pass

# Time
ntptime.settime()
rtc = RTC()
datetime = rtc.datetime()
# Configure Timezone
rtc.datetime([datetime[0], datetime[1], datetime[2], datetime[3], datetime[4] + 1, datetime[5], datetime[6], datetime[7]])

# Display, using default address 0x3C
i2c = SoftI2C(sda=Pin(4), scl=Pin(5))
display = SSD1306_I2C(128, 64, i2c)

# DHT11
pin = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_UP)
dht = dht.DHT11(pin)

# Plotting
datenpunkte = [0] * 95
index = 1
now = 123
von_bereich = (10, 35)
nach_bereich = (63, 12)

# Smileys
sad = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\xf8\x00\x00\x00\x7f\xfc\x00\x00\x00\xff\xff\x80\x00\x01\xff\xff\xe0\x00\x03\xff\xff\xf0\x00\x0f\xff\xff\xfc\x00\x0f\xff\xff\xfc\x00\x0c\xf9\xe7\xcc\x00\x1f\xff\xff\xfe\x00\x3f\x87\xf8\x7f\x00\x3f\xff\xff\xff\x00\x3f\xff\xff\xff\x00\x3f\xff\xff\xff\x00\x3f\xff\xff\xff\x00\x3f\xf8\x07\xff\x00\x1f\xff\xff\xfe\x00\x0f\xe7\xf9\xfc\x00\x0f\x9f\xfe\x7c\x00\x0f\x9f\xfe\x7c\x00\x03\xff\xff\xf0\x00\x01\xff\xff\xe0\x00\x00\xff\xff\xc0\x00\x00\x7f\xff\x80\x00\x00\x07\xf8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
happy = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\xf8\x00\x00\x00\x7f\xfc\x00\x00\x00\xff\xff\x80\x00\x01\xff\xff\xe0\x00\x03\xff\xff\xf0\x00\x0c\x01\xe0\x0c\x00\x0c\x01\xe0\x0c\x00\x03\xfe\x1f\xf0\x00\x13\xfe\x1f\xf2\x00\x33\xfe\x1f\xf3\x00\x3c\xf9\xe7\xcf\x00\x3c\x79\xe7\x8f\x00\x3f\x87\xf8\x7f\x00\x3f\x87\xf8\x7f\x00\x3f\xff\xff\xff\x00\x1f\xff\xff\xfe\x00\x0f\xe0\x01\xfc\x00\x0f\xff\xff\xfc\x00\x0f\xff\xff\xfc\x00\x03\xff\xff\xf0\x00\x01\xff\xff\xe0\x00\x00\xff\xff\xc0\x00\x00\x7f\xff\x80\x00\x00\x07\xf8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")

def measure_dht():
    dht.measure()
    temp = dht.temperature()
    humidity = dht.humidity()
    return temp, humidity

def display_time(time):
    display.fill(0)
    display.text(time, 0, 0, 1)

def display_dht(temp, humidity):
    temp = f"{temp} C"
    humidity = f"{humidity} %"
    display.text(temp, 95, 12, 1)
    display.text(humidity, 95, 24, 1)
    
def plot():
    for i in range(1, 94):
        if datenpunkte[i] == 0:
            pass
        else:
            y = map_data(datenpunkte[i])
            display.pixel(i, y, 1)
            display.pixel(i, y+1, 1)
    display.hline(0, 63, 95, 1)
    display.vline(0, 12, 51, 1)
    
def update_plot(temp):
    global index
    if index <= 94:
        datenpunkte[index] = temp
        index += 1
    if index == 95:
        datenpunkte.pop(0)
        datenpunkte[94] = temp
    
def map_data(x):
    von_bereich = (10, 35)
    nach_bereich = (63, 12)
    # Stellen Sie sicher, dass x im von_bereich liegt
    x = max(min(x, von_bereich[1]), von_bereich[0])
    # Berechnen Sie den prozentualen Anteil von x im von_bereich
    prozentualer_anteil = (x - von_bereich[0]) / (von_bereich[1] - von_bereich[0])
    # Verwenden Sie den prozentualen Anteil, um den Wert im nach_bereich zu bestimmen
    zielwert = int(nach_bereich[0] + prozentualer_anteil * (nach_bereich[1] - nach_bereich[0]))
    return zielwert

def smiley(temp, humidity):
    if temp <= 16 or temp >= 20:
        image = sad
    elif humidity <= 30 or humidity >= 60:
        image = sad
    else:
        image = happy
    fb = framebuf.FrameBuffer(image, 34, 28, framebuf.MONO_HLSB)
    display.blit(fb, 95, 36)
    display.show()
    
while True:
    try:
        datetime = rtc.datetime()
        time = f"{datetime[2]:02d}.{datetime[1]:02d}.{datetime[0]} {datetime[4]:02d}:{datetime[5]:02d}"
        display_time(time)
        temp, humidity = measure_dht()
        display_dht(temp, humidity)
        if now == 123:
            update_plot(temp)
            now = datetime[5]
            next_execution = now + 15
        elif now == next_execution:
            update_plot(temp)
            next_execution = now + 15
        now = datetime[5]
        plot()
        smiley(temp, humidity)
        sleep(30)
    except OSError:
        print('Failed to read sensor.')

