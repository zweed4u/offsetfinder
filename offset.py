#!/usr/bin/python3
# ensure joker and jtool downloaded and in path - symlink if needed
import os
import sys
import json
import requests
import zipfile
import subprocess
import shutil

if len(sys.argv) != 2:
    print('Invoke with desired fw version. (eg. ./offset.py 11.1)')
    sys.exit()
ios_version = sys.argv[1]
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
                if version["version"] == ios_version:
                    max_size = version['size']
                    downloaded_version = version['version']
                    firmwares_url[device] = {version["version"]: version['url']}
        try:  # maybe use found flag and conditional to continue loop
            fileurl = list(firmwares_url[device].values())[0]
            filename = fileurl.split('/')[-1]
            print(f'Downloading zipped ipa: {device} :: {downloaded_version} :: {filename}...')
            with open(f'/{os.getcwd()}/{filename}', 'wb') as f:
                f.write(requests.request('GET', fileurl).content)
            print(f'Unzipping ipa: {device} :: {filename}...')
            zip_ref = zipfile.ZipFile(f'{os.getcwd()}/{filename}', 'r')
            zip_ref.extractall(f'{os.getcwd()}/{filename.split(".")[0]}')
            zip_ref.close()
            kernelcache_location = f'{os.getcwd()}/{filename.split(".")[0]}/AssetData/boot/'
            kernelcache_location += \
                [string for string in os.listdir(kernelcache_location) if
                 'kernelcache.release.' in string][0]
            # handle errors: "I have no idea how to handle a file with a magic of..."
            # "Not handling IMG3. 32-bit is passe', man"
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
            os.remove(f'{os.getcwd()}/{filename}')  # remove zip
            try:
                os.remove('/tmp/kernel')  # remove /tmp/kernel
            except:
                pass
            shutil.rmtree(f'{os.getcwd()}/{filename.split(".")[0]}')  # remove unzipped folder
        except:
            continue
print(json.dumps(device_offset_dict, indent=4))
