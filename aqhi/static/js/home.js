"use strict";

moment.locale('zh-cn');

var CountdownLatch = function(limit) {
  this.limit = limit;
  this.count = 0;
  this.waitBlock = function (){};
};
CountdownLatch.prototype.countDown = function() {
  this.count = this.count + 1;
  if(this.limit <= this.count) {
    return this.waitBlock();
  }
};
CountdownLatch.prototype.await = function(callback) {
  this.waitBlock = callback;
};

var qualityTexts = {
  E: {cls: 'qlty-excellent', text: '优'},
  G: {cls: 'qlty-good', text: '良'},
  LP: {cls: 'qlty-lightly', text: '轻度污染'},
  MP: {cls: 'qlty-moderately', text: '中度污染'},
  HP: {cls: 'qlty-heavily', text: '重度污染'},
  SP: {cls: 'qlty-severely', text: '严重污染'}
};

var aqhiRange = [4, 7, 8, 11];
var aqhiTexts = {
  0: {cls: 'aqhi-low', text: '低'},
  1: {cls: 'aqhi-moderate', text: '中'},
  2: {cls: 'aqhi-high', text: '高'},
  3: {cls: 'aqhi-very-high', text: '较高'},
  4: {cls: 'aqhi-serious', text: '严重'}
};
var aqhiAdviceTextEles = {
  0: $(`
    <p class="card-text">
      所有人员均可正常活动。
    </p>
  `),
  1: $(`
    <p class="card-text">
      <span class="people-class">心脏病或呼吸系统疾病患者</span>
      <br>应<strong>考虑减少</strong>户外体力消耗。
    </p>
  `),
  2: $(`
    <p class="card-text">
      <span class="people-class">心脏病或呼吸系统疾病患者</span>
      <span class="people-class">儿童及老人</span>
      <br>应<strong>减少</strong>户外体力消耗和户外逗留时间。
    </p>
  `),
  3: $(`
    <p class="card-text">
      <span class="people-class">心脏病或呼吸系统疾病患者</span>
      <span class="people-class">儿童及老人</span>
      <br>应<strong>尽量减少</strong>户外体力消耗和户外逗留时间。
    </p>
    <p class="card-text">
      <span class="people-class">户外工作人员</span>
      <span class="people-class">一般市民</span>
      <br>应<strong>减少</strong>户外体力消耗和户外逗留时间。
    </p>
  `),
  4: $(`
    <p class="card-text">
      <span class="people-class">心脏病或呼吸系统疾病患者</span>
      <span class="people-class">儿童及老人</span>
      <br>应<strong>避免</strong>户外体力消耗和户外逗留。
    </p>
    <p class="card-text">
      <span class="people-class">户外工作人员</span>
      <span class="people-class">一般市民</span>
      <br>应<strong>尽量减少</strong>户外体力消耗和户外逗留时间。
    </p>
  `)
};

var pollutantNames = ['co', 'so2', 'o3', 'o3_8h', 'pm10', 'pm2_5', 'no2'];
var pollutantAndAqiNames = ['aqi', 'aqhi'].concat(pollutantNames);
var pollutantAndAqiProperties = {
  co: {maxValue: 5, color: 'f4e781', label: 'CO'},
  so2: {maxValue: 50, color: 'bda29a', label: 'SO2'},
  o3: {maxValue: 400, color: 'd48265', label: 'O3'},
  o3_8h: {maxValue: 400, color: '91c7aE', label: 'O3/8h'},
  pm10: {maxValue: 300, color: '749f83', label: 'PM10'},
  pm2_5: {maxValue: 500, color: 'ca8622', label: 'PM2.5'},
  no2: {maxValue: 100, color: '61a0a8', label: 'NO2'},
  aqi: {maxValue: 500, color: 'c23531', label: 'AQI'},
  aqhi: {maxValue: 12, color: 'cf2abf', label: 'AQHI'}
};

