const uiOutput = {
  'Rk': 'Ranking',
  'G': 'Games Played',
  'GS': 'Games Started',
  'Cmp': 'Completions',
  'Att': 'Attempts',
  'Cmp%': 'Completion %',
  'Yds': 'Yards',
  'TD': 'TouchDowns',
  'TD%': 'TouchDowns %',
  'Int': 'Interceptions',
  'Int%': 'Interceptions %',
  '1D': 'First Downs',
  'Lng': 'Longest Pass',
  'Y/A': 'Yards / Attempt',
  'Y/G': 'Yards / Game',
  'Rate': 'Rating',
  'Sk': 'Sacks'
};
var dataMap = {};
var currYear;
var currXAxisVariable;
var currYAxisVariable;
var margin;
var width;
var height;
var tooltip;
var colorScale;


async function init() {
  var startingDataYear = 2010;
  margin = { top: 50, right: 100, bottom: 80, left: 50 };
  width = 960 - margin.left - margin.right;
  height = 650 - margin.top - margin.bottom;

  var csvFiles = [...Array(10).keys()].map(i => d3.csv('https://jackdedobb.github.io/data/' + (i + startingDataYear) + 'Passing.csv'))
  Promise.all(csvFiles).then(function(files) {
    files.forEach(function(file, idx) {
      dataMap[idx + startingDataYear] = file;
    });
    renderGraphs(startingDataYear);
  });

  d3.selectAll('img').on('click', handleYearChange);
}

function renderGraphs(year) {
  var svg = d3.select('#treemap'), margin = { top: 35, left: 90, bottom: 0, right: 15 }, width = +svg.attr('width'), height = +svg.attr('height');

  svg.append('g').attr('transform', `translate(${margin.left},0)`).attr('class', 'y-axis');
  svg.append('g').attr('transform', `translate(0,${margin.top})`).attr('class', 'x-axis');

  d3.select('svg').append("text")
                  .attr("transform", "translate(" + ((width / 2) - 210) + " ," + (height + margin.bottom + 30) + ")")
                  .attr('font-size', 15)
                  .attr("font-weight", 700)
                  .style("text-anchor", "middle")
                  .text('Lowest Ranked');

  d3.select('svg').append("text")
                  .attr("transform", "translate(" + ((width / 2) + 30) + " ," + (height + margin.bottom + 30) + ")")
                  .attr('font-size', 15)
                  .attr("font-weight", 700)
                  .style("text-anchor", "middle")
                  .text('Highest Ranked');

  updateGraphs(year, 'TD', 'Yds', 0);
}

