import network, urequests, time, machine, neopixel
from machine import TouchPad, Pin
from ssd1306 import SSD1306_I2C

### SETUP ###

#OLED
i2c = machine.SoftI2C(sda=machine.Pin(22), scl=machine.Pin(23))
i2c.scan()
oled = SSD1306_I2C(128,64,i2c)

#LEDs
led_green_1 = Pin(0, Pin.OUT)
led_red_1 = Pin(4, Pin.OUT)
led_blue_1 = Pin(2, Pin.OUT)
led_green_2 = Pin(12, Pin.OUT)
led_red_2 = Pin(14, Pin.OUT)
led_blue_2 = Pin(13, Pin.OUT)

#Foil touch sensor
touch_pad = TouchPad(Pin(15, mode=Pin.IN))

#Buzzer
buzzer = Pin(18, Pin.OUT)
MORSE_UNIT_MS = 50

#Morse
DASH_THRESHOLD = 3500
PAUSE_THRESHOLD = 5000
WORD_THRESHOLD = 12000

hold_duration = 0
pause_duration = 0
paused = False
finished_word = False
signals = []

#Network
sta_if = network.WLAN(network.STA_IF); sta_if.active(True)

if (not sta_if.isconnected()):
    sta_if.connect("wifi_SSID_here", "wifi_password_here")
    time.sleep(10)

print("Connected to internet") if sta_if.isconnected() else print("Network error")

### FUNCTIONS ###

def translate_signals(signals):
    message = "".join(signals).strip()
    print(message)
    
    send_to_oled(message)
    
    if (message == "--- ... ---"):
        sos()
    elif (message == ".- .--. .."):
        get_cat_fact()
    elif (message == "-- . --- .--"):
        hiss()
    else:
        meow()
        
def clear_oled():
    oled.fill(0)
    oled.show()

def send_to_oled(display_string):
    clear_oled()
    oled.text(display_string, 0, 0)
    oled.show()
        
def show_credits():
    #screen 128px wide, chars 8px wide
    clear_oled()
    oled.text("MorseCat", 32, 10) #32-64-32
    oled.text("By", 56, 20) #56-16-56
    oled.text("Nicholas Romeo", 8, 30) #8-112-8
    oled.text("2023", 48, 40) #48-32-48
    oled.show()
    
    time.sleep(5)

def sos():
    send_to_oled("Help is coming!")
    
    for x in range(10):
        led_red_1.value(1)
        led_red_2.value(1)
        time.sleep_ms(500)
        led_red_1.value(0)
        led_red_2.value(0)
        time.sleep_ms(500)
    
def cat_fact_loading():
    clear_oled()
    oled.text("Getting", 36, 20) #36-56-36
    oled.text("Cat", 52, 30) #52-24-52
    oled.text("Fact", 48, 40) #48-32-48
    oled.show()

def get_cat_fact():
    cat_fact_loading()
    
    cat_fact = ""
    while (len(cat_fact) > 96 or len(cat_fact) == 0):
        try:
            request = urequests.get("https://catfact.ninja/fact")
            if request.status_code == 200:
                cat_fact =request.json()["fact"]
            else:
                print(request.status_code)
                
        except Exception as e:
            print(e)
        
    lines = len(cat_fact) / 16
    start = 0
    end = 15
    position = 0
    
    clear_oled()
        
    while (lines > 0):
        oled.text(cat_fact[start:end], 0, position)
        lines -=1
        start += 16
        end += 17
        position += 10
        
    oled.text(cat_fact, 0, 0)
    oled.show()
        
# Morse timing (https://morsecode.world/international/timing.html)

def dit():
    buzzer.value(1)
    led_green_1.value(1)
    led_green_2.value(1)
    
    time.sleep_ms(MORSE_UNIT_MS) # 1 unit
    
    buzzer.value(0)
    led_green_1.value(0)
    led_green_2.value(0)
    
def dah():
    buzzer.value(1)
    led_green_1.value(1)
    led_green_2.value(1)
    
    time.sleep_ms(3*MORSE_UNIT_MS) # 3 units
    
    buzzer.value(0)
    led_green_1.value(0)
    led_green_2.value(0)

def intra_character_pause():
    time.sleep_ms(MORSE_UNIT_MS) # 1 unit

def inter_character_pause():
    time.sleep_ms(3*MORSE_UNIT_MS) # 3 unit
    
def word_pause():
    time.sleep_ms(7*MORSE_UNIT_MS) # 7 unit

def meow():
    clear_oled()
    oled.text("-- . --- .--", 16, 10) # 16, 96, 16
    oled.text("meow", 48, 40) #48-32-48
    oled.show()
    morse_to_buzzer("-- . --- .--")
    
def hiss():
    clear_oled()
    oled.text(".... .. ... ...", 4, 10) # 4, 120, 4
    oled.text("-.-.--", 40, 20) # 40-48-40
    oled.text("hiss!", 44, 40) # 44-40-44
    oled.show()
    morse_to_buzzer(".... .. ... ... -.-.--")
    
def morse_to_buzzer(code):
    characters = code.split(" ")
    
    for character in characters:
        for sound in character: 
            if (sound == "."):
                dit()
            elif (sound == "-"):
                dah()
            
            intra_character_pause()
        
        inter_character_pause()

### PROGRAM LOGIC ###

show_credits()
meow()

while True:
    touch_value = touch_pad.read()
    
    if (touch_value < 300):
        buzzer.value(1)
        led_blue_1.value(1)
        led_blue_2.value(1)
        
        hold_duration += 1
        pause_duration = 0
        
        paused = False
        finished_word = False
    else:
        buzzer.value(0)
        led_blue_1.value(0)
        led_blue_2.value(0)
        
        if (hold_duration > DASH_THRESHOLD):
            signals.append("-")
            send_to_oled("".join(signals).strip())
            print("-")
        elif (hold_duration > 0):
            signals.append(".")
            send_to_oled("".join(signals).strip())
            print(".")
    
        if (pause_duration > PAUSE_THRESHOLD):
            if (paused == False):
                print("space")
                
                if (signals and signals != [" "]):
                    signals.append(" ")
                    send_to_oled("".join(signals).lstrip())
                    paused = True
        
        if (pause_duration > WORD_THRESHOLD):
            if (finished_word == False):
                if (signals and signals != [" "]):
                    translate_signals(signals)
                    signals = []                    
                    finished_word = True
        
        pause_duration += 1
        hold_duration = 0