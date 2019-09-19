#!/usr/bin/python

# Photo grouper program using Glicko rating system
# Author: Anthony VH, Stefaan
# Date:   August 2019

import sys        # Exit function
import os         # System function
import math       # Size calculations
import random     # Random number generation


from PyQt4 import QtGui, QtCore # GUI

from PhotoWidget import PhotoWidget
import Glicko

class MainWindow (QtGui.QMainWindow):

  appBasePath = os.path.dirname(os.path.realpath(__file__))

  def __init__ (self):
    super(MainWindow, self).__init__()
    # Setup variables
    self.isRating = False
    self.ratingTuples = []
    self.shownIndices = []
    self.maxSigma = 0.0

    self.defaultMu = 1500.0
    self.defaultSigma = 350.0

    self.numRatings = 0

    # Initialze GUI
    self.initGUI()

  def initGUI (self):
    # General geometry
    self.showMaximized()

    # Set background color
    #self.setBackgroundColor(QtGui.QColor(255, 255, 255))

    # Titlebar
    self.setWindowTitle("Stefaan's Photo Grouper")
    self.setWindowIcon(QtGui.QIcon(os.path.join(self.appBasePath, "icon-camera.png")))

    # Create widgets
    self.centralWidget = QtGui.QWidget()

    hbox = QtGui.QHBoxLayout()
    self.photoWidgets = []

    for i in range(2):
      self.photoWidgets.append(PhotoWidget(self, i))
      hbox.addWidget(self.photoWidgets[i])

    self.centralWidget.setLayout(hbox)

    self.setCentralWidget(self.centralWidget)

    # Create actions
    self.groupingAction = QtGui.QAction('Start/continue &grouping', self)
    self.groupingAction.setShortcut('Ctrl+G')
    self.groupingAction.setStatusTip("Start or continue grouping photos in a directory")
    self.groupingAction.triggered.connect(self.startGrouping)

    #exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
    self.exitAction = QtGui.QAction('E&xit', self)
    self.exitAction.setShortcut('Ctrl+X')
    self.exitAction.setStatusTip('Exit application')
    self.exitAction.triggered.connect(self.exitApp)


    # Create menu bar
    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    fileMenu.addAction(self.groupingAction)
    fileMenu.addAction(self.exitAction)

    # Create status bar
    self.statusbar = QtGui.QStatusBar(self)
    self.setStatusBar(self.statusbar)
    self.statusBar().clearMessage()

  def exitApp (self):
    # Store progress
    if self.isRating:
      # Store everything
      self.storeRatings()

    # Exit program
    QtGui.qApp.quit()

  def getFileList (self, fileDir):
      # Get all images files in directory
      imgTypes = [ ".jpg", ".JPG", ".jpeg", ".JPEG" ]
      imgFiles = [ os.path.relpath(os.path.join(dp, f), fileDir) for dp, dn, fs in os.walk(fileDir) for f in fs if os.path.splitext(f)[1] in imgTypes]

      return imgFiles

  def updateDisplayedPhotos (self):
    # Select 3 pictures "at random"
    self.shownIndices = []
    self.shownIndices.append(0)
    self.shownIndices.append(1)
    self.photoWidgets[0].setAll(self.imgFiles[0])
    self.photoWidgets[1].setAll(self.imgFiles[1])

  def startGrouping(self):
    self.curDir = str(QtGui.QFileDialog.getExistingDirectory(self, "Start - Select directory"))
    self.imgFiles = self.getFileList(self.curDir)
    self.updateDisplayedPhotos()



def main():
  app = QtGui.QApplication(sys.argv)
  mw = MainWindow()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
