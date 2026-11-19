// The streams the server lists at /ws/viewcam/ (see sup/stream_catalog.py),
// and opening one in a camera window of its own.
import utils from "@/utils.js";

// A camera window's size before the viewer fits it. Browsers keep a popup
// on screen, so this needn't account for the screen it lands on.
const POPUP_WIDTH = 720;
const POPUP_HEIGHT = 760;

let catalogPromise = null;

// The server finds the streams once, at startup, so one fetch per page will do.
export function fetchStreamCatalog() {
  if (catalogPromise === null) {
    catalogPromise = fetch(utils.buildBackendUrl('ws/viewcam/'))
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .catch((err) => {
        catalogPromise = null;
        throw err;
      });
  }
  return catalogPromise;
}

// A stream's dark and saturation mask, as its rtimv config names them;
// either may be null, and a stream without a config has neither.
export function companionsFor(catalog, name) {
  const info = catalog?.streams.find((stream) => stream.name === name);
  return { dark: info?.dark ?? null, saturation: info?.sat_mask ?? null };
}

export function cameraUrl(name, { popup = false } = {}) {
  const url = new URL('camera.html', window.location.origin + import.meta.env.BASE_URL);
  url.searchParams.set('name', name);
  if (popup) url.searchParams.set('popup', '1');
  return url.href;
}

// Opens a stream in a popup with as little browser chrome as browsers allow
// (no toolbars or menus, though the address bar stays), or brings forward
// the one already open for it. Must be called from a click or keypress, or
// it will be blocked. Returns whether a window opened; when it didn't, the
// browser blocked it.
export function openCameraPopup(name) {
  const features = `popup,width=${POPUP_WIDTH},height=${POPUP_HEIGHT}`;
  // Named per stream, so a second click reuses the window rather than opening another.
  const win = window.open(cameraUrl(name, { popup: true }), `camera-${name}`, features);
  if (!win) return false;
  win.focus();
  return true;
}
