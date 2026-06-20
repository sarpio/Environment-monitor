var weatherData = {{WEATHER_DATA}};

function formatTooltipPoint(point) {
    var options = point.series.options;
    var decimals = options.valueDecimals || 0;
    var unit = options.valueUnit || '';

    return '<div><b>' + point.series.name + ':</b> ' + point.y.toFixed(decimals) + ' ' + unit + '</div>';
}

function formatTooltipHour(point) {
    return '<div style="font-weight:bold;margin-bottom:6px;">Godz.: ' + point.hour + '</div>';
}

function formatAxisHour(hour) {
    return String(parseInt(String(hour).split(' ')[0].split(':')[0], 10));
}

function normalizePressure(pressure) {
    if (pressure < 850 || pressure > 1100) {
        return null;
    }

    return pressure;
}

function renderLatestValues() {
    var container = document.getElementById('latestValues');
    var latest = weatherData.current || weatherData.measurements[weatherData.measurements.length - 1];

    if (!container || !latest) {
        return;
    }

    var temperatureClass = latest.temperature >= 0 ? 'value-temperature-positive' : 'value-temperature-negative';

    var pressure = normalizePressure(latest.pressure);
    var pressureText = pressure === null ? '--' : pressure.toFixed(0);

    container.innerHTML =
        '<span class="latest-item ' + temperatureClass + '">' + latest.temperature.toFixed(1) + ' °C</span>' +
        '<span class="latest-item value-humidity">' + latest.humidity.toFixed(0) + ' %</span>' +
        '<span class="latest-item value-pressure">' + pressureText + ' hPa</span>';

    fitLatestValues(container);
}

function fitLatestValues(container) {
    var maxSize = 43;
    var minSize = 25;
    var size = maxSize;

    container.style.fontSize = size + 'px';

    while (container.scrollWidth > container.clientWidth && size > minSize) {
        size -= 1;
        container.style.fontSize = size + 'px';
    }
}

renderLatestValues();

Highcharts.chart('container', {

    chart: {
        backgroundColor: '#1e1e1e',
        plotBackgroundColor: '#1e1e1e',
        plotBorderWidth: 0,
        plotBorderColor: '#1e1e1e'
    },

    title: {
        text: 'Temperatura i Wilgotność',
        style: {
            fontSize: '18px',
            color: '#f5f5f5'
        }
    },

    xAxis: {
        categories: weatherData.measurements.map(function (point) {
            return formatAxisHour(point.hour);
        }),
        tickInterval: 4,
        tickColor: '#666',
        lineColor: '#444',
        gridLineColor: '#333',
        labels: {
            style: {
                fontSize: '12px',
                color: '#f5f5f5'
            }
        }
    },

    yAxis: [
        {
            title: {
                text: null,
                style: {
                    fontSize: '12px'
                }
            },
            labels: {
                style: {
                    fontSize: '12px',
                    color: '#f5f5f5'
                }
            },
            opposite: false
        },
        {
            title: {
                text: null,
                style: {
                    fontSize: '12px'
                }
            },
            labels: {
                style: {
                    fontSize: '12px',
                    color: '#f5f5f5'
                }
            },
            opposite: true
        }
    ],

    tooltip: {
        shared: true,
        useHTML: true,
        formatter: function () {
            if (this.points) {
                var html = '<div style="width:140px;padding:10px 15px 15px 0px;font-size:14px;">';
                html += formatTooltipHour(this.points[0].point);
                this.points.forEach(function (p) {
                    html += formatTooltipPoint(p);
                });
                html += '</div>';
                return html;
            } else {
                return '<div style="width:140px;padding:10px 15px 15px 0px;font-size:14px;">' + formatTooltipHour(this.point) + formatTooltipPoint(this.point) + '</div>';
            }
        }
    },

    legend: {
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'bottom',
        itemStyle: {
            fontSize: '12px'
        }
    },

    series: [
        {
            name: 'Temp.',
            type: 'spline',
            yAxis: 0,
            color: '#0b3d91',
            negativeColor: '#0b3d91',
            zones: [
                {
                    value: 0,
                    color: '#0b3d91'
                },
                {
                    color: '#ff3b30'
                }
            ],
            valueDecimals: 1,
            valueUnit: '°C',
            marker: {
                enabled: false
            },
            data: weatherData.measurements.map(function (point) {
                return {
                    y: point.temperature,
                    hour: point.hour
                };
            })
        },
        {
            name: ' Humi.',
            type: 'spline',
            yAxis: 1,
            color: '#34c759',
            valueDecimals: 0,
            valueUnit: '%',
            marker: {
                enabled: false
            },
            data: weatherData.measurements.map(function (point) {
                return {
                    y: point.humidity,
                    hour: point.hour
                };
            })
        }
    ]
});

Highcharts.chart('containerPressure', {

    chart: {
        backgroundColor: '#1e1e1e',
        plotBackgroundColor: '#1e1e1e',
        plotBorderWidth: 0,
        plotBorderColor: '#1e1e1e'
    },

    title: {
        text: 'Ciśnienie',
        style: {
            fontSize: '18px',
            color: '#f5f5f5'
        }
    },

    xAxis: {
        categories: weatherData.measurements.map(function (point) {
            return formatAxisHour(point.hour);
        }),
        tickInterval: 4,
        tickColor: '#666',
        lineColor: '#444',
        gridLineColor: '#333',
        labels: {
            style: {
                fontSize: '12px',
                color: '#f5f5f5'
            }
        }
    },

    yAxis: {
        allowDecimals: false,
        title: {
            text: null,
            style: {
                fontSize: '12px'
            }
        },
        labels: {
            enabled: true,
            reserveSpace: false,
            align: 'left',
            x: 8,
            y: 4,
            style: {
                fontSize: '12px',
                color: '#f5f5f5'
            }
        }
    },

    tooltip: {
        shared: true,
        useHTML: true,
        formatter: function () {
            if (this.points) {
                var rows = this.points.map(function (p) {
                    return formatTooltipPoint(p);
                }).join('');
                return '<div style="width:140px;padding:10px 15px 15px 0px;font-size:14px;">' + formatTooltipHour(this.points[0].point) + rows + '</div>';
            }
            return '<div style="width:140px;padding:10px 15px 15px 0px;font-size:14px;">' + formatTooltipHour(this.point) + formatTooltipPoint(this.point) + '</div>';
        }
    },

    legend: {
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'bottom',
        itemStyle: {
            fontSize: '12px'
        }
    },

    series: [
        {
            name: 'Ciśnienie',
            type: 'spline',
            color: '#ff9500',
            valueDecimals: 0,
            valueUnit: 'hPa',
            marker: {
                enabled: false
            },
            data: weatherData.measurements.map(function (point) {
                return {
                    y: normalizePressure(point.pressure),
                    hour: point.hour
                };
            })
        }
    ]
});
