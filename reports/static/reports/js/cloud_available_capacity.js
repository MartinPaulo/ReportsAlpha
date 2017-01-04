'use strict';

var report = report || {};

report.d3 = function () {


    utils.createDateButtons('#oneMonth');

    var flavors = [
        ['M2 tiny', 'capacity_768'],
        ['M2 xsmall', 'capacity_2048'],
        ['M2 small', 'capacity_4096'],
        ['M2 medium', 'capacity_6144'],
        ['M2 large', 'capacity_12288'],
        ['M2 xlarge', 'capacity_49152'],
        ['M1 small', 'capacity_4096'],
        ['M1 medium', 'capacity_8192'],
        ['M1 large', 'capacity_16384'],
        ['M1 xlarge', 'capacity_32768'],
        ['M1 xxlarge', 'capacity_65536']
    ];

    function changeSize(e) {
        render();
    }

    var parentDiv = d3.select('#graph-buttons')
        .append('div')
        .attr('class', 'size-select');

    parentDiv.append('select')
        .on('change', changeSize)
        .selectAll('option')
        .data(flavors)
        .enter()
        .append('option')
        .text(function (d) {
            return d[0];
        })
        .attr('value', function (d) {
            return d[1];
        })
    ;

    function findSize() {
        return d3.select('select').property('value');
    }

    var spinner = new Spinner(utils.SPINNER_OPTIONS);

    var render = function () {
        var data_path = '/reports/graphite/cloud_available_capacity/?from='
            + utils.findFrom() + '&type=' + findSize();

        // set the download link with the url, requesting csv instead of json
        d3.select('#a_data').attr('href', data_path + '&format=csv');

        spinner.spin(document.getElementById('chart'));

        d3.json(data_path, function (error, data) {
            if (error) {
                console.log("Error on loading data: " + error);
                spinner.stop();
                utils.showError(error);
                return;
            }
            nv.addGraph(function () {
                var chart = nv.models.lineChart()
                        .x(function (d) {
                            return d[1]
                        })
                        .y(function (d) {
                            return d[0]
                        })
                        .useInteractiveGuideline(true)
                        .rightAlignYAxis(true)
                        .noData('No Data available')
                        .margin({right: 75})
                        .color(function (d) {
                            return utils.cellColours.get(d['key']);
                        })
                    ;

                chart.yAxis
                    .tickFormat(d3.format(',.0f'))
                    .axisLabel('Available');

                chart.xAxis
                    .tickFormat(function (d) {
                        return d3.time.format('%Y-%m-%d')(new Date(d * 1000))
                    })
                    .axisLabel('Date');

                d3.select('#chart svg')
                    .datum(data)
                    .call(chart);

                spinner.stop();

                //figure out a good way to do this automatically
                nv.utils.windowResize(chart.update);

                return chart;
            });
        });
    };

    d3.select('#chart svg')[0][0].addEventListener('redraw', changeSize, false);

    return {
        render: render
    }
}();
