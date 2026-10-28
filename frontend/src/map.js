// Each page loads when its route is first visited, so a page's dependencies
// (maxGraph for the instrument graph, say) aren't in the bundle every page
// downloads.

// MagAOX
const PropertiesTable = () => import("@/pages/magaox/PropertiesTable.vue");
const Observation = () => import("@/pages/magaox/Observation.vue");
const VirtualMachine = () => import("@/pages/magaox/VirtualMachine.vue");
const LabMode = () => import("@/pages/magaox/LabMode.vue");
const Dashboard = () => import("@/pages/magaox/Dashboard.vue");
const Cameras = () => import("@/pages/magaox/Cameras.vue");
const AdaptiveOptics = () => import("@/pages/magaox/AdaptiveOptics.vue");
const Power = () => import("@/pages/magaox/Power.vue");
const InstGraph = () => import("@/pages/InstGraph.vue");
const FileBrowser = () => import("@/pages/FileBrowser.vue");

// SCOOB
const ScoobObservation = () => import("@/pages/scoob/Observation.vue");

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
                { path: '/instgraph', component: InstGraph},
                { path: '/files', component: FileBrowser},
            ],
        "tabs": {
            "observation": {"icon": "visibility", "path": "/", "label": "observation"},
            "quicklook": {"icon": "folder_open", "path": "/files", "label": "files"},
            // "cameras": {"icon": "camera", "path": "/cameras", "label": "cameras"},
            // "ao": {"icon": "blur_on", "path": "/ao", "label": "AO"},
            // "dashboard": {"icon": "speed", "path": "/dashboard", "label": "dashboard"},
            "state": {"icon": "power_settings_new", "path": "/instgraph", "label": "instgraph"},
            // "power": {"icon": "power_settings_new", "path": "/power", "label": "power"},
        }
    },
    'scoob': {
        "routes":
            [
                { path: '/', component: ScoobObservation},
                { path: '/cameras', component: Cameras},
                { path: '/power', component: Power},
                { path: '/files', component: FileBrowser},
            ],
        "tabs": {
            "observation": {"icon": "visibility", "path": "/", "label": "observation"},
            "cameras": {"icon": "camera", "path": "/cameras", "label": "cameras"},
            "power": {"icon": "power_settings_new", "path": "/power", "label": "power"},
            "files": {"icon": "folder_open", "path": "/files", "label": "files"},
        }
    }
}
