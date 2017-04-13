'use strict';

/**
 * A grab bag of common bits
 */
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

    const FACULTIES = ['VCAMCM', 'VAS', 'FoS', 'MDHS', 'MLS', 'MSE',
        'MGSE', 'FBE', 'FoA', 'ABP'];
    const CLOUD_FACULTIES = FACULTIES.concat('services', 'unknown');
    const STORAGE_FACULTIES = CLOUD_FACULTIES.concat('external');

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
        'Unknown': 'blue',
        'Services': 'red',
        'External': 'green',

        get: getColour
    };

    const STORAGE_PRODUCT_TYPES = ['computational', 'market', 'vault'];

    var storageColours = {
        'Market': 'blue',
        'Computational': 'lightblue',
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
        var parent_id = options.parent_id || 'iDateButtons';
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
        return d3.select('#iDateButtons .active').attr('id');
    }

    function findType() {
        return d3.select('#graph-buttons .active').attr('id');
    }

    function createDateButtons(chosen) {
        var selector = typeof chosen !== 'undefined' ? chosen : '#year';
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

    const SPINNER_OPTIONS = {
        lines: 9, // The number of lines to draw
        length: 9, // The length of each line
        width: 5, // The line thickness
        radius: 14, // The radius of the inner circle
        color: ['blue', 'grey'], // #rgb or #rrggbb or array of colors
        speed: 1.9, // Rounds per second
        trail: 40, // Afterglow percentage
        className: 'spinner' // The CSS class to assign to the spinner
    };

    function upperCaseFirstLetter(key_name) {
        return key_name.charAt(0).toUpperCase() + key_name.slice(1);
    }

    /**
     * Converts csv into a format that nvd3 prefers.
     * @param csv The source data in csv format
     * @param columnNames
     * @returns {Array} The translated data
     */
    function convertCsvToNvd3Format(csv, columnNames) {
        var result = [];
        csv.sort(function (a, b) {
            return new Date(a['date']) - new Date(b['date']);
        });
        for (var i = 0; i < columnNames.length; i++) {
            var o = {};
            o.key = upperCaseFirstLetter(columnNames[i]);
            o.values = csv.map(function (d) {
                return [new Date(d['date']).getTime(), parseInt(d[columnNames[i].toLowerCase()])];
            });
            result.push(o)
        }
        return result;
    }

    function renderStorageChart(data_path, series_names) {
        var colours = (series_names === STORAGE_PRODUCT_TYPES) ? storageColours : facultyColours;
        var spinner = new Spinner(SPINNER_OPTIONS);
        spinner.spin(document.getElementById('chart'));

        d3.csv(data_path, function (error, csv) {
            if (error) {
                console.log("Error on loading data: " + error);
                spinner.stop();
                utils.showError(error);
                return;
            }
            var nvd3Data = convertCsvToNvd3Format(csv, series_names);

            // for examples of these options see:
            // http://cmaurer.github.io/angularjs-nvd3-directives/line.chart.html
            var chart = nv.models.stackedAreaChart()
                .margin({right: 80})
                .x(function (d) {
                    return d[0]
                })
                .y(function (d) {
                    return d[1]
                })
                .useInteractiveGuideline(true)
                .rightAlignYAxis(true)
                // Don't allow user to choose 'Stacked', 'Stream' etc...
                .showControls(false)
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
                .datum(nvd3Data)
                .transition().duration(500)
                .call(chart);

            // Update chart when the window resizes
            nv.utils.windowResize(chart.update);

            spinner.stop();

            return chart;
        });
    }

    /**
     * A function that brings up a dialogue showing the passed in error
     * @param error An object with a statusText field containing the message
     * to be shown. If the field doesn't exit a default message will be shown
     * instead.
     */
    var showError = function (error) {
        // We'll go for a default error message
        var errorText = "The server is not responding";
        // and overwrite it if there is a more specific message
        if ('statusText' in error && error.statusText) {
            errorText = error.statusText;
        }
        d3.select('#md_message')
            .html(errorText);
        const errorDialog = d3.select('#md_error');
        errorDialog
            .style('opacity', '1')
            .style('pointer-events', 'auto');

        d3.select('#md_close')
            .on('click', function () {
                errorDialog
                    .style('opacity', '0')
                    .style('pointer-events', 'none');
            });
    };

    return { // exports
        STORAGE_PRODUCT_TYPES: STORAGE_PRODUCT_TYPES,
        STORAGE_FACULTIES: STORAGE_FACULTIES,
        CLOUD_FACULTIES: CLOUD_FACULTIES,
        SPINNER_OPTIONS: SPINNER_OPTIONS,
        generateFacultyKey: generateFacultyKey,
        createButton: createButton,
        createDateButtons: createDateButtons,
        createFacultyButtons: createFacultyButtons,
        findFrom: findFrom,
        findType: findType,
        cellColours: cellColours,
        facultyColors: facultyColours,
        renderStorageChart: renderStorageChart,
        convertCsvToNvd3Format: convertCsvToNvd3Format,
        showError: showError
    }
}();