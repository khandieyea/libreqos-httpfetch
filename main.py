import csv
import os
import shutil
from datetime import datetime

import requests
import yaml

config = []
configPaths = [os.path.dirname(__file__) + '/config.yml', '/etc/libq-httpfetch.conf']

for file in configPaths:
    if os.path.exists(file):
        with open(file, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            break


# If empty, throw, most probably failed to pull config
if not config:
    raise ImportError('Configs are empty, something not quite right')

defaultHTTPHeaders = {'accept': 'application/json'}


def fetch():
    config.update({'final_output_dir': config.get('final_output_dir') or os.path.dirname(os.path.realpath(__file__))})
    headers = (defaultHTTPHeaders.copy()).update(config.get('request_headers'))

    ts = datetime.now().strftime('%Y-%m-%d.%H-%M-%S')

    # Start devices
    devicesURL = config.get('base_url') + '/' + config.get('devices_uri').strip('/')

    raw = requests.get(devicesURL, headers=headers, verify=False)

    if raw.status_code != 200:
        print('Failed to request ' + devicesURL + ', got ' + str(raw.status_code))
        return False

    devicesCsvFP = config.get('final_output_dir') + '/Shaper.csv'

    with open(devicesCsvFP, 'w') as csvfile:
        wr = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        wr.writerow(
            ['ID', 'AP', 'MAC', 'Hostname', 'IPv4', 'IPv6', 'Download Min', 'Upload Min', 'Download Max', 'Upload Max'])
        for row in raw.json():
            if bool(config.get('devices_remap')):
                row = list(map(lambda key: (row[key] if row[key] else key), config.get('devices_remap')))
            else:
                row = list(row.values())
            wr.writerow(row)

    print('Wrote ' + devicesCsvFP)

    # Start network

    networkURL = config.get('base_url') + '/' + config.get('network_uri').strip('/')

    raw = requests.get(networkURL, headers=headers, verify=False)

    if raw.status_code != 200:
        print('Failed to request ' + networkURL + ', got ' + str(raw.status_code))
        return False

    networkJsonFP = config.get('final_output_dir') + '/network.json'

    with open(networkJsonFP, 'w') as handler:
        handler.write(raw.text)

    print('Wrote ' + networkJsonFP)

    if config.get('log_changes'):
        baseBakDir = config.get('log_changes').rstrip('/')

        os.makedirs(baseBakDir, exist_ok=True)

        devicesBakFilePath = baseBakDir + '/Shaper.' + ts + '.csv'
        shutil.copy(networkJsonFP, devicesBakFilePath)

        print('Added shadow copy to ' + devicesBakFilePath)

        networkBakFilePath = baseBakDir + '/network.' + ts + '.json'
        shutil.copy(devicesCsvFP, networkBakFilePath)

        print('Added shadow copy to ' + networkBakFilePath)


if __name__ == '__main__':
    fetch()
