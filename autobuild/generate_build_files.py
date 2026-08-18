import json
import os
import time
import sys
import re
import subprocess
import argparse
import urllib.request
from jinja2 import Environment, FileSystemLoader
from icecream import ic

from build_config import get_build_config

j2_env = Environment(loader=FileSystemLoader(''),
                     trim_blocks=True,
                     lstrip_blocks=True)

template = j2_env.get_template('Dockerfile.j2')
readmetemplate = j2_env.get_template('README.md.j2')

walletDict = {}


def load_template(template_url):
    """
    load_template - returns the data from a local file path or url provided
    """
    if os.path.isfile(template_url):
        with open(template_url) as f:
            return f.read()
    while True:
        response = urllib.request.urlopen(template_url)
        if response.getcode() == 200:
            data = response.read()
            result = data.decode('utf-8')
            return result
        time.sleep(10)


branch = subprocess.getoutput("git rev-parse --abbrev-ref HEAD")

parser = argparse.ArgumentParser()
parser.add_argument('--blockchain', help='blockchain name', default=branch)
parser.add_argument('--path', help='branch path', default='https://raw.githubusercontent.com/blocknetdx/blockchain-configuration-files/master')
parser.add_argument('--version', help='version of wallet', default="latest")
parser.add_argument('--manifest', help='coin manifest fragment', default=False)
parser.add_argument('--wallet_conf', help='coin wallet config', default=False)
parser.add_argument('--stem_only', help='special use: just return the coin daemon stem', default=False)
args = parser.parse_args()
blockchain_name = args.blockchain
wallet_version = args.version
config_path = args.path
manifest_config = args.manifest
wallet_config = args.wallet_conf
stem_only = args.stem_only
if not manifest_config:
    MANIFEST_URL = config_path+'/manifest-latest.json'
    WALLET_CONF_URL = config_path+'/wallet-confs/'
    #ic(MANIFEST_URL)
    #ic(WALLET_CONF_URL)
    try:
        manifest_config = json.loads(load_template(MANIFEST_URL))
    except Exception as e:
        print(f"Couldn't read manifest-latest.json: {e}")
        sys.exit(1)
else:
    manifest_config = json.loads(manifest_config)

found = False
for blockchain in manifest_config:
    if re.sub(r'\s+', '-', blockchain['blockchain'].lower()) != re.sub(r'\s+', '-', blockchain_name.lower()):
        continue
    if 'daemon_stem' in blockchain:
        walletDaemon = blockchain['daemon_stem']
    else:
        walletDaemon = blockchain['conf_name'].split('.conf')[0]
    if stem_only:
        print(walletDaemon)
        raise SystemExit
    walletDaemon = walletDaemon + 'd'
    walletConf = blockchain['wallet_conf']
    walletName = re.sub(r'\s+', '-', blockchain['blockchain'].lower())
    walletNameVerId = blockchain['ver_id']
    walletGitURL = blockchain['repo_url']
    walletConfName = blockchain['conf_name']
    walletLinuxDir = blockchain['dir_name_linux']
    build_cfg = get_build_config(walletLinuxDir)
    walletTicker = blockchain['ticker']
    walletVerList = blockchain['versions']
    testnetPort = '18332'
    testnetRPC = '19332'
    if wallet_version == "latest" or wallet_version == "":
        # latest intentionally keeps scanning: last manifest entry matching
        # the coin name wins (pinned versions break on first match below).
        walletVersion = walletVerList[-1]
        walletGitTag = walletVersion
        walletNameVerId = walletVersion
        found = True
    elif wallet_version in walletVerList:
        walletVersion = wallet_version
        walletGitTag = walletVersion
        walletNameVerId = walletVersion
        found = True
        break

if not found:
    sys.exit(f'Wallet version not found {wallet_version}')

# open up wallet_conf and get the rpc & port
if not wallet_config:
    try:
        walletData = load_template(WALLET_CONF_URL + walletConf).split('\n')
    except Exception as e:
        print(e)
        sys.exit(f'Wallet template not found for {blockchain_name}')
else:
    try:
        walletData = wallet_config.split(' ')
    except Exception as e:
        print(e)
        sys.exit(f'Bad wallet config for {blockchain_name}')

for z in walletData:
    if 'rpcport' in z:
        values = (z.split('='))
        walletRPCPort = values[1].strip('\n')
    elif 'port' in z:
        values = (z.split('='))
        walletPort = values[1].strip('\n')

rendered_file = template.render(walletName=walletName, walletDaemon=walletDaemon, walletGitTag=walletGitTag,
                                walletGitURL=walletGitURL, walletPort=walletPort, walletRPCPort=walletRPCPort,
                                testnetPort=testnetPort, testnetRPC=testnetRPC, walletConfName=walletConfName,
                                walletLinuxDir=walletLinuxDir, walletNameVerId=walletNameVerId,
                                walletDockerName=walletTicker.lower(), **build_cfg)


readme_rendered_file = readmetemplate.render(walletName=walletName, walletVersion=walletVersion, 
                                             walletDaemon=walletDaemon, walletGitTag=walletGitTag,
                                             walletGitURL=walletGitURL, walletTicker=walletTicker,
                                             walletPort=walletPort, walletRPCPort=walletRPCPort,
                                             testnetPort=testnetPort, testnetRPC=testnetRPC,
                                             walletConfName=walletConfName,
                                             walletLinuxDir=walletLinuxDir, walletNameVerId=walletNameVerId,
                                             walletDockerName=walletTicker.lower())

dockerpath = walletName
filename = '../images/' + dockerpath + '/Dockerfile'
print(filename)
os.makedirs(os.path.dirname(filename), exist_ok=True)
with open(filename, "w") as f:
    f.write(rendered_file)
    ic(rendered_file)

readmefilename = '../images/' + dockerpath + '/README.md'
print(readmefilename)
os.makedirs(os.path.dirname(filename), exist_ok=True)
with open(readmefilename, "w") as f:
    f.write(readme_rendered_file)
    ic(readme_rendered_file)
