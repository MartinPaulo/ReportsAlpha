/**
 * Created by martin paulo on 4/07/2016.
 */
'use strict';

var report = report || {};

report.d3 = function () {

    var uptimeHistoryData = [
        // each array entry will be rendered as a separate graph.
        [
            {
                service: 'Nova',
                outages: [
                    {start: 1457000000000, end: 1458000000000, planned: true},
                    {start: 1458000000000, end: 1458900000000, planned: false},
                    {start: 1468050000000, end: 1468060000000, planned: true},
                    {start: 1468800000000, end: 1468900000000, planned: false}
                ]
            },
            {
                service: 'Neutron',
                outages: [
                    {start: 1468986686293, end: 1468986700000, planned: true},
                    {start: 1469000000000, end: 1468990000000, planned: false}
                ]
            },
            {
                service: 'Ceilometer',
                outages: [
                    {start: new Date('2015-09-15').getTime(), end: new Date('2015-09-15').getTime(), planned: true},
                    {start: new Date('2016-01-15').getTime(), end: new Date('2016-01-16').getTime(), planned: false}
                ]
            },
            {
                service: 'Glance',
                outages: [
                    {start: 1457900000000, end: 1458000000000, planned: true},
                    {start: 1458099990000, end: 1458900000000, planned: false},
                    {start: 1468059999000, end: 1468060000000, planned: true},
                    {start: 1468800000000, end: 1468900000000, planned: false}
                ]
            }, {
            service: 'Cinder',
            outages: [
                {start: 1457000000000, end: 1458000000000, planned: true},
                {start: 1458000000000, end: 1458900000000, planned: false},
                {start: 1468050000000, end: 1468060000000, planned: true},
                {start: 1468800000000, end: 1468900000000, planned: false}
            ]
        }
        ]
    ];

    var uptimeData = [
        {
            service: 'Nova',
            national: 98.0, // will be drawn as a darker grey square to show how the national service compares
            target: 99.0,   // a white triangle demarcates the target uptime
            cells: [       // each value will be rendered as a bar, indicating the uptime of that cell
                {
                    name: 'NP',
                    uptime: 98.05   // the value represented by the line
                },
                {
                    name: 'QH2-UoM',
                    uptime: 97.05
                },
                {
                    name: 'QH2',
                    uptime: 99.05
                }
            ]
        }, {
            service: 'Neutron',
            national: 99.0, // will be drawn as a darker grey square to show how the national service compares
            target: 99.8,   // a white triangle demarcates the target uptime
            cells: [       // each value will be rendered as a bar, indicating the uptime of that cell
                {
                    name: 'NP',
                    uptime: 99.05   // the value represented by the line
                },
                {
                    name: 'QH2-UoM',
                    uptime: 98.05
                },
                {
                    name: 'QH2',
                    uptime: 99.9
                }
            ]
        }, {
            service: 'Ceilometer',
            national: 99.5, // will be drawn as a darker grey square to show how the national service compares
            target: 99.8,   // a white triangle demarcates the target uptime
            cells: [       // each value will be rendered as a bar, indicating the uptime of that cell
                {
                    name: 'NP',
                    uptime: 99.22   // the value represented by the line
                },
                {
                    name: 'QH2-UoM',
                    uptime: 98.89
                },
                {
                    name: 'QH2',
                    uptime: 99.87
                }
            ]
        }, {
            service: 'Glance',
            national: 99.13, // will be drawn as a darker grey square to show how the national service compares
            target: 99.56,   // a white triangle demarcates the target uptime
            cells: [       // each value will be rendered as a bar, indicating the uptime of that cell
                {
                    name: 'NP',
                    uptime: 99.15   // the value represented by the line
                },
                {
                    name: 'QH2-UoM',
                    uptime: 99.66
                },
                {
                    name: 'QH2',
                    uptime: 98.8
                }
            ]
        }, {
            service: 'Cinder',
            national: 99.40, // will be drawn as a darker grey square to show how the national service compares
            target: 99.9,   // a white triangle demarcates the target uptime
            cells: [       // each value will be rendered as a bar, indicating the uptime of that cell
                {
                    name: 'NP',
                    uptime: 97.05   // the value represented by the line
                },
                {
                    name: 'QH2-UoM',
                    uptime: 99.05
                },
                {
                    name: 'QH2',
                    uptime: 99.88
                }
            ]
        }
        // each object in this array will be rendered as a separate uptime bullet chart
    ];

    function drawHistory() {
        var ug = report.uptimeHistory();
        d3.select('#chart')
            .selectAll('svg')
            .data(uptimeHistoryData)
            .call(ug)
        ;
        nv.utils.windowResize(ug.update);
    }

    function drawAvailability() {

        //noinspection SpellCheckingInspection
        var dataCenterColours = {
            'QH2': 'chocolate',
            'QH2-UoM': 'green',
            'NP': 'blue',
            'Other data centers': 'lightblue'
        };

        /**
         * Looks up the color in the dataCenterColours object and returns it. If not found, returns black.
         * @param key {string}
         * @returns {string}
         */
        var getColour = function (key) {
            return key in dataCenterColours && typeof dataCenterColours[key] === 'string' ? dataCenterColours[key] : 'black';
        };

        var chart = report.uptimeBullet()
            .color(function (cell) {
                return getColour(cell.name);
            });

        // We need to find the floor that each chart will start from. This will be set by the
        // lowest uptime found across all of the data centers.
        var lowestUptime = 100;
        uptimeData.forEach(function (d) {
            var dataMinimum = chart.getLowestUptime(d);
            lowestUptime = dataMinimum < lowestUptime ? dataMinimum : lowestUptime;
        });
        chart.domainMinimum(lowestUptime);

        d3.select('#extra')
            .selectAll('svg')   // we have removed the one svg element
            .data(uptimeData)
            .enter()
            .append('svg')
            .call(chart)
        ;
        nv.utils.windowResize(chart.update);
    }

    var render = function () {
        // remove the svg element so our graphs can appear in the same
        // section (the append was appending to the #extra, not the <svg>
        d3.selectAll('#extra svg').remove();
        // The history chart sets its height: allow its container to contract to the best fit.
        d3.select('#chart')
            .style('height', 'auto');
        drawHistory();
        drawAvailability();

    };

    return {
        render: render
    }
}();