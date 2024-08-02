// MagAOX
import PropertiesTable from "~/pages/MagAOX/PropertiesTable.vue";
import Observation from "~/pages/MagAOX/Observation.vue";
import VirtualMachine from "~/pages/MagAOX/VirtualMachine.vue";
import LabMode from "~/pages/MagAOX/LabMode.vue";
import Dashboard from "~/pages/MagAOX/Dashboard.vue";
import Cameras from "~/pages/MagAOX/Cameras.vue";
import AdaptiveOptics from "~/pages/MagAOX/AdaptiveOptics.vue";
import Power from "~/pages/MagAOX/Power.vue";
import PlantStatus from "~/pages/MagAOX/PlantStatus.vue";

// SCOOB

export const MagAOX_routes = [
    { path: '/', component: Observation},
    { path: '/cameras', component: Cameras},
    { path: '/ao', component: AdaptiveOptics},
    { path: '/power', component: Power},
    { path: '/properties', component: PropertiesTable },
    { path: '/vm', component: VirtualMachine },
    { path: '/lab', component: LabMode },
    { path: '/dashboard', component: Dashboard },
    { path: '/plant-status', component: PlantStatus},
];

export const SCOOB_routes = [
    { path: '/', component: Observation},
    { path: '/cameras', component: Cameras},
    { path: '/power', component: Power},
];
