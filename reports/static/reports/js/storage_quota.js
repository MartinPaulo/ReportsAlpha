var report = report || {};

report.d3 = {


    render: function (jsonPath) {

        // one way of printing. downside is that css is not saved with the image...
        var download = d3.select("body").append("a").attr("href", "#").attr("accesskey","p").html("Print");
        download.on("click", function () {
                d3.select(this)
                    .attr("href", 'data:application/octet-stream;base64,' + btoa(d3.select("#chart svg").html()))
                    .attr("download", "chart.svg");
        });

        d3.json(jsonPath, function (error, data) {
            var chart = nv.models.stackedAreaChart()
                .margin({right: 100})
                .x(function (d) {
                    return d[0]
                })
                .y(function (d) {
                    return d[1]
                })
                .useInteractiveGuideline(true)    //Tooltips which show all data points. Very nice!
                .rightAlignYAxis(true)      //Let's move the y-axis to the right side.
                .showControls(false)       // Don't allow user to choose 'Stacked', 'Stream'
                .clipEdge(true).yDomain([0, 100])
                .color(function (d) {
                    return utils.facultyColours.get(d['key']);
                });

            //Format x-axis labels with custom function.
            chart.xAxis
                .tickFormat(function (d) {
                    return d3.time.format('%Y-%m-%d')(new Date(d))
                })
                .axisLabel('Date');

            chart.yAxis
                .tickFormat(d3.format(',.2f'))
                .axisLabel('Percentage (%)');

            d3.select('#chart svg')
                .datum(data)
                .call(chart);

            // Update chart when the window resizes
            nv.utils.windowResize(chart.update);

            return chart;
        });

    }
};