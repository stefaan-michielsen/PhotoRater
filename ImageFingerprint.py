import os
import sys
from wand.image import Image

class ImageFingerprint:

    def __init__(self, filename, img=None):
        self.filename = filename
        if (img == None):
            with Image(filename=filename) as img:
                print("Attempt to make %s an image" %filename)
                img.sample(160,160)
                img.modulate(saturation=100)
                img.blur(radius=3, sigma=99);
                img.normalize()
                img.equalize()
                img.sample(16,16)
                img.threshold()
                self.img = img.make_blob('MONO')
        else:
            if not os.path.exists(self.filename):
                raise FileNotFoundError("%s is not a valid file"%self.filename)
            self.img = bytes(img, 'utf-8')

    def fingerprint(self):
        return self.img

    def addmatches(self, byteinfo):
        match =  0
        intinfo = int(byteinfo)
        for i in range(8):
            # if xor returns 1, it means the fingerprint is different.
            # Zero return means match
            if not ((intinfo >> i) & 1):
                match += 1
        return match

    def match(self, other):
        xoring = [_a ^ _b for _a, _b in zip(self.fingerprint(), other.fingerprint())]
        matches = 0
        for byteinfo in xoring:
            matches = matches + self.addmatches(byteinfo)
        return matches/(16*16)
