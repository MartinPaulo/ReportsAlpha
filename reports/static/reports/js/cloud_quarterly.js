/**
 * Created by mpaulo on 12/1/17.
 */
'use strict';

var report = report || {};

report.d3 = function () {

    var spinner = new Spinner(utils.SPINNER_OPTIONS);

    var render = function () {
        var data_path = '/reports/actual/?from=all&model=CloudQuarterly';
        d3.select('#a_data').attr('href', data_path);

        spinner.spin(document.getElementById('chart'));

        d3.csv(data_path, function (error, csv) {
            if (error) {
                console.log('Error on loading data: ' + error);
                spinner.stop();
                utils.showError(error);
                return;
            }
            var nvd3Data = utils.convertCsvToNvd3Format(csv, utils.CLOUD_FACULTIES);
            // for examples of these options see: http://cmaurer.github.io/angularjs-nvd3-directives/line.chart.html
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
                    .showControls(false)
                    .clipEdge(true)
                    .noData('No Data available')
                    .color(function (d) {
                        return utils.facultyColors.get(d['key']);
                    })
                ;

            chart.xAxis
                .tickFormat(function (d) {
                    return d3.time.format('%Y-%m-%d')(new Date(d))
                })
                .axisLabel('Date');

            chart.yAxis
                .tickFormat(d3.format('4d'))
                .axisLabel("Projects");
            d3.select('#chart svg')
                .datum(nvd3Data)
                .transition().duration(500)
                .call(chart);
            spinner.stop();

            // Update chart when the window resizes
            nv.utils.windowResize(chart.update);
            return chart;
        });

    };

    d3.select('#chart svg')[0][0].addEventListener('redraw', function () {
        render();
    }, false);

    utils.generateFacultyKey();

    return {
        render: render
    }
}();