import datetime
import json
import math
import requests
import time
from flask import Flask
from flask import request
from flask_cors import CORS


app = Flask(__name__)
CORS(app)




def createParsableJSONResponse(value):
  return { 'value': value }


def castToIntIfExists(value):
  try:
    return int(value) if (value != None) else None
  except:
    return None


def parseDateTimeFromString(value):
  try:
    return datetime.datetime.strptime(value, '%Y-%m-%d') if (value != None) else None
  except:
    return None


def getInputParameters():
  return {
    'starRatingMin':  castToIntIfExists(request.args.get('starRatingMin'))  or 1,
    'starRatingMax':  castToIntIfExists(request.args.get('starRatingMax'))  or 5,
    'funnyVotesMin':  castToIntIfExists(request.args.get('funnyVotesMin'))  or 0,
    'funnyVotesMax':  castToIntIfExists(request.args.get('funnyVotesMax'))  or 999999999, # TODO: Flip back to Infinity
    'coolVotesMin':   castToIntIfExists(request.args.get('coolVotesMin'))   or 0,
    'coolVotesMax':   castToIntIfExists(request.args.get('coolVotesMax'))   or 999999999, # TODO: Flip back to Infinity
    'usefulVotesMin': castToIntIfExists(request.args.get('usefulVotesMin')) or 0,
    'usefulVotesMax': castToIntIfExists(request.args.get('usefulVotesMax')) or 999999999, # TODO: Flip back to Infinity
    'dateWrittenMin': parseDateTimeFromString(request.args.get('dateWrittenMin')) or datetime.datetime(2004, 6, 1),
    'dateWrittenMax': parseDateTimeFromString(request.args.get('dateWrittenMax')) or datetime.datetime.now()
  }


def checkIfRowPassesInputConditions(inputParameters, row):
  parseDate = parseDateTimeFromString(row['date'])

  retBool = True
  retBool &= (row['stars'] >= inputParameters['starRatingMin'] and row['stars'] <= inputParameters['starRatingMax'])
  retBool &= (row['votes']['funny'] >= inputParameters['funnyVotesMin'] and row['votes']['funny'] <= inputParameters['funnyVotesMax'])
  retBool &= (row['votes']['cool'] >= inputParameters['coolVotesMin'] and row['votes']['cool'] <= inputParameters['coolVotesMax'])
  retBool &= (row['votes']['useful'] >= inputParameters['usefulVotesMin'] and row['votes']['useful'] <= inputParameters['usefulVotesMax'])
  retBool &= (parseDate >= inputParameters['dateWrittenMin'] and parseDate <= inputParameters['dateWrittenMax'])

  return retBool


def getDataThatMatchesInputParameters(inputParameters):
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

  return recordsThatMatch


@app.route('/')
def runLDAGivenInputParameters():
  inputParameters = getInputParameters()
  retVal = getDataThatMatchesInputParameters(inputParameters)
  
  time.sleep(1)
  return createParsableJSONResponse(retVal)


if __name__ == '__main__':
  app.run(debug=True)
