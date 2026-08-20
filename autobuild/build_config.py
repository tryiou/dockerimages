DEFAULT_BUILD_SYSTEM = 'autotools'

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
}

# Keys are manifest dir_name_linux values.
COIN_BUILD_SYSTEMS = {
    'bitcoincash': 'cmake',
}

# Keys are manifest dir_name_linux values.
COIN_OVERRIDES = {
    'pivx': {
        'post_build': ['./params/install-params.sh'],
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
    'unobtanium': {
        'platform_path':   'x86_64-unknown-linux-gnu',
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
    'bitcore': ['147.189.175.115', '192.99.37.121', '194.62.1.213', '194.62.29.27', '31.25.241.224'],
    'digiwage': ['119.198.113.149', '185.197.194.5', '167.237.24.110'],
    'dogecash': ['183.88.212.13', '199.241.137.81', '213.199.51.234', '173.249.63.231', '207.180.212.131', '164.68.99.67', '167.86.88.137', '144.91.78.11'],
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
    cfg.setdefault('configure_flags', '')
    cfg['git_ref'] = COIN_GIT_REFS.get(wallet_linux_dir, '')
    cfg['addnodes'] = COIN_ADDNODES.get(wallet_linux_dir, [])
    return cfg
