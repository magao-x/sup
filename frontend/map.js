// MagAOX
import PropertiesTable from "~/pages/magaox/PropertiesTable.vue";
import Observation from "~/pages/magaox/Observation.vue";
import VirtualMachine from "~/pages/magaox/VirtualMachine.vue";
import LabMode from "~/pages/magaox/LabMode.vue";
import Dashboard from "~/pages/magaox/Dashboard.vue";
import Cameras from "~/pages/magaox/Cameras.vue";
import AdaptiveOptics from "~/pages/magaox/AdaptiveOptics.vue";
import Power from "~/pages/magaox/Power.vue";
import PlantStatus from "~/pages/magaox/PlantStatus.vue";

// SCOOB
import ScoobObservation from "~/pages/scoob/Observation.vue";

export const map =
{   "magaox": {
        "routes":
            [
                { path: '/', component: Observation},
                { path: '/cameras', component: Cameras},
                { path: '/ao', component: AdaptiveOptics},
                { path: '/power', component: Power},
                { path: '/properties', component: PropertiesTable },
                { path: '/vm', component: VirtualMachine },
                { path: '/lab', component: LabMode },
                { path: '/dashboard', component: PlantStatus },
                // { path: '/plant-status', component: PlantStatus},
            ],
        "tabs": {
            "observation": {"icon": "visibility", "path": "/", "label": "observation"},
            "cameras": {"icon": "camera", "path": "/cameras", "label": "cameras"},
            "ao": {"icon": "blur_on", "path": "/ao", "label": "AO"},
            "dashboard": {"icon": "speed", "path": "/dashboard", "label": "dashboard"},
            // "plant-status": {"icon": "account_tree", "path": "/plant-status", "label": "plant status"},
            "power": {"icon": "power_settings_new", "path": "/power", "label": "power"},
        }
    },
    'scoob': {
        "routes":
            [
                { path: '/', component: ScoobObservation},
                { path: '/cameras', component: Cameras},
                { path: '/power', component: Power},
            ],
        "tabs": {
            "observation": {"icon": "visibility", "path": "/", "label": "observation"},
            "cameras": {"icon": "camera", "path": "/cameras", "label": "cameras"},
            "power": {"icon": "power_settings_new", "path": "/power", "label": "power"},
        }
    }
}