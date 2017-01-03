'use strict';

var report = report || {};

report.d3 = function () {

    /**
     * @type {string}
     * @const
     */
    var ALLOCATED_BUTTON_CAPTION = 'Allocated';
    /**
     * @type {string}
     * @const
     */
    var USED_BUTTON_CAPTION = 'Used';

    utils.createDateButtons();

    /**
     * Takes a string as input and returns it with the first letter capitalized
     * @param string {string}
     * @returns {string}
     */
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    utils.createButton(ALLOCATED_BUTTON_CAPTION, {parent_id: 'graph-buttons'});
    utils.createButton(USED_BUTTON_CAPTION, {parent_id: 'graph-buttons'});
    d3.select('#allocated').on('click')();

    // We have to ensure that the used chart uses the same domain as the allocation chart.
    // This stores the domain between redraws. It works because the first graph rendered is the allocated one,
    // and because all of the graphs are fixed on the same end date. And because the allocated amount should
    // always be more than the used amount...
    var allocationDomain;

    var spinner = new Spinner(utils.SPINNER_OPTIONS);

    var render = function () {
        var source = d3.select('#graph-buttons .active').attr('id');
        var data_path = '/reports/actual/?from=' + utils.findFrom() + '&model=Cloud' + capitalizeFirstLetter(source);
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
                    .useInteractiveGuideline(true)  // Tooltips which show the data points. Very nice!
                    .rightAlignYAxis(true)          // Move the y-axis to the right side.
                    .showControls(false)            // Don't allow user to choose 'Stacked', 'Stream' etc...
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
                .axisLabel("VCPU's");

            // if set we can use this on every graph we draw
            if (allocationDomain) {
                chart.yDomain(allocationDomain)
            }

            d3.select('#chart svg')
                .datum(nvd3Data)
                .transition().duration(500)
                .call(chart);
            spinner.stop();

            // Update chart when the window resizes
            nv.utils.windowResize(chart.update);

            // should we record the allocation domain? (only need to do this first time round)
            if (!allocationDomain && source.toLowerCase() == ALLOCATED_BUTTON_CAPTION.toLowerCase()) {
                allocationDomain = chart.yAxis.scale().domain();
            }

            return chart;
        });
    };

    // listen for the button presses
    d3.select('#chart svg')[0][0].addEventListener('redraw', function () {
        render();
    }, false);

    utils.generateFacultyKey();

    return {
        render: render
    }
}();

