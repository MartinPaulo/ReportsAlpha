/**
 * Created by mpaulo on 25/07/2016.
 */
'use strict';

var report = report || {};

report.d3 = function () {


    (function checkIfStyleSheetLoaded() {
        var stylesheetName = "nv.d3.css";  // we'll piggy back off of the nvd3 bullet chart
        var found = false;
        for (var i = 0; i < document.styleSheets.length; i++) {
            if (document.styleSheets[i].href && document.styleSheets[i].href.indexOf(stylesheetName) > 0) {
                found = true;
            }
        }
        if (!found) {
            console.log("Required stylesheet " + stylesheetName + " is not found!")
        }
    })();


    var uptimeData = [
        {
            national: 98.0, // the gray marker
            target: 99.0,  // the white triangle
            values: [   // the bars
                {
                    cell: "NP",
                    value: 98.05   // the value represented by the line
                },
                {
                    cell: "QH2-UoM",
                    value: 97.05
                },
                {
                    cell: "QH2",
                    value: 99.05
                }
            ]
        }
    ];

    function uptimeBar() {

        //============================================================
        // Public Variables with Default Settings
        //------------------------------------------------------------

        var bulletMargin = {top: 0, right: 0, bottom: 0, left: 0}
            , margin = {top: 5, right: 40, bottom: 20, left: 120}
            , minimumWidth = 800
            , width = null
            , bulletHeight = 10
            , bulletSpacing = 10
            , headingText = "Uptime"
            , transitionDuration = 0
            , subtitle = "% Available"
            , rangeLabels = ["Maximum", "National"]
            , valueLabel = "Current"
            , targetLabel = "Target"
            , color = nv.utils.getColor(['#1f77b4'])
            , dispatch = d3.dispatch('elementMouseover', 'elementMouseout', 'elementMousemove')
            , tooltip = nv.models.tooltip()
            // need to make the no data message display if there is no data available...
            , noData = 'No Data Available'
            ;

        tooltip
            .duration(0)
            .headerEnabled(false);

        var calculateWidth = function (width, container, margin) {
            var newWidth = (width || parseInt(container.style('width'), 10) || 960) - margin.left - margin.right;
            return newWidth < minimumWidth ? minimumWidth : newWidth;
        };

        function chart(selection) {

            selection.each(function drawGraph(dataset, i) {

                var container = d3.select(this);

                // for the moment, just give it the nvd3-svg class so that it takes on the nvd3 stylesheet
                // attributes rather than the default ones. (needed for resizing)
                container.attr('class', 'nvd3-svg');

                chart.update = function () {
                    container.selectAll('*').remove();
                    // we aren't transitioning properly...
                    container.transition().duration(transitionDuration).call(chart);
                };

                var availableWidth = calculateWidth(width, container, margin);

                var noOfDataSets = dataset.length;

                var minimum = 99.00;
                dataset.forEach(function (d) {
                    minimum = d.national < minimum ? d.national : minimum;
                    minimum = d.target < minimum ? d.target : minimum;
                    d.values.forEach(function (v) {
                        minimum = v.value < minimum ? v.value : minimum;
                    })
                });
                minimum = Math.floor(minimum - 1); // round down to nearest number below the minimum

                var xScale = d3.scale.linear()
                        .domain([minimum, 100])
                        .range([0, availableWidth])
                        .clamp(true)
                    ;
                var xAxis = d3.svg.axis()
                        .scale(xScale)
                    ;

                var height = 0;
                dataset.forEach(function (d) {
                    // height += margin.top + margin.bottom;
                    var cellCount = d.values.length;
                    height += (bulletHeight + bulletSpacing) * cellCount + bulletSpacing;
                });

                var wrap = container.selectAll('g.nv-wrap.nv-bullet').data([dataset]);
                var wrapEnter = wrap.enter().append('g').attr('class', 'nvd3 nv-wrap nv-bullet');
                var gEnter = wrapEnter.append('g');
                var g = wrap.select('g');
                var rangeClassNames = 'nv-range nv-range0';
                gEnter.append('rect').attr('class', rangeClassNames);
                rangeClassNames = 'nv-range nv-range1';
                gEnter.append('rect').attr('class', rangeClassNames);

                for (var ii = 0, il = dataset[i].values.length; ii < il; ii++) {
                    gEnter.append('rect').attr('class', 'nv-measure' + ii);
                }
                wrap.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');
                g.select('rect.nv-range0')
                    .attr('height', height)
                    .attr('width', xScale(100))
                    .attr('x', xScale(minimum))
                ;
                g.select('rect.nv-range1')
                    .attr('height', height)
                    .attr('width', xScale(dataset[i].national))
                    .attr('x', xScale(minimum))
                ;

                for (var ii = 0, il = dataset[i].values.length; ii < il; ii++) {
                    var scaled = xScale(dataset[i].values[ii].value);
                    g.select('rect.nv-measure' + ii)
                        .data([dataset[i].values[ii]])
                        .style('fill', color)
                        .attr('height', bulletHeight)
                        .attr('y', bulletSpacing + (bulletHeight + bulletSpacing) * ii)
                        .attr('x', xScale(minimum))
                        .attr('width', scaled)
                        .on('mouseover', function (d) {
                            dispatch.elementMouseover({
                                value: d.value,
                                label: d.cell,
                                color: d3.select(this).style('fill')
                            })
                        })
                        .on('mousemove', function (d) {
                            dispatch.elementMousemove({
                                value: d.value,
                                label: d.cell,
                                color: d3.select(this).style('fill')
                            })
                        })
                        .on('mouseout', function (d) {
                            dispatch.elementMouseout({
                                value: d.value,
                                label: d.cell,
                                color: d3.select(this).style('fill')
                            })
                        })
                    ;
                }
                var h3 = height / 6;
                var markerData = [{value: dataset[i].target, label: "Target"}];
                gEnter
                    .selectAll('path.nv-markerTriangle')
                    .data(markerData)
                    .enter()
                    .append('path')
                    .attr('class', 'nv-markerTriangle')
                    .attr('d', 'M0,' + h3 + 'L' + h3 + ',' + (-h3) + ' ' + (-h3) + ',' + (-h3) + 'Z')
                    .on('mouseover', function (d) {
                        dispatch.elementMouseover({
                            value: d.value,
                            label: d.label,
                            color: d3.select(this).style('fill'),
                            pos: [d.value, height / 3]
                        })
                    })
                    .on('mousemove', function (d) {
                        dispatch.elementMousemove({
                            value: d.value,
                            label: d.label,
                            color: d3.select(this).style('fill')
                        })
                    })
                    .on('mouseout', function (d) {
                        dispatch.elementMouseout({
                            value: d.value,
                            label: d.label,
                            color: d3.select(this).style('fill')
                        })
                    });
                g.selectAll('path.nv-markerTriangle')
                    .data(markerData)
                    .attr('transform', function (d) {
                        return 'translate(' + xScale(d.value) + ', ' + (height / 2) + ')'
                    })
                ;
                wrap.selectAll('.nv-range')
                    .on('mouseover', function (d, index) {
                        dispatch.elementMouseover({
                            value: index != 0 ? d[i].national : 100,
                            label: rangeLabels[index],
                            color: d3.select(this).style('fill')
                        })
                    })
                    .on('mousemove', function (d, index) {
                        dispatch.elementMousemove({
                            value: index != 0 ? d[i].national : 100,
                            label: rangeLabels[index],
                            color: d3.select(this).style('fill')
                        })
                    })
                    .on('mouseout', function (d, index) {
                        dispatch.elementMouseout({
                            value: index != 0 ? d[i].national : 100,
                            label: rangeLabels[index],
                            color: d3.select(this).style('fill')
                        })
                    });
                var axis =  gEnter
                    .append('g')
                    .attr('class', 'nv-axis')
                    .attr('transform', function (d) {
                        return 'translate(' + xScale(minimum) + ', ' + height + ')'
                    })
                    .call(xAxis);

            });
            return chart;
        }

        dispatch.on('elementMouseover.tooltip', function (evt) {
                evt['series'] = {
                    key: evt.label,
                    value: evt.value,
                    color: evt.color
                };
                tooltip.data(evt).hidden(false);
            }
        );
        dispatch.on('elementMouseout.tooltip', function (evt) {
            tooltip.hidden(true);
        });
        dispatch.on('elementMousemove.tooltip', function (evt) {
            tooltip();
        });

        // Expose the public variables
        chart.margin = function (_) {
            if (!arguments.length) return margin;
            margin = _;
            return chart;
        };

        chart.width = function (_) {
            if (!arguments.length) return width;
            width = _;
            return chart;
        };

        chart.minimumWidth = function (_) {
            if (!arguments.length) return minimumWidth;
            minimumWidth = _;
            return chart;
        };

        chart.bulletHeight = function (_) {
            if (!arguments.length) return bulletHeight;
            bulletHeight = _;
            return chart;
        };

        chart.bulletSpacing = function (_) {
            if (!arguments.length) return bulletSpacing;
            bulletSpacing = _;
            return chart;
        };


        chart.headingText = function (_) {
            if (!arguments.length) return headingText;
            headingText = _;
            return chart;
        };

        chart.transitionDuration = function (_) {
            if (!arguments.length) return transitionDuration;
            transitionDuration = _;
            return chart;
        };

        chart.color = function (_) {
            if (!arguments.length) return color;
            color = _;
            return chart;
        };

        return chart;
    }


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

        var chart = uptimeBar()
            .color(function (d, i) {
                return getColour(d.cell);
            });

        var target = d3.select('#chart')
                .selectAll('svg')
                .datum(uptimeData)
                .call(chart)
            ;
        nv.utils.windowResize(chart.update);
    };


    return {
        render: render
    }
}();