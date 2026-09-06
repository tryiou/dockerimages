import re

DEFAULT_BUILD_SYSTEM = 'autotools'

# Default RPC password baked into generated wallet images (single source of truth).
DEFAULT_RPC_PASS = 'AZErty.1'

BUILD_SYSTEMS = {
    'autotools': {
        'buildOS':   'focal',
        'cc':        'gcc-9',
        'cxx':       'g++-9',
        'apt_extra': '',
    },
    'cmake': {
        'buildOS':   'jammy',
        'cc':        'gcc-11',
        'cxx':       'g++-11',
        'apt_extra': 'libssl-dev libevent-dev libboost-chrono-dev libboost-filesystem-dev libboost-test-dev libboost-thread-dev zlib1g-dev',
    },
    # Modern Core v25+: CMake-only via depends toolchain, static deps, C++20.
    'cmake_core': {
        'buildOS':   'jammy',
        'cc':        'gcc-11',
        'cxx':       'g++-11',
        'apt_extra': '',
    },
    # Plain `make -f makefile.unix` in src/ against system libs.
    'makefile_unix': {
        'buildOS':   'jammy',
        'cc':        'gcc-11',
        'cxx':       'g++-11',
        'apt_extra': 'libssl-dev libdb++-dev libboost-all-dev libminiupnpc-dev libevent-dev libcurl4-openssl-dev zlib1g-dev',
    },
    # Go daemons: golang builder stage, plain jammy runtime.
    'golang': {
        'buildOS':   'jammy',
        'cc':        '',
        'cxx':       '',
        'apt_extra': '',
    },
}

# Keys are manifest dir_name_linux values.
COIN_BUILD_SYSTEMS = {
    'bitcoincash': 'cmake',
    # CMake-only Bitcoin Core 28-30 bases (no autogen.sh/configure).
    'fujicoin': 'cmake_core',
    'qtum': 'cmake_core',
    # Binaries viacoind/viacoin-cli (src/CMakeLists.txt).
    'viacoin': 'cmake_core',
    # Manifest daemon_stem=firo; binaries firod/firo-cli.
    'firo': 'cmake_core',
    # nc31.1 is CMake-only (no autogen.sh/configure at root).
    'namecoin': 'cmake_core',
    # lbcd (Go) replaced lbrycrd; companion pinned in COIN_OVERRIDES['lbcd'].
    'lbcd': 'golang',
}

