import base64
import datetime
import gensim
import io
import json
import math
import matplotlib
import matplotlib.pyplot as plt
import nltk
import os
import pandas as pd
import re
import requests
from collections import Counter
from flask import Flask, request
from flask_cors import CORS
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from wordcloud import WordCloud


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
    'funnyVotesMax':  math.inf,
    'coolVotesMin':   0,
    'coolVotesMax':   math.inf,
    'usefulVotesMin': 0,
    'usefulVotesMax': math.inf,
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


def getDataThatMatchesInputParameters(inputParameters, stopWords, maxRecordsToPullIn):
  scriptDirectory = os.path.dirname(os.path.realpath(__file__))
  folderLocationOfDataFiles = scriptDirectory + '/../data/'
  dataLocationFiles = [folderLocationOfDataFiles + 'yelp_academic_dataset_review' + '{:02d}'.format(idx) + '.json' for idx in range(0, 21)]

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
  wordCloud = getWordCloud(stopWords, ldaModel)

  fig, ax = plt.subplots(1, 1, figsize=(100, 100), sharex=True, sharey=True)

  fig.add_subplot(ax)
  plt.gca().imshow(wordCloud)
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
  buf = np.frombuffer ( fig.canvas.tostring_argb(), dtype=np.uint8 )
  buf.shape = ( w, h,4 )

  # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
  buf = np.roll ( buf, 3, axis = 2 )
  return buf


def runLDAGivenInputParameters():
  # nltk.download('stopwords') # Comment back in, if need to download stopwords
  stopWords = nltk.corpus.stopwords.words('english')
  stopWords.extend(['go', 'get', 'like', 'got', 'us'])
  inputParameters = getInputParameters()
  numberTopics = 9
  maxRecordsToPullIn = 1000

  dataArrSegment = getDataThatMatchesInputParameters(inputParameters, stopWords, maxRecordsToPullIn)

  if (len(dataArrSegment) == 0):
    return createParsableJSONResponse({
      'noDataMatchingQuery': 'noDataMatchingQuery'
    })

  ldaTopicGraphsVisualization, ldaModel = getLDATopicGraphsVisualizationFromDataArr(dataArrSegment, numberTopics)
  ldaWordCloudVisualization = getLDAWordCloudVisualization(stopWords, ldaModel)

  outputLDATopicGraphsVisualization = io.BytesIO()
  FigureCanvas(ldaTopicGraphsVisualization).print_png(outputLDATopicGraphsVisualization)
  encodedLDATopicGraphsVisualization = base64.b64encode(outputLDATopicGraphsVisualization.getvalue()).decode('utf-8')

  outputLDAWordCloudVisualization = io.BytesIO()
  FigureCanvas(ldaWordCloudVisualization).print_png(outputLDAWordCloudVisualization)
  encodedLDAWordCloudVisualization = base64.b64encode(outputLDAWordCloudVisualization.getvalue()).decode('utf-8')

  # output = io.BytesIO()
  # FigureCanvas(ldaTopicGraphsVisualization).print_png(output)
  # return Response(output.getvalue(), mimetype='image/png')

  # image = Image.open(io.BytesIO(decodedLDAVisualization))
  # image.show()

  return createParsableJSONResponse({
    'topicGraphs': encodedLDATopicGraphsVisualization,
    'wordCloud': encodedLDAWordCloudVisualization
  })



  img1 = Image.frombytes('RGB', ldaVisualization.canvas.get_width_height(), ldaVisualization.canvas.tostring_rgb())
  img1.save('hererandom.png')
  img1.show()



  retTopicGraphs = fig2data(ldaVisualization)
  print(type(retTopicGraphs))

  img_w, img_h = 2560, 1600
  # data = np.zeros((img_h, img_w, 4), dtype=np.uint8)
  # data[100, 100] = [255, 0, 0]
  img = Image.fromarray(retTopicGraphs, 'RGBA')
  img.save('test.png')
  img.show()

  return createParsableJSONResponse({
    'topicGraphs': retTopicGraphs,
    'wordCloud': 69
  })


if __name__ == '__main__':
  runLDAGivenInputParameters()
