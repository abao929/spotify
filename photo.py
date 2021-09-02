import cv2
import os
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import math
import time

def open_images(folder):
    images = []
    for filename in os.listdir(folder):
        img = cv2.imread(os.path.join(folder,filename))
        if img.shape == (640, 640, 3):
            images.append([img, filename.split("cover")[1].split(".jpg")[0]])
    return images

FOLDER = ''
IMAGES = []
IMAGES = open_images(FOLDER)

def get_dominant_color(image, k=4, image_processing_size = None):
    if image_processing_size is not None:
        image = cv2.resize(image, image_processing_size, 
                            interpolation = cv2.INTER_AREA)
    image = image.reshape((image.shape[0] * image.shape[1], 3))
    clt = KMeans(n_clusters = k)
    labels = clt.fit_predict(image)
    label_counts = Counter(labels)
    dominant_color = clt.cluster_centers_[label_counts.most_common(1)[0][0]]
    return list(dominant_color)

def get_dominant_color2(image, k=4):
    clt = KMeans(n_clusters = k)
    labels = clt.fit_predict(image)
    label_counts = Counter(labels)
    dominant_color = clt.cluster_centers_[label_counts.most_common(1)[0][0]]
    return list(dominant_color)

def hsv2bgr(hsv):
    h = hsv[0] * 2
    s = hsv[1] / 255
    v = hsv[2] / 255
    c = s * v
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v-c
    if h < 60:
        bgr0 = [0, x, c]
    elif h < 120:
        bgr0 = [0, c, x]
    elif h < 180:
        bgr0 = [x, c, 0]
    elif h < 240:
        bgr0 = [c, x, 0]
    elif h < 300:
        bgr0 = [c, 0, x]
    elif h <= 360:
        bgr0 = [x, 0, c]
    bgr = list((y + m)*255 for y in bgr0)
    return bgr

def sort_color(k, size):
    colors = []
    bw = []
    count = 0
    for x in range(len(IMAGES)):
        hsv = cv2.cvtColor(IMAGES[x][0], cv2.COLOR_BGR2HSV)
        color = get_dominant_color(hsv, k, size)
        temp = (x, color)
        if color[1] > 32 and color[2] > 65:
            colors.append(temp)
        else:
            bw.append(temp)
        """ bgr = hsv2bgr(color)
        hsv = [color[0]*2, color[1]/2.55, color[2]/2.55]
        info_img = np.full((160, 160, 3), bgr)
        text =  ' '.join(str(int(round(y)))  for y in hsv)
        text2 = ' '.join(str(int(round(y))) for y in bgr)
        info_img = cv2.putText(info_img, text, (5, 40), cv2.FONT_HERSHEY_PLAIN, 1.4, (0, 0, 0), 2)
        info_img = cv2.putText(info_img, text2, (5, 80), cv2.FONT_HERSHEY_PLAIN, 1.4, (0, 0, 0), 2)
        info_img = cv2.putText(info_img, f'{IMAGES[x][1]} {x}', (5, 120), cv2.FONT_HERSHEY_PLAIN, 1.4, (0, 0, 0), 2)
        info_img = cv2.putText(info_img, f'{x}', (5, 80), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 2)
        IMAGES[x][0] = np.hstack((IMAGES[x][0], info_img)) """
    return (sorted(colors, key=lambda i: i[1][0]), sorted(bw, key=lambda i: i[1][2], reverse=True))

""" def sort_border(s, k):
    colors = []
    bw = []
    count = 0
    for i in IMAGES:
        hsv = cv2.cvtColor(i, cv2.COLOR_BGR2HSV)
        border = np.concatenate((i[:s].reshape(640*s, 3), i[-s:].reshape(640*s, 3), i[s:-s,:s].reshape((640-2*s)*s, 3), i[s:-s,-s:].reshape((640-2*s)*s, 3)))
        color = get_dominant_color2(border, k)
        temp = (count, color)
        if color[1] > 30 and color[2] > 77:
            colors.append(temp)
        else:
            bw.append(temp)
        count += 1
    return (sorted(colors, key=lambda i: i[1][0]), sorted(bw, key=lambda i: i[1][2], reverse=True)) """

def make_mosaich(indices_tuple, width):
    indices = [x[0] for x in indices_tuple]
    first_row = IMAGES[indices[0]][0]
    upper = math.floor(len(indices_tuple) / width)
    for x in range(1, width):
        first_row = np.hstack((first_row, IMAGES[indices[x]][0]))
    for x in range(1, upper):
        temp = IMAGES[indices[x*width]][0]
        for y in range(1, width):
            temp = np.hstack((temp, IMAGES[indices[x*width + y]][0]))
        first_row = np.vstack((first_row, temp))
    return first_row

def make_mosaicv(indices_tuple, height):
    indices = [x[0] for x in indices_tuple]
    first_row = IMAGES[indices[0]][0]
    upper = math.floor(len(indices_tuple) / height)
    for x in range(1, height):
        first_row = np.vstack((first_row, IMAGES[indices[x]][0]))
    for x in range(1, upper):
        temp = IMAGES[indices[x*height]][0]
        for y in range(1, height):
            temp = np.vstack((temp, IMAGES[indices[x*height + y]][0]))
        first_row = np.hstack((first_row, temp))
    return first_row

""" def test_border(s):
    for x in range(0, 30):
        i = IMAGES[x]
        hsv = cv2.cvtColor(i, cv2.COLOR_BGR2HSV)
        border = np.concatenate((i[:s].reshape(640*s, 3), i[-s:].reshape(640*s, 3), i[s:-s,:s].reshape((640-2*s)*s, 3), i[s:-s,-s:].reshape((640-2*s)*s, 3)))
        color = get_dominant_color2(border, 3)
        cv2.imwrite('mosaics/test.jpg', np.stack((i, np.full((640, 640, 3), color))))
        time.sleep(2) """

#test_border(40)
def resort_colors(c, w):
    n = math.floor(len(c) / w)
    temp = []
    for x in range(0, n):
        temp.extend(sorted(c[x*w:(x+1)*w], key=lambda i: i[1][1], reverse=True))
    temp.extend(c[n*w:])
    return temp

def combine_mosaic(c, b, h, w):
    result = np.hstack((make_mosaicv(c, h), make_mosaicv(b, h)))
    #new_c = resort_colors(c, w)
    #result = make_mosaicv(new_c, w)
    print(f'{result.shape[0]/640} by {result.shape[1]/640}')  
    cv2.imwrite('', result)

def sat_mosaic(c, b, h, w):
    c_width = w - math.floor(len(b) / h)
    c = c[:c_width*h]
    c = resort_colors(c, h)
    result = np.hstack((make_mosaicv(c, h),  make_mosaicv(b, h)))
    print(f'{result.shape[0]/640} by {result.shape[1]/640}')  
    cv2.imwrite('', result)

colors, bw = sort_color(5, (160, 160))
combined = colors + bw
print(f'colors is {len(colors)}, bw is {len(bw)}, sum is {len(combined)}, total should be {len(IMAGES)}')
#print(f'colors is {len(colors)}, bw is {len(bw)}, sum is {len(colors) + len(bw)}, total should be {len(IMAGES)}')

sat_mosaic(colors, bw, 27, 36)
