#!/usr/bin/env python

# Photo grouper program using Glicko rating system
# Author: Anthony VH, Stefaan
# Date:   August 2019

import sys        # Exit function
import os         # System function
import random     # Random number generation


from enum import Enum

from PyQt4 import QtGui, QtCore # GUI

from PhotoRating import PhotoRatingDb,StatusEnum, GroupedEnum, PhotoRating

from PhotoWidget import *
import Glicko

from pathlib import Path

class ClassifyingStateEnum(Enum):
    IDLE=0
    GOODBAD=1
    GROUPING=2
    GROUPSORTING=3
    SORTING=4

class MainWindow (QtGui.QMainWindow):

  appBasePath = os.path.dirname(os.path.realpath(__file__))

  def __init__ (self):
    super(MainWindow, self).__init__()
    # Setup variables
    self.hasDirectory = False
    self.isRating = ClassifyingStateEnum.IDLE
    self.ratingTuples = []
    self.shownIndices = []
    self.curPhoto = ""
    self.curBasePhoto = ""
    self.maxSigma = 200.0
    self.photoWidgets = []
    self.groupingWidgets = []
    self.groupsortWidgets = []
    self.sortWidgets = []
    self.bestWidgets = None

    self.defaultMu = 1500.0
    self.defaultSigma = 350.0

    self.numRatings = 0

    # Initialze GUI
    self.initGUI()

  def createPassFail(self):
    for i in range(1):
      self.photoWidgets.append(PhotoWidgetPassFail(self, i))
      self.hboxPassFail.addWidget(self.photoWidgets[i])
      self.photoWidgets[i].btnGood.setEnabled(False)
      self.photoWidgets[i].btnBad.setEnabled(False)


  def createGrouping(self):
    for i in range(2):
      self.groupingWidgets.append(PhotoWidgetGroup(self, i))
      self.hboxGrouping.addWidget(self.groupingWidgets[i])

      self.groupingProgress = QtGui.QProgressBar(self)
      self.groupingProgress.setGeometry(200, 80, 250, 20)
      self.hboxGrouping.addWidget(self.groupingProgress)

  def createGroupSorting(self):
    for i in range(2):
      self.groupsortWidgets.append(PhotoWidgetGroupSort(self, i))
      self.hboxGroupSorting.addWidget(self.groupsortWidgets[i])

  def createSorting(self):
    for i in range(3):
      self.sortWidgets.append(PhotoWidget(self, i))
      self.hboxSorting.addWidget(self.sortWidgets[i])

  def createBest(self):
    for i in [0]:
      self.bestWidgets = PhotoWidgetShowBest(self, i)
      self.hboxBest.addWidget(self.bestWidgets)

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

    self.SelectAction = QtGui.QAction('Open', self)
    self.SelectAction.setStatusTip("Select a directory")
    self.SelectAction.triggered.connect(self.setDirectory)

    # Create actions
    self.TriageAction = QtGui.QAction('Start/continue &triage', self)
    self.TriageAction.setShortcut('Ctrl+T')
    self.TriageAction.setStatusTip("Start or continue triaging photos in a directory")
    self.TriageAction.triggered.connect(self.startTriage)

    # Create actions
    self.groupingAction = QtGui.QAction('Start/continue &grouping', self)
    self.groupingAction.setShortcut('Ctrl+G')
    self.groupingAction.setStatusTip("Start or continue grouping photos in a directory")
    self.groupingAction.triggered.connect(self.startGrouping)

    # Create actions
    self.groupsortAction = QtGui.QAction('Start/continue &group sorting', self)
    self.groupsortAction.setShortcut('Ctrl+H')
    self.groupsortAction.setStatusTip("Start or continue group sorting photos in a directory")
    self.groupsortAction.triggered.connect(self.startGroupSorting)

    # Create actions
    self.sortAction = QtGui.QAction('Start/continue sorting', self)
    self.sortAction.setShortcut('Ctrl+R')
    self.sortAction.setStatusTip("Start or continue sorting photos in a directory")
    self.sortAction.triggered.connect(self.startSorting)

    #exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
    self.saveAction = QtGui.QAction('Save', self)
    self.saveAction.setShortcut('Ctrl+S')
    self.saveAction.setStatusTip('Save')
    self.saveAction.triggered.connect(self.save)

    self.bestAction = QtGui.QAction('Show &best', self)
    self.bestAction.setShortcut('Ctrl+B')
    self.bestAction.setStatusTip("Show a list of the best pictures")
    self.bestAction.triggered.connect(self.showBest)

    self.moveAction = QtGui.QAction('Move Pictures', self)
    self.moveAction.setShortcut('Ctrl+M')
    self.moveAction.setStatusTip("Move the pictures")
    self.moveAction.triggered.connect(self.movePhotosOut)

    #exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
    self.exitAction = QtGui.QAction('E&xit', self)
    self.exitAction.setShortcut('Ctrl+X')
    self.exitAction.setStatusTip('Exit application')
    self.exitAction.triggered.connect(self.exitApp)


    # Create menu bar
    menubar = self.menuBar()
    fileMenu = menubar.addMenu('&File')
    fileMenu.addAction(self.SelectAction)
    fileMenu.addAction(self.TriageAction)
    fileMenu.addAction(self.groupingAction)
    fileMenu.addAction(self.groupsortAction)
    fileMenu.addAction(self.sortAction)
    fileMenu.addAction(self.saveAction)
    fileMenu.addSeparator()
    fileMenu.addAction(self.bestAction)
    fileMenu.addAction(self.moveAction)
    fileMenu.addSeparator()
    fileMenu.addAction(self.exitAction)

    # Create status bar
    self.statusbar = QtGui.QStatusBar(self)
    self.setStatusBar(self.statusbar)
    self.statusBar().clearMessage()

    self.tabs = QtGui.QTabWidget()

    self.hboxPassFail = QtGui.QHBoxLayout()
    self.createPassFail()
    tab1 = QtGui.QWidget()
    tab1.setLayout(self.hboxPassFail)

    self.hboxGrouping = QtGui.QHBoxLayout()
    self.createGrouping()
    tab2 = QtGui.QWidget()
    tab2.setLayout(self.hboxGrouping)

    self.hboxGroupSorting = QtGui.QHBoxLayout()
    self.createGroupSorting()
    tab3 = QtGui.QWidget()
    tab3.setLayout(self.hboxGroupSorting)

    self.hboxSorting = QtGui.QHBoxLayout()
    self.createSorting()
    tab4 = QtGui.QWidget()
    tab4.setLayout(self.hboxSorting)

    self.hboxBest = QtGui.QHBoxLayout()
    self.createBest()
    tab5 = QtGui.QWidget()
    tab5.setLayout(self.hboxBest)

    self.tabs.addTab(tab1, "PassFail")
    self.tabs.addTab(tab2, "Grouping")
    self.tabs.addTab(tab3, "Group Sorteer")
    self.tabs.addTab(tab4, "Sorteer")
    self.tabs.addTab(tab5, "Best")
    for i in range(5):
        self.tabs.setTabEnabled(i, False)
    self.setCentralWidget(self.tabs)

  def save(self):
    # Store progress
    if hasattr(self, 'ratings'):
        self.ratings.saveRatings()

  def movePhotosOut (self):
    # First sort by rating
    self.bestratings = self.ratings.sortRatings()
    #°self.showid = int(len(self.bestratings)/4);
    # show best 40 or best 1/4 of photos, whichever is smaller
    #if self.showid > 40:
    #    self.showid  = 40
    self.showid = 100
    self.ratings.moveAfterSorting(self.showid)

  def showBest (self):
    self.tabs.setCurrentIndex(4)
    self.tabs.setTabEnabled(4, True)
    print("")
    print("[Best photographs]")

    if not self.isRating:
      print("Start rating a directory first!")
      return

    # First sort by rating
    self.bestratings = self.ratings.sortRatings()
    import math
    self.showid = int(math.ceil(len(self.bestratings)/4));
    # show best 40 or best 1/4 of photos, whichever is smaller
    if self.showid > 40:
        self.showid  = 40


    # Print the best 10 photos
    self.showNext()


  def showNext(self):
      if self.showid > 0:
          self.showid -= 1
          self.bestWidgets.setAll(self.curDir / self.bestratings[self.showid])
      else:
          self.tabs.setTabEnabled(4, False)
          box = QtGui.QMessageBox()
          box.setText("That was the best photo")
          box.exec_()
          self.isRating = ClassifyingStateEnum.IDLE


  def exitApp (self):
    self.save()

    # Exit program
    QtGui.qApp.quit()

  def updateDisplayedPassPhotos (self):
    # Go to next
    curStatus = self.ratings.photos[self.curPhoto].Status
    busy = True
    if (self.curPhotoIndex == (len(self.photoorder) - 1)):
      busy = False
    while (busy and (curStatus != StatusEnum.UNCHECKED)):
        self.curPhotoIndex += 1
        if (self.curPhotoIndex >= (len(self.photoorder))):
           busy = False
        else:
           self.curPhoto = self.photoorder[self.curPhotoIndex]
           curStatus = self.ratings.photos[self.curPhoto].Status
           if (curStatus == StatusEnum.UNCHECKED and self.markallgood):
               curStatus = StatusEnum.GOOD
               self.ratings.photos[self.curPhoto].Status = curStatus

    if (busy):
        self.photoWidgets[0].setAll(self.curDir / self.curPhoto)
    return busy



  def setDirectory(self):
    self.curDir = Path(str(QtGui.QFileDialog.getExistingDirectory(self, "Start - Select directory")))
    self.ratings = PhotoRatingDb(self.curDir)
    self.hasDirectory = True
    self.printStatistics()

  def printStatistics(self):
      box = QtGui.QMessageBox()
      box.setText(self.ratings.statistics())
      box.exec_()




  def startTriage(self):
    self.markallgood = False
    if not self.hasDirectory:
        self.setDirectory()
    self.isRating = ClassifyingStateEnum.GOODBAD
    self.curPhotoIndex = 0
    self.photoorder = sorted(self.ratings.photos.keys())
    self.curPhoto = self.photoorder[self.curPhotoIndex]
    self.tabs.setTabEnabled(0, True)
    self.tabs.setCurrentIndex(0)
    self.photoWidgets[0].btnGood.setEnabled(True)
    self.photoWidgets[0].btnBad.setEnabled(True)
    if (not self.updateDisplayedPassPhotos()):
        self.endTriage()

  def updatePassFailRankings(self, keynr):
      if keynr == 3:
          print("Marked all good")
          self.markallgood = True
      if keynr == 1: # Good
          self.ratings.photos[self.curPhoto].Status = StatusEnum.GOOD
      else:
          self.ratings.photos[self.curPhoto].Status = StatusEnum.BAD
      busy = self.updateDisplayedPassPhotos()
      if (not busy):
          self.endTriage()

  def endTriage(self):
      self.ratings.saveRatings()
      self.isRating = ClassifyingStateEnum.IDLE
      self.tabs.setTabEnabled(0, False)
      box = QtGui.QMessageBox()
      box.setText("Triaged all photo's in this folder")
      box.exec_()

  def startGrouping(self):
    if not self.hasDirectory: self.setDirectory()
    self.isRating = ClassifyingStateEnum.GROUPING
    self.curPhotoIndex = 0
    self.tabs.setTabEnabled(1, True)
    self.tabs.setCurrentIndex(1)
    self.photoorder = sorted(self.ratings.GoodPhotosForGrouping())
    #if len(self.photoorder) > 1:
    #    self.curPhoto = self.photoorder[self.curPhotoIndex + 1]
    #    self.curBasePhoto = self.photoorder[self.curPhotoIndex]
    #    self.updateDisplayedPhotosGrouping()
    #else:
    if len(self.photoorder) > 0:
        fingerprints = {}
        import pickle
        if os.path.exists(self.curDir / "fingerprints.my"):
            with open(self.curDir / "fingerprints.my", 'rb') as fh:
                fingerprints = pickle.load(fh)
                print("Loaded fingerprints successfully")
        else:
            print("Didn't find fingerprint file")

        from ImageFingerprint import ImageFingerprint
        current = 0
        self.groupingProgress.setValue(current/len(self.photoorder))
        for photo in self.photoorder:
            current += 1
            if not photo in fingerprints.keys():
                fingerprints[photo]  = ImageFingerprint(self.curDir / photo)
                print("Created")
            self.groupingProgress.setValue(current/len(self.photoorder))

        with open(self.curDir / "fingerprints.my", 'wb') as fh:
            pickle.dump(fingerprints, fh)
            print("Saved fingerprints successfully")

        matchtable = {}

        matchreq = 0.60
        sorted_images = sorted(fingerprints.keys())

        groups = []
        currentgroup = [sorted_images[0]]
        for previous, current in zip(sorted_images, sorted_images[1:]):
            if fingerprints[previous].match(fingerprints[current]) > matchreq:
                currentgroup.append(current)
            else:
                groups.append(currentgroup)
                currentgroup = [current]
        keepratio = len(sorted_images)/len(groups)
        print("%g : Divided %i images over %i groups" %( matchreq, len(sorted_images), len(groups)))
        photoorder_reverselut = {}
        for i in range(len(self.photoorder)):
            photoorder_reverselut[self.photoorder[i]] = i
        for group in groups:
            if len(group) == 1:
                self.ratings.photos[group[0]].Grouped = GroupedEnum.SINGLE
            else:
                for photo in group:
                    self.ratings.photos[photo].Grouped = GroupedEnum.GROUPED
                    self.ratings.photos[photo].GroupId = group[0]



    self.endGrouping()

  def updateGroupRankings(self, keynr):
      if keynr == 1: # New group
          if self.ratings.photos[self.curBasePhoto].Grouped == GroupedEnum.UNCHECKED:
              self.ratings.photos[self.curBasePhoto].Grouped = GroupedEnum.SINGLE
          self.curBasePhotoIndex = self.curPhotoIndex
          self.curBasePhoto = self.photoorder[self.curBasePhotoIndex]

      else: # curphoto belongs to base
          self.ratings.photos[self.curBasePhoto].Grouped = GroupedEnum.GROUPED
          self.ratings.photos[self.curBasePhoto].GroupId = self.curBasePhoto
          self.ratings.photos[self.curPhoto].Grouped = GroupedEnum.GROUPED
          self.ratings.photos[self.curPhoto].GroupId = self.curBasePhoto

      busy = True
      if (len(self.photoorder) > (self.curPhotoIndex + 1)):
          self.curPhotoIndex += 1
          self.curPhoto = self.photoorder[self.curPhotoIndex]
      else:
          busy = False

      if (busy):
          busy = self.updateDisplayedPhotosGrouping()

      if (not busy):
          self.endGrouping()



  def updateDisplayedPhotosGrouping (self):
    # Go to next
    curStatus = self.ratings.photos[self.curPhoto].Grouped
    busy = True
    if (self.curPhotoIndex == (len(self.photoorder))):
      busy = False
    while (busy and (curStatus != GroupedEnum.UNCHECKED)):
        self.curPhotoIndex += 1
        if (self.curPhotoIndex >= (len(self.photoorder))):
           busy = False
        else:
           self.curPhoto = self.photoorder[self.curPhotoIndex]
           curStatus = self.ratings.photos[self.curPhoto].Grouped

    if (busy):
        self.groupingWidgets[0].setAll(self.curDir / self.curBasePhoto)
        self.groupingWidgets[1].setAll(self.curDir / self.curPhoto)
    return busy


  def endGrouping(self):
      self.ratings.saveRatings()
      self.isRating = ClassifyingStateEnum.IDLE
      self.tabs.setTabEnabled(1, False)
      box = QtGui.QMessageBox()
      box.setText("Grouped all photo's in this folder")
      box.exec_()

  def startGroupSorting(self):
    if (not self.hasDirectory):
        self.setDirectory()
    self.isRating = ClassifyingStateEnum.GROUPSORTING
    self.photoGroupsUnsorted = self.ratings.GroupedPhotosPackets()
    self.photoorder = sorted(self.photoGroupsUnsorted.keys())
    print(self.photoorder)
    self.groupindex = 0;
    self.current_group = self.photoorder[self.groupindex]


    self.tabs.setTabEnabled(2, True)
    self.tabs.setCurrentIndex(2)
    (self.Photo1, self.Photo2) = self.getTwoNext()
    self.updateDisplayedPhotosGroupSort()

  def updateGroupSortRankings(self, keynr):
      if (keynr == 1):
          self.ratings.photos[self.Photo1].GroupMu += self.ratings.photos[self.Photo2].GroupMu
          self.ratings.photos[self.Photo2].GroupMu = 0
      if (keynr != 1):
          self.ratings.photos[self.Photo2].GroupMu += self.ratings.photos[self.Photo1].GroupMu
          self.ratings.photos[self.Photo1].GroupMu = 0
      (self.Photo1,  self.Photo2 ) = self.getTwoNext();
      if self.Photo2 == "" or self.Photo1 == "":
          self.groupindex += 1
          #print("Starting next group")
      if self.groupindex < (len(self.photoorder)):
          self.current_group = self.photoorder[self.groupindex]
          (self.Photo1,  self.Photo2 ) = self.getTwoNext();
          self.updateDisplayedPhotosGroupSort()
      else:
          self.endGroupSorting()


  def getTwoNext(self):
      # find first picture
      photoOne = ""
      photoTwo = ""
      for groupphoto in self.photoGroupsUnsorted[self.current_group]:
          if self.ratings.photos[groupphoto].GroupMu > 0:
              if photoOne == "":
                  photoOne = groupphoto
              else:
                  if photoTwo == "":
                      photoTwo = groupphoto
                      break
      return (photoOne, photoTwo)

  def updateDisplayedPhotosGroupSort(self):
    self.groupsortWidgets[0].setAll(self.curDir / self.Photo1)
    self.groupsortWidgets[1].setAll(self.curDir / self.Photo2)


  def endGroupSorting(self):
    self.ratings.pointToBestOfGroup()
    self.tabs.setTabEnabled(2, False)
    self.ratings.saveRatings()
    box = QtGui.QMessageBox()
    box.setText("Sorted all grouped photos in this folder")
    box.exec_()

  def startSorting(self):
    if not self.hasDirectory: self.setDirectory()
    self.tabs.setTabEnabled(3, True)
    self.tabs.setCurrentIndex(3)
    self.isRating = ClassifyingStateEnum.SORTING
    self.photoorder = self.ratings.getPreprocessedPhotos()

    self.selectPhotos()
    self.updateDisplayedPhotosSort()

  def getRandomTuple (self):
    randRolls = 0
    while True:
      randIndex = random.randint(0, len(self.photoorder) - 1)
      photoid = self.photoorder[randIndex]
      photorating = self.ratings.photos[photoid]
      acceptChance = photorating.sigma / self.maxSigma

      randRolls += 1

      if random.random() <= acceptChance:
        #print("[Rand] Did {0:d} random rolls".format(randRolls))
        return ( randIndex, photorating )

  def updateSortRankings(self, winnerID):
    self.numRatings += 1

    winnerIndex = self.shownIndices[winnerID - 1]
    loserIndices = [curIndex for curIndex in self.shownIndices if not curIndex == winnerIndex ]

    winnerRating = self.ratings.photos[self.photoorder[winnerIndex]]
    loserRatings = [ self.ratings.photos[self.photoorder[curIndex]] for curIndex in loserIndices ]

    # Calculate Glicko update
    loserR = [loserRating.mu for loserRating in loserRatings]
    loserRD = [loserRating.sigma for loserRating in loserRatings]

    (winnerRating.mu, winnerRating.sigma) = Glicko.newScores(1.0, winnerRating.mu, winnerRating.sigma, loserR, loserRD)

    for loserNum in range(2):
      curLoserRating = loserRatings[loserNum]
      (curLoserRating.mu, curLoserRating.sigma) = Glicko.newScores(0.0, curLoserRating.mu,
              curLoserRating.sigma, [ winnerRating.mu ], [ winnerRating.sigma ])


    # Select new photos
    self.selectPhotos()
    self.updateDisplayedPhotosSort()

  def selectPhotos(self):
    self.shownIndices = []

    # Update max sigma - Can't use simple max between 2 values, multiple elements might have max sigma
    self.maxSigma = 0.0
    for photoid in self.photoorder:
        rating = self.ratings.photos[photoid]
        self.maxSigma = max([rating.sigma, self.maxSigma])

    print ("Current Max Sigma (aim for < 133)" + str(self.maxSigma))
    if (self.maxSigma < 133.3):
        self.endSorting()


    for i in range(3):
      # Get "random" image and make sure it's not selected already
      while True:
        (randIndex, randRating) = self.getRandomTuple()

        if not (randIndex in self.shownIndices):
          break

        #print("[Rand] Image already selected!")

      # Add new filename to current file list
      #print randTuple
      self.shownIndices.append(randIndex)

      # Create absolute path for image display
      if i == 0 :
          self.Photo1 = self.photoorder[randIndex]
      if i == 1 :
          self.Photo2 = self.photoorder[randIndex]
      if i == 2 :
          self.Photo3 = self.photoorder[randIndex]


  def updateDisplayedPhotosSort(self):
    self.sortWidgets[0].setAll(self.curDir / self.Photo1)
    self.sortWidgets[1].setAll(self.curDir / self.Photo2)
    self.sortWidgets[2].setAll(self.curDir / self.Photo3)
    print ("showing " + self.Photo1 + " " + self.Photo2 + " " + self.Photo3)


  def endSorting(self):
    self.tabs.setTabEnabled(3, False)
    self.ratings.saveRatings()
    box = QtGui.QMessageBox()
    box.setText("Sorted photos enough")
    box.exec_()
    self.isRating = ClassifyingStateEnum.IDLE


  def keyPressIdle(self, key):
      print("Start doing something first")

  def keyPressPassFail(self, key):
    # If key 1 to 3 is pressed, click button
    keyNr = key - QtCore.Qt.Key_0
    if (keyNr >= 1) and (keyNr <= 3):
        self.updatePassFailRankings(keyNr)

  def keyPressGrouping(self, key):
    # If key 1 to 3 is pressed, click button
    # 0 - Part of group
    # 1 - new group
    keyNr = key - QtCore.Qt.Key_0
    if (keyNr >= 1) and (keyNr <= 2):
        self.updateGroupRankings(keyNr - 1)

  def keyPressGroupSorting(self, key):
    # If key 1 to 3 is pressed, click button
    keyNr = key - QtCore.Qt.Key_0
    if (keyNr >= 1) and (keyNr <= 2):
        self.updateGroupSortRankings(keyNr)

  def keyPressSorting(self, key):
    # If key 1 to 3 is pressed, click button
    keyNr = key - QtCore.Qt.Key_0
    if (keyNr >= 1) and (keyNr <= 3):
        self.updateSortRankings(keyNr)

  def keyPressEvent(self, event):
    key = event.key()

    switchKeyEvaluation = {
        ClassifyingStateEnum.IDLE         : self.keyPressIdle,
        ClassifyingStateEnum.GOODBAD      : self.keyPressPassFail,
        ClassifyingStateEnum.GROUPING     : self.keyPressGrouping,
        ClassifyingStateEnum.GROUPSORTING : self.keyPressGroupSorting,
        ClassifyingStateEnum.SORTING      : self.keyPressSorting
        }
    func = switchKeyEvaluation.get(self.isRating, lambda: "not implemented")
    func(key)
    super(MainWindow, self).keyPressEvent(event)


def main():
  app = QtGui.QApplication(sys.argv)
  mw = MainWindow()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
