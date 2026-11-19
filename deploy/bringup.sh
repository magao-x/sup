#!/usr/bin/env bash
# Bring up the image stream trial from this checkout: build the wheels, make
# the /opt/sup-trial environment, start sup-stream and the trial sup under
# systemd, and serve them through nginx on port 8443. DEPLOY.md describes
# each step; this does them in order, and can be run again to update a trial.
#
# Run it as yourself, not as root: the build needs your Rust toolchain, and
# the steps that need root use sudo.
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: deploy/bringup.sh --cert PATH --key PATH [options]

  --cert PATH           TLS certificate for nginx (the one the production
                        server block uses)
  --key PATH            its private key
  --isio-source PATH    ImageStreamIO source to build the Python binding from
                        (the one the instrument's milk was built from); needed
                        unless the trial environment already has it
  --open-firewall       open port 8443 with firewall-cmd
  --skip-build          reuse the wheels already in dist/
  -h, --help            show this help
EOF
}

PREFIX=/opt/sup-trial
SUP_ENV=/opt/conda/envs/sup
NGINX_CONF=/etc/nginx/conf.d/sup-trial.conf
STREAM_PORT=9192
TRIAL_PORT=9291
PROXY_PORT=8443

cert= key= isio_source= open_firewall= skip_build=
while (($#)); do
    case $1 in
        --cert) cert=${2:?--cert needs a path}; shift 2 ;;
        --key) key=${2:?--key needs a path}; shift 2 ;;
        --isio-source) isio_source=${2:?--isio-source needs a path}; shift 2 ;;
        --open-firewall) open_firewall=1; shift ;;
        --skip-build) skip_build=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    esac
done

step() { printf '\n==> %s\n' "$*"; }
fail() { printf 'error: %s\n' "$*" >&2; exit 1; }

cd "$(dirname "$0")/.."
ROOT=$(pwd)

# -----------------------------------------------------------------------------
step "Checking prerequisites"
# -----------------------------------------------------------------------------
((EUID != 0)) || fail "run this as yourself, not as root; it uses sudo where it must"
[[ -n $cert && -n $key ]] || { usage >&2; fail "--cert and --key are required"; }
sudo test -r "$cert" || fail "no readable certificate at $cert"
sudo test -r "$key" || fail "no readable key at $key"
[[ -x $SUP_ENV/bin/python ]] || fail "no $SUP_ENV/bin/python: the build uses the sup conda env"
for tool in systemctl nginx curl; do
    command -v "$tool" >/dev/null || fail "$tool is not on PATH"
done
if [[ -z $skip_build ]]; then
    for tool in cargo wasm-pack; do
        command -v "$tool" >/dev/null || fail "$tool is not on PATH; the build needs a Rust toolchain with wasm-pack"
    done
    [[ -x $SUP_ENV/bin/npm ]] || fail "no npm in $SUP_ENV; the build uses the sup env's npm"
fi
has_isio() { [[ -x $PREFIX/bin/python ]] && "$PREFIX/bin/python" -c 'import ImageStreamIOWrap' 2>/dev/null; }
if ! has_isio; then
    [[ -n $isio_source ]] || fail "$PREFIX has no ImageStreamIOWrap; give --isio-source, or sup-stream would read no real shmims"
    [[ -d $isio_source ]] || fail "no ImageStreamIO source at $isio_source"
fi

# -----------------------------------------------------------------------------
step "Building the wheels"
# -----------------------------------------------------------------------------
# Only a missing submodule: one checked out at another commit on purpose stays.
[[ -e viewarr-workspace/.git ]] || git submodule update --init --recursive
if [[ -z $skip_build ]]; then
    make wheel
fi
ls dist/sup-*.whl dist/viewcam_codec-*.whl >/dev/null 2>&1 || fail "no wheels in dist/; run without --skip-build"

# -----------------------------------------------------------------------------
step "Installing into $PREFIX"
# -----------------------------------------------------------------------------
if [[ ! -x $PREFIX/bin/python ]]; then
    sudo "$SUP_ENV/bin/python" -m venv "$PREFIX"
