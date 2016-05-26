var utils = function () {

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

        get: function (key) {
            return key in facultyColours && typeof facultyColours[key] === 'string' ? facultyColours[key] : 'black';
        }
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
            });
    }

    return { // exports
        facultyColours: facultyColours,
        createButton: createButton,
    }
}();