var primaryPollutantTexts = pollutantNames.reduce(function(prev, name) {
  var text = pollutantAndAqiProperties[name].label;
  prev[name] = {cls: 'pol-' + name, text: text};
  return prev;
}, Object.create(null));
primaryPollutantTexts['NA'] = {cls: '', text: '无'};


// weather icon class names
var weatherIconClassNames = {
  100: { day: "wi-day-sunny", night: "wi-night-clear"}, 
  101: { day: "wi-cloudy", night: "wi-cloudy"}, 
  102: { day: "wi-cloud", night: "wi-cloud"}, 
  103: { day: "wi-day-cloudy", night: "wi-night-cloudy"}, 
  104: { day: "wi-day-sunny-overcast", night: "wi-night-partly-cloudy"}, 
  200: { day: "wi-day-windy", night: "wi-windy"}, 
  202: { day: "wi-day-windy", night: "wi-windy"}, 
  203: { day: "wi-day-windy", night: "wi-windy"}, 
  204: { day: "wi-day-windy", night: "wi-windy"}, 
  205: { day: "wi-strong-wind", night: "wi-strong-wind"}, 
  206: { day: "wi-strong-wind", night: "wi-strong-wind"}, 
  207: { day: "wi-strong-wind", night: "wi-strong-wind"}, 
  208: { day: "wi-strong-wind", night: "wi-strong-wind"}, 
  209: { day: "wi-day-thunderstorm", night: "wi-night-thunderstorm"}, 
  210: { day: "wi-day-thunderstorm", night: "wi-night-thunderstorm"}, 
  211: { day: "wi-hurricane", night: "wi-hurricane"}, 
  212: { day: "wi-tornado", night: "wi-tornado"}, 
  213: { day: "wi-hurricane", night: "wi-hurricane"}, 
  300: { day: "wi-day-rain", night: "wi-night-rain"}, 
  301: { day: "wi-day-showers", night: "wi-night-showers"}, 
  302: { day: "wi-day-storm-showers", night: "wi-night-storm-showers"}, 
  303: { day: "wi-day-thunderstorm", night: "wi-night-thunderstorm"}, 
  304: { day: "wi-day-hail", night: "wi-night-hail"}, 
  305: { day: "wi-day-rain", night: "wi-night-rain"}, 
  306: { day: "wi-day-rain", night: "wi-night-rain"}, 
  307: { day: "wi-day-rain", night: "wi-night-rain"}, 
  308: { day: "wi-day-rain", night: "wi-night-rain"}, 
  309: { day: "wi-day-sprinkle", night: "wi-night-sprinkle"}, 
  310: { day: "wi-day-thunderstorm", night: "wi-night-thunderstorm"}, 
  311: { day: "wi-day-thunderstorm", night: "wi-night-thunderstorm"}, 
  312: { day: "wi-day-thunderstorm", night: "wi-night-thunderstorm"}, 
  313: { day: "wi-day-rain-mix", night: "wi-night-rain-mix"}, 
  400: { day: "wi-day-snow", night: "wi-night-snow"}, 
  401: { day: "wi-day-snow", night: "wi-night-snow"}, 
  402: { day: "wi-day-snow", night: "wi-night-snow"}, 
  403: { day: "wi-day-snow", night: "wi-night-snow"}, 
  404: { day: "wi-day-sleet", night: "wi-night-sleet"}, 
  405: { day: "wi-day-sleet", night: "wi-night-sleet"}, 
  406: { day: "wi-day-sleet", night: "wi-night-sleet"}, 
  407: { day: "wi-day-snow", night: "wi-night-snow"}, 
  500: { day: "wi-day-fog", night: "wi-night-fog"}, 
  501: { day: "wi-day-fog", night: "wi-night-fog"}, 
  502: { day: "wi-day-haze", night: "wi-dust"}, 
  503: { day: "wi-dust", night: "wi-dust"}, 
  504: { day: "wi-dust", night: "wi-dust"}, 
  506: { day: "wi-volcano", night: "wi-volcano"}, 
  507: { day: "wi-sandstorm", night: "wi-sandstorm"}, 
  508: { day: "wi-sandstorm", night: "wi-sandstorm"}, 
  900: { day: "wi-thermometer", night: "wi-thermometer"}, 
  901: { day: "wi-thermometer-exterior", night: "wi-thermometer-exterior"}, 
  999: { day: "wi-na", night: "wi-na"}
};