function updateGraphs(year, xAxisVariable, yAxisVariable, speed) {
  currYear = year || currYear;
  currXAxisVariable = xAxisVariable || currXAxisVariable;
  currYAxisVariable = yAxisVariable || currYAxisVariable;

  var dataForYear = dataMap[currYear];
  var xDataPoints = dataForYear.map(x => parseFloat(x[currXAxisVariable]));
  var yDataPoints = dataForYear.map(x => parseFloat(x[currYAxisVariable]));
  var rankDataPoints = dataForYear.map(x => parseFloat(parseInt(x['Rk'])));

  var xAxisScale = d3.scaleLinear().domain([Math.min(...xDataPoints), Math.max(...xDataPoints)]).range([0,500]);
  var yAxisScale = d3.scaleLinear().domain([Math.min(...yDataPoints), Math.max(...yDataPoints)]).range([500,0]);
  colorScale = d3.scaleQuantile().domain(rankDataPoints).range(['#0A2F51', '#0E4D64', '#137177', '#188977', '#1D9A6C', '#39A96B', '#56B870', '#74C67A', '#99D492', '#BFE1B0', '#DEEDCF']);


  // Remove Previous
  d3.selectAll('circle').remove();
  d3.selectAll('text').remove();
  d3.selectAll('line').remove();
  d3.selectAll('g').filter(function() { return d3.select(this).attr('class') === 'tick'; }).remove();
  d3.selectAll('path').filter(function() { return d3.select(this).attr('class') === 'domain'; }).remove();

  // circles
  d3.select('svg').append('g')
                  .attr('transform', 'translate(75,50)')
                  .selectAll().data(dataForYear.slice().reverse()).enter().append('circle')
                                                  .attr('cx', x => xAxisScale(parseFloat(x[currXAxisVariable])))
                                                  .attr('cy', x => yAxisScale(parseFloat(x[currYAxisVariable])))
                                                  .attr('r', x => (8))
                                                  .style('fill', x => (parseInt(x['Rk']) == 1)? 'red' : colorScale(parseInt(x['Rk'])))
                                                  .on('mousemove', tooltipHover)
                                                  .on('mouseout', tooltipLeave);

  // axes
  d3.select('svg').append('g')
                  .attr('transform', 'translate(75,50)')
                  .attr('fill', 'none')
                  .attr('font-size', 10)
                  .attr('font-family', 'sans-serif')
                  .attr('text-anchor', 'middle').call(d3.axisLeft(yAxisScale))
                                                .attr('transform', 'translate(64,50)');

  d3.select('svg').append('g')
                  .attr('transform', 'translate(75,50)')
                  .attr('fill', 'none')
                  .attr('font-size', 10)
                  .attr('font-family', 'sans-serif')
                  .attr('text-anchor', 'middle').call(d3.axisBottom(xAxisScale))
                                                .attr('transform', 'translate(75,561)');

  // axes labels
  d3.select('svg').append("text")
                  .attr("transform", "translate(" + ((width / 2) - 80) + " ," + (height + margin.bottom + 3) + ")")
                  .attr('font-size', 20)
                  .attr("font-weight", 700)
                  .style("text-anchor", "middle")
                  .text(uiOutput[currXAxisVariable]);

  d3.select('svg').append("text")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 8)
                  .attr("x",0 - (height / 2) - 30)
                  .attr("dy", "1em")
                  .attr('font-size', 20)
                  .attr("font-weight", 700)
                  .style("text-anchor", "middle")
                  .text(uiOutput[currYAxisVariable]);

  // color key labels
  d3.select('svg').append("text")
                  .attr("transform", "translate(" + ((width / 2) - 210) + " ," + (height + margin.bottom + 30) + ")")
                  .attr('font-size', 15)
                  .attr("font-weight", 700)
                  .style("text-anchor", "middle")
                  .text('Lowest Ranked');

  d3.select('svg').append("text")
                  .attr("transform", "translate(" + ((width / 2) + 30) + " ," + (height + margin.bottom + 30) + ")")
                  .attr('font-size', 15)
                  .attr("font-weight", 700)
                  .style("text-anchor", "middle")
                  .text('Highest Ranked');

  // best quarterback blurb
  var bestQuarterback = dataForYear.filter(x => (parseInt(x['Rk']) == 1))[0];
  var bestQuarterBackXHighest = dataForYear.slice().sort(function(a, b) {
    return parseFloat(a[currXAxisVariable]) - parseFloat(b[currXAxisVariable]);
  }).reverse().findIndex(x => parseInt(x['Rk']) == 1) + 1;
  var bestQuarterBackYHighest = dataForYear.slice().sort(function(a, b) {
    return parseFloat(a[currYAxisVariable]) - parseFloat(b[currYAxisVariable]);
  }).reverse().findIndex(x => parseInt(x['Rk']) == 1) + 1;
  var linesOfText = [
    bestQuarterback['Player'].slice(0, bestQuarterback['Player'].indexOf('\\')).replace(/\*/g, '').replace(/\+/g, '') + ' was ranked as',
    'the best Quarterback in ' + currYear + '.',
    'On this chart specifically, he has',
    'the ' + ordinal_suffix_of(bestQuarterBackXHighest) + ' highest ' + uiOutput[currXAxisVariable] + ' (' + bestQuarterback[currXAxisVariable] + ')',
    'and the ' + ordinal_suffix_of(bestQuarterBackYHighest) + ' highest ' + uiOutput[currYAxisVariable] + ' (' + bestQuarterback[currYAxisVariable] + ').'
  ];
  linesOfText.forEach(function(lineOfText, idx) {
    d3.select('svg').append("text")
                    .attr("transform", "translate(" + ((width - 150)) + " ," + (margin.top + 30 + (idx * 20)) + ")")
                    .attr('font-size', 15)
                    .attr("font-weight", 700)
                    .style("text-anchor", "left")
                    .text(lineOfText);
  });

  // red line to best quarterback blurb
  var redDotXLocation = xAxisScale(parseFloat(bestQuarterback[currXAxisVariable])) + 75;
  var redDotYLocation = yAxisScale(parseFloat(bestQuarterback[currYAxisVariable])) + 50;
  d3.select('svg').append('line')
                  .style("stroke", "red")
                  .style("stroke-width", 2)
                  .attr("x1", redDotXLocation + 15)
                  .attr("y1", redDotYLocation)
                  .attr("x2", (width - 155))
                  .attr("y2", (margin.top + 25));

  var linearEquation = findLineByLeastSquares(xDataPoints, yDataPoints);
  var m = linearEquation[0], b = linearEquation[1];
  d3.select('svg').append('line')
                  .attr('transform', 'translate(75,50)')
                  .style("stroke", "black")
                  .style("stroke-width", 4)
                  .attr("x1", xAxisScale(Math.min(...xDataPoints)))
                  .attr("y1", yAxisScale(m * Math.min(...xDataPoints) + b))
                  .attr("x2", xAxisScale(Math.max(...xDataPoints)))
                  .attr("y2", yAxisScale(m * Math.max(...xDataPoints) + b));

  d3.select('svg').append("text")
                  .attr("transform", "translate(" + ((width - 150)) + " ," + (margin.top + 310) + ")")
                  .attr('font-size', 15)
                  .attr("font-weight", 700)
                  .style("text-anchor", "left")
                  .text('The line of best fit for this chart is:');
  d3.select('svg').append("text")
                  .attr("transform", "translate(" + ((width - 150)) + " ," + (margin.top + 330) + ")")
                  .attr('font-size', 15)
                  .attr("font-weight", 700)
                  .style("text-anchor", "left")
                  .text(uiOutput[yAxisVariable] + ' = ' + m.toFixed(3) + ' * ' + uiOutput[xAxisVariable] + ' + ' + b.toFixed(3));
}

