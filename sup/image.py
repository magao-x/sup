import numpy as np

class BogusImageStream:
    def __init__(self, name):
        self.name = name
        img = np.zeros(128, 128)
        img = np.zeros((128, 128))
        img[20:100,54:60] = 1
        img[94:100,54:100] = 1
        img[60:66,54:85] = 1
        self.fake_image = img
    def grab_latest(self):
        return np.copy(img)

try:
    from magpyx.utils import ImageStream
except ImportError:
    ImageStream = BogusImageStream