'use strict';

var report = report || {};

report.d3 = function () {

    // Some thoughts on uptime: http://uptime.netcraft.com/accuracy.html#uptime

    utils.createDateButtons();

    function userColours(key) {
        switch (key) {
            case "at_uom_only":
                return "darkblue"; // UoM blue is really #002952ff
            case "elsewhere_only":
                return "lightblue";
            case "in_both":
                return "blue";
            case "others_at_uom":
                return "brown";
            default:
                return "black";
        }
    }

    function getStreamName(key) {
        switch (key) {
            case "at_uom_only":
                return "UoM @ UoM only";
            case "elsewhere_only":
                return "UoM @ elsewhere";
            case "in_both":
                return "UoM @ UoM and elsewhere";
            case "others_at_uom":
                return "Others @ UoM";
            default:
                return key;
        }
    }

    var render = function () {
        var data_path = '/reports/actual/?model=CloudActiveUsers&from=' + utils.findFrom();

        d3.select('#a_data').attr('href', data_path);
        d3.csv(data_path, function (error, csv) {
            if (error) {
                console.log("Error on loading data: " + error);
                return;
            }

            csv.sort(function (a, b) {
                return new Date(a['date']) - new Date(b['date']);
            });

            var nvd3_data = [];
            var totals = ["at_uom_only", "elsewhere_only", "in_both", "others_at_uom"];
            for (var i = 0; i < totals.length; i++) {
                var o = {};
                o.key = getStreamName(totals[i]);
                o.color = userColours(totals[i]);
                o.values = csv.map(function (d) {
                    return [new Date(d["date"]).getTime(), parseInt(d[totals[i].toLowerCase()])];
                });
                nvd3_data.push(o);
            }

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
                            return d['color'];
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

                var timeout;

                chart.interactiveLayer.dispatch.on('elementMousemove.name', function (e) {
                    clearTimeout(timeout);
                    timeout = setTimeout(function () {
                        var date = chart.xAxis.tickFormat()(e.pointXValue);
                        //console.log("e: " + date);
                        generateTopTwenty(date);
                    }, 1000);
                });

                d3.select('#chart svg')
                    .datum(nvd3_data)
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


    // We want to keep the colours between redraws more or less consistent
    // Hence we remember them as attributes on this object.
    var topTwentyColours = {};
    // The source of our initial colours
    var colors = d3.scale.category20();
    // to draw a line:
    // http://stackoverflow.com/questions/18856060/how-do-i-add-an-average-line-to-an-nvd3-js-stacked-area-chart
    function generateTopTwenty(date) {
        var data_path = '/reports/actual/?model=CloudTopTwenty&on=' + date;


        d3.csv(data_path, function (error, csv) {
            if (error) {
                // should perhaps also clear any older graph?
                console.log("Error on loading data: " + error);
                return;
            }
            d3.select('#extra_title h3').remove();

            d3.select('#extra_title')
                .insert('h3')
                .text('The top 20 users as at ' + date)
            ;

            csv.sort(function (a, b) {
                // By the number of vcpu's used.
                return b['vcpus'] - a['vcpus'];
            });
            var nvd3_data = [];
            var coloursToKeep = {};
            var availableColours = [];
            var o = {};
            o.key = "Top Twenty Users";
            o.values = csv.map(function (d) {
                // we want to use the old colour for this tenant, if they were in the last top twenty
                coloursToKeep[d["tenant_name"]] = true;
                return [d["tenant_name"], parseInt(d["vcpus"])];
            });
            nvd3_data.push(o);
            // if the top twenty colour isn't in use, free it up
            for (var key in topTwentyColours) {
                if (!coloursToKeep.hasOwnProperty(key)) {
                    availableColours.push(topTwentyColours[key]);
                    delete topTwentyColours[key];
                }
            }
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
                        .noData('No Data available')
                        .rotateLabels(45)
                        .color(function (d, i) {
                            if (!topTwentyColours.hasOwnProperty(d[0])) {
                                // we try to take from the pool of free colours
                                var colour = availableColours.pop();
                                // but sometimes we just have to grab a random colour
                                topTwentyColours[d[0]] = colour ? colour : colors(i);
                            }
                            return topTwentyColours[d[0]];
                        })
                    ;
                chart.yAxis
                    .tickFormat(d3.format('4d'))
                    .axisLabel("VM's");

                d3.select('#extra svg')
                    .datum(nvd3_data)
                    .call(chart);

                nv.utils.windowResize(chart.update);
                return chart;
            });
        })

    }

    generateTopTwenty(new Date().toISOString().slice(0, 10));

    return {
        render: render
    }
}();