var zhWeekDays = {
  1: '一',
  2: '二',
  3: '三',
  4: '四',
  5: '五',
  6: '六',
  7: '日'
};

$(function() {
  // City accordion
  $('#city-accordion').on('click', '.panel-heading a', function(event) {
    var body_ele = $($(this).attr('href'));
    if (body_ele.children().length == 0) {
      event.stopPropagation();

      var cityName = $(this).closest('.city-panel').data('city');
      $.get('api/core/city_panel_body', {
          city_en: cityName
      }).done(function(response) {
        body_ele.html(response);
        body_ele.collapse({
          parent: '#city-accordion'
        });

        initCity(cityName, body_ele.closest('.city-panel'));
      });
    }
  });

  var primaryCityPanel = $('.city-panel.primary-city-panel');
  var primaryCityName = primaryCityPanel.data('city');
  // Init primary city
  initCity(primaryCityName, primaryCityPanel)
});

function initCity(cityName, cityPanel) {
  $.getJSON('api/airquality/latest_city_record', {
    city: cityName
  }).done(function(latestCityRecord) {
    initRankChart(latestCityRecord.update_dtm);
    initCityAirCondition(latestCityRecord, cityPanel.find('.air-condition-card'));
    initCityWeather(latestCityRecord, cityPanel);
    initStationsMap(latestCityRecord, cityPanel);
    initCityHistoryChart(latestCityRecord, cityPanel);
  });
}

function initStationsMap(cityRecord, cityPanel) {
  var option = {
    backgroundColor: '#404a59',
    tooltip: {
      formatter: function(params) {
        return params.name + "：" + params.value[2];
      }
    },
    legend: {
      orient: 'vertical',
      data: [],
      top: 'bottom',
      left: 'right',
      textStyle: {
        color: '#fff'
      },
      selectedMode: 'single'
    },
    visualMap: {
      type: 'continuous',
      min: 0,
      max: 500,
      text: ['High', 'Low'],
      inRange: {
        color: ['lightskyblue','yellow','orangered']
      },
      textStyle: {
        color: '#fff'
      }
    },
    geo: {
      map: '',
      roam: true,
      itemStyle: {
        normal: {
          color: '#323c48',
          borderColor: '#111'
        },
        emphasis: {
          color: '#2a333d'
        }
      },
      label: {
        normal: { show: false },
        emphasis: {
          show: true,
          textStyle: { color: '#fff'}
        }
      },
      top: 'top',
      left: 'center'
    },
    series: []
  };

  var cityName = cityRecord.city.name_en;
  var myChart = echarts.init(document.getElementById('map-' + cityName));
  setChartSize(myChart, 0.6);
  myChart.showLoading();

  $(window).on('resize', function() {
    setChartSize(myChart, 0.6);
    myChart.resize();
  });

  // load data
  var loadingLatch = new CountdownLatch(2);
  // load map geo data
  $.getJSON('static/geo/' + cityName + '.json', function (geoData) {
    echarts.registerMap(cityName, geoData);
    loadingLatch.countDown();
  });
  // load map air quality data
  var qualityData;
  $.getJSON('api/airquality/station_record', {
    city_record: cityRecord.id
  }).done(function(data) {
    qualityData = data.results;
    loadingLatch.countDown();
  });

  loadingLatch.await(function() {
    pollutantAndAqiNames.forEach(function(pollutantName) {
      var label = pollutantAndAqiProperties[pollutantName].label;

      option.legend.data.push(label);
      var valueArray = qualityData.map(function (data) {
        return parsePollutantOrAqiValue(pollutantName, data[pollutantName]);
      });

      option.geo.map = cityName;
      var seriesData = {
        type: 'scatter',
        name: label,
        coordinateSystem: 'geo',
        itemStyle: {
          emphasis: {
            borderColor: '#fff',
              borderWidth: 1
          }
        },
        data: []
      };

      seriesData.data = valueArray.map(function(value, i) {
        var station = qualityData[i].station;
        return {
          name: station.name_cn,
          value: [station.longitude, station.latitude, value]
        }
      });
      var maxVal = valueArray.reduce(function(max, val) {
        return isNaN(val) ? max : Math.max(val, max)
      }, valueArray.find(function(v) { return !isNaN(v) }));
      var minVal = valueArray.reduce(function(min, val) {
        return isNaN(val) ? min : Math.min(val, min)
      }, valueArray.find(function(v) { return !isNaN(v) }));
      var ratio = (maxVal - minVal) / (100 - 20);
      var diff = minVal / ratio - 20;
      seriesData.symbolSize = function(val) {
        return val[2] / ratio - diff;
      };
      option.series.push(seriesData);
    });
    myChart.hideLoading();
    myChart.setOption(option);
    myChart.resize();
  });

}

