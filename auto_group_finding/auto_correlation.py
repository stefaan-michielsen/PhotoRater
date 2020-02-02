#!/usr/bin/env python

from PIL import Image,ImageMath
import numpy
#im = Image.open("../../../2019-08-09 Silsomhof/IMG_2720.JPG").convert('L') #open and keep only grayscale
#im2 = Image.open("../../../2019-08-09 Silsomhof/IMG_2721.JPG").convert('L') #open and keep only grayscale
#
#out = ImageMath.eval("convert((a-b), 'L')", a=im, b=im2)
#out.save("test1.png")

def getNumber(file1, file2):
    size = 32, 32
    
    im  = Image.open(file1).convert('L') #open and keep only grayscale
    im2 = Image.open(file2).convert('L') #open and keep only grayscale
    im.thumbnail(size, Image.ANTIALIAS)
    im2.thumbnail(size, Image.ANTIALIAS)
    
    out = ImageMath.eval("convert((a-b), 'L')", a=im, b=im2)
    temp=numpy.asarray(out)
    
    single_number = 0
    for onedarray in temp:
        for number in onedarray:
            single_number += number
    
    return single_number

def getNumber(file1, file2):
    size = 32, 32
    
    im  = Image.open(file1).convert('L') #open and keep only grayscale
    im2 = Image.open(file2).convert('L') #open and keep only grayscale
    im.thumbnail(size, Image.ANTIALIAS)
    im2.thumbnail(size, Image.ANTIALIAS)
    
    out = ImageMath.eval("convert((a-b), 'L')", a=im, b=im2)
    temp=numpy.asarray(out)
    
    single_number = 0
    for onedarray in temp:
        for number in onedarray:
            single_number += number
    
    return single_number


import os
filenames = []
for (root, dirname, files) in os.walk("../../../2019-04-11 Hallerbos/"):
    for filename in files:
        if filename[-3:] in ["jpg", "JPG"]: 
            filenames.append(root + "/" + filename)
        if filename[-4:] in ["jpeg", "JPEG"]: 
            filenames.append(root + "/" + filename)

print(filenames)

single_numbers = []
#for i in range(len(filenames)-1): # test with less images
for i in range(10):
    single_numbers.append((filenames[i], getNumber(filenames[i], filenames[i+1])))

sortedlist = sorted(single_numbers, key=lambda x: x[1])
for i in sortedlist:
    print(i)
