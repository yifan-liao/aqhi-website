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
  LP: {cls: 'qlty-lightly', text: '轻度<br>污染'},
  MP: {cls: 'qlty-moderately', text: '中度<br>污染'},
  HP: {cls: 'qlty-heavily', text: '重度<br>污染'},
  SP: {cls: 'qlty-severely', text: '严重<br>污染'}
};

var pollutantNames = ['co', 'so2', 'o3', 'o3_8h', 'pm10', 'pm2_5', 'no2'];
var primaryPollutantTexts = pollutantNames.reduce(function(prev, name) {
  var text = name.toUpperCase();
  if (name == 'o3_8h') 
    text = 'O3/8h';
  else if (name == 'pm2_5')
    text = 'PM2.5';
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
  initCityAirCondition(cityName, cityPanel.find('.air-condition-card'));
  initCityWeather(cityName, cityPanel);
  initCityCharts(cityName, cityPanel);
}

function initCityCharts(cityName, cityPanel) {
  var myChart = echarts.init(document.getElementById('map-' + cityName));
  setChartSize(myChart, 0.6);

  $(window).on('resize', function() {
    setChartSize(myChart, 0.6);
    myChart.resize();
  });

  myChart.showLoading();
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
    latest: 'True',
    city: cityName
  }).done(function(data) {
    qualityData = data.results;
    loadingLatch.countDown();
  });

  loadingLatch.await(function() {
    ['aqi', 'co', 'no2', 'o3', 'o3_8h', 'pm10', 'pm2_5', 'so2'].forEach(function(pollutantName) {
      var label = pollutantName.toUpperCase();
      if (pollutantName == 'o3_8h')
        label = 'O3/8h';
      else if (pollutantName == 'pm2_5')
        label = 'PM2.5';

      option.legend.data.push(label);
      var convertFunc = pollutantName == 'co'? function (d) { return d } : parseInt;
      var valueArray = qualityData.map(function (data) {
        return convertFunc(data[pollutantName]);
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

function initCityAirCondition(cityEngName, cityAirCard) {
  $.getJSON('api/airquality/city_record', {
    city: cityEngName,
    latest: 'True'
  }).done(function(jsonData) {
    var record = jsonData.results[0];

    var qualityEle = cityAirCard.find('.quality-head');
    var primaryPolListEle = cityAirCard.find('.primary-pollutant-list');
    var polDataEles = pollutantNames.reduce(function(prev, name) {
      prev[name] = cityAirCard.find('.pollutant-data.pol-' + name);
      return prev;
    }, Object.create(null));

    cityAirCard.find('.aqi-head').text(parseInt(record.aqi));
    qualityEle.addClass(qualityTexts[record.quality].cls);
    qualityEle.html(qualityTexts[record.quality].text);
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
    })
  }).done(function() {
    // Hide loading effect
    hideLoading(cityAirCard.find('.card-content'));
  })
}

function initCityWeather(cityEngName, cityPanel) {
  // test
  $.getJSON(`static/weather/test-${cityEngName}.json`).done(function(jsonData) {
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