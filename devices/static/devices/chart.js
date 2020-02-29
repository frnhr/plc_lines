/**
 * JS which runs on chart page.
 *
 * Party like it's 1995!
 * This JS runs inside pdfkit virtual browser (wkhtmltopdf), which doesn't understand
 * many modern JS constructs (e.g. cannot use "let" even).
 */

function initDatepickers() {
    var datefield = document.getElementById('id_date_min');
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
        .y(function(d) { return y(d.uptime); })
    ;

    // Adds the svg canvas
    var svg = d3.select("#universe")
        .append("div")
        .classed("svg-container", true)
        .append("svg")
        .attr("preserveAspectRatio", "xMinYMin meet")
        .attr("viewBox", "0 0 600 400")
        .classed("svg-content-responsive", true)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
    ;

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
        .key(function(d) { return d.symbol; })
        .entries(data);
    // set the colour scale
    var color = d3.scaleOrdinal(d3.schemeCategory10);

    var legendCount = 0;
    dataNest.forEach(function(d, i) {
        if (d.values[0].uptime !== undefined) legendCount++;
    });
    var legendSpace = legendCount ? width / legendCount : width; // spacing for the legend

    // Loop through each symbol / key
    var legend_i = -1;
    dataNest.forEach(function(d, i) {
        var c = color(i);
        if (d.values[0].uptime === undefined) return;
        legend_i += 1;
        svg.append("path")
            .attr("class", "line")
            .style("stroke", function() { return d.color = c; })
            .attr("id", 'tag'+d.key.replace(/\s+/g, '').replace(/\./g, '_')) // assign an ID
            .attr("d", plcline(d.values))
        ;


        // Add the Legend
        var x_pos = (legendSpace/2 + legend_i * legendSpace) - 20;
        var y_pos = (height + (margin.bottom / 2) + 55);
        var rot = 25 * Math.min(1, Math.max(0, (legendCount - 4) / 3));
        svg.append("text")
            .attr("transform", "rotate(" + rot + " " + x_pos + " " + y_pos +")")
            .attr("text-anchor","middle")
            .attr("x", x_pos )  // space legend
            .attr("y", y_pos )
            .attr("class", "legend")    // style the legend
            .style("fill", function() { return d.color = c; })
            // .on("click", function(){  # toggle line visibility
            //     // Determine if current line is visible
            //     var active = d.active ? false : true,
            //         newOpacity = active ? 0 : 1;
            //     // Hide or show the elements based on the ID
            //     d3.select("#tag"+d.key.replace(/\s+/g, '').replace(/\./g, '_'))
            //         .transition().duration(100)
            //         .style("opacity", newOpacity);
            //     // Update whether or not the elements are active
            //     d.active = active;
            // })
            .text(d.key)
        ;
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
        .call(d3.axisLeft(y).tickFormat(d3.format(".2p")))
    ;
}

document.addEventListener("DOMContentLoaded", initDatepickers);
document.addEventListener("DOMContentLoaded", renderChart);
