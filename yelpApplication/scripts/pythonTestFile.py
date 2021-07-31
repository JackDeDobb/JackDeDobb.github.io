import datetime
import math
import requests
import time
from flask import Flask
from flask import request
from flask_cors import CORS




if __name__ == '__main__':
  folderLocationOfDataFiles = 'https://raw.githubusercontent.com/JackDeDobb/JackDeDobb.github.io/master/yelpApplication/data/'
  dataLocationFiles = [folderLocationOfDataFiles + 'yelp_academic_dataset_review' + '{:02d}'.format(idx) + '.json' for idx in range(0, 21)]

  maxRecordsToPullIn = 100
  recordsThatMatch = []

  for dataLocationFile in dataLocationFiles:
    textFile = requests.get(dataLocationFile).text
    for line in textFile:
      # parse line
      # check line
      # add line to records that match array if it matches
      recordsThatMatch.append(1)
      if (len(recordsThatMatch) >= maxRecordsToPullIn):
        break
    if (len(recordsThatMatch) >= maxRecordsToPullIn):
      break

print(recordsThatMatch)