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
    'unobtanium': {
        'platform_path':   'x86_64-unknown-linux-gnu',
        'launch_flags':    ['-reindex'],
        'configure_flags': '--disable-tests --disable-bench',
        'depends_prep': [
            # boostorg.jfrog.io redirects to a dead "reactivate server" page; use archives.boost.io
            'sed -i "s|\\$(package)_download_path=https://boostorg.jfrog.io/artifactory/main/release/1.70.0/source/|\\$(package)_download_path=https://archives.boost.io/release/1.70.0/source/|" packages/boost.mk',
        ],
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
    cfg.setdefault('launch_flags', [])
    cfg.setdefault('configure_flags', '')
    cfg['git_ref'] = COIN_GIT_REFS.get(wallet_linux_dir, '')
    cfg['addnodes'] = COIN_ADDNODES.get(wallet_linux_dir, [])
    return cfg
