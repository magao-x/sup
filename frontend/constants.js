const MAX_LASTUPDATE_DELTA_SEC = 10;
const MAGAOX = "MAGAOX";
const SCOOB = "SCOOB";
const config_url = 'http://127.0.0.1:8000/config';

export default {
    MAX_LASTUPDATE_DELTA_SEC,
    plots: {
        numMinutes: 30,
    },
    MAGAOX,
    SCOOB,
    DEFAULT_LAYOUT: MAGAOX,
    LAYOUT_OPTIONS: [MAGAOX, SCOOB],
    CONFIG_URL: config_url,
}
