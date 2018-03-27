import time
count = 0
alive = True
while alive:
    time.sleep(1)
    count += 1
    if count > 10:
        alive = False
        import os
        os.kill(os.getpid(), 9)