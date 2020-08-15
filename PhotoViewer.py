#!/usr/bin/env python

# Viewer for best rated photos
# Author: Anthony VH
# Date:   June 2014

import sys        # Exit function
import os         # System function
import math       # Size calculations

from PyQt4 import QtGui, QtCore # GUI
import pyexiv2

import Glicko

class MainWindow (QtGui.QMainWindow):
  # Class variables
  appBasePath = os.path.dirname(os.path.realpath(__file__))

  def __init__ (self):
    super(MainWindow, self).__init__()

    # Setup variables
    self.ratingTuples = []
    self.isRating = 0
    self.curPos = 0

    self.curDir = ""

    self.curPixmap = None
    self.resizedPixmap = None

    # Initialze GUI
    self.initGUI()

  def initGUI (self):
    # General geometry
    self.showMaximized()

    # Titlebar
    self.setWindowTitle("Tony's Photo Viewer")
    self.setWindowIcon(QtGui.QIcon(os.path.join(self.appBasePath, "icon-camera.png")))

    # Create widgets
    self.centralWidget = QtGui.QWidget()
    self.vBox = QtGui.QVBoxLayout()

    self.photoBox = QtGui.QLabel()
    self.photoBox.setAlignment(QtCore.Qt.AlignCenter)
    self.photoBox.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    self.photoBox.setStyleSheet("border: 0px solid #070; color: #777")

    self.lblInfo = QtGui.QLabel()
    self.lblInfo.setAlignment(QtCore.Qt.AlignHCenter)
    self.lblInfo.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
    self.lblInfo.setStyleSheet("color: #777;")
    self.lblInfo.setText("Info")

    self.vBox.addWidget(self.photoBox)
    self.vBox.addWidget(self.lblInfo)

    self.centralWidget.setLayout(self.vBox)
    self.setCentralWidget(self.centralWidget)

    # Create actions
    self.exitAction = QtGui.QAction('E&xit', self)
    self.exitAction.setShortcut('Ctrl+X')
    self.exitAction.setStatusTip('Exit application')
    self.exitAction.triggered.connect(self.exitApp)

    self.viewAction = QtGui.QAction('Show &best photos', self)
    self.viewAction.setShortcut('Ctrl+B')
    self.viewAction.setStatusTip("Show best rated photos in a directory")
    self.viewAction.triggered.connect(self.showBest)

    # Connect shortcuts to application
    self.addAction(self.viewAction)
    self.addAction(self.exitAction)

    ## Create menu bar
    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')

    fileMenu.addAction(self.viewAction)
    fileMenu.addSeparator()
    fileMenu.addAction(self.exitAction)

    #self.menuBar().setVisible(False)

  def exitApp (self):
    # Exit program
    QtGui.qApp.quit()

  def showBest (self):
    # Get directory
    self.curDir = str(QtGui.QFileDialog.getExistingDirectory(self, "View - Select directory"))

    if not self.curDir:
      return

    # Check if ratings file already exists
    ratingFilePath = os.path.join(self.curDir, "photoRaterDB.txt")
    ratingsExist = os.path.isfile(ratingFilePath)

    if ratingsExist:
      self.loadRatings()
    else:
      return

    # First sort by rating
    self.sortRatings()

    # Display picture
    self.updateDisplayedPhoto()

  def sortRatings (self):
    # Sort by perceived minimum rating (see Glicko system)
    self.ratingTuples = sorted(self.ratingTuples, key=lambda curTuple: Glicko.getMinimalRating(curTuple[1], curTuple[2]), reverse=True)

  def getFileList (self, fileDir):
    # Get all images files in directory
    imgTypes = [ ".jpg", ".JPG", ".jpeg", ".JPEG" ]
    imgFiles = [ os.path.relpath(os.path.join(dp, f), fileDir) for dp, dn, fs in os.walk(fileDir) for f in fs if os.path.splitext(f)[1] in imgTypes]

  def loadRatings (self):
    # Make sure ratings file exists
    ratingFilePath = os.path.join(self.curDir, "photoRaterDB.txt")
    if not os.path.isfile(ratingFilePath):
      return

    # Read out rating file
    fp = open(ratingFilePath)

    # Clear current tuples
    self.ratingTuples = []

    # Parse lines
    for line in fp.readlines():
      parts = line.split(";")

      # Make sure file exists
      curFile = str(parts[0])
      curFilePath = os.path.join(self.curDir, curFile)
      if not os.path.isfile(curFilePath):
        continue

      curMu = float(parts[1])
      curSigma = float(parts[2])

      # Add tuple to list
      self.ratingTuples.append((curFile, curMu, curSigma))

    fp.close()

  def updateDisplayedPhoto (self):
    # Exit if no pictures
    if len(self.ratingTuples) == 0:
      return

    # Update photo - First check if picture exists
    imgPath = os.path.join(self.curDir, self.ratingTuples[self.curPos][0])

    if os.path.isfile(imgPath):
      # Create image
      self.curPixmap = QtGui.QPixmap(imgPath)

      # Rotate if necessary
      try:
        imgMetadata = pyexiv2.ImageMetadata(imgPath)
        imgMetadata.read()
        imgOrientation = int(imgMetadata['Exif.Image.Orientation'].raw_value)

        if imgOrientation in [ 6, 8 ]:
          self.curPixmap = self.curPixmap.transformed(QtGui.QTransform().rotate(90 * (imgOrientation - 5)))
      except KeyError:
        pass

    # Update display
    self.repaint()

  def paintEvent(self, e):
    qp = QtGui.QPainter()
    qp.begin(self)
    self.repaintPhoto(qp)
    qp.end()

  def repaintPhoto (self, qp):
    # Exit if no picture shown
    if not self.curPixmap:
      return

    # Find best way to rescale
    cSize = self.photoBox.size()
    cw = cSize.width()
    ch = cSize.height()

    pw = self.curPixmap.width()
    ph = self.curPixmap.height()

    if (pw > cw and ph > ch and pw/cw > ph/ch) or (pw > cw and ph <= ch) or (pw < cw and ph < ch and cw/pw < ch/ph):
        self.resizedPixmap = self.curPixmap.scaledToWidth(cw, QtCore.Qt.SmoothTransformation)
    elif (pw > cw and ph > ch and pw/cw <= ph/ch) or (ph > ch and pw <= cw) or (pw < cw and ph < ch and cw/pw > ch/ph):
        self.resizedPixmap = self.curPixmap.scaledToHeight(ch, QtCore.Qt.SmoothTransformation)

    # Calculate drawing position
    drawOffset = self.photoBox.mapToParent(self.photoBox.pos())
    drawExtraOffset = QtCore.QPoint(-9, 18) # With menu shown
    drawExtraOffset = QtCore.QPoint(-9, -9) # Without menu shown
    x = (cw - self.resizedPixmap.width()) / 2 + drawOffset.x() + drawExtraOffset.x()
    y = (ch - self.resizedPixmap.height()) / 2 + drawOffset.y() + drawExtraOffset.y()

    # Draw picture
    qp.drawPixmap(x, y, self.resizedPixmap)

    # Draw border
    borderPen = QtGui.QPen(QtGui.QColor(80, 80, 80))
    qp.setPen(borderPen)
    qp.drawRect(x, y, self.resizedPixmap.width(), self.resizedPixmap.height())

    # Update label text
    self.lblInfo.setText("{curPos:d} of {totNum:d} - {fileName:s}".format(curPos = self.curPos + 1, totNum = len(self.ratingTuples), fileName = self.ratingTuples[self.curPos][0]))

  def keyPressEvent(self, event):
    # Capture key presses
    key = event.key()

    # Change picture index if left or right is pressed
    if key == QtCore.Qt.Key_Left:
      self.curPos -= 1
      if self.curPos < 0:
        self.curPos = len(self.ratingTuples) - 1
    elif key == QtCore.Qt.Key_Right:
      self.curPos += 1
      if self.curPos >= len(self.ratingTuples):
        self.curPos = 0

    # Update display
    self.updateDisplayedPhoto()

    super(MainWindow, self).keyPressEvent(event)

def main():
  app = QtGui.QApplication(sys.argv)
  mw = MainWindow()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
