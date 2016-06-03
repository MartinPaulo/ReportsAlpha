'use strict';

var report = report || {};

report.d3 = function () {

    utils.createDateButtons();

    var render = function () {
        var data_path = '/reports/data/storage/allocated/?from=' + utils.findFrom();
        d3.select('#a_data').attr('href', data_path);
        d3.json(data_path, utils.getStorageChart());
    };

    d3.select('#chart svg')[0][0].addEventListener('redraw', function (e) {
        render();
    }, false);

    return {
        render: render
    }
}();