# Keys are manifest dir_name_linux values.
COIN_OVERRIDES = {
    'lynx': {
        # Needs C++20 + make NAME=lynx (per-chain -DCURRENT_CHAIN, Makefile.am).
        'buildOS': 'jammy',
        'cc': 'gcc-11',
        'cxx': 'g++-11',
        'make_args': 'NAME=lynx',
    },
    'metrixcoin': {
        # EVM in src/cpp-ethereum submodule; skip test/bench suites.
        'git_clone_flags': ' --recurse-submodules',
        'configure_flags': '--disable-tests --disable-bench',
    },
    'pivx': {
        'post_build': ['./params/install-params.sh'],
    },
    'stakecubecoin': {
        # Upstream test/util/setup_common.cpp passes a stale llmq init
        # signature (bool vs CChainState&); test sources don't compile,
        # daemon itself unaffected.
        'configure_flags': '--disable-tests --disable-bench',
    },
    'qtum': {
        # EVM in src/evmone submodule (same shape as metrixcoin).
        'git_clone_flags': ' --recurse-submodules',
    },
    'syscoin': {
        # v5.x depends need C++20 (focal ships gcc-9). Covers SYS + TSYS.
        'buildOS': 'jammy',
        'cc':      'gcc-11',
        'cxx':     'g++-11',
        # Upstream syscoind boots its bundled SysGeth chain by default; an
        # empty zmqpubnevm disables it (XBridge/XRouter tests need UTXO only).
        # CLI form here; the exrproxy-env entrypoint appends launch_flags to
        # the daemon command line except when it enables NEVM itself.
        'launch_flags': ['-zmqpubnevm='],
    },
    'dashcore': {
        # v23.x depends need C++20 (same pattern as syscoin).
        'buildOS': 'jammy',
        'cc':      'gcc-11',
        'cxx':     'g++-11',
    },
    'particl': {
        # v27 mandates C++20; depends eudev needs gperf on host.
        'buildOS': 'jammy',
        'cc':      'gcc-11',
        'cxx':     'g++-11',
        'apt_extra': 'gperf',
    },
    'unobtanium': {
        'platform_path':   'x86_64-unknown-linux-gnu',
        # Fresh volumes exit(1) with "rebuild the database using -reindex to
        # enable auxpow support"; the flag is required on every boot.
        'launch_flags':    ['-reindex'],
        'configure_flags': '--disable-tests --disable-bench',
        'tail_debuglog': True,
        'depends_prep': [
            # boostorg.jfrog.io redirects to a dead "reactivate server" page; use archives.boost.io
            'sed -i "s|\\$(package)_download_path=https://boostorg.jfrog.io/artifactory/main/release/1.70.0/source/|\\$(package)_download_path=https://archives.boost.io/release/1.70.0/source/|" packages/boost.mk',
        ],
    },
    'ColossusXT': {
        # minizip needs system zlib (depends builds it only via qt_packages).
        'apt_extra': 'zlib1g-dev',
        # colxd holds stdout at 0 bytes while debug.log stays active.
        'tail_debuglog': True,
    },
    'divi': {
        # Sources live under a `divi/` subdir of the repo root.
        'source_subdir': 'divi',
        # File-only logging: tail debug.log (cf. unobtanium).
        'tail_debuglog': True,
    },
    'digiwage': {
        # digiwaged holds stdout at 0 bytes (38MB active debug.log seen).
        'tail_debuglog': True,
        # gmplib.org refuses connections; same tarball on ftp.gnu.org.
        'depends_prep': [
            'sed -i "s|\\$(package)_download_path=https://gmplib.org/download/gmp|\\$(package)_download_path=https://ftp.gnu.org/gnu/gmp|" packages/gmp.mk',
        ],
    },
    'vertcoin': {
        # gmplib.org 404s the depends fetch (curl --fail); ftp.gnu.org
        # serves the byte-identical tarball (sha256 verified).
        'depends_prep': [
            'sed -i "s|\\$(package)_download_path=https://gmplib.org/download/gmp|\\$(package)_download_path=https://ftp.gnu.org/gnu/gmp|" packages/gmp.mk',
        # boostorg.jfrog.io serves an HTML landing page, failing the sha256
        # gate; match only up to /release/ (version stays an unexpanded
        # $($(package)_version) variable in boost.mk).
            'sed -i "s|https://boostorg.jfrog.io/artifactory/main/release/|https://archives.boost.io/release/|" packages/boost.mk',
        ],
        # Fuzz tests don't compile; daemon builds fine without them.
        'configure_flags': '--disable-tests --disable-bench',
    },
    'vivocore': {
        # dl.bintray.com dead since 2021; same tarball on archives.boost.io.
        'depends_prep': [
            'sed -i "s|https://dl.bintray.com/boostorg/release/|https://archives.boost.io/release/|" packages/boost.mk',
        ],
        # File-only logging: tail debug.log (cf. unobtanium).
        'tail_debuglog': True,
    },
    'firo': {
        # File-only logging: tail debug.log (cf. unobtanium).
        'tail_debuglog': True,
        # Drop the '[*]' spinner ticks from docker logs (file keeps all).
        'tail_filter': '^[[][*][]] *$',
    },
    'dogecash': {
        # boostorg.jfrog.io is dead; use archives.boost.io.
        'depends_prep': [
            'sed -i "s|\\$(package)_download_path=https://boostorg.jfrog.io/artifactory/main/release/1.71.0/source/|\\$(package)_download_path=https://archives.boost.io/release/1.71.0/source/|" packages/boost.mk',
        ],
        # Sapling params required at startup; fetch at build like PIVX.
        'post_build': ['./params/install-params.sh'],
    },
    'dogecoin': {
        # File-only logging: tail debug.log (cf. unobtanium).
        'tail_debuglog': True,
    },
    'emercoin': {
        # Makefile.am links emercoin-tx with LIBBITCOIN_COMMON before
        # LIBBITCOIN_CONSENSUS, so GetMinFee() never resolves; daemon
        # and cli link fine, only the util binary fails.
        'configure_flags': '--disable-util-tx',
    },
    'ixcoin': {
        # File-only logging: tail debug.log (cf. unobtanium).
        'tail_debuglog': True,
    },
    'goldcoin': {
        # 0 stdout bytes against a 3.5MB active debug.log.
        'tail_debuglog': True,
    },
    'raven': {
        # 0 stdout bytes against a 25KB active debug.log with peers.
        'tail_debuglog': True,
    },
    'swiftcash': {
        # 0 stdout bytes against a 29MB active debug.log.
        'tail_debuglog': True,
    },
    'terracoincore': {
        # 0 stdout bytes against a 29MB+ active debug.log.
        'tail_debuglog': True,
    },
    'lbcd': {
        # lbcwallet companion provides the Core-compatible RPC facade.
        'wallet_repo': 'https://github.com/LBRYFoundation/lbcwallet',
        'wallet_tag':  'v0.13.111',
        # Node RPC is localhost-only; offset avoids wallet-RPC collision.
        'daemon_rpc_port': '19245',
    },
}


# Keys are manifest dir_name_linux values. Pin the git ref when the upstream
# tag for a version is unreliable (BitCore tagged 0.90.9.10 at a commit that
# still self-reports 0.90.9.9; the real 0.90.9.10 build is 129111b on master).
# Overrides walletGitTag.
COIN_GIT_REFS = {
    'bitcore': '129111bca490c237fa080e9cd95a3b93e0f132d8',
}


