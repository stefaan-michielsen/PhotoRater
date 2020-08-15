#!/usr/bin/env python


fingerprints = {}
import pickle
if os.path.exists("fingerprints.my"):
    with open("fingerprints.my", 'rb') as fh:
        fingerprints = pickle.load(fh)

for root, dirnames, filenames in os.walk('.'):
    for filename in filenames:
        if filename.lower().endswith('jpg'):
            if not filename in fingerprints.keys():
                fingerprints[filename] = ImageFingerprint(filename)

with open("fingerprints.my", 'wb') as fh:
    pickle.dump(fingerprints, fh, pickle.HIGHEST_PROTOCOL)


matchtable = {}

matchreq = 0.

groups = []
sorted_images = sorted(fingerprints.keys())

currentgroup = [sorted_images[0]]
for previous, current in zip(sorted_images, sorted_images[1:]):
    if fingerprints[previous].match(fingerprints[current]) > matchreq:
        currentgroup.append(current)
    else:
        groups.append(currentgroup)
        currentgroup = [current]
keepratio = len(sorted_images)/len(groups)
print("%g : Divided %i images over %i groups" %( matchreq, len(sorted_images), len(groups)))


# Expect 2-D array.
# an element in the first array represents a group
# The second layer contains a list of strings of images inside the same group.
def display(groups):
    from PIL import Image, ImageOps
    for group in groups:
        currentimages = []
        for image in group:
            print(image)
            image = Image.open(image)
            image = ImageOps.exif_transpose(image)
            currentimages.append(image)
        for i, currentimage in enumerate(currentimages):
            currentimage.thumbnail((512,512))
    
            
            currentimage.show(currentimage, "image%i"%i)
        input("Press Enter to continue...")


