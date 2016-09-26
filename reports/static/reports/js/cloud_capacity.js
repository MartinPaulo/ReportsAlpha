'use strict';

var report = report || {};

report.d3 = function () {

    utils.createDateButtons();

    function getColour(key) {
        switch (key) {
            case 'NeCTAR Contribution':
                return 'orange';
            case 'UoM Contribution':
                return 'blue';
            default:
                return 'lightblue';
        }
    }

    var render = function () {
        var data_path = '/reports/actual/?from=' + utils.findFrom()+ '&model=CloudCapacity';

        d3.select('#a_data').attr('href', data_path);
        d3.csv(data_path, function (error, csv) {
            if (error) {
                console.log('Error on loading data: ' + error);
                return;
            }
            csv.sort(function (a, b) {
                return new Date(a['date']) - new Date(b['date']);
            });

            // convert the csv passed in as an argument into the format that nvd3 prefers.
            var nvd3Data = [];
            var sources = [
                'nectar_contribution', 'uom_contribution', 'co_contribution'];
            for (var i = 0; i < sources.length; i++) {
                var o = {};
                o.key = sources[i];
                o.values = csv.map(function (d) {
                    return [new Date(d['date']).getTime(), parseInt(d[sources[i].toLowerCase()])];
                });
                nvd3Data.push(o)
            }
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
                        return getColour(d['key']);
                    })
                ;

            chart.xAxis
                .tickFormat(function (d) {
                    return d3.time.format('%Y-%m-%d')(new Date(d))
                })
                .axisLabel('Date');

            chart.yAxis
                .tickFormat(d3.format('4d'))
                .axisLabel("Cores");

            d3.select('#chart svg')
                .datum(nvd3Data)
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