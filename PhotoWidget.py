# Widget to show photo, rating and select button
# Author: Anthony VH
# Date:   June 2014

import os         # System function

from PyQt5 import QtGui, QtCore # GUI
import pyexiv2

import Glicko

class PhotoWidget (QtGui.QWidget):
  def __init__(self, parent, widgetID):
    super(PhotoWidget, self).__init__()

    # Set variables
    self.parent = parent
    self.ID = widgetID

    self.imgPath = ""
    self.mu = 1500.0
    self.sigma = 350.0

    #self.curPixmap = QtGui.QPixmap()
    self.curPixmap = None

    self.initUI()

  def initUI(self):
    self.setMinimumSize(100, 200)

    # Create layout
    vbox = QtGui.QVBoxLayout()

    self.photoBox = QtGui.QLabel()
    self.photoBox.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
    self.photoBox.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
    self.photoBox.setStyleSheet("border: 1px solid #777; color: #777")

    self.lblInfo = QtGui.QLabel()
    self.lblInfo.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
    self.lblInfo.setStyleSheet("color: #777;")

    self.btnSelect = QtGui.QPushButton()

    vbox.addStretch(1)
    vbox.addWidget(self.photoBox)
    vbox.addWidget(self.lblInfo)
    vbox.addStretch(1)
    vbox.addWidget(self.btnSelect)

    self.setLayout(vbox)

    # Some basic GUI setup
    self.btnSelect.setText("Press {0:d}".format(self.ID + 1))
    self.btnSelect.clicked.connect(self.doSelect)

  def doSelect (self):
    self.parent.updateRankings(self.ID + 1)

  def getID (self):
    return self.ID

  def setMu (self, mu):
    self.mu = mu

  def setSigma (self, sigma):
    self.sigma = sigma

  def setImage (self, imgPath):
    # Update variable
    self.imgPath = imgPath

  def getImage (self):
    return self.imgPath

  def setAll (self, imgPath, mu, sigma):
    self.setImage(imgPath)
    self.setMu(mu)
    self.setSigma(sigma)

    # Update display
    self.repaint()

  def setAll (self, dataTuple):
    self.setImage(dataTuple[0])
    self.setMu(dataTuple[1])
    self.setSigma(dataTuple[2])

    # Update photo - First check if picture exists
    if os.path.isfile(self.imgPath):
      # Create image
      self.curPixmap = QtGui.QPixmap(self.imgPath)

      # Scale and rotate if necessary
      imgOrientation = 1

      try:
        imgMetadata = pyexiv2.ImageMetadata(self.imgPath)
        imgMetadata.read()
        imgOrientation = int(imgMetadata['Exif.Image.Orientation'].raw_value)
      except KeyError:
        pass

      if imgOrientation in [ 6, 8 ]:
        self.curPixmap = self.curPixmap.scaledToHeight(self.photoBox.width(), QtCore.Qt.SmoothTransformation)
        self.curPixmap = self.curPixmap.transformed(QtGui.QTransform().rotate(90 * (imgOrientation - 5)))
      else:
        self.curPixmap = self.curPixmap.scaledToWidth(self.photoBox.width(), QtCore.Qt.SmoothTransformation)

    # Update display
    self.repaint()

  def paintEvent(self, e):
    qp = QtGui.QPainter()
    qp.begin(self)
    self.drawWidget(qp)
    qp.end()

  def drawWidget(self, qp):
    # Show picture
    if self.curPixmap:
      self.photoBox.setPixmap(self.curPixmap)
#      self.photoBox.setPixmap(newPixmap)
#    else:
#      self.photoBox.setText("Empty")

    # Update label
    strInfo = QtCore.QString()
    strInfo.append(QtCore.QChar(0x03BC))
    strInfo.append(": {0:.2f} - ".format(self.mu))
    strInfo.append(QtCore.QChar(0x03C3))
    strInfo.append(": {0:.2f}".format(self.sigma))
    strInfo.append("\nR: {0:.0f}".format(Glicko.getMinimalRating(self.mu, self.sigma)))

    self.lblInfo.setText(strInfo)

    # Don't show text, it influences decission
    self.lblInfo.setVisible(False)
