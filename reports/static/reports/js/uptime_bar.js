/**
 * Created by mpaulo on 25/07/2016.
 */
'use strict';

var report = report || {};

report.d3 = function () {

    var uptimeData = [
        {
            national: 98.0, // will be drawn as a darker grey square to show how the national service compares
            target: 99.0,   // a white triangle demarcates the target uptime
            cells: [       // each value will be rendered as a bar, indicating the uptime of that cell
                {
                    name: "NP",
                    uptime: 98.05   // the value represented by the line
                },
                {
                    name: "QH2-UoM",
                    uptime: 97.05
                },
                {
                    name: "QH2",
                    uptime: 99.05
                }
            ]
        }
        // each object in this array will be rendered as a separate uptime bullet chart
    ];

    var datacenterColours = {
        'QH2': 'chocolate',
        'QH2-UoM': 'green',
        'NP': 'blue',
        'Other data centers': 'lightblue'
    };

    var getColour = function (key) {
        return key in datacenterColours && typeof datacenterColours[key] === 'string' ? datacenterColours[key] : 'black';
    };

    var render = function () {

        var chart = report.uptimeBullet()
            .color(function (cell) {
                return getColour(cell.name);
            });

        d3.select('#chart')
            .selectAll('svg')
            .data(uptimeData)
            .call(chart)
        ;
        nv.utils.windowResize(chart.update);
    };


    return {
        render: render
    }
}();