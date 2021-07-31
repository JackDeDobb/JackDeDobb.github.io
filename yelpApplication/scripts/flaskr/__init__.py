import datetime
import math
import time
from flask import Flask
from flask import request
from flask_cors import CORS


app = Flask(__name__)
CORS(app)




def createParsableJSONResponse(value):
  return { 'value': value }


def getInputParameters():
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


@app.route('/')
def runLDAGivenInputParameters():
  retVal = getInputParameters()
  
  time.sleep(1)
  return createParsableJSONResponse(retVal)


if __name__ == '__main__':
  app.run(debug=True)
