'use strict';

var report = report || {};

report.d3 = function () {


    utils.createDateButtons();

    var flavors = [
        ['m2.tiny', '768'],
        ['m2.xsmall', '2048'],
        ['m2.small', '4096'],
        ['m2.medium', '6144'],
        ['m2.large', '12288'],
        ['m2.xlarge', '49152'],
        ['m1.small', '4096'],
        ['m1.medium', '8192'],
        ['m1.large', '16384'],
        ['m1.xlarge', '32768'],
        ['m1.xxlarge', '65536']
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

    var render = function () {
        var data_path = '/reports/manufactured/cloud_available_capacity/?from=' + utils.findFrom() + '&type=' + findSize();
        d3.select('#a_data').attr('href', data_path);
        d3.json(data_path, function (data) {
            nv.addGraph(function () {
                var chart = nv.models.lineChart()
                        .x(function (d) {
                            return d[0]
                        })
                        .y(function (d) {
                            return d[1]
                        })
                        .useInteractiveGuideline(true)
                        .rightAlignYAxis(true)          // Move the y-axis to the right side.
                        .noData('No Data available')
                        .margin({right: 75})
                        .color(function (d) {
                            return utils.cellColours.get(d['key']);
                        })
                    ;

                chart.yAxis
                    .tickFormat(d3.format('4d'))
                    .axisLabel('Available');

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

    d3.select('#chart svg')[0][0].addEventListener('redraw', changeSize, false);

    return {
        render: render
    }
}();
