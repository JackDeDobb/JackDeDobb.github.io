var dataMap = {};
var margin;
var width;
var height;
var tooltip;
var x;
var y;
var z;
var keys;
var _csv;


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

    //TODO: call own function
    console.log(dataMap);
  });

  d3.selectAll('img').on('click', handleYearChange);
}

function chart(csv, filterYear) {
  keys = csv.columns.slice(2);
  _csv = csv;

  var svg = d3.select('#treemap'), margin = { top: 35, left: 90, bottom: 0, right: 15 }, width = +svg.attr('width'), height = +svg.attr('height');

  y = d3.scaleBand().range([margin.top, height - margin.bottom])
                    .padding(0.1)
                    .paddingOuter(0.2)
                    .paddingInner(0.2)

  x = d3.scaleLinear().range([margin.left, width - margin.right])

  svg.append('g').attr('transform', `translate(${margin.left},0)`).attr("class", "y-axis");
  svg.append('g').attr('transform', `translate(0,${margin.top})`).attr("class", "x-axis");

  z = d3.scaleOrdinal().range(['red', 'steelblue']).domain(keys);

  update(filterYear, 0)
}

function update(input, speed) {
  var svg = d3.select('#treemap');
  var data = (input != null)? _csv.filter(f => f.year == input) : _csv;

  data.forEach(function(d) {
    d.total = d3.sum(keys, k => +d[k])
    return d
  })

  x.domain([0, d3.max(data, d => d.total)]).nice();

  svg.selectAll(".x-axis").transition().duration(speed).call(d3.axisTop(x).ticks(null, "s"));

  data.sort((a, b) => b.total - a.total);

  y.domain(data.map(d => d.lexeme));

  svg.selectAll(".y-axis").transition().duration(speed).call(d3.axisLeft(y).tickSizeOuter(0));

  var group = svg.selectAll("g.layer").data(d3.stack().keys(keys)(data), d => d.key);
  group.exit().remove()
  group.enter().insert("g", ".y-axis").append("g")
                                      .classed("layer", true)
                                      .attr("fill", function (d) {return z(d.key)});

  var bars = svg.selectAll("g.layer").selectAll("rect").data(d => d, function (e) { return e.data.lexeme; });
  bars.exit().remove();
  bars.enter().append("rect")
              .attr("height", y.bandwidth())
              .merge(bars)
              .on("mouseout", tooltipleave)
              .transition().duration(speed)
              .attr("y", d => y(d.data.lexeme))
              .attr("x", function (d) {return x(d[0]);})
              .attr("width", d => x(d[1]) - x(d[0]));
}

function handleYearChange() {
  var id = this.id;
  d3.selectAll('img').each(function() {
    d3.select(this).style('opacity', (this.id == id)? '1' : '.5')
                   .style('border', ((this.id == id)? '8px solid green' : '4px solid black'));
  });
  update(id, 750);
}

function tooltipleave() {
  tooltip.transition().duration(200).style('opacity', 0);
}
