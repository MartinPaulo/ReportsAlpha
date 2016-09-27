'use strict';

var report = report || {};

report.d3 = function () {

    utils.createFacultyButtons();
    utils.createDateButtons();

    var render = function () {
        var type = utils.findType();
        if (type == 'total') {
            type = '';
        }
        var data_path = '/reports/actual/?from=' + utils.findFrom() +
            '&model=StorageAllocatedByFaculty' + type;

        // set the download link on the page
        d3.select('#a_data').attr('href', data_path);
        utils.renderStorageChart(data_path, utils.STORAGE_FACULTIES);
    };

    d3.select('#chart svg')[0][0].addEventListener('redraw', function (e) {
        render();
    }, false);

    utils.generateFacultyKey();

    return {
        render: render
    }
}();
