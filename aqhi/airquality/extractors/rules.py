import re


# Web page info to xpath selector string mapping
info_xpath_mappings = dict(
    city_quality_names="//*[contains(concat(' ', @class, ' '), ' data ')]/div[not(position() >= 9)]"
                       "//*[contains(concat(' ', @class, ' '), ' caption ')]",
    city_quality_values="//*[contains(concat(' ', @class, ' '), ' data ')]/div[not(position() >= 9)]"
                        "//*[contains(concat(' ', @class, ' '), ' value ')]",
    area_cn="//*[contains(concat(' ', @class, ' '), ' city_name ')]/*[count(*)=0]",
    update_dtm="//*[contains(concat(' ', @class, ' '), ' live_data_time ')]/p",
    quality="//*[contains(concat(' ', @class, ' '), ' level ')]/*[count(*)=0]",
    primary_pollutant="//*[contains(concat(' ', @class, ' '), ' primary_pollutant ')]/p",
    station_quality_names="//table[@id='detail-data']/thead//th",
    station_quality_rows=["//table[@id='detail-data']/tbody//tr", "td[not(position()>11)]"]
)

info_preprocessors = dict(
    update_dtm=lambda data_list: [re.search(r'([0-9]{4}\D.*$)', data).group() for data in data_list],
    primary_pollutant=lambda data_list:
    re.split(
        r'[, \uff0c]+',
        re.split(r'[: \uff1a]+', re.sub(r'\s+', ' ', data_list[0]), maxsplit=1)[-1]
    ),
)

# RE pattern to const field name mapping
consts_pattern_field_mappings = {
    # pollutants
    re.compile(r'aqi', re.I): 'aqi',
    re.compile(r'pm2\.5', re.I): 'pm2_5',
    re.compile(r'pm10', re.I): 'pm10',
    re.compile(r'co|一氧化碳', re.I): 'co',
    re.compile(r'no2|二氧化氮', re.I): 'no2',
    re.compile(r'(?:o3|臭氧).*?1(?:h|小时)', re.I | re.S): 'o3',
    re.compile(r'(?:o3|臭氧).*?8(?:h|小时)', re.I | re.S): 'o3_8h',
    re.compile(r'so2|二氧化硫', re.I): 'so2',
    # quality
    # E = Excellent, G = Good, LP = Lightly Polluted, MP = Moderately Polluted,
    # HP = Heavily Polluted, SP = Severely Polluted
    re.compile(r'一级|优'): 'E',
    re.compile(r'二级|良'): 'G',
    re.compile(r'三级|轻度污染'): 'LP',
    re.compile(r'四级|中度污染'): 'MP',
    re.compile(r'五级|重度污染'): 'HP',
    re.compile(r'六级|严重污染'): 'SP',
    # Station info header
    re.compile(r'监测点'): 'name',
    re.compile(r'空气质量指数类别'): 'quality',
    re.compile(r'首要污染物'): 'primary_pollutant',
    # Value consts
    re.compile(r'^(_|—||->)$'): '',
}

# patterns to parse info crawled from pages
# Each info has a list of patterns.
# Each pattern can be one of the types:
# 1. 'consts': use the conts_patterns above
# 2. 'num': use built-in number pattern to get a number value
# 3. 'zh_name': use built-in chinese char pattern to match and get original value
# 4. 'datetime': use built-in dtm pattern to get a datetime
# Order is important. Each pattern will be applied by the list order.
info_patterns = dict(
    city_quality_names=['consts'],
    city_quality_values=['num'],
    area_cn=['zh_name'],
    primary_pollutant=['consts'],
    quality=['consts'],
    station_quality_names=['consts'],
    station_quality_rows=['consts', 'num', 'zh_name'],
    update_dtm=['datetime']
)


