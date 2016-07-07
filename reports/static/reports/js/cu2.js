/**
 * Created by mpaulo on 4/07/2016.
 */


var report = report || {};

report.d3 = function () {


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

        // nv.addGraph(function () {
        var margin = {top: 5, right: 40, bottom: 25, left: 120},
            width = 960 - margin.left - margin.right,
            height = 60 - margin.top - margin.bottom;
        var chart = nv.models.bulletChart();
        chart.bullet.color(function(d) {return d.color});
        var data = exampleData();
        function renderBullet(target) {
            target
                .attr("class", "bullet")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom)
                .append('g')
                .transition().duration(500)
                .call(chart)
            ;
        }
        //    d3.select('#chart').select('svg').remove();
        var target = d3.select('#chart')
            .selectAll('svg') // required to move parentNode
            .data(data);    // join data to any existing elements
        renderBullet(target); // render on the existing elements
        renderBullet(target.enter().append('svg')); // render on the missing elements
    };

    function exampleData() {
        return [
            {
                "title": "NP Uptime",  // Label the bullet chart
                "subtitle": "% Available", // sub-label for bullet chart
                "ranges": [93.00, 100], // Minimum, mean and maximum values.
                "rangeLabels": ["National", ""],
                "measures": [98.05], // Value representing current measurement (the thick blue line in the example)
                "measureLabels": ["Current"],
                "markers": [99.99], // Place a marker on the chart (the white triangle marker)
                "markerLabels": ["Target"],
                "color": 'blue'
            },
            {
                "title": "QH2-UoM Uptime",
                "subtitle": "% Available",
                "ranges": [93.00, 100],
                "rangeLabels": ["National", ""],
                "measures": [97.05],
                "measureLabels": ["Current"],
                "markers": [99.99],
                "markerLabels": ["Target"]
                ,"color": 'green'
            },
            {
                "title": "QH2 Uptime",
                "subtitle": "% Available",
                "ranges": [93.00, 100],
                "rangeLabels": ["National", ""],
                "measures": [98.05],
                "measureLabels": ["Current"],
                "markers": [99.99],
                "markerLabels": ["Target"],
                "color": 'chocolate'
            }
        ];
    }

    return {
        render: render,
        exampleData: exampleData
    }
}();