fi
make install SUP_ENV="$PREFIX"
if ! has_isio; then
    sudo "$PREFIX/bin/python" -m pip install --no-cache-dir "$isio_source"
    has_isio || fail "ImageStreamIOWrap still doesn't import in $PREFIX"
fi
echo "ImageStreamIOWrap: $("$PREFIX/bin/python" -c 'import ImageStreamIOWrap; print(ImageStreamIOWrap.__file__)')"

# -----------------------------------------------------------------------------
step "Starting sup-stream and sup-trial"
# -----------------------------------------------------------------------------
sudo install -m 644 deploy/systemd/sup-stream.service deploy/systemd/sup-trial.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sup-stream sup-trial
# restart rather than start, so that a rerun picks up the new install.
started=$(date '+%Y-%m-%d %H:%M:%S')
sudo systemctl restart sup-stream sup-trial

# -----------------------------------------------------------------------------
step "Configuring nginx"
# -----------------------------------------------------------------------------
rendered=$(mktemp)
backup=
trap 'rm -f "$rendered" ${backup:+"$backup"}' EXIT
sed -e "s|^\(\s*ssl_certificate\s\+\).*;|\1$cert;|" \
    -e "s|^\(\s*ssl_certificate_key\s\+\).*;|\1$key;|" \
    deploy/nginx/sup-trial.conf > "$rendered"
# nginx refuses a second definition of the same map variable.
if sudo grep -rlsE 'map[[:space:]]+\$http_upgrade[[:space:]]+\$connection_upgrade' /etc/nginx \
        --exclude="$(basename "$NGINX_CONF")" >/dev/null; then
    echo "\$connection_upgrade is already defined; leaving out this file's copy"
    sed -i '/^map \$http_upgrade \$connection_upgrade {/,/^}/d' "$rendered"
fi
if sudo test -e "$NGINX_CONF"; then
    backup=$(mktemp)
    sudo cat "$NGINX_CONF" > "$backup"
fi
sudo install -m 644 "$rendered" "$NGINX_CONF"
if ! sudo nginx -t; then
    # Put back what was there, so a bad config doesn't stop nginx's next reload.
    if [[ -n $backup ]]; then sudo install -m 644 "$backup" "$NGINX_CONF"; else sudo rm -f "$NGINX_CONF"; fi
    fail "nginx -t rejected $NGINX_CONF; it has been put back as it was"
fi
sudo systemctl reload nginx

if [[ -n $open_firewall ]]; then
    command -v firewall-cmd >/dev/null || fail "--open-firewall needs firewall-cmd"
    sudo firewall-cmd --permanent --add-port="$PROXY_PORT/tcp"
    sudo firewall-cmd --reload
fi

# -----------------------------------------------------------------------------
step "Checking it works"
# -----------------------------------------------------------------------------
wait_for() {
    local url=$1 tries=30
    until curl -ksf -o /dev/null "$url"; do
        ((--tries)) || return 1
        sleep 1
    done
}
wait_for "http://127.0.0.1:$STREAM_PORT/ws/viewcam/" || fail "sup-stream isn't answering; see journalctl -u sup-stream"
wait_for "http://127.0.0.1:$TRIAL_PORT/" || fail "sup-trial isn't answering; see journalctl -u sup-trial"
wait_for "https://127.0.0.1:$PROXY_PORT/ws/viewcam/" || fail "nginx isn't serving the trial on $PROXY_PORT"
if sudo journalctl -u sup-stream --since "$started" --no-pager | grep -q "ImageStreamIOWrap is not installed"; then
    fail "sup-stream is using its mock; check ImageStreamIOWrap in $PREFIX"
fi
streams=$(curl -ksf "https://127.0.0.1:$PROXY_PORT/ws/viewcam/" | "$PREFIX/bin/python" -c 'import json, sys; print(len(json.load(sys.stdin)["streams"]))')

cat <<EOF

The trial is up: https://$(hostname -f 2>/dev/null || hostname):$PROXY_PORT/ ($streams streams listed)
  logs:    journalctl -u sup-stream -u sup-trial -f
  update:  rerun this script
  remove:  see "Removing it" in DEPLOY.md
EOF
[[ -n $open_firewall ]] || echo "  (port $PROXY_PORT may need opening in the firewall: --open-firewall)"
