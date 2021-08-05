async function init() {
  var currentDate = new Date().toISOString().split('T')[0];
  dateWrittenMin.max = currentDate;
  dateWrittenMax.max = currentDate;
  dateWrittenMax.value = currentDate;

  addRowsToExampleReviewsTable(exampleReviewsTable);
}


async function getResponseFromBackEnd(url, jsonRequestParameters) {
  if (jsonRequestParameters && Object.keys(jsonRequestParameters).length > 0) {
    url += '?' + Object.keys(jsonRequestParameters).map(x => x + '=' + jsonRequestParameters[x]).join('&')
  }

  var response = null;
  await fetch(url)
        .then(function(response) {
          return response.json();
        }).then(function(data) {
          response = data.value;
        });

  return response;
}


function addRowsToExampleReviewsTable(tableReference) {
  var firstJsonFile = d3.text('https://jackdedobb.github.io/yelpApplication/data/exampleReviews.json');
  var rowCount = tableReference.rows.length;
  var colCount = tableReference.rows[0].cells.length;

  Promise.resolve(firstJsonFile).then(function(result) {
    var lines = result.split('\n').slice(0, 15);
    lines.forEach(function(line) {
      var parsedLine = JSON.parse(line);

      var row = tableReference.insertRow(rowCount);
      for (var i = 0; i < colCount; i++) {
        var newCellInnerHTML = null;
        var columnHeader = tableReference.rows[0].cells[i].innerHTML;
        switch (columnHeader) {
          case 'Star Rating': {
            newCellInnerHTML = parsedLine['stars'];
            break;
          } case '# Funny Votes': {
            newCellInnerHTML = parsedLine['votes']['funny'];
            break;
          } case '# Cool Votes': {
            newCellInnerHTML = parsedLine['votes']['cool'];
            break;
          } case '# Useful Votes': {
            newCellInnerHTML = parsedLine['votes']['useful'];
            break;
          } case 'User ID': {
            newCellInnerHTML = parsedLine['user_id'];
            break;
          } case 'Review ID': {
            newCellInnerHTML = parsedLine['review_id'];
            break;
          } case 'Business ID': {
            newCellInnerHTML = parsedLine['business_id'];
            break;
          } case 'Date': {
            newCellInnerHTML = parsedLine['date'];
            break;
          } case 'Review Text': {
            newCellInnerHTML = parsedLine['text'];
            break;
          }
        }
        row.insertCell(i).innerHTML = newCellInnerHTML;
      }
    });
  });
}

var functionProgressIdx = 0;
var interval;
function beginMoveProgressBar(progressBarElement, speed) {
  if (functionProgressIdx == 0) {
    functionProgressIdx = 1;
    var width = 1;
    interval = setInterval(frame, speed);
    function frame() {
      if (width >= 100) {
        clearInterval(interval);
        functionProgressIdx = 0;
      } else {
        progressBarElement.style.width = ++width + '%';
      }
    }
  }
}

async function runLDA() {
  var urlOfHostedBackendPythonCode = 'https://yelp-application-lda.herokuapp.com';
  var jsonRequestParameters = {
    'starRatingMin':  starRatingMin.value,
    'starRatingMax':  starRatingMax.value,
    'funnyVotesMin':  funnyVotesMin.value,
    'funnyVotesMax':  funnyVotesMax.value,
    'coolVotesMin':   coolVotesMin.value,
    'coolVotesMax':   coolVotesMax.value,
    'usefulVotesMin': usefulVotesMin.value,
    'usefulVotesMax': usefulVotesMax.value,
    'dateWrittenMin': dateWrittenMin.value,
    'dateWrittenMax': dateWrittenMax.value,
  };


  if (functionProgressIdx == 0) {
    ldaTopicGraphs.src = '';
    ldaWordCloud.src   = '';

    var progressBarElement = document.getElementById('loadingProgressBar');
    progressBarElement.style.backgroundColor = 'green';
    progressBarElement.style.width = 1 + '%';


    /*
    // Old Code below
    var hasErrored = false;
    beginMoveProgressBar(progressBarElement, 4000);
    var promiseFromBackendCall = await getResponseFromBackEnd(urlOfHostedBackendPythonCode, jsonRequestParameters)
    .catch(function(err) {
      hasErrored = true;
      progressBarElement.style.backgroundColor = 'red';
    });

    if (!hasErrored) {
      if ('noDataMatchingQuery' in promiseFromBackendCall) {
        progressBarElement.style.backgroundColor = 'yellow';
        ldaTopicGraphs.src = '/yelpApplication/images/no-results-found.jpg';
        ldaWordCloud.src   = '/yelpApplication/images/no-results-found.jpg';
      } else {
        ldaTopicGraphs.src = 'data:image/jpeg;base64,' + promiseFromBackendCall.topicGraphs;
        ldaWordCloud.src   = 'data:image/jpeg;base64,' + promiseFromBackendCall.wordCloud;
      }
    }
    */

    // New Code below



    clearInterval(interval);
    functionProgressIdx = 0;
    progressBarElement.style.width = 100 + '%';
  }
}
