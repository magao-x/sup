import constants from '../constants.json';

const MAX_LASTUPDATE_DELTA_SEC = constants.MAX_LASTUPDATE_DELTA_SEC;
const MAGAOX = constants.MAGAOX;
const SCOOB = constants.SCOOB;
const config_url = constants.CONFIG_URL;
const LAYOUT_OPTIONS = constants.LAYOUT_OPTIONS;
const REPLICATED_CAMERAS = constants.REPLICATED_CAMERAS;

export default {
    MAX_LASTUPDATE_DELTA_SEC,
    plots: {
        numMinutes: 30,
    },
    MAGAOX,
    SCOOB,
    DEFAULT_LAYOUT: MAGAOX,
    LAYOUT_OPTIONS: LAYOUT_OPTIONS,
    CONFIG_URL: config_url,
    REPLICATED_CAMERAS: REPLICATED_CAMERAS,
}
