import time

interval = 0.5

last_send = 0

for i in range(10):

    now = time.time()

    if now - last_send < interval:
        time.sleep(interval - (now - last_send))

    print("Sending frame:", i, time.strftime("%H:%M:%S"))

    last_send = time.time()