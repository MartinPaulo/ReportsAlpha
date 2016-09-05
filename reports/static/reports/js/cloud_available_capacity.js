'use strict';

var report = report || {};

report.d3 = function () {


    utils.createDateButtons('#oneMonth');

    var flavors = [
        ['m2.tiny', 'capacity_768'],
        ['m2.xsmall', 'capacity_2048'],
        ['m2.small', 'capacity_4096'],
        ['m2.medium', 'capacity_6144'],
        ['m2.large', 'capacity_12288'],
        ['m2.xlarge', 'capacity_49152'],
        ['m1.small', 'capacity_4096'],
        ['m1.medium', 'capacity_8192'],
        ['m1.large', 'capacity_16384'],
        ['m1.xlarge', 'capacity_32768'],
        ['m1.xxlarge', 'capacity_65536']
    ];

    function changeSize(e) {
        render();
    }

    var select = d3.select('#' + 'graph-buttons')
            .append('label').text('Flavor: ')
            .attr('for', 'size_select')
            .append('select')
            .attr('class', 'select')
            .attr('id', 'size_select')
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

    var opts = {
        lines: 9, // The number of lines to draw
        length: 9, // The length of each line
        width: 5, // The line thickness
        radius: 14, // The radius of the inner circle
        color: 'blue', // #rgb or #rrggbb or array of colors
        speed: 1.9, // Rounds per second
        trail: 40, // Afterglow percentage
        className: 'spinner' // The CSS class to assign to the spinner
    };

    var spinner = new Spinner(opts);

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
