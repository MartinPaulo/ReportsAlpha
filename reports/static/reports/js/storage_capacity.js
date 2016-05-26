var report = report || {};

report.d3 = {
    render: function (csv_path) {

        utils.createDateButtons();

        d3.json(csv_path, function (error, data) {
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
                .showControls(true)
                .controlOptions(['Stacked', 'Expanded'])
                .clipEdge(true);

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
};