function handleYearChange() {
  var id = this.id;
  d3.selectAll('img').each(function() {
    d3.select(this).style('opacity', (this.id == id)? '1' : '.5')
                   .style('border', ((this.id == id)? '8px solid green' : '4px solid black'));
  });
  updateGraphs(id, null, null, 750);
}

function handleDropDown(xAxis, value) {
  updateGraphs(null, xAxis? value : null, xAxis? null : value, 750);
}

function swapAxes() {
  document.getElementById('xAxisDropDown').value = currYAxisVariable;
  document.getElementById('yAxisDropDown').value = currXAxisVariable;
  updateGraphs(null, currYAxisVariable, currXAxisVariable, 750);
}

function tooltipLeave() {
  tooltip.transition().duration(200).style('opacity', 0);
  d3.selectAll('#tooltip').remove();
}

function tooltipHover(dataPoint) {
  d3.selectAll('#tooltip').remove();
  tooltip = d3.select('body').append('div')
                             .attr('id', 'tooltip')
                             .style('opacity', 0)
                             .style('font-size', '16px')
                             .attr('class', 'tooltip')
                             .style('border', 'thick solid black');

  var fieldOrder = ['Rk', 'G', 'GS', 'Cmp', 'Att', 'Cmp%', 'Yds', 'TD', 'TD%', 'Int', 'Int%', '1D', 'Lng', 'Y/A', 'Y/G', 'Rate', 'Sk'];

  var htmlString = '<div><strong>' + dataPoint['Player'].slice(0, dataPoint['Player'].indexOf('\\')).replace(/\*/g, '').replace(/\+/g, '') + '</strong></div>';
  htmlString += '-----------------------';
  fieldOrder.forEach(function(field) {
    var styleRed = (field === currXAxisVariable || field === currYAxisVariable)? ' style="color:green;"' : '';
    htmlString += '<div' + styleRed + '><strong>' + uiOutput[field] + ': </strong>' + parseFloat(dataPoint[field].toString()) + '</div>';
  });

  tooltip.style('opacity', 1)
         .style('left', (d3.event.pageX + 5) + 'px')
         .style('top', (d3.event.pageY + 5) + 'px').html(htmlString)
         .style('backgroundColor', colorScale(parseInt(dataPoint['Rk'])));
}

function ordinal_suffix_of(i) {
  var j = i % 10, k = i % 100;
  if (j == 1 && k != 11) {
    return i + 'st';
  } else if (j == 2 && k != 12) {
    return i + 'nd';
  } else if (j == 3 && k != 13) {
    return i + 'rd';
  }
  return i + 'th';
}

function findLineByLeastSquares(values_x, values_y) {
  var x_sum = 0;
  var y_sum = 0;
  var xy_sum = 0;
  var xx_sum = 0;
  var count = 0;
  var x = 0;
  var y = 0;
  var values_length = values_x.length;

  for (let i = 0; i < values_length; i++) {
    x = values_x[i];
    y = values_y[i];
    x_sum += x;
    y_sum += y;
    xx_sum += x*x;
    xy_sum += x*y;
    count++;
  }

  var m = (count*xy_sum - x_sum*y_sum) / (count*xx_sum - x_sum*x_sum);
  var b = (y_sum/count) - (m*x_sum) / count;
  return [m, b];
}
