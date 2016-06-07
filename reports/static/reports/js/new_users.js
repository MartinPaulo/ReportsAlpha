/**
 * Created by mpaulo on 29/04/2016.
 */
'use strict';

var report = report || {};

report.d3 = function () {

    var render = function () {

        var csv_path = '/reports/data/NewUsers?format=csv';
        d3.select('#a_data').attr('href', csv_path);

        d3.csv(csv_path, function (error, data) {
            if (error) throw error;

            nv.addGraph(function () {
                var chart = nv.models.lineChart()
                        .x(getSampleDate)
                        .y(getSampleCount)
                        .showLegend(false)
                        .color(d3.scale.category10().range())
                        .useInteractiveGuideline(true)
                    ;

                chart.dispatch.on('renderEnd', function () {
                    console.log('render complete: cumulative line with guide line');
                });

                chart.xAxis.tickFormat(xAxisFormatter)
                    .axisLabel("Month");

                chart.yAxis.tickFormat(yAxisFormatter)
                    .axisLabel("Total");

                d3.select('#chart svg')
                    .datum(wrap(data))
                    .call(chart);

                // Update chart when the window resizes
                nv.utils.windowResize(chart.update);

                return chart;
            })
        });

        var yAxisFormatter = function (yValue) {
            return d3.format(',.0d')(yValue)
        };

        var xAxisFormatter = function (d) {
            return d3.time.format('%b \'%y')(new Date(d));
        };

        var getSampleDate = function (sample) {
            return d3.time.format("%b-%y").parse(sample.date);
        };

        var getSampleCount = function (sample) {
            return +sample.count;
        };

        /* translates the data into the format expected by nv3 */
        function wrap(data) {
            var result = [];
            result.push({values: data});
            result[0].key = "New Users";
            result[0].area = true;
            console.log(result);
            return result;
        }
    };

    return {
        render: render
    }
}();