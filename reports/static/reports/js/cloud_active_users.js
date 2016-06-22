'use strict';

var report = report || {};

report.d3 = function () {

    // Some thoughts on uptime: http://uptime.netcraft.com/accuracy.html#uptime

    utils.createDateButtons();

    function userColours(key) {
        console.log('key: ' + key);
        if (key == 'UoM') return 'blue';
        else if (key == 'Others @ UoM') return 'brown';
        else return 'lightblue';
    }

    var render = function () {
        var data_path = '/reports/manufactured/cloud_active_users/?from=' + utils.findFrom();
        d3.select('#a_data').attr('href', data_path);
        d3.json(data_path, function (data) {
            nv.addGraph(function () {
                var chart = nv.models.stackedAreaChart()
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
                        .showControls(false)            // Don't allow user to choose 'Stacked', 'Stream' etc...
                        .color(function (d) {
                            return userColours(d['key']);
                        })
                    ;

                chart.yAxis
                    .tickFormat(d3.format('4d'))
                    .axisLabel('User Count');

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

    d3.select('#chart svg')[0][0].addEventListener('redraw', function (e) {
        render();
    }, false);

    var projectUsage = [{
        key: "Top Twenty Users",
        values: [
            ['Parrot squawk', 140],
            ['Soniti', 96],
            ['Exhibili', 94],
            ['Fmpse', 89],
            ['Borgward', 75],
            ['Fullsome', 60],
            ['Flighty', 55],
            ['Aardvark', 46],
            ['Fonesca', 45],
            ['XL',40],
            ['VB', 36],
            ['DB', 35],
            ['Castle', 34],
            ['Lion', 34],
            ['Windhoek', 30],
            ['Black', 20],
            ['Ice', 19],
            ['Coopers', 18],
            ['Amstel', 13],
            ['Adair', 10]
        ]
    }
    ];

    // to draw a line:
    // http://stackoverflow.com/questions/18856060/how-do-i-add-an-average-line-to-an-nvd3-js-stacked-area-chart
    function generateTopTwenty() {
        d3.select('#extra_title')
            .insert('h3')
            .text('The top 20 users')
        ;
        nv.addGraph(function () {
            var chart = nv.models.discreteBarChart()
                    .x(function (d) {
                        return d[0]
                    })
                    .y(function (d) {
                        return d[1]
                    })
                    //.staggerLabels(true)
                    .wrapLabels(true)
                    .rotateLabels(45)
                ;
            chart.yAxis
                .tickFormat(d3.format('4d'))
                .axisLabel('TB');

            d3.select('#extra svg')
                .datum(projectUsage)
                .call(chart);

            nv.utils.windowResize(chart.update);
            return chart;
        });

    }

    generateTopTwenty();

    return {
        render: render
    }
}();