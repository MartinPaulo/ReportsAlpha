/**
 * Created by mpaulo on 4/07/2016.
 */
'use strict';

var report = report || {};

report.d3 = function () {


    (function checkIfStyleSheetLoaded() {
        var stylesheetName = "UptimeGraph.css";
        var found = false;
        for (var i = 0; i < document.styleSheets.length; i++) {
            if (document.styleSheets[i].href && document.styleSheets[i].href.indexOf("UptimeGraph.css") > 0) {
                found = true;
            }
        }
        console.log("Required stylesheet " + stylesheetName + " is present: " + found)
    })();


    var uptimeDataTemplate = [
        {
            key: "first service",
            values: [
                // start and end time being number of milliseconds since 1970/01/01.
                // As returned by new Date().getTime();
                // to convert to a date simply do var date = new Date(1468986686293);
                {start: 1457000000000, end: 1458000000000, planned: true},
                {start: 1458000000000, end: 1458900000000, planned: false},
                {start: 1468050000000, end: 1468060000000, planned: true},
                {start: 1468800000000, end: 1468900000000, planned: false}
            ]
        },
        {
            key: "second service",
            values: [
                {start: 1468986686293, end: 1468986700000, planned: true},
                {start: 1468000000000, end: 1468900000000, planned: false}
            ]
        }
    ];


    function uptimeGraph() {

        /*
         Based on work done by Florian Roscheck: so this graph is, I guess:

         Copyright (c) 2016 Florian Roscheck

         Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
         associated documentation files (the "Software"), to deal in the Software without restriction,
         including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
         and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
         subject to the following conditions:

         The above copyright notice and this permission notice shall be included in all copies or substantial
         portions of the Software.

         THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
         LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
         IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
         WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
         SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

         */
        var margin = {top: 70, right: 100, bottom: 20, left: 100}
            , width = null
            , minimumWidth = 800
            , barHeight = 18    // it would be good if we could read this off of the style.
            , lineSpacing = 14
            , paddingLeft = -100
            , paddingBottom = 10
            , dataHeight = 18 // height of bars
            , paddingTopHeading = -50
            , headingText = "Uptime"
            , transitionDuration = 0
            ;

        var calculateWidth = function (width, container, margin) {
            var newWidth = (width || parseInt(container.style('width'), 10) || 960) - margin.left - margin.right;
            return newWidth < minimumWidth ? minimumWidth : newWidth;
        };

        // global div for tooltip
        var div = d3.select('body').append('div')
            .attr('class', 'tooltip')
            .style('opacity', 0);

        function chart(selection) {
            var endDate = new Date(); // end today
            var startDate = new Date(endDate.getTime());
            startDate.setFullYear(startDate.getFullYear() - 1); // and start one year ago
            console.log("Start: " + startDate);
            console.log("End  : " + endDate);

            selection.each(function drawGraph(dataset, i) {

                var container = d3.select(this);

                // for the moment, just give it the nvd3-svg class so that it takes on the nvd3 stylesheet
                // attributes rather than the default ones. (needed for resizing)
                container.attr('class', 'nvd3-svg');

                chart.update = function () {
                    container.selectAll('*').remove();
                    container.transition().duration(transitionDuration).call(chart);
                };

                var availableWidth = calculateWidth(width, container, margin);

                var noOfDataSets = dataset.length;

                var xScale = d3.time.scale()
                        .domain([startDate, endDate])
                        .range([0, availableWidth])
                    ;
                var xAxis = d3.svg.axis()
                        .orient('top')
                        .scale(xScale)
                    ;

                var height = (barHeight + lineSpacing) * noOfDataSets;

                var svg = d3.select(this)
                        .attr('width', availableWidth + margin.left + margin.right)
                        .attr('height', height + margin.top + margin.bottom)
                        .append('g')
                        .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')
                    ;

                svg.append('g').attr('id', 'g_title');
                svg.append('g').attr('id', 'g_axis');
                svg.append('g').attr('id', 'g_data');

                // set the y axis labels
                svg.select('#g_axis')
                    .selectAll('text')
                    .data(dataset)
                    .enter()
                    .append('text')
                    .attr('x', paddingLeft)
                    .attr('y', lineSpacing + barHeight / 2)
                    .text(function (d) {
                        return d.key;
                    })
                    .attr('transform', function (d, i) {
                        return 'translate(0,' + ((lineSpacing + barHeight) * i) + ')';
                    })
                    .attr('class', 'uptm_ytitle');

                // the vertical lines
                svg.select('#g_axis').selectAll('line.uptm_vert_grid')
                    .data(xScale.ticks())
                    .enter()
                    .append('line')
                    .attr({
                        'class': 'uptm_vert_grid',
                        'x1': function (d) {
                            return xScale(d.getTime());
                        },
                        'x2': function (d) {
                            return xScale(d.getTime());
                        },
                        'y1': 0,
                        'y2': dataHeight * noOfDataSets + lineSpacing * noOfDataSets - 1 + paddingBottom
                    });

                // draw the uptime lines (assume that it is up 100% of the time)
                svg.select('#g_axis').selectAll('line.uptime_line')
                    .data(dataset)
                    .enter()
                    .append('rect')
                    .attr('class', 'uptime_line')
                    .attr('height', dataHeight)
                    .attr('width', xScale(endDate))
                    .attr('x', xScale(startDate))
                    .attr('y', function (d, i) {
                        return (lineSpacing + dataHeight) * i + lineSpacing;
                    })
                ;

                // the x axis labels
                svg.select('#g_axis')
                    .append('g')
                    .attr('class', 'uptm_axis')
                    .call(xAxis);

                var g = svg.select('#g_data').selectAll('.g_data')
                    .data(dataset)
                    .enter()
                    .append('g')
                    .attr('transform', function (d, i) {
                        return 'translate(0,' + ((lineSpacing + dataHeight) * i) + ')';
                    })
                    .attr('class', 'dataset');

                g.selectAll('rect')
                    .data(function (d) {
                        return d.values;
                    })
                    .enter()
                    .append('rect')
                    .attr('x', function (d) {
                        return xScale(new Date(d.start));
                    })
                    .attr('y', lineSpacing)
                    .attr('width', function (d) {
                        return (Math.ceil(xScale(new Date(d.end)) - xScale(new Date(d.start))));
                    })
                    .attr('height', dataHeight)
                    .attr('class', function (d) {
                        if (d.planned) {
                            return 'uptm_planned';
                        }
                        return 'uptm_unplanned';
                    })
                    .on('mouseover', function (d, i) {
                        var matrix = this.getScreenCTM().translate(+this.getAttribute('x'), +this.getAttribute('y'));
                        div.transition()
                            .duration(200)
                            .style('opacity', 0.9);
                        div.html(function () {
                            var output = '';
                            if (d.planned) {
                                output = '<i class="uptm_tooltip uptm_tooltip_check tooltip_has_data"></i>';
                            } else {
                                output = '<i class="uptm_tooltip uptm_tooltip_cross tooltip_has_no_data"></i>';
                            }
                            var hoursOut = Math.abs(d.start - d.end) / 36e5;
                            hoursOut = hoursOut > 1 ? hoursOut.toFixed(1) : hoursOut.toPrecision(1);
                            return output + new Date(d.start).toISOString().slice(0, 10) + ' ' + hoursOut + 'h';
                        }).style('left', function () {
                            return window.pageXOffset + matrix.e + 'px';
                        }).style('top', function () {
                            return window.pageYOffset + matrix.f - 11 + 'px';
                        }).style('height', dataHeight + 11 + 'px');
                    })
                    .on('mouseout', function () {
                        div.transition()
                            .duration(500)
                            .style('opacity', 0);
                    })
                ;
                svg.select('#g_title')
                    .append('text')
                    .attr('x', paddingLeft)
                    .attr('y', paddingTopHeading)
                    .text(headingText)
                    .attr('class', 'uptm_heading');

                svg.select('#g_title')
                    .append('text')
                    .attr('x', paddingLeft)
                    .attr('y', paddingTopHeading + 17)
                    .text('from ' + startDate.toISOString().slice(0, 10) + ' to ' + endDate.toISOString().slice(0, 10))
                    .attr('class', 'uptm_subheading');

                // create legend
                var legend = svg.select('#g_title')
                    .append('g')
                    .attr('id', 'g_legend')
                    .attr('transform', 'translate(0,-12)');

                legend.append('rect')
                    .attr('x', availableWidth + margin.right - 150)
                    .attr('y', paddingTopHeading)
                    .attr('height', 15)
                    .attr('width', 15)
                    .attr('class', 'uptm_planned');

                legend.append('text')
                    .attr('x', availableWidth + margin.right - 150 + 20)
                    .attr('y', paddingTopHeading + 8.5)
                    .text('Planned')
                    .attr('class', 'uptm_legend');

                legend.append('rect')
                    .attr('x', availableWidth + margin.right - 150)
                    .attr('y', paddingTopHeading + 17)
                    .attr('height', 15)
                    .attr('width', 15)
                    .attr('class', 'uptm_unplanned');

                legend.append('text')
                    .attr('x', availableWidth + margin.right - 150 + 20)
                    .attr('y', paddingTopHeading + 8.5 + 15 + 2)
                    .text('Unplanned')
                    .attr('class', 'uptm_legend');

            });

        }

        chart.width = function (_) {
            if (!arguments.length) return width;
            width = _;
            return chart;
        };

        return chart;
    }


    var datacenterColours = {
        'QH2': 'chocolate',
        'QH2-UoM': 'green',
        'NP': 'blue',
        'Other data centers': 'lightblue'
    };

    var getColour = function (key) {
        return key in datacenterColours && typeof datacenterColours[key] === 'string' ? datacenterColours[key] : 'black';
    };

    var render = function () {

        var margin = {top: 5, right: 40, bottom: 25, left: 120},
            width = 960 - margin.left - margin.right,
            height = 60 - margin.top - margin.bottom;
        var chart = nv.models.bulletChart();
        chart.bullet.color(function (d) {
            return d.color
        });
        var data = exampleData();

        function renderBullet(target) {
            target
                .attr("class", "bullet")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append('g')
                .transition().duration(500)
                .call(chart)
            ;

        }

        //    d3.select('#chart').select('svg').remove();
        var target = d3.select('#chart')
            .selectAll('svg') // required to move parentNode
            .data(data);    // join data to any existing elements
        renderBullet(target); // render on the existing elements
        renderBullet(target.enter().append('svg')); // render on the missing elements
        //nv.utils.windowResize(chart.update);

        console.log("Width " + d3.select('#extra svg').style('width'));
        var ug = uptimeGraph();
        d3.select('#extra svg')
            .datum(uptimeDataTemplate)
            .call(ug);

        nv.utils.windowResize(ug.update);

    };

    function exampleData() {
        return [
            {
                "title": "NP Uptime",  // Label the bullet chart
                "subtitle": "% Available", // sub-label for bullet chart
                "ranges": [93.00, 100], // Minimum, mean and maximum values.
                "rangeLabels": ["National", ""],
                "measures": [98.05], // Value representing current measurement (the thick blue line in the example)
                "measureLabels": ["Current"],
                "markers": [99.99], // Place a marker on the chart (the white triangle marker)
                "markerLabels": ["Target"],
                "color": 'blue'
            },
            {
                "title": "QH2-UoM Uptime",
                "subtitle": "% Available",
                "ranges": [93.00, 100],
                "rangeLabels": ["National", ""],
                "measures": [97.05],
                "measureLabels": ["Current"],
                "markers": [99.99],
                "markerLabels": ["Target"]
                , "color": 'green'
            },
            {
                "title": "QH2 Uptime",
                "subtitle": "% Available",
                "ranges": [93.00, 100],
                "rangeLabels": ["National", ""],
                "measures": [98.05],
                "measureLabels": ["Current"],
                "markers": [99.99],
                "markerLabels": ["Target"],
                "color": 'chocolate'
            }
        ];
    }

    return {
        render: render,
        exampleData: exampleData
    }
}();