const devBackendPort = 8000;
let backendHostPort;
if (process.env.NODE_ENV == 'development') {
  // When using `make servejs` we still want to use the current hostname
  // but the actual Python backend will be running on a different port
  if (window.location.port) {
    backendHostPort = `${window.location.hostname}:${devBackendPort}`;
  } else {
    backendHostPort = `${window.location.hostname}`;
  }
} else {
  if (window.location.port) {
    backendHostPort = `${window.location.hostname}:${window.location.port}`;
  } else {
    backendHostPort = `${window.location.hostname}`;
  }
}
const backendTlsEnabled = window.location.protocol == "https:";

function buildWebSocketUrl(endpoint) {
  const wsProto = backendTlsEnabled ? "wss:" : "ws:";
  return `${wsProto}//${backendHostPort}/${endpoint}`;
}

function buildBackendUrl(endpoint) {
  return `${window.location.protocol}//${backendHostPort}/${endpoint}`;
}

export default {
    buildWebSocketUrl,
    buildBackendUrl
}