'use strict';

var report = report || {};

report.d3 = function () {

    utils.createDateButtons();


    var render = function (csv_path) {

        var data_path = '/reports/csv/3?from=' + utils.findFrom();

        d3.json(data_path, function (error, data) {
            var chart = nv.models.stackedAreaChart()
                .margin({right: 100})
                .x(function (d) {
                    return d[0]
                })
                .y(function (d) {
                    return d[1]
                })
                .useInteractiveGuideline(true)
                .rightAlignYAxis(true)
                .showControls(true)
                .controlOptions(['Stacked', 'Expanded'])
                .clipEdge(true);

            chart.xAxis
                .tickFormat(function (d) {
                    return d3.time.format('%Y-%m-%d')(new Date(d))
                });

            chart.yAxis
                .tickFormat(d3.format(',.2f'));

            d3.select('#chart svg')
                .datum(data)
                .transition().duration(500)
                .call(chart);

            // Update chart when the window resizes
            nv.utils.windowResize(chart.update);

            return chart;
        });
    };

    d3.select('#chart svg')[0][0].addEventListener('redraw', function (e) {
        render();
    }, false);

    return {
        render: render
    }
}();