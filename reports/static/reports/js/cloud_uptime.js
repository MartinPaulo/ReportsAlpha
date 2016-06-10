'use strict';

var report = report || {};

report.d3 = function () {

    // Some thoughts on uptime: http://uptime.netcraft.com/accuracy.html#uptime
    
    utils.createDateButtons();

    var datacenterColours = {
        'queensbury 1': 'chocolate',
        'queensbury 2': 'green',
        'noble park': 'blue',
        'other data centers': 'lightblue'
    };

    var getColour = function (key) {
        return key in datacenterColours && typeof datacenterColours[key] === 'string' ? datacenterColours[key] : 'black';
    };

    var render = function () {
        var data_path = '/reports/manufactured/cloud_uptime/?from=' + utils.findFrom();
        d3.select('#a_data').attr('href', data_path);
        d3.json(data_path, function (data) {
            nv.addGraph(function () {
                var chart = nv.models.multiBarChart()
                        .x(function (d) {
                            return d[0]
                        })
                        .y(function (d) {
                            return d[1]
                        })
                        .useInteractiveGuideline(true)
                        //.rightAlignYAxis(true)          // Move the y-axis to the right side.
                        .noData('No Data available')
                        .clipEdge(true)
                        .reduceXTicks(true)   //If 'false', every single x-axis tick label will be rendered.
                        .groupSpacing(0.1)    //Distance between each group of bars.
                        .showControls(false)            // Don't allow user to choose 'Stacked', 'Stream' etc...
                    .color(function (d) {
                        return getColour(d['key']);
                    })
                    ;

                chart.yAxis
                    .tickFormat(d3.format('4d'))
                    .axisLabel('Days');

                chart.xAxis
                    .tickFormat(function (d) {
                        return d3.time.format('%Y-%m-%d')(new Date(d))
                    })
                    .axisLabel('Date');

                d3.select('#chart svg')
                    .datum(data)
                    .call(chart);

                //figure out a good way to do this automatically
                nv.utils.windowResize(chart.update);

                return chart;
            });
        });
    };

    d3.select('#chart svg')[0][0].addEventListener('redraw', function (e) {
        render();
    }, false);

    return {
        render: render
    }
}();