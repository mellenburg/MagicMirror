#!/usr/bin/python3
import csv
import json
import os
import requests
from urllib.parse import urlencode

import forecastio
from flask import Flask, render_template

app = Flask(__name__)

HOME = "2351 Arlington Ct, San Leandro, CA"
MEGANS_WORK = "2300 Talavera Dr, San Ramon, CA"

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
FORECAST_API_KEY = os.environ['FORECAST_API_KEY']
CACHE_DIR = os.path.join(os.getcwd(), '.cache')
try:
    os.makedirs(CACHE_DIR)
except:
    pass

MAP_REQ_COUNTER = 0
IMG_CACHE = []


@app.route('/d3.v3.min.js')
def get_d3():
    app.send_static_file('d3.v3.min.js')


@app.route('/current_map')
def current_map():
    global MAP_REQ_COUNTER
    return IMG_CACHE[MAP_REQ_COUNTER % len(IMG_CACHE)].content


@app.route('/current_map/<map_id>')
def current_map_i(map_id):
    return IMG_CACHE[int(map_id)].content


@app.route('/hello')
def test():
    return render_template('hello.html',
                           map_src='http://127.0.0.1:5000/current_map')


@app.route('/simple_table')
def directions_table():
    return render_template('simple_table.html',
                           data=get_instructions_from_request())


@app.route('/route_switch')
def route_switch():
    return render_template('route_switch.html',
                           API_KEY=GOOGLE_API_KEY,
                           home=HOME,
                           work=MEGANS_WORK)


@app.route('/d3_<item>')
def d3_weather(item):
    return render_template('d3_{}.html'.format(item))


@app.route('/cache/<data_file>')
def get_cache_data(data_file):
    """
    Use whatever is on disk. Generate if not present
    TODO: add cache updating
    TODO: add cache updating on demand
    TODO: write the data in such a way that doesn assume
        that the keys are homogenous in the dataset
    """
    data_formats = ['tsv', 'csv']
    app.logger.debug('Data cache request for: '+data_file)
    data_ext = data_file.split('.')[-1]
    assert data_ext in data_formats, 'Must pick a valid extension'
    cache_file = os.path.join(CACHE_DIR, data_file)
    if not os.path.isfile(cache_file):
        app.logger.debug('No cached data; generating: '+data_file)
        forecast = get_weather_forecast()
        if data_file.split('.')[0] == 'daily':
            data_i = forecast.daily()
        elif data_file.split('.')[0] == 'hourly':
            data_i = forecast.hourly()
        else:
            raise AssertionError
        data_header = list(data_i.data[0].d.keys())
        app.logger.debug('Headers for {}: {}'.format(data_file, data_header))
        with open(cache_file, 'w') as cache_fh:
            if data_ext == 'tsv':
                writer = csv.writer(cache_fh, delimiter='\t')
            else:
                writer = csv.writer(cache_fh)
            writer.writerow(data_header)
            for point in data_i.data:
                data_list = []
                for key in data_header:
                    try:
                        data_list.append(point.d[key])
                    except KeyError:
                        data_list.append('')
                        msg = 'Missing data for {} at {}'.format(
                                key, point.time)
                        app.logger.debug(msg)
                writer.writerow(data_list)
    with open(cache_file, 'r') as data_fh:
        return data_fh.read()


@app.route('/home')
def homepage():
    """Place-holder for homepage generator
    Shared features:
        -Hourly weather forecast including percipitation for entire day
        -Email-capable reminder pad (use MailGun)
    Michael features:
        -BART schedule and BART delays
    Megan features:
        -Fastest route to work
    """
    pass


def make_js_data_list(data, key):
    return repr([i.d[key] for i in data])


def check_environ():
    assert 'GOOGLE_API_KEY' in os.environ
    assert 'FORECAST_API_KEY' in os.environ


def refresh_maps():
    global IMG_CACHE
    colors = [u'green', u'yellow', u'red']
    routes = get_direction_routes()
    max_routes = min(len(colors), len(routes))
    for i in range(max_routes):
        req_url, payload = map_url(colors[i],
                                   routes[i]['overview_polyline']['points'])
        r = requests.get(req_url, params=payload)
        print(len(r.url))
        IMG_CACHE.append(r)


def get_weather_forecast():
    forecast = forecastio.load_forecast(FORECAST_API_KEY, 37.8267, -122.423)
    for point in forecast.daily().data:
        print(point)
    return forecast


def map_url(color, path):
    base_url = "https://maps.googleapis.com/maps/api/staticmap?"
    args_dict = {}
    args_dict['size'] = '600x300'
    args_dict['maptype'] = 'roadmap'
    args_dict['markers'] = ['color:green|label:H|' + HOME]
    args_dict['markers'].append('color:blue|label:W|' + MEGANS_WORK)
    args_dict['path'] = 'color:' + color + '|weight:3|enc:' + path
    args_dict['key'] = GOOGLE_API_KEY
    return base_url, args_dict


def get_instructions_from_request():
    output = []
    dir_req = direction_request()
    r = requests.get(dir_req)
    direction_data = json.loads(r.text)
    for route in direction_data['routes']:
        for leg in route['legs']:
            for step in leg['steps']:
                output.append(step['html_instructions'])
    return output


def direction_request():
    base_url = "https://maps.googleapis.com/maps/api/directions/json?"
    arg_list = []
    arg_list.append(("origin", HOME))
    arg_list.append(("destination", MEGANS_WORK))
    arg_list.append(("alternatives", "true"))
    arg_list.append(("key", GOOGLE_API_KEY))
    return base_url + urlencode(arg_list)


def get_direction_routes():
    output = []
    dir_req = direction_request()
    r = requests.get(dir_req)
    direction_data = json.loads(r.text)
    for route in direction_data['routes']:
        output.append(route)
    return output


def main():
    # refresh_maps()
    check_environ()
    assert app.has_static_folder
    app.run(debug=True)


if __name__ == '__main__':
    main()
