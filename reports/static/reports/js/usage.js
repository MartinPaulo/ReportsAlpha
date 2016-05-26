/**
 * Created by mpaulo on 29/04/2016.
 */

'use strict';

var report = report || {};

report.d3 = {

    render: function (csv_path) {

        d3.json(csv_path, function (error, data) {
            if (error) throw error;

            nv.addGraph(function () {
                var chart = nv.models.lineChart()
                        .x(getXValue)
                        .y(getYValue)
                        .useInteractiveGuideline(true);

                chart.dispatch.on('renderEnd', function () {
                    console.log('render complete: cumulative line with guide line');
                });

                chart.xAxis.tickFormat(xAxisFormatter)
                    .axisLabel("Date");

                chart.yAxis.tickFormat(yAxisFormatter)
                    .axisLabel("Instance Count");

                d3.select('#chart svg')
                    .datum(format_data(data))
                    .call(chart);

                // Update chart when the window resizes
                nv.utils.windowResize(chart.update);

                return chart;
            })
        });

        var unix_timestamp = function (timestamp) {
            return new Date(timestamp * 1000);
        };

        var yAxisFormatter = function (count) {
            return d3.format(',.0f')(count);
        };

        var xAxisFormatter = function (date) {
            return d3.time.format("%Y-%m-%d")(unix_timestamp(date));
        };

        var getXValue = function (sample) {
            return sample[1];
        };

        var getYValue = function (sample) {
            return sample[0];
        };

        var format_data = function (data) {
            return data.map(function (series) {
                series.values = series.datapoints;
                series.values = series.values.map(
                    function (value) {
                        if (!value[0]) {
                            value[0] = 0;
                        }
                        return value;
                    });

                delete series.datapoints;
                series.key = series.target;
                return series;
            });
        };
    }
}
