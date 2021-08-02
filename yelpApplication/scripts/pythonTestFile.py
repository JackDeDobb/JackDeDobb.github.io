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
    'starRatingMin':  1,
    'starRatingMax':  5,
    'funnyVotesMin':  0,
    'funnyVotesMax':  999999999, # TODO: Flip back to Infinity
    'coolVotesMin':   0,
    'coolVotesMax':   999999999, # TODO: Flip back to Infinity
    'usefulVotesMin': 0,
    'usefulVotesMax': 999999999, # TODO: Flip back to Infinity
    'dateWrittenMin': datetime.datetime(2004, 6, 1),
    'dateWrittenMax': datetime.datetime.now()
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
  scriptDirectory = os.path.dirname(os.path.realpath(__file__))
  folderLocationOfDataFiles = scriptDirectory + '/../data/'
  dataLocationFiles = [folderLocationOfDataFiles + 'yelp_academic_dataset_review' + '{:02d}'.format(idx) + '.json' for idx in range(0, 21)]

  maxRecordsToPullIn = 10
  recordsThatMatch = []
  for dataLocationFile in dataLocationFiles:
    textFile = open(dataLocationFile)
    for line in list(textFile):
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
  ldaVisualization = visualizeLDATopicGraphs(ldaModel, dataWords)

  return [ldaVisualization, ldaModel]


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


def runLDAGivenInputParameters():
  # nltk.download('stopwords') # Comment back in, if need to download stopwords
  stopWords = nltk.corpus.stopwords.words('english')
  stopWords.extend(['go', 'get', 'like', 'got', 'us'])
  inputParameters = getInputParameters()
  numberTopics = 9

  dataArrSegment = getDataThatMatchesInputParameters(inputParameters, stopWords)
  ldaTopicGraphsVisualization, ldaModel = getLDATopicGraphsVisualizationFromDataArr(dataArrSegment, numberTopics)
  ldaWordCloudVisualization = getLDAWordCloudVisualization(stopWords, ldaModel)

  output = io.BytesIO()
  FigureCanvas(ldaTopicGraphsVisualization).print_png(output)
  return Response(output.getvalue(), mimetype='image/png')
  # return make_response(jsonify(Response(output.getvalue(), mimetype='image/png')), 200)


  # canvas = FigureCanvas(ldaVisualization)
  # ax = ldaVisualization.gca()
  # ax.text(0.0,0.0, 'Test', fontsize=45)
  # ax.axis('off')
  # canvas.draw()       # draw the canvas, cache the renderer
  # image = np.fromstring(canvas.tostring_rgb(), dtype='uint8')
  # json_dump = json.dumps(image, cls=NumpyEncoder)
  outputLDATopicGraphsVisualization = io.BytesIO()
  FigureCanvas(ldaTopicGraphsVisualization).print_png(outputLDATopicGraphsVisualization)
  encodedLDATopicGraphsVisualization = base64.b64encode(outputLDATopicGraphsVisualization.getvalue()).decode('utf-8')

  outputLDAWordCloudVisualization = io.BytesIO()
  FigureCanvas(ldaWordCloudVisualization).print_png(outputLDAWordCloudVisualization)
  encodedLDAWordCloudVisualization = base64.b64encode(outputLDAWordCloudVisualization.getvalue()).decode('utf-8')

  return createParsableJSONResponse({
    'topicGraphs': encodedLDATopicGraphsVisualization,
    'wordCloud': encodedLDAWordCloudVisualization
  })


if __name__ == '__main__':
  runLDAGivenInputParameters()
