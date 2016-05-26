var report = report || {};

report.d3 = {

    render: function (jsonPath) {
        
        utils.createButton('Year');
        utils.createButton('6 Months', {target_id: 'six_months'});
        utils.createButton('3 Months', {target_id: 'three_months'});
        utils.createButton('1 Month', {target_id: 'one_month'});
        d3.select('#year')
            .on('click')();

        utils.createButton('Total', {parent_id: 'graph-buttons'});
        utils.createButton('Vault', {parent_id: 'graph-buttons'});
        utils.createButton('Market', {parent_id: 'graph-buttons'});
        utils.createButton('Compute', {parent_id: 'graph-buttons'});
        d3.select('#total')
            .on('click')();

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