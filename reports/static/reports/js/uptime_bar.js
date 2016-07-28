/**
 * Created by mpaulo on 25/07/2016.
 */
'use strict';

var report = report || {};

report.d3 = function () {


    (function checkIfStyleSheetLoaded() {
        var stylesheetName = "nv.d3.css";  // we'll piggy back off of the nvd3 bullet chart styles
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

        var margin = {top: 5, right: 40, bottom: 20, left: 120} // margin is not properly used yet
            , minimumWidth = 800
            , width = null
            , bulletHeight = 15
            , bulletSpacing = 15
            , transitionDuration = 0
            , subtitle = "% Available"
            , rangeLabels = ["Maximum", "National"]
            , targetLabel = "Target"
            , noData = "No Data Available."
            , color = nv.utils.getColor(['#1f77b4'])
            ;

        //============================================================
        // Private Variables
        //------------------------------------------------------------

        var dispatch = d3.dispatch('elementMouseover', 'elementMouseout', 'elementMousemove')
            , tooltip = nv.models.tooltip()
            ;

        tooltip
            .duration(0)
            .headerEnabled(false);

        var calculateWidth = function (width, container, margin) {
            var newWidth = (width || parseInt(container.style('width'), 10) || 960) - margin.left - margin.right;
            return newWidth < minimumWidth ? minimumWidth : newWidth;
        };


        function chart(selection) {

            selection.each(function drawGraph(d) {
                // here `d` is the data and `this` is the element
                var container = d3.select(this);

                // for the moment, we give it the nvd3-svg class so that it takes on the nvd3 stylesheet
                // attributes rather than the default ones. (needed for resizing)
                container.attr('class', 'nvd3-svg');

                chart.update = function () {
                    container.selectAll('*').remove();
                    // we aren't transitioning properly...
                    container.transition().duration(transitionDuration).call(chart);
                };

                var usableWidth = calculateWidth(width, container, margin);
                // height will default to 3 bars...
                var height = (bulletHeight + bulletSpacing) * 3 + bulletSpacing;

                if (!d) {
                    //Remove any previously created chart components
                    container.selectAll('g').remove();

                    container.selectAll('.nv-noData')
                        .data([noData])
                        .enter()
                        .append('text')
                        .attr('class', 'nvd3 nv-noData')
                        .attr('dy', '-.7em')
                        .attr('x', margin.left + usableWidth / 2)
                        .attr('y', margin.top + height / 2)
                        .style('text-anchor', 'middle')
                        .text(function (t) {
                            return t;
                        });
                    return chart;
                } else {
                    container.selectAll('.nv-noData').remove();
                }


                var minimum = 99.00;
                minimum = d.national < minimum ? d.national : minimum;
                minimum = d.target < minimum ? d.target : minimum;
                d.values.forEach(function (v) {
                    minimum = v.value < minimum ? v.value : minimum;
                });

                minimum = Math.floor(minimum - 1); // round down to nearest number below the minimum

                var xScale = d3.scale.linear()
                        .domain([minimum, 100])
                        .range([0, usableWidth])
                        .clamp(true)
                    ;
                var xAxis = d3.svg.axis()
                        .scale(xScale)
                    ;

                // calculate the actual height needed.
                height = 0;

                height += (bulletHeight + bulletSpacing) * d.values.length + bulletSpacing;

                var wrap = container.selectAll('g.nv-wrap.nv-bullet')
                    .data([d]);
                var wrapEnter = wrap.enter().append('g').attr('class', 'nvd3 nv-wrap nv-bullet');
                var gEnter = wrapEnter.append('g');
                var g = wrap.select('g');
                var rangeClassNames = 'nv-range nv-range0';
                gEnter.append('rect').attr('class', rangeClassNames);
                rangeClassNames = 'nv-range nv-range1';
                gEnter.append('rect').attr('class', rangeClassNames);

                wrap.attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');
                g.select('rect.nv-range0')
                    .attr('height', height)
                    .attr('width', xScale(100))
                    .attr('x', xScale(minimum))
                ;
                g.select('rect.nv-range1')
                    .attr('height', height)
                    .attr('width', xScale(d.national))
                    .attr('x', xScale(minimum))
                ;

                var titles = gEnter.append('g')
                        .attr('class', 'nv-titles')
                    ;
                for (var i = 0; i < d.values.length; i++) {
                    var bulletTopY = bulletSpacing + (bulletHeight + bulletSpacing) * i;
                    var titleTopY = bulletTopY + bulletHeight / 2;

                    var title = titles.append('g')
                            .attr('text-anchor', 'end')
                            .attr('transform', 'translate(-6,' + titleTopY + ')')
                        ;
                    title.append('text')
                        .attr('class', 'nv-title')
                        .text(d.values[i].cell);
                    title.append('text')
                        .attr('class', 'nv-subtitle')
                        .attr('dy', '1em')
                        .text(subtitle);
                    gEnter.append('rect').attr('class', 'nv-measure' + i);

                    var scaled = xScale(d.values[i].value);
                    g.select('rect.nv-measure' + i)
                        .data([d.values[i]])
                        .style('fill', color)
                        .attr('height', bulletHeight)
                        .attr('y', bulletTopY)
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
                var markerData = [{value: d.target, label: targetLabel}];
                gEnter.selectAll('path.nv-markerTriangle')
                    .data(markerData)
                    .enter()
                    .append('path')
                    .attr('class', 'nv-markerTriangle')
                    .attr('transform', function (d) {
                        return 'translate(' + xScale(d.value) + ', ' + (height / 2) + ')'
                    })
                    .attr('d', 'M 0 ' + h3 + ' L ' + h3 + ' ' + (-h3) + ' L ' + (-h3) + ' ' + (-h3) + ' Z')
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
                    })
                ;
                wrap.selectAll('.nv-range')
                    .on('mouseover', function (d, index) {
                        dispatch.elementMouseover({
                            value: index != 0 ? d.national : 100,
                            label: rangeLabels[index],
                            color: d3.select(this).style('fill')
                        })
                    })
                    .on('mousemove', function (d, index) {
                        dispatch.elementMousemove({
                            value: index != 0 ? d.national : 100,
                            label: rangeLabels[index],
                            color: d3.select(this).style('fill')
                        })
                    })
                    .on('mouseout', function (d, index) {
                        dispatch.elementMouseout({
                            value: index != 0 ? d.national : 100,
                            label: rangeLabels[index],
                            color: d3.select(this).style('fill')
                        })
                    });
                var axis = gEnter
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

        chart.transitionDuration = function (_) {
            if (!arguments.length) return transitionDuration;
            transitionDuration = _;
            return chart;
        };

        chart.subtitle = function (_) {
            if (!arguments.length) return subtitle;
            subtitle = _;
            return chart;
        };

        chart.rangeLabels = function (_) {
            if (!arguments.length) return rangeLabels;
            rangeLabels = _;
            return chart;
        };

        chart.targetLabel = function (_) {
            if (!arguments.length) return targetLabel;
            targetLabel = _;
            return chart;
        };

        chart.color = function (_) {
            if (!arguments.length) return color;
            color = _;
            return chart;
        };

        chart.noData = function (_) {
            if (!arguments.length) return noData;
            noData = _;
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