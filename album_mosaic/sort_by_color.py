import argparse
import os
import cv2
import imutils
import imutils.paths as paths

import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import utils

class results_montage:
    """
    class to combine input images into a single image displaying a combined grid
    of the input images
    """

    def __init__(self, image_size, images_per_main_axis, num_results, by_row=True):
        # store the target image size and the number of images per row
        self.imageW = image_size[0]
        self.imageH = image_size[1]
        self.images_per_main_axis = images_per_main_axis
        self.by_row = by_row

        # allocate memory for the output image
        num_main_axis = -(-num_results // images_per_main_axis)  # ceiling division
        if by_row:
            self.montage = np.zeros(
                (num_main_axis * self.imageW, min(images_per_main_axis, num_results) * self.imageH, 3),
                dtype="uint8"
            )
        else:
            self.montage = np.zeros(
                (min(images_per_main_axis, num_results) * self.imageW, num_main_axis * self.imageH, 3),
                dtype="uint8"
            )

        # initialize the counter for the current image along with the row and column
        # number
        self.counter = 0
        self.row = 0
        self.col = 0

    def add_result(self, image, text=None, highlight=False):
        # check to see if the number of images per row/col has been met, and if so, reset
        # the row/col counter and increment the row
        if self.by_row:
            if self.counter != 0 and self.counter % self.images_per_main_axis == 0:
                self.col = 0
                self.row += 1
        else:
            if self.counter != 0 and self.counter % self.images_per_main_axis == 0:
                self.col += 1
                self.row = 0

        # resize the image to the fixed width and height and set it in the montage
        image = cv2.resize(image, (self.imageH, self.imageW))
        (startY, endY) = (self.row * self.imageW, (self.row + 1) * self.imageW)
        (startX, endX) = (self.col * self.imageH, (self.col + 1) * self.imageH)
        self.montage[startY:endY, startX:endX] = image

        # if the text is not None, draw it
        if text is not None:
            cv2.putText(self.montage, text, (startX + 5, startY + 13), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 0, 255), 2)

        # check to see if the result should be highlighted
        if highlight:
            cv2.rectangle(self.montage, (startX + 3, startY + 3), (endX - 3, endY - 3), (0, 255, 0), 4)

        if self.by_row:
            # increment the column counter
            self.col += 1
        else:
            # increment the row counter
            self.row += 1
        # increment total image counter
        self.counter += 1

def get_dominant_color(image, k=4, image_processing_size = None):
    """
    takes an image as input
    returns the dominant color of the image as a list
    
    dominant color is found by running k means on the 
    pixels & returning the centroid of the largest cluster

    processing time is sped up by working with a smaller image; 
    this resizing can be done with the image_processing_size param 
    which takes a tuple of image dims as input

    >>> get_dominant_color(my_image, k=4, image_processing_size = (25, 25))
    [56.2423442, 34.0834233, 70.1234123]
    """
    #resize image if new dims provided
    if image_processing_size is not None:
        image = cv2.resize(image, image_processing_size, 
                            interpolation = cv2.INTER_AREA)
    
    #reshape the image to be a list of pixels
    image = image.reshape((image.shape[0] * image.shape[1], 3))

    #cluster and assign labels to the pixels 
    clt = KMeans(n_clusters = k)
    labels = clt.fit_predict(image)

    #count labels to find most popular
    label_counts = Counter(labels)

    #subset out most popular centroid
    dominant_color = clt.cluster_centers_[label_counts.most_common(1)[0][0]]

    return list(dominant_color)

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", default='C:\\Users\\alexb\\Desktop\\Photos\\Photoshop\\mike mosaic',
                help="Path to the dir that contains the images to be sorted")
ap.add_argument("-o", "--output", default='sorted_images5.jpg',
                help="Path to the dir to write feature output to")
ap.add_argument("-k", "--clusters", type=int, default=3,
                help="# of clusters to use when finding image dominant color")
ap.add_argument("-s", "--sizeHeight", type=int, default=300,
                help="output height of sorted output image in pixels")
args = vars(ap.parse_args())

# grab the image paths from the dataset directory
def open_images(folder):
    images = []
    for filename in os.listdir(folder):
        img = cv2.imread(os.path.join(folder,filename))
        images.append(img)
    return images

FOLDER = 'C:\\Users\\alexb\\Desktop\\Photos\\Photoshop\\mike mosaic'
IMAGES = []
IMAGES = open_images(FOLDER)
filtered_images = list(filter(lambda img: img.shape == (640, 640, 3), IMAGES))
filtered_images = filtered_images[:900]
# init dominant color store
colors = []
# iterate over ims
for i in filtered_images:
    # read in image
    image = i
    # convert to hsv colorspace
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # get dominant color
    color = get_dominant_color(hsv_image, k=5,
                                     image_processing_size=(320, 320))
    # store color
    colors.append(color)

# sort colors by hue (return list of image inds sorted)
sorted_inds = sorted(range(len(colors)), key=lambda i: colors[i], reverse=True)
print

# use last image's shape as default shape for all images
image_shape = (640, 640)

# init montage
montage = results_montage(
    image_size=image_shape,
    images_per_main_axis=20,
    num_results=len(filtered_images),
    by_row=False
)

# iter over sorted image inds
for ind in sorted_inds:
    montage.add_result(filtered_images[ind])

# resize output collage
out = imutils.resize(montage.montage, height=1280)

# show image to screen
cv2.imshow('Sorted Images', out)
cv2.waitKey(0)
# save output
cv2.imwrite(args["output"], out)