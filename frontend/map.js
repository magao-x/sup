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
                { path: '/dashboard', component: Dashboard },
                { path: '/plant-status', component: PlantStatus},
            ],
        "tabBar": () => import('~/pages/magaox/TabBar.vue')
    },
    'scoob': {
        "routes":
            [
                { path: '/', component: Observation},
                { path: '/cameras', component: Cameras},
                { path: '/power', component: Power},
            ],
        "tabBar": () => import('~/pages/scoob/TabBar.vue')
    }
}