import json
from submodule import _settings


def get_top_stations(limit=200, min_passengers=None):
    if min_passengers is None:
        min_passengers = _settings.min_station_passengers

    with open(_settings.station_geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stations = []
    for feature in data['features']:
        props = feature.get('properties', {})
        geometry = feature.get('geometry', {})

        name = props.get('S12_001', '')
        company = props.get('S12_002', '')
        line = props.get('S12_003', '')
        passengers = props.get('S12_049') or 0

        if not name or passengers < min_passengers:
            continue

        coords = geometry.get('coordinates', [])
        if not coords:
            continue
        # LineStringの場合は最初の座標点を使用
        if isinstance(coords[0], list):
            lng, lat = coords[0][0], coords[0][1]
        else:
            lng, lat = coords[0], coords[1]

        stations.append({
            'name': name,
            'company': company,
            'line': line,
            'passengers': passengers,
            'lat': lat,
            'lng': lng,
        })

    stations.sort(key=lambda x: x['passengers'], reverse=True)
    return stations[:limit]
