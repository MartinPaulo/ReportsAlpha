var report = report || {};

report.d3 = {
    render: function (csv_path) {

        d3.json(csv_path, function (error, data) {
            var chart = nv.models.stackedAreaChart()
                .margin({right: 100})
                .x(function (d) {
                    return d[0]
                })   //We can modify the data accessor functions...
                .y(function (d) {
                    return d[1]
                })   //...in case your data is formatted differently.
                .useInteractiveGuideline(true)    //Tooltips which show all data points. Very nice!
                .rightAlignYAxis(true)      //Let's move the y-axis to the right side.
                .showControls(true)       //Allow user to choose 'Stacked', 'Stream', 'Expanded' mode.
                .clipEdge(true);

            //Format x-axis labels with custom function.
            chart.xAxis
                .tickFormat(function (d) {
                    return d3.time.format('%Y-%m-%d')(new Date(d))
                });

            chart.yAxis
                .tickFormat(d3.format(',.2f'));

            d3.select('#chart svg')
                .datum(data)
                .call(chart);

            // Update chart when the window resizes
            nv.utils.windowResize(chart.update);

            return chart;
        });
    }
}