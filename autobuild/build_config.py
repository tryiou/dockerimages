DEFAULT_BUILD_SYSTEM = 'autotools'

# Default RPC password baked into generated wallet images. Single source of
# truth: surfaced to every template via get_build_config() as `default_rpc_pass`
# so it is declared exactly once in the codebase.
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
    # Modern Bitcoin Core v25+ (e.g. Xaya): CMake-only build, no autogen.sh/configure.
    # Builds with the depends-generated toolchain file
    # (depends/<host>/toolchain.cmake); deps are compiled statically by
    # depends, so no extra apt packages are needed. Requires C++20 and
    # cmake >= 3.22 (jammy ships cmake 3.22.1 + gcc-11).
    'cmake_core': {
        'buildOS':   'jammy',
        'cc':        'gcc-11',
        'cxx':       'g++-11',
        'apt_extra': '',
    },
    # Plain `make -f makefile.unix` in src/ (no depends/, autotools, or cmake),
    # e.g. Innova v5.0.0.0. Compiles against system libs. OpenSSL 3.x
    # (jammy) auto-disables the bundled native-tor build (makefile.unix:43-48),
    # so we force USE_NATIVETOR=- and skip it entirely. Needs Berkeley DB,
    # boost, openssl, libevent, miniupnpc, curl, zlib.
    'makefile_unix': {
        'buildOS':   'jammy',
        'cc':        'gcc-11',
        'cxx':       'g++-11',
        'apt_extra': 'libssl-dev libdb++-dev libboost-all-dev libminiupnpc-dev libevent-dev libcurl4-openssl-dev zlib1g-dev',
    },
    # Go daemons (e.g. LBC via LBRYFoundation/lbcd). Built in a multi-stage
    # Dockerfile: golang:1.19 builder compiles the Go binaries, the runtime
    # stage is a plain ubuntu:jammy. No gcc/g++ toolchain needed at runtime.
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
    # fujicoin v28+ (Bitcoin Core 28-30 base) is a CMake-only build: no
    # autogen.sh/configure, uses the depends-generated toolchain.cmake.
    'fujicoin': 'cmake_core',
    # qtum v29+ (Bitcoin Core 29-30 base) is a CMake-only build, same as
    # fujicoin above.
    'qtum': 'cmake_core',
    # viacoin v30.2.0 (Bitcoin Core 30 base) is a CMake-only build, same as
    # qtum/fujicoin above; binaries viacoind/viacoin-cli (src/CMakeLists.txt).
    'viacoin': 'cmake_core',
    # firo v0.14.17.x (ex-Zcoin, rebranded 2020) is a CMake-only build with the
    # depends-generated toolchain.cmake; binaries firod/firo-cli (manifest
    # daemon_stem=firo).
    'firo': 'cmake_core',
    # LBC: lbcd (Go) replaced lbrycrd (deprecated). wallet_repo/wallet_tag in
    # COIN_OVERRIDES['lbcd'] pin the lbcwallet companion binary.
    'lbcd': 'golang',
}

