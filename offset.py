#!/usr/bin/python3
# ensure joker and jtool downloaded and in path - symlink if needed
import os
import requests
import zipfile
import subprocess

firmwares = {}
firmwares_url = {}  # {device: {size: link}, ...}
device_offset_dict = {}
ota_json = requests.request('GET', 'https://api.ipsw.me/v2.1/ota.json').json()
for device in ota_json.keys():
    min_size = 10000000  # 10 MB - filter out ill-structure ipas (1.3 KB)
    max_size = 10000000000  # 10 GB
    if 'iPhone' in device:  # only iphones
        device_offset_dict[device] = {}
        firmwares[device] = ota_json[device]['firmwares']
        for version in firmwares[device]:
            if version['size'] < max_size and version['size'] > min_size:
                max_size = version['size']
                firmwares_url[device] = {version["version"]: version['url']}
        fileurl = list(firmwares_url[device].values())[0]
        filename = fileurl.split('/')[-1]
        print(f'Downloading zipped ipa: {device} :: {filename}...')
        with open(f'/{os.getcwd()}/{filename}', 'wb') as f:
            f.write(requests.request('GET', fileurl).content)
        print(f'Unzipping ipa: {device} :: {filename}...')
        zip_ref = zipfile.ZipFile(f'{os.getcwd()}/{filename}', 'r')
        zip_ref.extractall(f'{os.getcwd()}/{filename.split(".")[0]}')
        zip_ref.close()
        # remove zip here
        kernelcache_location = f'{os.getcwd()}/{filename.split(".")[0]}/AssetData/boot/'
        kernelcache_location += \
            [string for string in os.listdir(kernelcache_location) if
             'kernelcache.release.' in string][0]
        joker_decompression = subprocess.run(
            ['joker', '-dec', f'{kernelcache_location}'],
            stdout=subprocess.PIPE)
        joker_results = joker_decompression.stdout
        jtool_symbol = subprocess.run(['jtool', '-S', '/tmp/kernel'],
                                      stdout=subprocess.PIPE)
        jtool_results = jtool_symbol.stdout
        # grep-esque
        for line in jtool_results.decode('utf8').split('\n'):
            if '_kernproc' in line or '_rootvnode' in line:
                device_offset_dict[device].update(
                    {f'{line.split()[1]} {line.split()[2]}': line.split()[0]})
        print(device_offset_dict)
        input('')
