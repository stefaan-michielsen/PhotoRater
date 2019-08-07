# Implementation of the Glicko rating system
# Author: Anthony VH
# Date:   June 2014

# Imports
import math       # Size calculations

# Variables
q = math.log(10.0) / 400.0

def g (RD):
  return 1.0 / math.sqrt(1.0 + (3.0 * math.pow(q, 2) * math.pow(RD, 2)) / math.pow(math.pi, 2))

def E (r, ri, RDi):
  return 1.0 / (1.0 + math.pow(10.0, (g(RDi) * (r - ri)) / -400.0))

def dTwo (r, listR, listRD):
  curSumItems = []
  for curIndex in range(len(listR)):
    curE = E(r, listR[curIndex], listRD[curIndex])
    curSumItems.append(math.pow(g(listRD[curIndex]), 2) * curE * (1.0 - curE))

  denom = math.pow(q, 2) * sum(curSumItems)

  return 1.0 / denom

def newRating (s, r, RD, listR, listRD):
  curSumItems = []
  for curIndex in range(len(listR)):
    curSumItems.append(g(listRD[curIndex]) * (s - E(r, listR[curIndex], listRD[curIndex])))

  return r + q / ((1.0 / math.pow(RD, 2)) + (1.0 / dTwo(r, listR, listRD))) * sum(curSumItems)

def newRD (r, RD, listR, listRD):
  return math.sqrt(1.0 / (1.0/math.pow(RD, 2) + 1.0/dTwo(r, listR, listRD)))

def newScores (s, r, RD, listR, listRD):
  return ( newRating(s, r, RD, listR, listRD), newRD(r, RD, listR, listRD) )

def getMinimalRating (r, RD):
  return r - 2 * RD
