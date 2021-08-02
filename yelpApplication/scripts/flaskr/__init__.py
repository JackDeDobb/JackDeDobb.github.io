import base64
import datetime
import gensim
import io
import json
import math
import matplotlib
import matplotlib.pyplot as plt
import nltk
import numpy as np
import pandas as pd
import pickle
import re
import os
import requests
import time
from base64 import encodebytes
from collections import Counter
from flask import Flask, jsonify, make_response, Response, request
from flask_cors import CORS
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from PIL import Image
from pprint import pprint
from wordcloud import WordCloud, STOPWORDS


matplotlib.use('Agg')
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
    'starRatingMin':        castToIntIfExists(request.args.get('starRatingMin'))  or 1,
    'starRatingMax':        castToIntIfExists(request.args.get('starRatingMax'))  or 5,
    'funnyVotesMin':        castToIntIfExists(request.args.get('funnyVotesMin'))  or 0,
    'funnyVotesMax':        castToIntIfExists(request.args.get('funnyVotesMax'))  or 999999999, # TODO: Flip back to Infinity
    'coolVotesMin':         castToIntIfExists(request.args.get('coolVotesMin'))   or 0,
    'coolVotesMax':         castToIntIfExists(request.args.get('coolVotesMax'))   or 999999999, # TODO: Flip back to Infinity
    'usefulVotesMin':       castToIntIfExists(request.args.get('usefulVotesMin')) or 0,
    'usefulVotesMax':       castToIntIfExists(request.args.get('usefulVotesMax')) or 999999999, # TODO: Flip back to Infinity
    'dateWrittenMin': parseDateTimeFromString(request.args.get('dateWrittenMin')) or datetime.datetime(2004, 6, 1),
    'dateWrittenMax': parseDateTimeFromString(request.args.get('dateWrittenMax')) or datetime.datetime.now()
  }


def checkIfRowPassesInputConditions(inputParameters, row):
  parseDate = parseDateTimeFromString(row['date'])

  retBool = True
  retBool &= (row['stars']           >= inputParameters['starRatingMin']   and  row['stars']           <= inputParameters['starRatingMax'])
  retBool &= (row['votes']['funny']  >= inputParameters['funnyVotesMin']   and  row['votes']['funny']  <= inputParameters['funnyVotesMax'])
  retBool &= (row['votes']['cool']   >= inputParameters['coolVotesMin']    and  row['votes']['cool']   <= inputParameters['coolVotesMax'])
  retBool &= (row['votes']['useful'] >= inputParameters['usefulVotesMin']  and  row['votes']['useful'] <= inputParameters['usefulVotesMax'])
  retBool &= (parseDate              >= inputParameters['dateWrittenMin']  and  parseDate              <= inputParameters['dateWrittenMax'])

  return retBool


def parseAndCleanTextIntoWords(text, stopWords):
  text = re.sub('[,\.!?]', '', text) # Remove punctuation
  text = text.lower() # Convert words to lowercase
  words = gensim.utils.simple_preprocess(str(text), deacc=True) # Grab words
  words = [word for word in words if word not in stopWords] # Remove stop words

  return words


def getDataThatMatchesInputParameters(inputParameters, stopWords):
  folderLocationOfDataFiles = 'https://raw.githubusercontent.com/JackDeDobb/JackDeDobb.github.io/master/yelpApplication/data/'
  dataLocationFiles = [folderLocationOfDataFiles + 'yelp_academic_dataset_review' + '{:02d}'.format(idx) + '.json' for idx in range(0, 21)]

  maxRecordsToPullIn = 10
  recordsThatMatch = []
  for dataLocationFile in dataLocationFiles:
    textFile = requests.get(dataLocationFile).text
    for line in textFile.split('\n'):
      jsonParsedLine = json.loads(line)
      if (checkIfRowPassesInputConditions(inputParameters, jsonParsedLine)):
        jsonParsedLine['textProcessed'] = parseAndCleanTextIntoWords(jsonParsedLine['text'], stopWords)
        recordsThatMatch.append(jsonParsedLine)
      if (len(recordsThatMatch) >= maxRecordsToPullIn):
        break
    if (len(recordsThatMatch) >= maxRecordsToPullIn):
      break

  return recordsThatMatch


def runLDA(dataArrSegment, numberTopics):
  dataWords = [x['textProcessed'] for x in dataArrSegment]
  indexToWord = gensim.corpora.Dictionary(dataWords) # Create Dictionary
  copyDataWords = dataWords
  corpus = [indexToWord.doc2bow(x) for x in copyDataWords] # Create corpus, Term Document Frequency
  ldaModel = gensim.models.LdaMulticore(corpus=corpus, id2word=indexToWord, num_topics=numberTopics)

  return [ldaModel, dataWords]


