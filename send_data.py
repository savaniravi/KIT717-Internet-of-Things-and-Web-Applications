from sense_emu import SenseHat
import time
import requests

sense = SenseHat()

light_threshold = 50  # default threshold
collision_threshold = 2.0  # final collision threshold
collision_state = "Normal"
power_state = "Normal"
setup_mode = False
last_button_time = time.time()
reporting_interval = 15  # 15 seconds for demo
last_report_time = time.time()

def send_data(light, power, collision, threshold):
    try:
        payload = {
            "light": light,
            "power": power,
            "collision": collision_state,
            "threshold": threshold,
            "device_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        r = requests.get("http://iotserver.com/logger.php", params=payload, timeout=5)
        if "ACK" not in r.text:
            sense.show_message("OFFLINE", scroll_speed=0.05, text_colour=[255, 0, 0])
    except:
        sense.show_message("OFFLINE", scroll_speed=0.05, text_colour=[255, 0, 0])

def flash_collision():
    for i in range(8):
        for j in range(8):
            sense.set_pixel(i, j, 255, 0, 0)
    time.sleep(0.3)
    sense.clear()
    time.sleep(0.3)

def update_light_state(light):
    if light < light_threshold - 1:
        sense.clear(255, 255, 0)
    else:
        sense.clear()

def check_collision():
    global collision_state
    acc = sense.get_accelerometer_raw()
    x = abs(round(acc['x'], 2))
    y = abs(round(acc['y'], 2))
    z = abs(round(acc['z'], 2))
    
    if collision_state != "Collision":
        if x > 1 or y > 1 or z > 1:
            time.sleep(0.1)
            acc2 = sense.get_accelerometer_raw()
            x2 = abs(round(acc2['x'], 2))
            y2 = abs(round(acc2['y'], 2))
            z2 = abs(round(acc2['z'], 2))
            if x2 > 1 or y2 > 1 or z2 > 1:
                collision_state = "Collision"
                print("Collision Detected!")

    return collision_state

def check_button_press():
    global collision_state, setup_mode, light_threshold, last_button_time
    for event in sense.stick.get_events():
        if event.action == "pressed":
            last_button_time = time.time()
            if event.direction == "middle":
                if collision_state == "Collision":
                    collision_state = "Normal"
                    print("Collision manually reset to Normal.")
                else:
                    setup_mode = not setup_mode
                    if not setup_mode:
                        send_data(sense.get_humidity(), sense.get_temperature(), collision_state, light_threshold)
            elif setup_mode:
                if event.direction == "up":
                    light_threshold += 1
                    sense.show_message(str(light_threshold))
                elif event.direction == "down":
                    light_threshold -= 1
                    sense.show_message(str(light_threshold))

def check_power(temp):
    if temp < 0:
        return "Brownout"
    elif temp > 100:
        return "Surge"
    else:
        return "Normal"

while True:
    temp = sense.get_temperature()
    humidity = sense.get_humidity()

    check_button_press()  # Always check button first

    if setup_mode and (time.time() - last_button_time) > 10:
        setup_mode = False
        send_data(humidity, temp, collision_state, light_threshold)

    if not setup_mode:
        if collision_state != "Collision":
            collision_state = check_collision()

        if collision_state == "Collision":
            flash_collision()

        power_state = check_power(temp)

        if power_state == "Normal":
            update_light_state(humidity)
        else:
            sense.clear()

        if time.time() - last_report_time > reporting_interval:
            send_data(humidity, temp, collision_state, light_threshold)
            last_report_time = time.time()

    time.sleep(0.1)
