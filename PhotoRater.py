#!/usr/bin/python

# Photo rater program using Glicko rating system
# Author: Anthony VH
# Date:   June 2014

import sys        # Exit function
import os         # System function
import math       # Size calculations
import random     # Random number generation


from PyQt4 import QtGui, QtCore # GUI

from PhotoWidget import PhotoWidget
import Glicko

class MainWindow (QtGui.QMainWindow):
  # Class variables
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
    self.setWindowTitle("Tony's Photo Rater")
    self.setWindowIcon(QtGui.QIcon(os.path.join(self.appBasePath, "icon-camera.png")))

    # Create widgets
    self.centralWidget = QtGui.QWidget()

    hbox = QtGui.QHBoxLayout()
    self.photoWidgets = []

    for i in range(3):
      self.photoWidgets.append(PhotoWidget(self, i))
      hbox.addWidget(self.photoWidgets[i])

    self.centralWidget.setLayout(hbox)

    self.setCentralWidget(self.centralWidget)

    # Create actions
    #exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
    self.exitAction = QtGui.QAction('E&xit', self)
    self.exitAction.setShortcut('Ctrl+X')
    self.exitAction.setStatusTip('Exit application')
    self.exitAction.triggered.connect(self.exitApp)

    self.ratingAction = QtGui.QAction('Start/continue &rating', self)
    self.ratingAction.setShortcut('Ctrl+R')
    self.ratingAction.setStatusTip("Start or continue rating photos in a directory")
    self.ratingAction.triggered.connect(self.startRating)

    self.updateAction = QtGui.QAction('&Update file list and rate', self)
    self.updateAction.setShortcut('Ctrl+U')
    self.updateAction.setStatusTip("Update list of files in directory and continue rating")
    self.updateAction.triggered.connect(self.startRatingWithUpdate)

    self.storeAction = QtGui.QAction('&Store current ratings', self)
    self.storeAction.setShortcut('Ctrl+S')
    self.storeAction.setStatusTip("Store current ratings to file")
    self.storeAction.triggered.connect(self.storeRatings)

    self.bestAction = QtGui.QAction('Show &best', self)
    self.bestAction.setShortcut('Ctrl+B')
    self.bestAction.setStatusTip("Show a list of the best pictures")
    self.bestAction.triggered.connect(self.showBest)

    # Create menu bar
    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')

    fileMenu.addAction(self.ratingAction)
    fileMenu.addAction(self.updateAction)
    fileMenu.addAction(self.storeAction)
    fileMenu.addSeparator()
    fileMenu.addAction(self.bestAction)
    fileMenu.addSeparator()
    fileMenu.addAction(self.exitAction)

    self.storeAction.setVisible(False)
    self.bestAction.setVisible(False)

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

  def showBest (self):
    print("")
    print("[Best photographs]")

    if not self.isRating:
      print("Start rating a directory first!")
      return

    # First sort by rating
    self.sortRatings()

    # Print the best 10 photos
    for i in range(10):
      curTuple = self.ratingTuples[i]
      print("[{0:2d}] {1:s} (R: {2:4.0f})".format(i + 1, curTuple[0], Glicko.getMinimalRating(curTuple[1], curTuple[2])))

  def sortRatings (self):
    # Sort by perceived minimum rating (see Glicko system)
    self.ratingTuples = sorted(self.ratingTuples, key=lambda curTuple: Glicko.getMinimalRating(curTuple[1], curTuple[2]), reverse=True)

  def getFileList (self, fileDir):
      # Get all images files in directory
      imgTypes = [ ".jpg", ".JPG", ".jpeg", ".JPEG" ]
      imgFiles = [ os.path.relpath(os.path.join(dp, f), fileDir) for dp, dn, fs in os.walk(fileDir) for f in fs if os.path.splitext(f)[1] in imgTypes]

      return imgFiles

  def startRatingWithUpdate (self):
    self.startRating(True)

  def startRating (self, updateFileList = False):
    # Store ratings (will check if already rating)
    self.storeRatings()

    # Get directory
    self.curDir = str(QtGui.QFileDialog.getExistingDirectory(self, "Start - Select directory"))

    if not self.curDir:
      return

    # Clear variables
    self.ratingTuples = []
    self.maxSigma = 0.0

    # Attempt to load existing ratings
    self.loadRatings()

    if updateFileList:
      # Get all images files in directory
      imgFiles = self.getFileList(self.curDir)

      # Append new tuple if file is not yet in list
      addedFiles = False
      fileList = [ curTuple[0] for curTuple in self.ratingTuples ]

      for curFile in imgFiles:
        # Skip if file is already in list
        if curFile in fileList:
          continue

        addedFiles = True

        # Add file to list
        curTuple = (curFile, self.defaultMu, self.defaultSigma)
        self.ratingTuples.append(curTuple)

      # Update max sigma
      if addedFiles:
        print("[Ratings] New files added!")
        self.maxSigma = max(self.maxSigma, self.defaultSigma)

    # Set flag
    self.isRating = True

    self.storeAction.setVisible(True)
    self.bestAction.setVisible(True)

    # Set the status bar text
    self.statusBar().showMessage("[Load] {numImg:d} images".format(numImg = len(self.ratingTuples)))

    # Start the ratings
    self.updateDisplayedPhotos()

  def loadRatings (self):
    # Make sure ratings file exists
    ratingFilePath = os.path.join(self.curDir, "photoRaterDB.txt")
    if not os.path.isfile(ratingFilePath):
      return

    # Read out rating file
    fp = open(ratingFilePath)

    # Clear current tuples
    self.ratingTuples = []
    self.maxSigma = 0.0

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
      self.maxSigma = max(self.maxSigma, curSigma)

    fp.close()

    print("[Load] Loaded existing ratings for {numImg:d} images".format(numImg = len(self.ratingTuples)))

  def storeRatings (self):
    if self.isRating:
      # Some debug output
      print("[Store] Sorting & storing rankings")

      # Sort so it's easy to manually find best photos
      self.sortRatings()

      # Create rating files
      ratingFilePath = os.path.join(self.curDir, "photoRaterDB.txt")
      fp = open(ratingFilePath, "w")
      for curTuple in self.ratingTuples:
        fp.write("{0:s};{1:.2f};{2:.2f}\n".format(curTuple[0], curTuple[1], curTuple[2]))
      fp.close()

  def updateDisplayedPhotos (self):
    # Select 3 pictures "at random"
    self.shownIndices = []

    for i in range(3):
      # Get "random" image and make sure it's not selected already
      while True:
        (randIndex, randTuple) = self.getRandomTuple()

        if not (randIndex in self.shownIndices):
          break

        print("[Rand] Image already selected!")

      # Add new filename to current file list
      #print randTuple
      self.shownIndices.append(randIndex)

      # Create absolute path for image display
      randTuple = ( os.path.join(self.curDir, randTuple[0]), randTuple[1], randTuple[2] )

      self.photoWidgets[i].setAll(randTuple)
      #self.photoWidgets[i].setAll(randTuple[0], randTuple[1], randTuple[2])

  def getRandomTuple (self):
