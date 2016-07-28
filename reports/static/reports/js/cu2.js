/**
 * Created by mpaulo on 4/07/2016.
 */
'use strict';

var report = report || {};

report.d3 = function () {

    var bulletData = [
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

    var uptimeData = [
        // each array entry will be rendered as a separate graph.
        [
            {
                service: "first service",
                outages: [
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
                service: "second service",
                outages: [
                    {start: 1468986686293, end: 1468986700000, planned: true},
                    {start: 1468000000000, end: 1468900000000, planned: false}
                ]
            }
        ]
    ];

    var render = function () {

        var margin = {top: 5, right: 40, bottom: 25, left: 120},
            width = 960 - margin.left - margin.right,
            height = 60 - margin.top - margin.bottom;

        var chart = nv.models.bulletChart();
        chart.bullet.color(function (d) {
            return d.color
        });

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

        var target = d3.select('#chart')
            .selectAll('svg') // required to move parentNode
            .data(bulletData);    // join data to any existing elements
        renderBullet(target); // render on the existing elements
        renderBullet(target.enter().append('svg')); // render on the missing elements

        var ug = report.uptimeHistory();
        d3.select('#extra').selectAll('svg')
            .data(uptimeData)
            //.datum(null)
            .call(ug)
        ;

        nv.utils.windowResize(ug.update);
    };

    return {
        render: render
    }
}();