# Keys are manifest dir_name_linux values. Bootstrap addnodes baked into the
# image's default conf, for coins whose DNS seeds are dead. Every entry is
# port-probed open on the coin's P2P port before pinning.
COIN_ADDNODES = {
    # DNS seeds dead (NXDOMAIN / stale records); peers taken from the
    # community bootstrap vivo.conf, each port-verified open.
    'vivocore': [
        '109.173.160.12:12845',
        '144.91.99.72:12845',
        '161.97.187.4:12845',
        '178.18.244.223:12845',
        '193.87.75.153:12845',
        '37.60.248.165:12845',
        '5.189.131.160:12845',
        '62.171.138.11:12845',
        '62.171.185.166:12845',
        '82.198.187.90:12845',
        '82.198.187.90:12853',
    ],
    'bitcore': ['147.189.175.115', '192.99.37.121', '194.62.1.213', '194.62.29.27', '31.25.241.224'],
    'digiwage': ['119.198.113.149', '185.197.194.5', '167.237.24.110'],
    'dogecash': ['183.88.212.13', '199.241.137.81', '213.199.51.234', '173.249.63.231', '207.180.212.131', '164.68.99.67', '167.86.88.137', '144.91.78.11'],
    'namecoin': ['116.203.63.94', '13.246.63.174', '162.19.96.8', '162.210.198.133', '174.142.241.152', '23.106.38.114', '3.212.41.153', '46.165.244.225', '69.147.224.247'],
    'metrixcoin': ['46.101.142.112', '138.68.3.71', '123.253.61.161', '45.77.222.249', '137.184.168.50', '168.119.88.177', '206.189.214.150', '135.181.155.76', '23.88.58.244'],
    'pocketcoin': ['38.23.148.12', '93.170.82.253', '94.190.60.151', '98.19.181.21', '188.244.43.168'],
    'terracoincore': ['167.86.96.5', '173.212.230.25', '176.58.104.46', '185.203.216.63', '208.97.57.26', '38.242.153.224', '83.221.211.116'],
    'ufo': ['151.30.52.244', '91.121.62.2'],
    'unobtanium': ['107.170.173.232', '159.195.61.39', '172.99.188.170', '194.163.144.75', '205.209.102.70', '31.25.241.224', '66.151.242.154', '83.221.211.116', '89.185.100.229', '92.53.224.27'],
}


def get_build_config(wallet_linux_dir):
    system = COIN_BUILD_SYSTEMS.get(wallet_linux_dir, DEFAULT_BUILD_SYSTEM)
    if system not in BUILD_SYSTEMS:
        system = DEFAULT_BUILD_SYSTEM
    # NOTE: a coin override key replaces (not appends) the matching base key.
    cfg = dict(BUILD_SYSTEMS[system])
    cfg.update(COIN_OVERRIDES.get(wallet_linux_dir, {}))
    # build_system comes only from COIN_BUILD_SYSTEMS, never from a coin override.
    cfg['build_system'] = system
    cfg.setdefault('depends_prep', [])
    cfg.setdefault('post_build', [])
    cfg.setdefault('platform_path', '')
    cfg.setdefault('source_subdir', '')
    cfg.setdefault('launch_flags', [])
    cfg.setdefault('tail_debuglog', False)
    cfg.setdefault('tail_filter', '')
    if system == 'golang' and (cfg['launch_flags'] or cfg['tail_debuglog']
                               or cfg['tail_filter']
                               or COIN_ADDNODES.get(wallet_linux_dir)):
        # The golang Dockerfile branch renders no coin-params block and no
        # tail pipe; silently dropping declared runtime needs would ship a
        # deaf image, so refuse loudly instead.
        raise ValueError(
            "golang coin '%s' declares launch/tail/addnode params with nowhere to render them"
            % wallet_linux_dir)
    for token in cfg['launch_flags'] + COIN_ADDNODES.get(wallet_linux_dir, []):
        # Same plain-token alphabet the Dockerfile guard enforces, checked
        # here so a bad value fails at generate time instead of mid-build.
        # '=' is allowed (e.g. syscoin's -zmqpubnevm=): safe in double-quoted
        # assignment, exec-form CMD and verbatim CLI append; '/', whitespace,
        # quotes, '$' and backticks stay forbidden.
        if re.search(r'[^A-Za-z0-9_.:=-]', token):
            raise ValueError(
                "coin '%s' has an unsafe launch/addnode token: %r"
                % (wallet_linux_dir, token))
    if "'" in cfg['tail_filter'] or '"' in cfg['tail_filter']:
        # The filter value travels single-quoted (expansion-proof) while the
        # file line is double-quoted for the consumer parser; either quote
        # type in a value would break one side, so refuse at generate time.
        raise ValueError(
            "coin '%s' tail_filter contains a quote" % wallet_linux_dir)
    cfg.setdefault('make_args', '')
    cfg.setdefault('git_clone_flags', '')
    cfg.setdefault('configure_flags', '')
    cfg.setdefault('wallet_repo', '')
    cfg.setdefault('wallet_tag', '')
    cfg['git_ref'] = COIN_GIT_REFS.get(wallet_linux_dir, '')
    cfg['addnodes'] = COIN_ADDNODES.get(wallet_linux_dir, [])
    cfg['default_rpc_pass'] = DEFAULT_RPC_PASS
    return cfg
