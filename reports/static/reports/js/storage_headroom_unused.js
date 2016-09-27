'use strict';

var report = report || {};

report.d3 = function () {

    utils.createDateButtons();

    var render = function () {
        var data_path = '/reports/actual/?from=' + utils.findFrom() +
            '&model=StorageHeadroomUnused';
        // set the download link on the page
        d3.select('#a_data').attr('href', data_path);
        utils.renderStorageChart(data_path, utils.STORAGE_PRODUCT_TYPES);
    };
    // listen for redraw events
    d3.select('#chart svg')[0][0].addEventListener('redraw', function (e) {
        render();
    }, false);

    return {
        render: render
    }
}();