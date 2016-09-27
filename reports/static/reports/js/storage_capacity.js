'use strict';

var report = report || {};

report.d3 = function () {

    utils.createDateButtons();

    /* mixin method to return colour value from colour classes */
    var getColour = function (key) {
        return key in this && typeof this[key] === 'string' ? this[key] : 'black';
    };

    var storageColours = {
        'Market': 'blue',
        'Computational': 'lightblue',
        'Vault': 'orange',

        get: getColour
    };

    function getKey(key_name) {
        return key_name.charAt(0).toUpperCase() + key_name.slice(1);
    }

    var render = function () {
        var data_path = '/reports/actual/?from=' + utils.findFrom() + '&model=StorageCapacity';
        d3.select('#a_data').attr('href', data_path);
        // d3.json(data_path, utils.getStorageChart());
        d3.csv(data_path, function (error, csv) {
            if (error) {
                console.log('Error on loading data: ' + error);
                return;
            }
            csv.sort(function (a, b) {
                return new Date(a['date']) - new Date(b['date']);
            });

            // convert the csv passed in as an argument into the format that nvd3 prefers.
            var nvd3Data = [];
            var types = ['computational', 'market', 'vault'];
            for (var i = 0; i < types.length; i++) {
                var o = {};
                o.key = getKey(types[i]);
                o.values = csv.map(function (d) {
                    return [new Date(d['date']).getTime(), parseInt(d[types[i].toLowerCase()])];
                });
                nvd3Data.push(o)
            }
            var chart = nv.models.stackedAreaChart()
                .margin({right: 100})
                .x(function (d) {
                    return d[0]
                })
                .y(function (d) {
                    return d[1]
                })
                .useInteractiveGuideline(true)
                .rightAlignYAxis(true)
                .showControls(false)
                .clipEdge(true)
                .noData('No Data available')
                .color(function (d) {
                    return storageColours.get(d['key']);
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

            return chart;
        });
    };

    d3.select('#chart svg')[0][0].addEventListener('redraw', function (e) {
        render();
    }, false);

    return {
        render: render
    }
}();