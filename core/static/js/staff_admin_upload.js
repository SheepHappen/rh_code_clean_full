
$(document).ready(function() {
    $('#records').DataTable({
        dom: 'rtip',
        paging: false,
    });
    var generateGraph = function (data) {
        var layout = {
            title: "Risk Score",
            hovermode: "closest",
            legend: {
                tracegroupgap: 0
            },
            violingap: 0,
            violingroupgap: 0,
            violinmode: "overlay",
            height: 500,
            xaxis: {
                tickmode: 'array',
                tickvals: ['0', '1', '2', '3', '4', '5' ,'6','7','8','9', '10'],
                ticktext: [
                    '0 <br> (Very Low)',
                    '1',
                    '2',
                    '3',
                    '4',
                    '5',
                    '6',
                    '7',
                    '8',
                    '9',
                    '10 <br> (Very High)'
                ],
                range: [0, 10]
            },
            yaxis: {
                showgrid: true,
                range: [0, 1]
            }
        };
        var spline = {
            x: Object.values(data),
            text: Object.keys(data),
            hoveron: "points+kde",
            meanline: {
                visible: true
            },
            points: "all",
            pointpos: 0.4,
            box: {
                visible: true
            },
            jitter: 0.05,
            scalemode: "count",
            marker: {
                line: {
                    width: 2,
                    color: "red"
                },
                symbol: "circle"
            },
            showlegend: false,
            side: "positive",
            type: "violin",
            name: "",
            span: [
                0
            ],
            line: {
                color: "#bebada"
            },
            orientation: "h"
        };
        var extras = {
            responsive: true,
            displayModeBar: false
        }

        Plotly.newPlot("preview-chart", [spline], layout, extras);
    };

    if ($( "#initial-preview-chart" ).length) {
        var graphData = JSON.parse($( "#initial-preview-chart" ).html());
        if (graphData) {
            generateGraph(graphData);
        }
    }
    
});