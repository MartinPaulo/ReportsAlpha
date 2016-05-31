'use strict';

var report = report || {};

report.d3 = function () {

    utils.createFacultyButtons();
    utils.createDateButtons();

    var render = function () {

        var data_path = '/reports/manufactured/faculty_allocated/?from=' + utils.findFrom() + '&type=' + utils.findType();
        
        document.getElementById('a_data').href = data_path;

        d3.json(data_path, function (error, data) {
            var chart = nv.models.stackedAreaChart()
                .margin({right: 100})
                .x(function (d) {
                    return d[0]
                })
                .y(function (d) {
                    return d[1]
                })
                .useInteractiveGuideline(true)    //Tooltips which show all data points. Very nice!
                .rightAlignYAxis(true)      //Let's move the y-axis to the right side.
                .showControls(false)       // Don't allow user to choose 'Stacked', 'Stream'
                .color(function (d) {
                    return utils.facultyColours.get(d['key']);
                });

            //Format x-axis labels with custom function.
            chart.xAxis
                .tickFormat(function (d) {
                    return d3.time.format('%Y-%m-%d')(new Date(d))
                })
                .axisLabel('Date');

            chart.yAxis
                .tickFormat(d3.format(',.2f'))
                .axisLabel('TB');

            d3.select('#chart svg')
                .datum(data)
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
