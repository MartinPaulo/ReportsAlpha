'use strict';

var report = report || {};

report.d3 = function () {


    var render = function () {

        // one way of printing. downside is that css is not saved with the image...
        var download = d3.select("body").append("a").attr("href", "#").attr("accesskey", "p").html("Print");
        download.on("click", function () {
            d3.select(this)
                .attr("href", 'data:application/octet-stream;base64,' + btoa(d3.select("#chart svg").html()))
                .attr("download", "chart.svg");
        });

        var data_path = '/reports/manufactured/storage/quota/';
        d3.select('#a_data').attr('href', data_path);
        d3.json(data_path, utils.getStorageChart({'useFacultyColours': true}));
        
    };
    return {
        render: render
    }
}();