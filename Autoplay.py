from collections import deque
from pykeyboard import PyKeyboard
from pymouse import PyMouse
from PIL.ImageGrab import grab
from PIL import ImageFilter
from msvcrt import getch
from sklearn.cluster import KMeans
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


def find_rex(mouse, keyboard):
    mouse.click(10, 100)
    time.sleep(0.1)
    keyboard.tap_key(keyboard.up_key)
    time.sleep(0.5)
    img = grab()
    img = img.filter(ImageFilter.MinFilter(3))
    rex_on_ground = np.array(img)[:, :, 0] / 128
    time.sleep(0.1)
    keyboard.tap_key(keyboard.up_key)
    time.sleep(0.05)
    img = grab()
    img = img.filter(ImageFilter.MinFilter(3))
    rex_jump = np.array(img)[:, :, 0] / 128
    diff = zip(*np.where(rex_on_ground != rex_jump))
    km = KMeans(n_clusters=2).fit(diff)
    centers = [list(s) for s in km.cluster_centers_[:, [1, 0]]]
    centers.sort()
    x, y = [int(s) for s in centers[0]]
    time.sleep(1)
    radius = 50
    rex_pixels = np.array(zip(*np.where(rex_on_ground[y-radius:y+radius, x-radius:x+radius] != 1)))
    rex_center = rex_pixels.mean(axis=0)
    dy, dx = [int(round(s - radius)) for s in rex_center]
    cy = y + dy
    cx = x + dx
    w = min(800, rex_on_ground.shape[1] - cx)
    return cx, cy, w


def find_obstacle(cx, cy, w):
    img = np.array(grab())[cy - 50:cy + 50, cx:cx + w, 0] / 128
    if img.sum() * 2 > w * 100:
        img = 1 - img
    hist = img.sum(axis=0)
    obstacles = []
    owner = 'rex'
    count = 0
    for i in xrange(w):
        s = hist[i]
        if s > 10:
            count = 0
            if owner == 'desert':
                owner = 'obstacle'
                left = i
        elif owner != 'desert':
            count += 1
            if count >= 15:
                count = 0
                if owner == 'obstacle':
                    obstacles.append([left, i-count, 100])
                owner = 'desert'
    for obs in obstacles:
        left, right = obs[:2]
        h_hist = img[:, left:right].sum(axis=1)
        count = 0
        for i in xrange(100-1, -1, -1):
            if h_hist[i] > 5:
                if count > 5:
                    height = 100 - i + count
                    obs[2] = height
                    break
                count += 1
            else:
                count = 0
    return obstacles


def autoplay(imgnum):
    keyboard = PyKeyboard()
    mouse = PyMouse()
    mouse.click(10, 100)
    cx, cy, w = find_rex(mouse, keyboard)
    time.sleep(1)

    prev_dist = None
    speed_record = deque([400] * 7)
    start_t = time.time()
    prev_t = 0
    n_jump = 0
    obstacles = None
    n_retry = 0
    while True:
        snap = obstacles
        obstacles = find_obstacle(cx, cy, w)
        # print 'obstacles =', obstacles
        if not obstacles:
            prev_dist = None
            time.sleep(0.1)
        else:
            current_t = time.time() - start_t
            start, end, height = obstacles[0]
            if prev_dist is not None:
                speed = (prev_dist - start) / (current_t - prev_t)
                if speed < 1:
                    print 'oops'
                    print snap
                    n_retry += 1
                    if n_retry > 3:
                        return time.time() - start_t
                    time.sleep(0.005 * n_retry)
                    continue
                speed_record.popleft()
                speed_record.append(speed)
            prev_dist = start
            prev_t = current_t
            ave_speed = (sum(speed_record) - max(speed_record) - min(speed_record)) / 5.0
            # print 'speed =', ave_speed
            if start < ave_speed * 0.36:
                if height < 60:
                    n_jump += 1
                    keyboard.tap_key(keyboard.up_key)  # jump
                    # print 'jump', start, end, height
                    if n_jump < 30 and end - start > 50:
                        time.sleep(end / ave_speed - 0.05 + (30-n_jump) * 0.005)
                    else:
                        time.sleep(end / ave_speed - 0.05)
                    keyboard.press_key(keyboard.down_key)  # land
                    time.sleep(0.13)
                    keyboard.release_key(keyboard.down_key)
                    prev_dist = None
                else:
                    keyboard.press_key(keyboard.down_key)
                    # print 'dodge', start, end, height
                    time.sleep(end / ave_speed + 0.01)
                    keyboard.release_key(keyboard.down_key)
                    prev_dist = None


for i in range(10):
    print autoplay(i)
    time.sleep(10)