function initCityHistoryChart(cityRecord, cityPanel) {
  var option = {
    backgroundColor: '#404a59',
    tooltip : {
      trigger: 'axis'
    },
    legend: {
      data:[], //Legend names
      selectedMode: 'single'
    },
    toolbox: {
      feature: {
        saveAsImage: {}
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '8%',
      containLabel: true
    },
    xAxis: [
      {
        type : 'category',
        boundaryGap : false,
        data : [], // hour names
        axisLabel: {textStyle: {color: '#fff'}},
        axisLine: {lineStyle: {color: '#fff'}},
        splitLine: {show: false}
      }
    ],
    yAxis: [
      {
        type : 'value',
        axisLine: {lineStyle: {color: '#fff'}},
        axisLabel: {textStyle: {color: '#fff'}}
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0],
        start: 50,
        end: 100,
        zoomLock: true
      },
      {
        type: 'slider',
        xAxisIndex: [0],
        start: 50,
        end: 100,
        zoomLock: true
      }
    ],
    series : []
  };

  var seriesDataTemplate = {
    name:'',
    type:'line',
    areaStyle: {normal: {}},
    label: {
      normal: {
        show: true,
        position: 'top'
      }
    }
    // data = []
  };

  var cityName = cityRecord.city.name_en;
  var chart = echarts.init(document.getElementById(`history-chart-${cityName}`));
  setChartSize(chart, 0.6);

  $(window).on('resize', function() {
    setChartSize(chart, 0.6);
    chart.resize();
  });

  chart.showLoading();

  var pollutantAndAqiSeriesData = pollutantAndAqiNames.reduce(function(obj, name) {
    var datum = Object.assign({}, seriesDataTemplate);
    datum.data = [];
    var label = pollutantAndAqiProperties[name].label;
    option.legend.data.push(label);
    datum.name = label;
    option.series.push(datum);

    obj[name] = datum;
    return obj;
  }, Object.create(null));
  var now = moment.utc(cityRecord.update_dtm);
  var startDtm = now.clone().subtract(1, 'days');
  var endDtm = now.clone();
  $.getJSON('api/airquality/city_record', {
    city: cityName,
    start_dtm: startDtm.format(),
    end_dtm: endDtm.format(),
    limit: 30,
    ordering: '-update_dtm'
  }).done(function(data) {
    var records = data.results;

    for (var curDtm = startDtm.clone(); curDtm <= endDtm; curDtm.add(1, 'hours')) {
      option.xAxis[0].data.push(
        curDtm.isSame(endDtm) ?
          "现在" :
          `${curDtm.hours()}时`
      );
      var curRecord = records.find(function(ele) { return moment(ele.update_dtm).isSame(curDtm)});
      if (curRecord == undefined) {
        curRecord = pollutantAndAqiNames.reduce(function(rec, name) {
          rec[name] = '';
          return rec;
        }, Object.create(null));
      }

      pollutantAndAqiNames.forEach(function(name) {
        var value = parsePollutantOrAqiValue(name, curRecord[name]);
        if (isNaN(value)) value = '-';
        pollutantAndAqiSeriesData[name].data.push(value);
      })
    }
    chart.setOption(option);
    chart.resize();
    chart.hideLoading();
  });


}

