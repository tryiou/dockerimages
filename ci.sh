#!/bin/bash

function generate() {

  pip3 install -r autobuild/requirements.txt
  cd autobuild && python3 generate_build_files.py --blockchain=$1 --version=$2 --path=$3 && cd ../

}

function build() {

    if docker build --build-arg WALLET=$1 \
                    --build-arg TAG=$2 \
                    --build-arg BRANCH=$3 \
                    --build-arg cores=$(nproc) \
                    -f ./images/"$1"/Dockerfile -t "$repo"/"$1":"$2" ./images/"$1"; then
      docker image ls "$repo"/"$1":"$2"
    else
      echo "Docker build Failed"
      exit 1
    fi
}

function run () {
    docker run -d --name="$1"-"$2" "$repo"/"$1":"$2"

    echo 'Sleep 5 sec to allow the container to start'
    sleep 5
    docker ps -a
    docker logs $(docker ps -q -l)

    container_id=$(docker ps -q -f status=running -f name="$1"-"$2")

    if [ "${container_id}" ]; then
      echo "${container_id}"
    else
      echo 'No running container' "$1"-"$2"
      docker stop "$1"-"$2"
      docker rm "$1"-"$2"
      exit 1
    fi
}

function test() {
    # dont use getwalletinfo for the test; newer bitcoin and alts don't automatically
    # create a wallet on first startup and getwalletinfo will fail with eg:
    # error code: -18
    # error message:
    # No wallet is loaded. Load a wallet using loadwallet or create a new one with createwallet. (Note: A default wallet is no longer automatically created)

    if [[ "$1" = "servicenode" ]] ; then
      cli="blocknet-cli"
    else
      # Need to get the executable stem from manifest because it might not be the same as the chain name
      # Subshell keeps our working directory intact even if the generator fails.
      stem=$(cd autobuild && python3 generate_build_files.py --blockchain=$1 --version=$2 --path=$3 --stem_only=true)
      if [ -z "${stem}" ]; then
        echo "could not derive daemon stem for $1 $2"
        docker stop "$1"-"$2" 2>/dev/null
        docker rm "$1"-"$2" 2>/dev/null
        exit 1
      fi
      cli="$stem-cli"
    fi
    # Slow first boots (Verthash datafile, Syscoin Geth bootstrap, block-index
    # load) keep RPC closed for many minutes on a healthy daemon: poll until
    # the chain answers. Deadline via CI_RPC_WAIT (default 3600s); every
    # failure path cleans the container up and exits non-zero.
    case "${CI_RPC_WAIT:-3600}" in ''|*[!0-9]*) rpc_wait_limit=3600;; *) rpc_wait_limit=${CI_RPC_WAIT:-3600};; esac
    rpc_fail() {
      echo "$1"
      echo "${info}" | tail -3
      docker stop "$2"-"$3" 2>/dev/null
      docker rm "$2"-"$3" 2>/dev/null
      exit 1
    }
    waited=0
    info=""
    while true; do
      info=$(docker exec "$1"-"$2" "$cli" getblockchaininfo 2>&1)
      if echo "${info}" | grep -q '"chain"'; then
        break
      fi
      if [ "$(docker inspect -f '{{.State.Running}}' "$1"-"$2" 2>/dev/null)" != "true" ]; then
        rpc_fail "container exited while waiting for RPC; last output:" "$1" "$2"
      fi
      if [ "${waited}" -ge "${rpc_wait_limit}" ]; then
        rpc_fail "RPC not ready after ${rpc_wait_limit}s; last output:" "$1" "$2"
      fi
      echo "waiting for RPC (${waited}s; last: $(echo "${info}" | tail -1 | cut -c1-120))"
      sleep 30
      waited=$((waited+30))
    done
    # The loop only breaks once the chain answers, so reaching here means success.
    echo "Good result."
    echo "${info}"

    # Verify the daemon supports every RPC method the Blocknet coin connector
    # (XBridge + XRouter) requires. The container may have no wallet loaded
    # (error -18) or reject the call for other reasons; any result other than
    # -32601 "Method not found" proves the method exists.
    if [[ "$1" != "servicenode" ]] ; then
      # $stem was derived above; reuse it instead of re-running the generator.
      if python3 autobuild/probe_rpc_methods.py --container "$1"-"$2" --stem "$stem"; then
        echo "RPC probe passed."
      else
        echo "RPC probe failed."
        docker stop "$1"-"$2" 2>/dev/null
        docker rm "$1"-"$2" 2>/dev/null
        exit 1
      fi
    fi
}

function push() {
  docker push "$repo"/"$1":"$2"
}

function clean() {

    echo 'Stop container'
    docker stop "$1"-"$2"

    echo 'Remove container'
    docker rm "$1"-"$2"

}

function release() {
    docker pull "$repo"/"$1":"$2"
    docker tag "$repo"/"$1":"$2" "$repo"/"$1":"$3"
    docker push "$repo"/"$1":"$3"
}

wallet=$(echo $2 | sed -e 's/\s\+/-/g' | tr '[:upper:]' '[:lower:]' )
version=$3
branch_or_path=$4
repo=$5

if [[ -z "$5" ]]; then
   repo="blocknetdx"
fi

if [ "$1" == "generate" ]; then
  generate "${wallet}" "${version}" "${branch_or_path}"
  exit $?
fi

if [ ! -f images/"${wallet}"/Dockerfile ]; then
  echo "No Dockerfile for ${wallet}"
  exit 1
fi

if [ "${version}" == "latest" ] || [ -z "${version}" ]; then
  version=$(grep "LABEL version" images/"${wallet}"/Dockerfile | cut -d '=' -f 2)
fi

staging_tag=$version"-staging"

case $1 in
  build)
    build "${wallet}" "${staging_tag}" "${branch_or_path}"
  ;;
  run)
    run "${wallet}" "${staging_tag}"
  ;;
  test)
    test "${wallet}" "${staging_tag}" "${branch_or_path}"
  ;;
  push)
    push "${wallet}" "${staging_tag}"
  ;;
  clean)
    clean "${wallet}" "${staging_tag}"
  ;;
  release)
    release "${wallet}" "${staging_tag}" "${version}"
  ;;
  release-as-latest)
    release "${wallet}" "${staging_tag}" "latest"
  ;;
  *)
    echo 'Unknown command'
esac
