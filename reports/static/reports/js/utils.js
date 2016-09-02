'use strict';

var utils = function () {

    var facultyNames = [
        // http://about.unimelb.edu.au/governance-and-leadership/faculties#
        ['VCAMCM', 'Victorian College of the Arts and Melbourne Conservatorium of Music'],
        ['VAS', 'Veterinary and Agricultural Sciences'],
        ['FoS', 'Faculty of Science'],
        ['MDHS', 'Medicine, Dentistry and Health Sciences'],
        ['MLS', 'Melbourne Law School'],
        ['MSE', 'Melbourne School of Engineering'],
        ['MGSE', 'Melbourne Graduate School of Education'],
        ['FBE', 'Faculty of Business and Economics'],
        ['FoA', 'Faculty of Arts'],
        ['ABP', 'Architecture, Building and Planning']
    ];

    function generateFacultyKey() {
        var headings = ['Abbreviation', 'Meaning'];
        var table = d3.select('body').append('table');
        table.append("thead").append('tr')
            .selectAll('th')
            .data(headings)
            .enter()
            .append('th')
            .text(function (column) {
                return column;
            });
        table.append("tbody").selectAll('tr')
            .data(facultyNames)
            .enter()
            .append('tr')
            .selectAll('td')
            .data(function (row) {
                return row;
            })
            .enter()
            .append('td').text(function (column) {
            return column;
        });
    }

    /* mixin method to return colour value from colour classes */
    var getColour = function (key) {
        return key in this && typeof this[key] === 'string' ? this[key] : 'black';
    };

    var facultyColours = {
        'VCAMCM': '#1f77b4',
        'VAS': '#ff7f0e',
        'FoS': '#2ca02c',
        'MDHS': '#d62728',
        'MLS': '#9467bd',
        'MSE': '#8c564b',
        'MGSE': '#e377c2',
        'FBE': '#7f7f7f',
        'FoA': '#bcbd22',
        'ABP': '#17becf',
        'Other': 'red',
        'Unknown': 'blue',

        get: getColour
    };

    var storageColours = {
        'Market': 'blue',
        'Compute': 'lightblue',
        'Vault': 'orange',

        get: getColour
    };

    var cellColours = {
        'QH2': 'chocolate',
        'QH2-UoM': 'green',
        'NP': 'blue',
        'QH2 and NP': 'darkblue',
        'Other data centers': 'lightblue',

        get: getColour
    };

// https://github.com/d3/d3/wiki/Selections
    function createButton(title, options) {
        options = options || {};
        var target_id = options.target_id || title.toLowerCase();
        var parent_id = options.parent_id || 'date-buttons';
        d3.select('#' + parent_id)
            .append('input')
            .attr('type', 'button')
            .attr('id', target_id)
            .attr('value', title)
            .on('click', function () {
                d3.selectAll('#' + parent_id + ' input')
                    .classed('active', false);
                d3.select('#' + target_id)
                    .attr('class', 'active');
                d3.select('#chart svg')[0][0].dispatchEvent(new Event('redraw'));
            });
    }

    function findFrom() {
        return d3.select('#date-buttons .active').attr('id');
    }

    function findType() {
        return d3.select('#graph-buttons .active').attr('id');
    }

    function createDateButtons(chosen) {
        var selector = typeof chosen !== 'undefined' ? chosen:  '#year';
        createButton('Year');
        createButton('6 Months', {target_id: 'sixMonths'});
        createButton('3 Months', {target_id: 'threeMonths'});
        createButton('1 Month', {target_id: 'oneMonth'});
        d3.select(selector)
            .on('click')();
    }

    function createFacultyButtons() {
        createButton('Total', {parent_id: 'graph-buttons'});
        createButton('Vault', {parent_id: 'graph-buttons'});
        createButton('Market', {parent_id: 'graph-buttons'});
        createButton('Compute', {parent_id: 'graph-buttons'});
        d3.select('#total')
            .on('click')();
    }

    function getStorageChart(options) {
        options = options || {};
        var colours = ('useFacultyColours' in options && options.useFacultyColours) ? facultyColours : storageColours;
        return function (error, data) {

            // for examples of these options see: http://cmaurer.github.io/angularjs-nvd3-directives/line.chart.html
            var chart = nv.models.stackedAreaChart()
                .margin({right: 100})
                .x(function (d) {
                    return d[0]
                })
                .y(function (d) {
                    return d[1]
                })
                .useInteractiveGuideline(true)  // Tooltips which show the data points. Very nice!
                .rightAlignYAxis(true)          // Move the y-axis to the right side.
                .showControls(false)            // Don't allow user to choose 'Stacked', 'Stream' etc...
                .clipEdge(true)
                .noData('No Data available')
                .color(function (d) {
                    return colours.get(d['key']);
                });

            chart.xAxis
                .tickFormat(function (d) {
                    return d3.time.format('%Y-%m-%d')(new Date(d))
                })
                .axisLabel('Date');

            chart.yAxis
                .tickFormat(d3.format(',.2f'))
                .axisLabel('TB');

            d3.select('#chart svg')
                .datum(data)
                .transition().duration(500)
                .call(chart);

            // Update chart when the window resizes
            nv.utils.windowResize(chart.update);

            return chart;
        };
    }

    return { // exports
        generateFacultyKey: generateFacultyKey,
        getStorageChart: getStorageChart,
        createDateButtons: createDateButtons,
        createFacultyButtons: createFacultyButtons,
        findFrom: findFrom,
        findType: findType,
        cellColours: cellColours,
        facultyColors: facultyColours
    }
}();