def visualizeLDATopicGraphs(ldaModel, dataWords):
  topics = ldaModel.show_topics(formatted=False)
  dataWordsFlattened = [word for wordList in dataWords for word in wordList]
  counter = Counter(dataWordsFlattened)

  out = []
  for idx, topic in topics:
    for word, weight in topic:
        out.append([word, idx, weight, counter[word]])

  df = pd.DataFrame(out, columns=['word', 'topic', 'importance', 'wordCount'])
  maxWordCount = df['wordCount'].max()

  fig, axes = plt.subplots(3, 3, figsize=(16, 10), sharey=True, dpi=160)
  colors = [color for _, color in matplotlib.colors.TABLEAU_COLORS.items()]
  for idx, axis in enumerate(axes.flatten()):
    axis.set_title('Topic: ' + str(idx + 1), color=colors[idx], fontsize=16)
    axis.set_ylabel('Word Count', color=colors[idx])
    axis.tick_params(axis='y', left=False)
    axis.set_xticklabels(df.loc[df.topic==idx, 'word'], rotation=30, horizontalalignment='right')

    axis.set_ylim(0, 1.2 * maxWordCount)
    axis.bar(x='word', height='wordCount', data=df.loc[df.topic == idx, :], color=colors[idx], width=0.5, alpha=0.3, label='Word Count')
    axis.legend(loc='upper left')

    twinAxis = axis.twinx()
    twinAxis.set_ylim(0, 0.030)
    twinAxis.bar(x='word', height='importance', data=df.loc[df.topic == idx, :], color=colors[idx], width=0.2, label='Weights')
    twinAxis.legend(loc='upper right')

  fig.tight_layout(w_pad=2)
  fig.suptitle('Word Count and Importance of Topic Keywords', fontsize=20, y=1.02)

  return fig


def getLDATopicGraphsVisualizationFromDataArr(dataArrSegment, numberTopics):
  ldaModel, dataWords = runLDA(dataArrSegment, numberTopics)
  ldaTopicGraphsVisualization = visualizeLDATopicGraphs(ldaModel, dataWords)

  return [ldaTopicGraphsVisualization, ldaModel]


def getWordCloud(stopWords, ldaModel):
  colors = [color for _, color in matplotlib.colors.TABLEAU_COLORS.items()]  # more colors: 'mcolors.XKCD_COLORS'
  topics = ldaModel.show_topics(formatted=False)

  topicsListOfSetsOfWords = []
  for wordList in topics:
    topicsListOfSetsOfWords.append(set([x[0] for x in wordList[1]]))

  def colorFunction(word, font_size, position, orientation, font_path, random_state):
    for innerIdx, setOfWords in enumerate(topicsListOfSetsOfWords):
      if (word in setOfWords):
        return colors[innerIdx]

  cloud = WordCloud(stopwords=stopWords,
                    background_color='white',
                    width=2500,
                    height=1800,
                    max_words=200,
                    colormap='tab10',
                    color_func=colorFunction,
                    prefer_horizontal=1.0)

  cloudDict = {}
  for wordAndImportance in topics:
    for word, importance in wordAndImportance[1]:
      if (word not in cloudDict):
        cloudDict[word] = importance

  cloud.generate_from_frequencies(cloudDict, max_font_size=300)

  return cloud


def getLDAWordCloudVisualization(stopWords, ldaModel):
  cloud1 = getWordCloud(stopWords, ldaModel)

  fig, axes = plt.subplots(1, 2, figsize=(100, 100), sharex=True, sharey=True)

  fig.add_subplot(axes.flatten()[0])
  plt.gca().imshow(cloud1)
  plt.gca().set_title('Positive Word Cloud', fontdict=dict(size=160))
  plt.gca().axis('off')

  fig.add_subplot(axes.flatten()[1])
  plt.gca().imshow(cloud1)
  plt.gca().set_title('Negative Word Cloud', fontdict=dict(size=160))
  plt.gca().axis('off')

  plt.subplots_adjust(wspace=0, hspace=0)
  plt.axis('off')
  plt.margins(x=0, y=0)
  plt.tight_layout()

  return fig


def fig2data ( fig ):
  """
  @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
  @param fig a matplotlib figure
  @return a numpy 3D array of RGBA values
  """
  # draw the renderer
  fig.canvas.draw ( )

  # Get the RGBA buffer from the figure
  w,h = fig.canvas.get_width_height()
  buf = np.fromstring ( fig.canvas.tostring_argb(), dtype=np.uint8 )
  buf.shape = ( w, h,4 )

  # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
  buf = np.roll ( buf, 3, axis = 2 )
  return buf