function initCityAirCondition(cityRecord, cityAirCard) {
  var record = cityRecord;

  var qualityEle = cityAirCard.find('.quality-level');
  var aqhiEle = cityAirCard.find('.aqhi-level');
  var primaryPolListEle = cityAirCard.find('.primary-pollutant-list');
  var polDataEles = pollutantNames.reduce(function(prev, name) {
    prev[name] = cityAirCard.find('.pollutant-data.pol-' + name);
    return prev;
  }, Object.create(null));

  cityAirCard.find('.aqhi-head').text(parseFloat(record.aqhi).toFixed(1));
  cityAirCard.find('.aqi-head').text(parseInt(record.aqi));
  qualityEle.addClass(qualityTexts[record.quality].cls);
  qualityEle.html(qualityTexts[record.quality].text);
  var aqhiLevel = getAqhiLevel(record.aqhi);
  aqhiEle.addClass(aqhiTexts[aqhiLevel].cls);
  aqhiEle.html(aqhiTexts[aqhiLevel].text);
  cityAirCard.find('.people-advice-text').html(aqhiAdviceTextEles[aqhiLevel]);
  cityAirCard.find('.air-condition-update-time-data').text(moment(record.update_dtm).fromNow());

  var primaryPollutants = record.primary_pollutants;
  if (record.primary_pollutants.length == 0)
    primaryPollutants.push({pollutant: 'NA'});
  primaryPollutants.forEach(function(pol) {
    var name = pol.pollutant;
    $('<li></li>')
      .addClass(primaryPollutantTexts[name].cls)
      .html(primaryPollutantTexts[name].text)
      .appendTo(primaryPolListEle);
  });


  pollutantNames.forEach(function(name) {
    var valueString = record[name];
    if (valueString == '')
      polDataEles[name].text('——');
    else
      polDataEles[name].text(Number(valueString));
  });

  hideLoading(cityAirCard.find('.card-content'));
}

