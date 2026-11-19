# Deploying the image streams for a trial

How to run this branch's web UI and image stream server on an instrument
computer beside the production web UI, so the camera viewer can be tried on
real streams without disturbing the control room. The files are in
[`deploy/`](deploy/):

| File | What it runs |
| ---- | ------------ |
| [`deploy/systemd/sup-stream.service`](deploy/systemd/sup-stream.service) | `sup-stream`, the image stream server, on 127.0.0.1:9192 |
| [`deploy/systemd/sup-trial.service`](deploy/systemd/sup-trial.service) | a trial `sup`, the web UI, on 127.0.0.1:9291 |
| [`deploy/nginx/sup-trial.conf`](deploy/nginx/sup-trial.conf) | HTTPS on port 8443: `/ws/viewcam/` to `sup-stream`, the rest to the trial `sup` |

Once it's running:

| URL | Served by |
| --- | --------- |
| `https://<host>/` | the production web UI, as before (port 9191, untouched) |
| `https://<host>:8443/` | the trial web UI, with the **streams** tab and camera viewer |

Both UIs read `/opt/MagAOX/config/gui_sup.conf` and talk to the same INDI
server. The trial UI is a fully working UI: commands sent from it reach the
instrument.

## 1. Build the wheels

On the instrument computer, as your own user (not root), in a checkout of
this branch with its submodule:

```bash
git clone --recurse-submodules -b isio-streaming git@github.com:magao-x/sup.git
cd sup
make wheel
```

This is the same build as for production (see the README): it needs your
Rust toolchain with wasm-pack, and uses the `sup` conda env's Python and npm.
It leaves `dist/sup-*.whl` and `dist/viewcam_codec-*.whl`.

## 2. Make the trial environment

A virtualenv of its own at `/opt/sup-trial`, so that production's
`/opt/conda/envs/sup` stays as it is:

```bash
sudo /opt/conda/envs/sup/bin/python -m venv /opt/sup-trial
make install SUP_ENV=/opt/sup-trial
```

`make install` installs the two wheels into whichever environment `SUP_ENV`
names.

Then the ImageStreamIO Python binding, `ImageStreamIOWrap`. **Without it,
`sup-stream` falls back to a mock that reads no real shmims**, and every
feed shows "no image". Build it from the same ImageStreamIO source the
instrument's milk was built from, so the image header layout matches:

```bash
sudo /opt/sup-trial/bin/python -m pip install /path/to/ImageStreamIO
/opt/sup-trial/bin/python -c "import ImageStreamIOWrap; print(ImageStreamIOWrap.__file__)"
```

(Building it needs a C compiler; pip fetches its CMake and pybind11.)

## 3. Start the services

```bash
sudo cp deploy/systemd/sup-stream.service deploy/systemd/sup-trial.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sup-stream sup-trial
systemctl status sup-stream sup-trial
```

Both run as `xsup`. ImageStreamIO opens shmims read-write even to read them,
so `xsup` needs read and write access to the files in `/milk/shm`. On
MagAO-X the instrument's processes run as `xsup` too, so it has that already.
If shmims are elsewhere, set `MILK_SHM_DIR` in `sup-stream.service`.

Check the logs:

```bash
journalctl -u sup-stream -f
```

At startup `sup-stream` logs how many streams it found. A warning that
`ImageStreamIOWrap is not installed` means step 2's binding is missing.

## 4. Proxy them

```bash
sudo cp deploy/nginx/sup-trial.conf /etc/nginx/conf.d/
sudoedit /etc/nginx/conf.d/sup-trial.conf   # certificate paths
sudo nginx -t && sudo systemctl reload nginx
```

In `sup-trial.conf`:

- Set `ssl_certificate` and `ssl_certificate_key` to the certificate the
  production server block uses.
- If your nginx config already defines `map $http_upgrade
  $connection_upgrade`, delete the copy in this file, or `nginx -t` will
  refuse the duplicate.
- Port 8443 must be open to the people trying it, e.g. with firewalld:
  `sudo firewall-cmd --permanent --add-port=8443/tcp && sudo firewall-cmd --reload`.

The proxy raises nginx's idle timeout to a day, because a feed can be quiet
for much longer than nginx's default 60 s (a dark is sent once; a hidden tab
pauses its feeds). It also turns off buffering for the streams, which are
already compressed and paced by each browser's window.

## 5. Try it

- Open `https://<host>:8443/` and go to the **streams** tab. Cameras and DMs
  with rtimv configs are listed first, then the other shmims.
- Click one to open it in its own window. The status line under the image
  gives each feed's size, frame number and rate, and the total bandwidth.
- The list itself is at `https://<host>:8443/ws/viewcam/`, as JSON.
- Directly, on the instrument: `curl -s http://127.0.0.1:9192/ws/viewcam/`.

Frames are rounded to a quarter of their noise and compressed with zstd. A
camera's values arrive as floats, and the viewer's hover readout shows the
rounded values.

## Configuration

`sup-stream` reads `/opt/MagAOX/config/gui_sup_stream.conf` if it exists (a
TOML file; `sup-stream --dump-config` prints the effective settings).
Settings given on its command line in the unit file override it. For
example:

```toml
[streaming]
max_fps = 30.0       # most frames per second sent of any one stream
noise_step = 0.25    # round frames to this fraction of their noise; 0 sends them exact
compress = true      # zstd; false sends frames raw
rtimv_config_dir = "/opt/MagAOX/config"   # rtimv_*.conf: the streams listed first
shmim_dir = ""       # "" for ImageStreamIO's: $MILK_SHM_DIR, else /milk/shm
```

The list of streams is made when `sup-stream` starts. Restart it to pick up
new rtimv configs or shmims; any shmim can be opened by name meanwhile.

## Updating the trial

```bash
git pull --recurse-submodules
make wheel
make install SUP_ENV=/opt/sup-trial
sudo systemctl restart sup-stream sup-trial
```

## Removing it

```bash
sudo systemctl disable --now sup-trial sup-stream
sudo rm /etc/systemd/system/sup-trial.service /etc/systemd/system/sup-stream.service
sudo rm /etc/nginx/conf.d/sup-trial.conf && sudo systemctl reload nginx
sudo rm -rf /opt/sup-trial
```

The production UI is unaffected throughout.

## Moving to production

Once this branch is merged and installed in `/opt/conda/envs/sup` with
`make install`:

1. Point `sup-stream.service` at `/opt/conda/envs/sup/bin/sup-stream`.
2. Add the image streams to the production server block on 443, beside its
   existing `location /`, with the same `map` and proxy settings as
   `sup-trial.conf`:

   ```nginx
   location /ws/viewcam/ {
       proxy_pass http://127.0.0.1:9192;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection $connection_upgrade;
       proxy_set_header Host $host;
       proxy_read_timeout 1d;
       proxy_send_timeout 1d;
       proxy_buffering off;
   }
   ```

3. Set `serve_shmims = false` in `gui_sup.conf`, so the production `sup`
   leaves shmims to `sup-stream`.
4. Remove the trial, as above.
