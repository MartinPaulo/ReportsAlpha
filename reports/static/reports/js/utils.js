'use strict';

var utils = function () {

    // mixin method to return colour value from colour classes
    var getColour = function(key) {
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

        get: getColour
    };

    var storageColours = {
        'Market': 'blue',
        'Compute': 'lightblue',
        'Vault': 'orange',

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
                var event = new Event('redraw');
                d3.select('#chart svg')[0][0].dispatchEvent(event);

            });
    }

    function findFrom() {
        return d3.select('#date-buttons .active').attr('id');
    }

    function createDateButtons() {
        createButton('Year');
        createButton('6 Months', {target_id: 'sixMonths'});
        createButton('3 Months', {target_id: 'threeMonths'});
        createButton('1 Month', {target_id: 'oneMonth'});
        d3.select('#year')
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

    return { // exports
        storageColours: storageColours,
        facultyColours: facultyColours,
        createDateButtons: createDateButtons,
        createFacultyButtons: createFacultyButtons,
        findFrom: findFrom
    }
}();