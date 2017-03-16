from collections import deque
from pykeyboard import PyKeyboard
from pymouse import PyMouse
from PIL.ImageGrab import grab
from msvcrt import getch
import numpy as np
import time


def set_params(mouse, cmd_str='wsad', pace=10, xx=200, yy=200, step=0):
    if step:
        print 'Step', step
    print 'use {}(up){}(down){}(left){}(right) keys to move mouse to T-Rex then hit enter to start'.format(*cmd_str)
    while True:
        print xx, yy
        mouse.move(xx, yy)
        c = getch().decode()
        if c == cmd_str[0]:
            yy -= pace
        elif c == cmd_str[1]:
            yy += pace
        elif c == cmd_str[2]:
            xx -= pace
        elif c == cmd_str[3]:
            xx += pace
        elif c == '\r':
            return xx, yy
        else:
            break


def find_obstacle(cx, cy, jx, jy):
    img = np.array(grab())[cy - 50:cy + 50, cx:cx + 800] / 128
    if img.sum() > 120000:
        img = 1 - img
    hist = img[20:60, :, 0].sum(axis=0)
    start, end = None, None
    count = 0
    for i in xrange(30, 800):
        s = hist[i]
        if s > 10:
            if img[jy-cy+50, jx-cx, 0] == 1:
                return None
            if start is None:
                start = i
                end = i
            else:
                end = i
        elif start is not None:
            count += 1
            if count >= 15:
                break
    return start, end


def autoplay(imgnum):
    keyboard = PyKeyboard()
    mouse = PyMouse()
    # cx, cy = set_params(mouse)
    cx, cy = 970, 250
    jx, jy = 1290, 210
    mouse.click(10, 100)
    time.sleep(0.1)
    keyboard.tap_key(keyboard.up_key)
    time.sleep(3)
    # keyboard.tap_key(keyboard.alt_key)  # pause

    prev_dist = None
    speed_record = deque([400, 400, 400])
    start_t = time.time()
    prev_t = 0
    while True:
        keyboard.press_key(keyboard.down_key)
        obstacle = find_obstacle(cx, cy, jx, jy)
        if obstacle is None:
            print 'oops'
            break
        elif obstacle[0] is None:
            prev_dist = None
            time.sleep(0.1)
        else:
            current_t = time.time() - start_t
            start, end = obstacle
            if prev_dist is not None:
                speed = (prev_dist - start) / (current_t - prev_t)
                speed_record.popleft()
                speed_record.append(speed)
            prev_dist = start
            prev_t = current_t
            ave_speed = sum(speed_record) / 3.0
            print 'speed =', ave_speed
            if start < ave_speed * 0.2 + 60:
                keyboard.release_key(keyboard.down_key)
                keyboard.tap_key(keyboard.up_key)  # jump
                print 'jump', start, end/ave_speed
                time.sleep(end / ave_speed)
                prev_dist = None


for i in range(1):
    autoplay(i)
    time.sleep(1)