# Keys are manifest dir_name_linux values.
COIN_OVERRIDES = {
    'lynx': {
        # Bitcoin Core v26 fork (v28.0.0): needs C++20 (gcc-11/jammy), and the
        # daemon is compiled per-chain via -DCURRENT_CHAIN="$(NAME)" (Makefile.am),
        # so make must be told NAME=lynx or the image builds the wrong chain.
        'buildOS': 'jammy',
        'cc': 'gcc-11',
        'cxx': 'g++-11',
        'make_args': 'NAME=lynx',
    },
    'metrixcoin': {
        # Qtum fork: the EVM (aleth/cpp-ethereum) lives in the src/cpp-ethereum
        # git submodule; without it the build dies on missing
        # libethashseal/libdevcore headers.
        'git_clone_flags': ' --recurse-submodules',
        # Upstream CI flags: skip test/bench suites (~20% faster build).
        'configure_flags': '--disable-tests --disable-bench',
    },
    'pivx': {
        'post_build': ['./params/install-params.sh'],
    },
    'stakecubecoin': {
        # v3.5.1.0: upstream test/util/setup_common.cpp calls
        # llmq::InitLLMQSystem(*evoDb, true) with a stale signature (bool vs
        # CChainState&) - test sources do not compile; the daemon itself is
        # unaffected.
        'configure_flags': '--disable-tests --disable-bench',
    },
    'qtum': {
        # The EVM (evmone/evmc) lives in the src/evmone git submodule; without
        # it CMake generate dies on missing evmone sources (same shape as the
        # Metrix Qtum fork above).
        'git_clone_flags': ' --recurse-submodules',
    },
    'syscoin': {
        # v5.x depends set CXX_STANDARD=c++20 (needs gcc-10+; focal only ships
        # gcc-9). Applies to both SYS mainnet and TSYS testnet: they share the
        # dir_name_linux value 'syscoin'.
        'buildOS': 'jammy',
        'cc':      'gcc-11',
        'cxx':     'g++-11',
    },
    'dashcore': {
        # v23.x depends set CXX_STANDARD=c++20 (needs gcc-10+; focal only ships
        # gcc-9). Same pattern as syscoin.
        'buildOS': 'jammy',
        'cc':      'gcc-11',
        'cxx':     'g++-11',
    },
    'particl': {
        # v27 (Bitcoin Core 27 base) mandates C++20 (AX_CXX_COMPILE_STDCXX
        # [20] mandatory; GCC >= 10.1). Autotools flow otherwise unchanged.
        # depends builds eudev, whose configure needs gperf on the host.
        'buildOS': 'jammy',
        'cc':      'gcc-11',
        'cxx':     'g++-11',
        'apt_extra': 'gperf',
    },
    'unobtanium': {
        'platform_path':   'x86_64-unknown-linux-gnu',
        # A/B-tested 2026-08-25: without -reindex the daemon exits(1) on boot
        # with "You need to rebuild the database using -reindex to enable
        # auxpow support." — required for every fresh volume.
        'launch_flags':    ['-reindex'],
        'configure_flags': '--disable-tests --disable-bench',
        'depends_prep': [
            # boostorg.jfrog.io redirects to a dead "reactivate server" page; use archives.boost.io
            'sed -i "s|\\$(package)_download_path=https://boostorg.jfrog.io/artifactory/main/release/1.70.0/source/|\\$(package)_download_path=https://archives.boost.io/release/1.70.0/source/|" packages/boost.mk',
        ],
    },
    'ColossusXT': {
        # colxd links the source-tree minizip (AC_CONFIG_SUBDIRS), which needs
        # zlib.h; but depends builds zlib only via qt_packages, and this build
        # runs NO_QT=1. Provide zlib from the system.
        'apt_extra': 'zlib1g-dev',
    },
    'divi': {
        # v3.0.0 source lives under a `divi/` subdir of the repo root
        # (depends/, src/, autogen.sh are all inside it). The Dockerfile clones
        # into /opt/<dir>/<dir>/ then cds into this subdir before building.
        'source_subdir': 'divi',
        # Daemon defaults to file-only logging (fPrintToConsole=false); stream
        # debug.log to stdout (docker logs) while keeping the file written.
        'tail_debuglog': True,
    },
    'vertcoin': {
        # gmplib.org intermittently 404s the depends gmp fetch (curl --location
        # --fail); ftp.gnu.org serves the byte-identical tarball (sha256 verified)
        'depends_prep': [
            'sed -i "s|\\$(package)_download_path=https://gmplib.org/download/gmp|\\$(package)_download_path=https://ftp.gnu.org/gnu/gmp|" packages/gmp.mk',
        # boostorg.jfrog.io serves an HTML landing page instead of the tarball
        # (sha256 gate would fail); archives.boost.io hosts identical files.
        # Domain-prefix sed: boost.mk embeds the version as an unexpanded
        # $($(package)_version) variable, so match only up to /release/
            'sed -i "s|https://boostorg.jfrog.io/artifactory/main/release/|https://archives.boost.io/release/|" packages/boost.mk',
        ],
        # upstream v23.2 fuzz tests don't compile (test/fuzz/string.cpp:145
        # CopyrightHolders arity bug) — daemon builds fine without them
        'configure_flags': '--disable-tests --disable-bench',
    },
    'vivocore': {
        # boost 1.64.0 pinned to dl.bintray.com (dead since 2021); archives.boost.io
        # hosts the identical tarball (sha256 verified against depends/packages/boost.mk)
        'depends_prep': [
            'sed -i "s|https://dl.bintray.com/boostorg/release/|https://archives.boost.io/release/|" packages/boost.mk',
        ],
        # Dash-0.12.1-era daemon defaults to file-only logging (docker logs empty);
        # stream debug.log to docker logs while keeping the file written.
        'tail_debuglog': True,
    },
    'firo': {
        # Dash-0.14-era daemon defaults to file-only logging (docker logs
        # empty); stream debug.log to docker logs while keeping it written.
        'tail_debuglog': True,
        # firod writes a '[*]' progress-spinner tick into debug.log around
        # every masternode-list update line (hundreds per block during the
        # historical DMN rebuild); drop those empty frames from docker logs.
        'tail_filter': '^[[][*][]] *$',
    },
    'dogecash': {
        # boostorg.jfrog.io is dead (reactivate-server page); use archives.boost.io
        'depends_prep': [
            'sed -i "s|\\$(package)_download_path=https://boostorg.jfrog.io/artifactory/main/release/1.71.0/source/|\\$(package)_download_path=https://archives.boost.io/release/1.71.0/source/|" packages/boost.mk',
        ],
        # Sapling params are required at startup (init.cpp aborts without them);
        # fetch them during the build like PIVX does.
        'post_build': ['./params/install-params.sh'],
    },
    'dogecoin': {
        # Daemon defaults to file-only logging (fPrintToConsole=false,
        # util.cpp:115); stream debug.log to stdout (docker logs) while keeping
        # the file written.
        'tail_debuglog': True,
    },
    'emercoin': {
        # v0.8.5emc Makefile.am links emercoin-tx with LIBBITCOIN_COMMON
        # (provider of the free GetMinFee() in policy/feerate.cpp) before
        # LIBBITCOIN_CONSENSUS (consumer in primitives/transaction.cpp), so the
        # static link never resolves it. Upstream bug, present on master too.
        # The daemon/cli/wallet binaries link fine (WALLET/SERVER pull
        # feerate.o first) — only emercoin-tx fails, so skip it.
        'configure_flags': '--disable-util-tx',
    },
    'ixcoin': {
        # Daemon defaults to file-only logging (fPrintToConsole=false); stream
        # debug.log to stdout (docker logs) while keeping the file written.
        'tail_debuglog': True,
    },
    'lbcd': {
        # lbcd is the LBRY Foundation Go daemon; lbcwallet provides the
        # Bitcoin-Core-compatible legacy RPC facade (wallet + node passthrough).
        # The manifest points at lbcd only; the lbcwallet companion is pinned
        # here so the golang Dockerfile can build both.
        'wallet_repo': 'https://github.com/LBRYFoundation/lbcwallet',
        'wallet_tag':  'v0.13.111',
        # Node RPC is bound to localhost and only reached by the wallet facade;
        # it uses a port offset from the exposed wallet RPC to avoid collision.
        'daemon_rpc_port': '19245',
    },
}


