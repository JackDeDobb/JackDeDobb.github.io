var dataMap = {};
var margin;
var width;
var height;
var tooltip;
var x;
var y;
var z;


async function init() {
  var startingDataYear = 2010;
  margin = { top: 50, right: 100, bottom: 80, left: 50 };
  width = 960 - margin.left - margin.right;
  height = 650 - margin.top - margin.bottom;

  tooltip = d3.select('body').append('div')
                             .style('opacity', 0)
                             .style('font-size', '16px')
                             .attr('class', 'tooltip');

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
  x = d3.scaleLinear().range([margin.left, width - margin.right]);
  y = d3.scaleBand().range([margin.top, height - margin.bottom]).padding(0.1).paddingOuter(0.2).paddingInner(0.2);
  // z = d3.scaleOrdinal().range(['red', 'steelblue']).domain(keys);

  svg.append('g').attr('transform', `translate(${margin.left},0)`).attr('class', 'y-axis');
  svg.append('g').attr('transform', `translate(0,${margin.top})`).attr('class', 'x-axis');

  updateGraphs(year, 'TD', 'Yds', 0);
}

function updateGraphs(year, xAxisVariable, yAxisVariable, speed) {
  var svg = d3.select('#treemap');
  var dataForYear = dataMap[year];

  var xDataPoints = dataForYear.map(x => parseInt(x[xAxisVariable]));
  var yDataPoints = dataForYear.map(x => parseInt(x[yAxisVariable]));


  var xAxisScale = d3.scaleLinear().domain([Math.min(...xDataPoints), Math.max(...xDataPoints)]).range([0,500]);
  var yAxisScale = d3.scaleLinear().domain([Math.min(...yDataPoints), Math.max(...yDataPoints)]).range([500,0]);

  d3.selectAll('circle').remove();
  d3.select('svg').append('g')
                  .attr('transform', 'translate(50,50)')
                  .selectAll().data(dataForYear).enter().append('circle')
                                                  .attr('cx', x => xAxisScale(parseInt(x[xAxisVariable])))
                                                  .attr('cy', x => yAxisScale(parseInt(x[yAxisVariable])))
                                                  .attr('r', x => (8));


  d3.selectAll('g').filter(function() {
    return d3.select(this).attr('class') === 'tick';
  }).remove();
  d3.selectAll('path').filter(function() {
    return d3.select(this).attr('class') === 'domain';
  }).remove();

  d3.select('svg').append('g')
                  .attr('transform', 'translate(50,50)')
                  .attr('fill', 'none')
                  .attr('font-size', 10)
                  .attr('font-family', 'sans-serif')
                  .attr('text-anchor', 'middle').call(d3.axisLeft(yAxisScale))
                                                .attr('transform', 'translate(39,50)');

  d3.select('svg').append('g')
                  .attr('transform', 'translate(50,50)')
                  .attr('fill', 'none')
                  .attr('font-size', 10)
                  .attr('font-family', 'sans-serif')
                  .attr('text-anchor', 'middle').call(d3.axisBottom(xAxisScale))
                                                .attr('transform', 'translate(50,561)');
}

function handleYearChange() {
  var id = this.id;
  d3.selectAll('img').each(function() {
    d3.select(this).style('opacity', (this.id == id)? '1' : '.5')
                   .style('border', ((this.id == id)? '8px solid green' : '4px solid black'));
  });
  updateGraphs(id, 'TD', 'Yds', 750);
}

function tooltipleave() {
  tooltip.transition().duration(200).style('opacity', 0);
}
