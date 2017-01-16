/**
 * Created by mpaulo on 12/1/17.
 */
'use strict';

var report = report || {};

report.d3 = function () {

    var spinner = new Spinner(utils.SPINNER_OPTIONS);

    var render = function () {
        var data_path = '/reports/actual/?from=all&model=CloudQuarterly';
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
                    .useInteractiveGuideline(true)
                    .rightAlignYAxis(true)
                    .showControls(false)
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
                .axisLabel("UoM Administrators");
            d3.select('#chart svg')
                .datum(nvd3Data)
                .transition().duration(500)
                .call(chart);
            spinner.stop();

            // Update chart when the window resizes
            nv.utils.windowResize(chart.update);
            return chart;
        });

    };

    d3.select('#chart svg')[0][0].addEventListener('redraw', function () {
        render();
    }, false);

    // utils.generateFacultyKey();

    (function generate_quarterly_usage() {
        var data_path = '/reports/actual/?from=all&model=CloudQuarterlyUsage';
        var columns = [
            {
                head: 'Quarter End Date', cl: 'center', html: function (row) {
                return row.date;
            }
            },
            {
                head: 'All Projects', cl: 'right', html: function (row) {
                return row.projects_active;
            }
            },
            {
                head: 'Allocated UoM Projects', cl: 'right',
                html: function (row) {
                    return row.uom_projects_active;
                }
            },
            {
                head: 'All UoM Projects', cl: 'right', html: function (row) {
                return row.all_uom_projects_active;
            }
            },
            {
                head: 'All Projects with active UoM Admins', cl: 'right',
                html: function (row) {
                    return row.uom_participation;
                }
            },
            {
                head: 'All Admins', cl: 'right', html: function (row) {
                return row.all_users_active;
            }
            },
            {
                head: 'UoM Admins', cl: 'right', html: function (row) {
                return row.uom_users_active;
            }
            }
        ];
        d3.select('#extra svg').remove();
        d3.select('#extra_title')
            .insert('h3')
            .text('Activity by Quarter')
        ;

        const selection = d3.select('#extra .chart-wrapper');
        var table = selection.append('table')
            .attr('class', 'center');

        table.append('thead').append('tr')
            .selectAll('th')
            .data(columns).enter()
            .append('th')
            .attr('class', 'center')
            .text(function (row) {
                return row.head;
            });
        d3.csv(data_path, function (error, csv) {
            if (error) {
                // should perhaps also clear any older graph?
                console.log("Error on loading data: " + error);
                utils.showError(error);
                return;
            }
            // Below is a temporary hack: each line, plus the 3 for the
            // table headers
            selection.style("height", (csv.length + 3) * 1.6 + "em");
            if (csv.length > 0) {
                // we need to give a download link...
                d3.select('#extra_link').append("p").html(
                    '<p>The <a id="a_data" href="'
                    + data_path
                    + '">data file</a> behind this graph</p>');
            }

            table.append('tbody')
                .selectAll('tr')
                .data(csv).enter()
                .append('tr')
                .selectAll('td')
                .data(function (row) {
                    return columns.map(function (column) {
                        return {column: column, value: column.html(row)};
                    });
                }).enter()
                .append('td')
                .html(function (r) {
                    return r.value
                })
                .attr('class', function (r) {
                    return r.column.cl
                });

        });
    })();

    return {
        render: render
    }
}();