function initCityWeather(cityRecord, cityPanel) {
  // test
  $.getJSON(`static/weather/test-${cityRecord.city.name_en}.json`).done(function(jsonData) {
    var weatherData = jsonData['HeWeather data service 3.0'][0];
    var todayWeatherData = weatherData.daily_forecast[0];

    var updateTimes = weatherData.basic.update;
    var localUtcOffset = moment(updateTimes.loc).diff(moment(updateTimes.utc), 'hours');
    var now = moment.utc(updateTimes.utc); // the update time, not user time
    var isDay = (function() {
      var locTime = moment.duration(moment(updateTimes.loc).format('HH:mm')).as('minutes');
      var astroTimes = todayWeatherData.astro;
      var sunriseTime = moment.duration(astroTimes.sr).as('minutes');
      var sunsetTime = moment.duration(astroTimes.ss).as('minutes');

      return !!(locTime >= sunriseTime && locTime <= sunsetTime);
    })();

    var nowWeatherData = weatherData.now;
    var curWeatherIcon = cityPanel.find('.cur-weather-block i');
    cityPanel.find('.weather-update-time-data').text(now.fromNow());
    cityPanel.find('.weather-update-weekday-text small').text(`周${zhWeekDays[now.isoWeekday()]}`);
    cityPanel.find('.today-max-temp').text(todayWeatherData.tmp.max);
    cityPanel.find('.today-min-temp').text(todayWeatherData.tmp.min);
    cityPanel.find('.temp-head-data').text(nowWeatherData.tmp);
    cityPanel.find('.cur-weather-text').text(nowWeatherData.cond.txt);
    curWeatherIcon.removeClass().addClass(
      `wi ${weatherIconClassNames[nowWeatherData.cond.code][isDay ? 'day' : 'night']}`
    );

    var tomorrowWeatherData = weatherData.daily_forecast[1];
    var nextDayWeatherFirstRow = cityPanel.find('.next-day-weather-col').first();
    var nextDayWeatherSecondRow = nextDayWeatherFirstRow.next();
    nextDayWeatherFirstRow.find('.next-day-weather-header').text(
      isDay ? '今天白天' : '今天夜间'
    );
    nextDayWeatherFirstRow.find('.next-day-weather-text').text(
      isDay ? todayWeatherData.cond.txt_d : todayWeatherData.cond.txt_n
    );
    nextDayWeatherFirstRow.find('i').removeClass().addClass(
      `wi ${isDay ? 
        weatherIconClassNames[todayWeatherData.cond.code_d].day : 
        weatherIconClassNames[todayWeatherData.cond.code_n].night
        }`
    );
    nextDayWeatherSecondRow.find('.next-day-weather-header').text(
      isDay ? '今天夜间' : '明天白天'
    );
    nextDayWeatherSecondRow.find('.next-day-weather-text').text(
      isDay ? todayWeatherData.cond.txt_n : tomorrowWeatherData.cond.txt_d
    );
    nextDayWeatherSecondRow.find('i').removeClass().addClass(
      `wi ${isDay ? 
        weatherIconClassNames[todayWeatherData.cond.code_n].night : 
        weatherIconClassNames[tomorrowWeatherData.cond.code_d].day
        }`
    );

    var hourlyForecasts = weatherData.hourly_forecast;
    var hourlyForecastList = cityPanel.find('.hourly-weather-list');
    // Add now temp first
    hourlyForecastList.empty().append(getNewHourlyWeatherListItem(
      '<strong>现在</strong>',
      nowWeatherData.tmp
    ));
    hourlyForecasts.forEach(function(forecast) {
      var forecastCurTime = getCurDatetime(localUtcOffset, forecast.date);
      hourlyForecastList.append(getNewHourlyWeatherListItem(forecastCurTime.format('HH:mm'), forecast.tmp));
    });

    var dailyForecastList = cityPanel.find('.weekday-weather-list');
    var dailyForecastData = weatherData.daily_forecast.slice(1);
    dailyForecastList.empty();
    dailyForecastData.forEach(function(forecast) {
      var curWeekday = getCurDatetime(localUtcOffset, forecast.date).isoWeekday();
      dailyForecastList.append(getNewDailyWeatherItem(
        `周${zhWeekDays[curWeekday]}`,
        forecast.cond.txt_d,
        weatherIconClassNames[forecast.cond.code_d].day,
        forecast.tmp.max,
        forecast.tmp.min
      ))
    })

  }).done(function() {
    // Hide loading effect
    hideLoading(cityPanel.find('.card-content'));
  });
}

