function initDatepickers() {
    const datefield = document.getElementById('id_date_min');
    if (datefield.type != "date") { //if browser doesn't support input type="date", initialize date picker widget:
        $(document).ready(function () {
            $('#id_date_min').datepicker({dateFormat: 'yy-mm-dd'});
            $('#id_date_max').datepicker({dateFormat: 'yy-mm-dd'});
        });
    }
}


function renderChart() {
    // Set the dimensions of the canvas / graph
    var margin = {top: 30, right: 20, bottom: 70, left: 50},
        width = 600 - margin.left - margin.right,
        height = 300 - margin.top - margin.bottom;

    // Parse the date / time
    var parseDate = d3.timeParse("%Y-%m-%d");

    // Set the ranges
    var x = d3.scaleTime().range([0, width]);
    var y = d3.scaleLinear().range([height, 0]);

    // Define the line
    var plcline = d3.line()
        .x(function(d) { return x(d.date); })
        .y(function(d) { return y(d.uptime); });

    // Adds the svg canvas
    var svg = d3.select("#universe")
        .append("div")
        .classed("svg-container", true)
        .append("svg")
        .attr("preserveAspectRatio", "xMinYMin meet")
        .attr("viewBox", "0 0 600 400")
        .classed("svg-content-responsive", true)
        // .attr("width", width + margin.left + margin.right)
        // .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform",
            "translate(" + margin.left + "," + margin.top + ")");

    // Prepare the data
    window.data.forEach(function(d) {
        d.date = parseDate(d.date);
        d.uptime = d.uptime === null ? undefined : d.uptime;
    });

    // Scale the range of the data
    x.domain(d3.extent(data, function(d) { return d.date; }));
    y.domain([0, d3.max(data, function(d) { return d.uptime; })]);

    // Nest the entries by symbol
    var dataNest = d3.nest()
        .key(function(d) {return d.symbol;})
        .entries(data);
    // set the colour scale
    var color = d3.scaleOrdinal(d3.schemeCategory10);
    legendSpace = width/dataNest.length; // spacing for the legend

    // Loop through each symbol / key
    dataNest.forEach(function(d,i) {
        const c = color(i);
        svg.append("path")
            .attr("class", "line")
            .style("stroke", function() { // Add the colours dynamically
                return d.color = c; })
            .attr("id", 'tag'+d.key.replace(/\s+/g, '')) // assign an ID
            .attr("d", plcline(d.values));

        // Add the Legend
        svg.append("text")
            .attr("x", (legendSpace/2)+i*legendSpace)  // space legend
            .attr("y", height + (margin.bottom / 2) + 45)
            .attr("class", "legend")    // style the legend
            .style("fill", function() { // Add the colours dynamically
                return d.color = c; })
            .on("click", function(){
                // Determine if current line is visible
                var active = d.active ? false : true,
                    newOpacity = active ? 0 : 1;
                // Hide or show the elements based on the ID
                d3.select("#tag"+d.key.replace(/\s+/g, ''))
                    .transition().duration(100)
                    .style("opacity", newOpacity);
                // Update whether or not the elements are active
                d.active = active;
            })
            .text(d.key);
    });

    // Add the X Axis
    svg.append("g")
        .attr("class", "axis")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "translate(-15 20) rotate(315)")
    ;

    // Add the Y Axis
    svg.append("g")
        .attr("class", "axis")
        .call(d3.axisLeft(y).tickFormat(d3.format(".2p")));
}

document.addEventListener("DOMContentLoaded", initDatepickers);
document.addEventListener("DOMContentLoaded", renderChart);
