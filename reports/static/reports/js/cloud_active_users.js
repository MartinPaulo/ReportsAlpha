'use strict';

var report = report || {};

report.d3 = function () {

    // Some thoughts on uptime: http://uptime.netcraft.com/accuracy.html#uptime

    utils.createDateButtons();

    function userColours(key) {
        switch (key) {
            case "at_uom_only":
                return "darkblue";
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
                nvd3_data.push(o)
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

    var projectUsage = [{
        key: "Top Twenty Users",
        values: [
            ['vSpartan', 3536],
            ['Matlab_DCS', 1939],
            ['GenomicsVL', 1728],
            ['CoEPP-Tier3', 1218],
            ['Endo_VL', 632],
            ['GPaaS', 576],
            ['MeG-LIDAR', 510],
            ['InfectiousDiseases', 472],
            ['UoM_Genomic_Adaptation', 455],
            ['UoM_iDDSS', 434],
            ['Unimelb_Peter_Mac_Research_Dropbox', 370],
            ['AURIN', 272],
            ['TbPc2', 256],
            ['Melbourne_Genomics_Health_Alliance', 245],
            ['Myzus_persicea_transcriptomics', 224],
            ['UoM_NGSDA', 192],
            ['OpenAPI', 176],
            ['GenomicsVL_Devt', 174],
            ['Thylacine_Genome_Project', 168],
            ['Unimelb_VM_Co-resident_Attacks', 164]
        ]
    }
    ];

    // to draw a line:
    // http://stackoverflow.com/questions/18856060/how-do-i-add-an-average-line-to-an-nvd3-js-stacked-area-chart
    function generateTopTwenty() {
        d3.select('#extra_title')
            .insert('h3')
            .text('The top 20 users as at xx/yy/zzzz')
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
                .axisLabel("VM's");

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