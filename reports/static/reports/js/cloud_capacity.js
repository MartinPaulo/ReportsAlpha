'use strict';

var report = report || {};

report.d3 = function () {


    utils.createDateButtons();

    var datacenterColours = {
        'QH2': 'chocolate',
        'QH2-UoM': 'green',
        'NP': 'blue',
        'Other data centers': 'lightblue'
    };

    var getColour = function (key) {
        return key in datacenterColours && typeof datacenterColours[key] === 'string' ? datacenterColours[key] : 'black';
    };

    var sizes = ["768", "2048", "4096", "6144", "8192", "12288", "16384", "32768", "49152", "65536"];
    var parent_id = 'graph-buttons';

    function changeSize(e) {
        render();
    }

    var select = d3.select('#' + parent_id)
            .append('label').text('Size: ')
            .attr('for', 'size_select')
            .append('select')
            .attr('class', 'select')
            .attr('id', 'size_select')
            .on('change', changeSize)
            .selectAll('option')
            .data(sizes)
            .enter()
            .append('option')
            .text(function (d) {
                return d + 'MB';
            })
            .attr('value', function (d) {
                return d;
            })
        ;

    function findSize() {
        return d3.select('select').property('value');
    }

    var render = function () {
        var data_path = '/reports/manufactured/cloud_capacity/?from=' + utils.findFrom() + '&type=' + findSize();
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
                            return getColour(d['key']);
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