def fig2img ( fig ):
  """
  @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
  @param fig a matplotlib figure
  @return a Python Imaging Library ( PIL ) image
  """
  # put the figure pixmap into a numpy array
  buf = fig2data ( fig )
  w, h, d = buf.shape
  return Image.fromstring( "RGBA", ( w ,h ), buf.tostring( ) )


@app.route('/')
def runLDAGivenInputParameters():
  # nltk.download('stopwords') # Comment back in, if need to download stopwords
  stopWords = nltk.corpus.stopwords.words('english')
  stopWords.extend(['go', 'get', 'like', 'got', 'us'])
  inputParameters = getInputParameters()
  numberTopics = 9

  dataArrSegment = getDataThatMatchesInputParameters(inputParameters, stopWords)
  ldaTopicGraphsVisualization, ldaModel = getLDATopicGraphsVisualizationFromDataArr(dataArrSegment, numberTopics)
  ldaWordCloudVisualization = getLDAWordCloudVisualization(stopWords, ldaModel)

  outputLDATopicGraphsVisualization = io.BytesIO()
  FigureCanvas(ldaTopicGraphsVisualization).print_png(outputLDATopicGraphsVisualization)
  encodedLDATopicGraphsVisualization = base64.b64encode(outputLDATopicGraphsVisualization.getvalue()).decode('utf-8')

  outputLDAVisualization = io.BytesIO()
  FigureCanvas(ldaTopicGraphsVisualization).print_png(outputLDAVisualization)
  encodedLDAVisualization = base64.b64encode(outputLDAVisualization.getvalue()).decode('ascii')
  # decodedLDAVisualization = base64.b64decode(encodedLDAVisualization.encode('ascii'))
  # image = Image.open(io.BytesIO(decodedLDAVisualization))
  # image.show()

  return createParsableJSONResponse({
    'topicGraphs': encodedLDAVisualization,
    'wordCloud': 69
  })





  # image = Image.open(io.BytesIO(imagesBytes))
  # image.show()

  b = createParsableJSONResponse({
    'topicGraphs': encoded,
    'wordCloud': 69
  })

  return b

  # output = io.BytesIO()
  # FigureCanvas(ldaTopicGraphsVisualization).print_png(output)
  # return Response(output.getvalue(), mimetype='image/png')

  output = io.BytesIO()
  # print(type(output))
  FigureCanvas(ldaTopicGraphsVisualization).print_png(output)
  # print(type(output.getvalue()))
  # print(output.getvalue())
  a = Response(output.getvalue(), mimetype='image/png')
  # print(type(a))

  imagesBytes = output.getvalue()

  image = Image.open(io.BytesIO(imagesBytes))
  # image.show()

  b = createParsableJSONResponse({
    'topicGraphs': imagesBytes,
    'wordCloud': 69
  })

  return b


  return fig2img(ldaTopicGraphsVisualization)

  # output = io.BytesIO()
  # FigureCanvas(ldaTopicGraphsVisualization).print_png(output)
  # return Response(output.getvalue(), mimetype='image/png')
  # return make_response(jsonify(Response(output.getvalue(), mimetype='image/png')), 200)


  # canvas = FigureCanvas(ldaTopicGraphsVisualization)
  # ax = ldaTopicGraphsVisualization.gca()
  # ax.text(0.0,0.0, 'Test', fontsize=45)
  # ax.axis('off')
  # canvas.draw()       # draw the canvas, cache the renderer
  # image = np.fromstring(canvas.tostring_rgb(), dtype='uint8')
  # json_dump = json.dumps(image, cls=NumpyEncoder)

  outputLDAVisualization = io.BytesIO()
  FigureCanvas(ldaTopicGraphsVisualization).print_png(outputLDAVisualization)
  encodedLDAVisualization = base64.b64encode(outputLDAVisualization.getvalue()).decode('utf-8')
  outputLDAWordCloudVisualization = io.BytesIO()
  FigureCanvas(ldaWordCloudVisualization).print_png(outputLDAWordCloudVisualization)
  encodedLDAWordCloudVisualization = base64.b64encode(outputLDAWordCloudVisualization.getvalue()).decode('utf-8')

  return createParsableJSONResponse({
    'topicGraphs': encodedLDATopicGraphsVisualization,
    'wordCloud': encodedLDAWordCloudVisualization
  })


if __name__ == '__main__':
  app.run(debug=True)
