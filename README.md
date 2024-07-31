# sup

The MagAO-X web user interface in [Vue.js 2](https://v2.vuejs.org/) and async Python with [Starlette](https://www.starlette.io/). Built with [PurePyINDI2](https://github.com/xwcl/purepyindi2/).

![MagAO-X web UI in use](./doc/magao-x_web_ui_working.png)

This application uses the Parcel bundler (v. 1.x). There is of course a version 2.0 that has all-new bugs, and we'll transition some day, maybe.

## Development

There is a Makefile that provides `init`, `justjs`, and `servejs` targets (among others). A typical workflow would start with using `make init` to install the Python portion of sup in editable mode (`pip install -e ...`) and the JavaScript dependencies with `yarn install` from the `frontend/` directory.

### Python

The Python code is a Starlette ASGI app. In MagAO-X, it's launched by a SystemD unit via `uvicorn`:

```
[Unit]
Description=MagAO-X Web UI
Requires=network.target
After=network.target

[Service]
User=xsup
WorkingDirectory=/home/xsup
ExecStart=/opt/conda/envs/sup/bin/uvicorn sup:app

[Install]
WantedBy=default.target
```

(Note that for MagAO-X there's a `sup` env created in `/opt/conda` used by this app.)

The entry-point is thus the Starlette class instance called `app` in `sup/core.py`.

There is also a console command `sup` installed by `pip install`. It invokes `console_entrypoint` in `core.py`, which invokes `main`, which calls `uvicorn.run`. So, basically the same, but allows you to specify connection details.

### JavaScript

Most interesting stuff is in `*.vue` single-file component files, which combine HTML with JavaScript and stylesheet information.

Visual Studio Code with the official Vue extension improves development considerably.

If you use `make servejs`, you launch the bundler in live-reload mode, which saves time. The "live" part of live-reloading is not an easy thing to do in general, so you probably need to reload the page on changes. You will *also* need the Python server process running on port 8000 for the connection to MagAO-X to work. (You can use the `sup` command to launch it, and port 8000 is default.)

The entry point is the `index.html` file, which loads `index.js`, which displays `App.vue` as its root component.

WebSocket connection / reconnection is kind of hard to find, but it's in the `mounted` hook for the `common.js` mixin used in `index.js`. (It is common *not* to all components, but to all *top-level* components, of which there is currently one non-trivial example.)
