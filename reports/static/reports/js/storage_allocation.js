'use strict';

var report = report || {};

report.d3 = {

    render: function (jsonPath) {

        utils.createDateButtons();
        utils.createFacultyButtons();


        // d3.json(jsonPath, function (error, data) {
        //     var chart = nv.models.stackedAreaChart()
        //         .margin({right: 100})
        //         .x(function (d) {
        //             return d[0]
        //         })
        //         .y(function (d) {
        //             return d[1]
        //         })
        //         .useInteractiveGuideline(true)    //Tooltips which show all data points. Very nice!
        //         .rightAlignYAxis(true)      //Let's move the y-axis to the right side.
        //         .showControls(true)       //Allow user to choose 'Stacked', 'Stream'
        //         .clipEdge(true).yDomain([0, 100])
        //         .controlOptions(['Stacked', 'Stream'])
        //         .color(function (d) {
        //             return schoolColors.hasOwnProperty(d['key']) ? schoolColors[d['key']] : 'black';
        //         });
        //
        //     //Format x-axis labels with custom function.
        //     chart.xAxis
        //         .tickFormat(function (d) {
        //             return d3.time.format('%Y-%m-%d')(new Date(d))
        //         })
        //         .axisLabel('Date');
        //     ;
        //
        //     chart.yAxis
        //         .tickFormat(d3.format(',.2f'))
        //         .axisLabel('Percentage (%)');
        //
        //     d3.select('#chart svg')
        //         .datum(data)
        //         .call(chart);
        //
        //     // Update chart when the window resizes
        //     nv.utils.windowResize(chart.update);
        //
        //     return chart;
        // });


    }
};