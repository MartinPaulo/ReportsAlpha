'use strict';

var report = report || {};

report.d3 = function () {

    utils.createDateButtons();

    function addRadioButton(caption, checked) {
        d3.select('#graph-buttons')
            .append('label')
            .text(caption)
            .insert('input')
            .attr('type', 'radio')
            .attr('name', 'allocated-used')
            .attr('value', caption.toLowerCase())
            .property('checked', checked)
            .on('click', function () {
                d3.select('#chart svg')[0][0].dispatchEvent(new Event('redraw'));
            })
        ;
    }

    addRadioButton('Allocated', true);
    addRadioButton('Used', false);

    var render = function () {
        var source = d3.select('input[name="allocated-used"]:checked').node().value.toLowerCase();
        var data_path = '/reports/manufactured/cloud_' + source + '/?from=' + utils.findFrom();
        d3.select('#a_data').attr('href', data_path);
        d3.json(data_path, function (error, data) {

            // for examples of these options see: http://cmaurer.github.io/angularjs-nvd3-directives/line.chart.html
            var chart = nv.models.stackedAreaChart()
                .margin({right: 100})
                .x(function (d) {
                    return d[0]
                })
                .y(function (d) {
                    return d[1]
                })
                .useInteractiveGuideline(true)  // Tooltips which show the data points. Very nice!
                .rightAlignYAxis(true)          // Move the y-axis to the right side.
                .showControls(false)            // Don't allow user to choose 'Stacked', 'Stream' etc...
                .clipEdge(true)
                .noData('No Data available')
                .color(function (d) {
                    return utils.facultyColors.get(d['key']);
                });

            chart.xAxis
                .tickFormat(function (d) {
                    return d3.time.format('%Y-%m-%d')(new Date(d))
                })
                .axisLabel('Date');

            chart.yAxis
                .tickFormat(d3.format('4d'))
                .axisLabel("VCPU's");

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

    utils.generateFacultyKey();

    return {
        render: render
    }
}();