# Keys are manifest dir_name_linux values. Pin the git ref (commit/branch/tag)
# to clone when the upstream tag for a version is unreliable (e.g. BitCore
# tagged 0.90.9.10 at a commit that still self-reports 0.90.9.9; the real
# 0.90.9.10 build lives at 129111b on master). Overrides walletGitTag.
COIN_GIT_REFS = {
    'bitcore': '129111bca490c237fa080e9cd95a3b93e0f132d8',
}


# Keys are manifest dir_name_linux values. Bootstrap addnode peers baked into
# the image's default conf. Used when the coin has no working DNS seed
# (e.g. BitCore: seed.bitcore.biz returns nothing). Peers probed live on the
# P2P port (8555 for bitcore) before pinning.
COIN_ADDNODES = {
    # DNS seeds dead network-wide (4/5 families NXDOMAIN, remaining one serves
    # stale IPs); peers sourced from the community bootstrap-8.2.26 vivo.conf,
    # every entry port-verified open at bake time (2026-08-25)
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
    'unobtanium': ['107.170.173.232', '159.195.61.39', '172.99.188.170', '194.163.144.75', '205.209.102.70', '31.25.241.224', '66.151.242.154', '83.221.211.116', '89.185.100.229'],
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
    cfg.setdefault('make_args', '')
    cfg.setdefault('git_clone_flags', '')
    cfg.setdefault('configure_flags', '')
    cfg.setdefault('wallet_repo', '')
    cfg.setdefault('wallet_tag', '')
    cfg['git_ref'] = COIN_GIT_REFS.get(wallet_linux_dir, '')
    cfg['addnodes'] = COIN_ADDNODES.get(wallet_linux_dir, [])
    cfg['default_rpc_pass'] = DEFAULT_RPC_PASS
    return cfg
