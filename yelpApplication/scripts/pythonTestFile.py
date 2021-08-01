import datetime
import json
import math
import requests
import time
from flask import Flask
from flask import request
from flask_cors import CORS


def checkIfRowPassesInputConditions(inputParameters, row):
  return True

if __name__ == '__main__':
  folderLocationOfDataFiles = 'https://raw.githubusercontent.com/JackDeDobb/JackDeDobb.github.io/master/yelpApplication/data/'
  dataLocationFiles = [folderLocationOfDataFiles + 'yelp_academic_dataset_review' + '{:02d}'.format(idx) + '.json' for idx in range(0, 21)]

  maxRecordsToPullIn = 10
  recordsThatMatch = []
  for dataLocationFile in dataLocationFiles:
    textFile = requests.get(dataLocationFile).text
    for line in textFile.split('\n'):
      jsonParsedLine = json.loads(line)
      if (checkIfRowPassesInputConditions(inputParameters, jsonParsedLine)):
        recordsThatMatch.append(jsonParsedLine)
      if (len(recordsThatMatch) >= maxRecordsToPullIn):
        break
    if (len(recordsThatMatch) >= maxRecordsToPullIn):
      break

  print(recordsThatMatch)
