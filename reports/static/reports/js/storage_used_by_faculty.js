'use strict';

var report = report || {};

report.d3 = function () {

    utils.createFacultyButtons();
    utils.createDateButtons();

    var render = function () {
        var data_path = '/reports/manufactured/faculty_used/?from=' + utils.findFrom() + '&type=' + utils.findType();
        d3.select('#a_data').attr('href', data_path);
        d3.json(data_path, utils.getStorageChart({'useFacultyColours': true}));
    };

    d3.select('#chart svg')[0][0].addEventListener('redraw', function (e) {
        render();
    }, false);

    return {
        render: render
    }
}();
