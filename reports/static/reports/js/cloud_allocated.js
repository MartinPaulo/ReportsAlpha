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
     * Adds a radio button with the given caption and checked value.
     * When clicked the button will force the graph to redraw
     * @param caption {string}
     * @param checked {boolean}
     */
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

    /**
     * Takes a string as input and returns it with the first letter capitalized
     * @param string {string}
     * @returns {string}
     */
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    addRadioButton(ALLOCATED_BUTTON_CAPTION, true);
    addRadioButton(USED_BUTTON_CAPTION, false);

    // We have to ensure that the used chart uses the same domain as the allocation chart.
    // This stores the domain between redraws. It works because the first graph rendered is the allocated one,
    // and because all of the graphs are fixed on the same end date. And because the allocated amount should
    // always be more than the used amount...
    var allocationDomain;

    var render = function () {
        var source = d3.select('input[name="allocated-used"]:checked').node().value.toLowerCase();
        var data_path = '/reports/actual/?from=' + utils.findFrom() + '&model=Cloud' + capitalizeFirstLetter(source);
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
            var faculties = [
                'FoA', 'VAS', 'FBE', 'MSE', 'MGSE', 'MDHS', 'FoS', 'ABP', 'MLS', 'VCAMCM', 'Other', 'Unknown'];
            for (var i = 0; i < faculties.length; i++) {
                var o = {};
                o.key = faculties[i];
                o.values = csv.map(function (d) {
                    return [new Date(d['date']).getTime(), parseInt(d[faculties[i].toLowerCase()])];
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