function initRankChart(dtmString) {
  var option = {
    tooltip : {
        trigger: 'axis',
        axisPointer : {            // 坐标轴指示器，坐标轴触发有效
            type : 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
        }
    },
    grid: {
        top: '5%',
        bottom: '5%'
    },
    backgroundColor: '#404a59',
    xAxis: {
        type : 'value',
        position: 'top',
        axisLine: {lineStyle: {color: '#fff'}},
        splitLine: {lineStyle:{type:'dashed'}},
        axisLabel: {textStyle: {color: '#fff'}}
    },
    yAxis: {
        type : 'category',
        axisLine: {show: false},
        axisLabel: {show: false},
        axisTick: {show: false},
        splitLine: {show: false},
        data : [] // city names
    },
    dataZoom: [
      {
        type: 'inside',
        yAxisIndex: [0],
        startValue: 0,
        endValue: 5,
        zoomLock: true
      },
      {
        type: 'slider',
        yAxisIndex: [0],
        startValue: 0,
        endValue: 5,
        zoomLock: true
      }
    ],
    series : []
  };
  var seriesDataTemplate = {
    name: '',
    type: 'bar',
    label: {
      normal: {
        show: true,
        formatter: '{b}'
      }
    }
    // data: []
  };

  var chart = echarts.init(document.getElementById('rank-chart'));
  setChartSize(chart, 0.6);
  chart.resize();

  $(window).on('resize', function() {
    setChartSize(chart, 0.6);
    chart.resize();
  });

  chart.showLoading();
  // AQHI Rank
  var aqhiSeriesData = Object.assign({}, seriesDataTemplate);
  aqhiSeriesData.name = 'AQHI';
  aqhiSeriesData.data = [];
  option.series.push(aqhiSeriesData);
  $.getJSON('api/airquality/city_record', {
    update_dtm: dtmString,
    ordering: '-aqhi',
    limit: 50,
    fields: 'aqhi,city__name_cn'
  }).done(function(data) {
    var records = data.results;

    records.forEach(function(record) {
      option.yAxis.data.push(record.city.name_cn);
      aqhiSeriesData.data.push(parsePollutantOrAqiValue('aqhi', record.aqhi));
    });

    option.dataZoom.forEach(function(dataZoomItem) {
      dataZoomItem.startValue = records.length - 1;
      dataZoomItem.endValue = Math.max(dataZoomItem.startValue - 5, 0);
    });

    chart.setOption(option);
    chart.hideLoading();
  });

}

function getCurDatetime(utcOffset, string) {
  return moment(string).utcOffset(utcOffset).local();
}

function getNewHourlyWeatherListItem(time, temp) {
  return $(`
    <li class="hourly-weather-item halign-row">
      <div class="hourly-weather-time">${time}</div>
      <div class="hourly-weather-temp"><span class="hourly-weather-temp-data">${temp}</span>º</div>
    </li>
  `);
}

function getNewDailyWeatherItem(weekday, weatherText, weatherIconClass, maxTemp, minTemp) {
  return $(`
    <div class="row valign-row">
      <div class="col-md-4">
        <p class="card-text weather-weekday-text pull-xs-left">
          <small class="text-muted weekday-text">${weekday}</small>
        </p>
      </div>
      <div class="col-md-4">
        <div class="weekday-weather valign-row">
          <span class="weekday-weather-text">${weatherText}</span>
          <i class="wi ${weatherIconClass}"></i>
        </div>
      </div>
      <div class="col-md-4">
        <div class="weekday-temp-range pull-xs-right">
          <strong class="weekday-max-temp">${maxTemp}</strong>
          <span class="weekday-min-temp">${minTemp}</span>
        </div>
      </div>
    </div>
  `)
}

function hideLoading(parent) {
  var overlayEle = parent.find('.loading-overlay');
  overlayEle.fadeOut('slow');
  parent.removeClass('loading');
}

function setChartSize(chart, ratio) {
  var container = $(chart.getDom());
  var containerWidth = container.width();
  container.css({
    width: containerWidth,
    height: containerWidth * ratio
  });
}

function getAqhiLevel(indexString) {
  var indexValue = parseFloat(indexString);
  var level = 0;
  for (let value of aqhiRange) {
    if (indexValue < value)
      break;
    level += 1;
  }
  return level;
}

function parsePollutantOrAqiValue(name, valueString, decimalPlaces) {
  decimalPlaces = typeof decimalPlaces !== 'undefined' ? decimalPlaces : 2;
  if (['co', 'aqhi'].indexOf(name) == -1)
    return parseInt(valueString);
  else
    return parseFloat(parseFloat(valueString).toFixed(decimalPlaces))
}