#    # Pick a random number uniform at random between 0 and sumSigma
#    curRand = random.uniform(0, self.sumSigma)
#
#    #print("[Rand] {0:.2f} - [sumSigma] {1:.2f}".format(curRand, self.sumSigma))
#
#    # Select the file for which this random number is in the cumsum range of sigmas
#    selectedTuple = []
#    cumSigma = 0.0
#    curIndex = -1
#
#    for curTuple in self.ratingTuples:
#      cumSigma += curTuple[2]
#      curIndex += 1
#
#      if cumSigma >= curRand:
#    return (curIndex, curTuple)

    # Much faster O(1) implementation (see Wikipedia on Fitness proportionate selection)
    randRolls = 0
    while True:
      randIndex = random.randint(0, len(self.ratingTuples) - 1)
      randTuple = self.ratingTuples[randIndex]
      acceptChance = randTuple[2] / self.maxSigma

      randRolls += 1

      if random.random() <= acceptChance:
        print("[Rand] Did {0:d} random rolls".format(randRolls))
        return ( randIndex, randTuple )

  def updateRankings (self, winnerID):
    # Disable GUI buttons first
    for curPhotoWidget in self.photoWidgets:
      curPhotoWidget.btnSelect.setEnabled(False)

    # Increase counter
    self.numRatings += 1
    self.statusBar().showMessage("[Session] {numRatings:d} ratings given.".format(numRatings = self.numRatings))

    print("")
    print("[Winner ID] {0:d}".format(winnerID))

    winnerIndex = self.shownIndices[winnerID - 1]
    loserIndices = [curIndex for curIndex in self.shownIndices if not curIndex == winnerIndex ]

    winnerTuple = self.ratingTuples[winnerIndex]
    loserTuples = [ self.ratingTuples[curIndex] for curIndex in loserIndices ]

    #print(winnerTuple)
    #print(loserTuples)

    # Calculate Glicko update
    loserR = [loserTuple[1] for loserTuple in loserTuples]
    loserRD = [loserTuple[2] for loserTuple in loserTuples]

    (winnerR, winnerRD) = Glicko.newScores(1.0, winnerTuple[1], winnerTuple[2], loserR, loserRD)

    newWinnerTuple = ( winnerTuple[0], winnerR, winnerRD )
    self.ratingTuples[winnerIndex] = newWinnerTuple

    print("[Winner]  r: {0:7.2f} - RD: {1:6.2f} (R: {2:4.0f})".format(winnerR, winnerRD, Glicko.getMinimalRating(winnerR, winnerRD)))

    for loserNum in range(2):
      curLoserTuple = loserTuples[loserNum]
      (curLoserR, curLoserRD) = Glicko.newScores(0.0, curLoserTuple[1], curLoserTuple[2], [ winnerTuple[1] ], [ winnerTuple[2] ])

      curLoserTuple = ( curLoserTuple[0], curLoserR, curLoserRD )
      self.ratingTuples[loserIndices[loserNum]] = curLoserTuple

      print("[Loser {0:d}] r: {1:7.2f} - RD: {2:6.2f} (R: {3:4.0f})".format(loserNum + 1, curLoserR, curLoserRD, Glicko.getMinimalRating(curLoserR, curLoserRD)))

    # Update max sigma - Can't use simple max between 2 values, multiple elements might have max sigma
    self.maxSigma = max([ curTuple[2] for curTuple in self.ratingTuples ])

    # Select new photos
    self.updateDisplayedPhotos()

    # Re-enable GUI buttons
    for curPhotoWidget in self.photoWidgets:
      curPhotoWidget.btnSelect.setEnabled(True)

  def keyPressEvent(self, event):
    # Capture key presses
    key = event.key()

    # If key 1 to 3 is pressed, click button
    keyNr = key - QtCore.Qt.Key_0
    if (keyNr >= 1) and (keyNr <= 3):
      #self.photoWidgets[keyNr - 1].btnSelect.click()
      self.updateRankings(keyNr)

    super(MainWindow, self).keyPressEvent(event)

def main():
  app = QtGui.QApplication(sys.argv)
  mw = MainWindow()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
