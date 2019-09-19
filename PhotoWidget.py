# Widget to show photo, rating and select button
# Author: Anthony VH
# Date:   June 2014

import os         # System function

from PyQt4 import QtGui, QtCore # GUI
import piexif

class PhotoWidget (QtGui.QWidget):
  def __init__(self, parent, widgetID):
    super(PhotoWidget, self).__init__()
    # Set variables
    self.parent = parent
    self.ID = widgetID
    self.imgPath = ""
    self.curPixmap = None
    self.initUI()

    self.maxWorkingH = 0
    self.maxWorkingW = 0

  def initUI(self):
    self.setMinimumSize(100, 200)

    # Create layout
    vbox = QtGui.QVBoxLayout()

    self.photoBox = QtGui.QLabel()
    self.photoBox.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
    self.photoBox.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
    self.photoBox.setStyleSheet("border: 1px solid #777; color: #777")

    self.btnSelect = QtGui.QPushButton()

    vbox.addStretch(1)
    vbox.addWidget(self.photoBox)
    vbox.addStretch(1)
    vbox.addWidget(self.btnSelect)

    self.setLayout(vbox)

    # Some basic GUI setup
    self.btnSelect.setText(self.getDecode())
    self.btnSelect.clicked.connect(self.doSelect)

  def doSelect (self):
    self.parent.updateRankings(self.ID + 1)

  def getDecode(self):
      return "Press %d" %(self.ID + 1)

  def getID (self):
    return self.ID

  def setImage (self, imgPath):
    # Update variable
    self.imgPath = imgPath

  def getImage (self):
    return self.imgPath

  def setAll (self, imgPath):
    self.setImage(imgPath)

    # Update photo - First check if picture exists
    if os.path.isfile(self.imgPath):
      # Create image
      self.curPixmap = QtGui.QPixmap(str(self.imgPath))

      # Scale and rotate if necessary
      imgX = 0
      imgY = 0
      imgOrientation = 1

      try:
          exif_dict = piexif.load(str(self.imgPath))
          print(str(self.imgPath))
          imgOrientation = exif_dict["0th"].pop(piexif.ImageIFD.Orientation)
      except KeyError:
          print("Couldn't get rotation info")
      except piexif._exceptions.InvalidImageDataError:
          print("This is not an image file " + self.imgPath)

      try:
          #imgX = exif_dict["0th"].pop(piexif.ImageIFD.ImageWidth)
          #imgY = exif_dict["0th"].pop(piexif.ImageIFD.ImageLength)
          imgX = self.curPixmap.width()
          imgY = self.curPixmap.height()
      except KeyError:
          print("Couldn't get pixel info")

      ratio = self.curPixmap.width()/self.curPixmap.height()

      (heightguess, widthguess) = self.guess_size(imgX, imgY, imgOrientation)


      if imgOrientation in [ 6, 8 ]: # portrait
        self.curPixmap = self.curPixmap.transformed(QtGui.QTransform().rotate(90 * (imgOrientation - 5)))

      self.curPixmap = self.curPixmap.scaledToWidth(widthguess, QtCore.Qt.SmoothTransformation)
      print ("Using width "+ str(widthguess))
    else:
        print("Can't open "+ self.imgPath )
    # Update display
    self.repaint()

  def guess_size(self, x, y, imgOrientation):
      heightguess = self.photoBox.height()
      widthguess = self.photoBox.width()
      if heightguess < 30:
          # Sometimes the photobox is only 17 pixels high.
          #print("bumping up very small height")
          heightguess = int(self.photoBox.width()/(20/9)*self.num_images())

      #print ("fitting an image of (X x Y) %d x %d in a box of (w x d) %d x %d"
      #        %(x, y, widthguess, heightguess))
      if heightguess < self.maxWorkingH:
          heightguess = self.maxWorkingH

      imgX = x
      imgY = y
      if imgOrientation in [ 6, 8 ]: # portrait
          imgX = y
          imgY = x
      if (imgY/imgX) * widthguess > heightguess:
          widthguess = heightguess / (imgY/imgX)

      #print ("Fitted an image of (X x Y) %d x %d in a box of (w x d) %d x %d"
      #        %(imgX, imgY, widthguess, heightguess))
      if heightguess > self.maxWorkingH:
          self.maxWorkingH = heightguess
      if heightguess > self.maxWorkingH:
          self.maxWorkingW = widthguess
      return (heightguess , widthguess)



  def paintEvent(self, e):
    qp = QtGui.QPainter()
    qp.begin(self)
    self.drawWidget(qp)
    qp.end()

  def drawWidget(self, qp):
    # Show picture
    if self.curPixmap:
      self.photoBox.setPixmap(self.curPixmap)

  def num_images(self):
      return 3


class PhotoWidgetShowBest(PhotoWidget):
  def doSelect (self):
    self.parent.showNext()

  def num_images(self):
      return 1

class PhotoWidgetGroup (PhotoWidget):
  def getDecode(self):
      labels = { 0 : "Hoort bij deze groep -  (1)",
                 1 : "Nieuwe groep - (2)"}
      return labels[self.ID]

  def doSelect (self):
    self.parent.updateGroupRankings(self.ID)

  def getID (self):
    return self.ID

  def num_images(self):
      return 2

class PhotoWidgetGroupSort(PhotoWidget):
  def doSelect (self):
    self.parent.updateGroupSortRankings(self.ID + 1)

  def num_images(self):
      return 2

class PhotoWidgetPassFail (PhotoWidget):

  def initUI(self):
    self.setMinimumSize(100, 200)

    # Create layout
    vbox = QtGui.QVBoxLayout()

    self.photoBox = QtGui.QLabel()
    self.photoBox.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
    self.photoBox.setSizePolicy(QtGui.QSizePolicy.Preferred,
            QtGui.QSizePolicy.Maximum)
    self.photoBox.setStyleSheet("border: 1px solid #777; color: #777")

    self.btnGood = QtGui.QPushButton()
    self.btnBad = QtGui.QPushButton()

    vbox.addStretch(1)
    vbox.addWidget(self.photoBox)
    vbox.addStretch(1)
    vbox.addWidget(self.btnGood)
    vbox.addWidget(self.btnBad)

    self.setLayout(vbox)

    # Some basic GUI setup
    self.btnGood.setText("Goed - (1)")
    self.btnGood.clicked.connect(self.doSelect)
    self.btnBad.setText("Slecht - (2)")
    self.btnBad.clicked.connect(self.doNotSelect)

  def doSelect (self):
    self.parent.updatePassFailRankings(1)

  def doNotSelect (self):
    self.parent.updatePassFailRankings(2)

  def num_images(self):
      return 1
