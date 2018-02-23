#!/usr/bin/python3
# ensure joker and jtool downloaded and in path - symlink if needed
import os
import requests
import zipfile
import subprocess

firmwares = {}
firmwares_url = {}  # {device: {size: link}, ...}
ota_json = requests.request('GET', 'https://api.ipsw.me/v2.1/ota.json').json()
for device in ota_json.keys():
    min_size = 10000000  # 10 MB - filter out ill-structure ipas (1.3 KB)
    max_size = 10000000000  # 10 GB
    if 'iPhone' in device:  # only iphones
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
        result = subprocess.run(['joker', '-dec', f'{kernelcache_location}'],
                                stdout=subprocess.PIPE)
        print(str(result.stdout.decode('utf8')))
        jtool_symbol = subprocess.run(['jtool', '-S', '/tmp/kernel'],
                                      stdout=subprocess.PIPE)
        print(str(jtool_symbol.stdout.decode('utf8')))
        kernproc_offset = '_kernproc'
        rootvnode_offset = '_rootvnode'
        input('')
