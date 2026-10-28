import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';
import os from 'node:os';
import path from 'node:path';

// High ports, so a developer running the real INDI server (7624) or a real sup
// (9191) alongside these tests does not collide with them.
const INDI_PORT = 17624;
const CONTROL_PORT = 17625;
const SUP_PORT = 19191;
const CACHE_ROOT = path.join(os.tmpdir(), 'sup-e2e-audible-alerts');
const repoRoot = fileURLToPath(new URL('..', import.meta.url));

export const ports = { INDI_PORT, CONTROL_PORT, SUP_PORT };

export default defineConfig({
  testDir: './tests',
  // sup serves built assets, so the build has to be current or the suite
  // quietly tests stale code.
  globalSetup: './tests/global-setup.mjs',
  // Playback is inherently about elapsed time, and these tests share one sup
  // and one fake device, so they run one at a time.
  workers: 1,
  fullyParallel: false,
  reporter: process.env.CI ? 'list' : [['list']],
  use: {
    baseURL: `http://127.0.0.1:${SUP_PORT}`,
    trace: 'retain-on-failure',
  },
  projects: [
    {
      // Audio is allowed only after the user interacts, which is how a browser
      // behaves for someone visiting sup for the first time.
      name: 'autoplay-blocked',
      use: { ...devices['Desktop Chrome'], channel: 'chromium' },
      metadata: { autoplayAllowed: false },
    },
    {
      // Stands in for a user who has allowed audio for this site in their
      // browser settings (Chrome calls it Sound, Firefox Autoplay, Safari
      // Auto-Play), which is what makes the opt-in survive a reload.
      name: 'autoplay-allowed',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chromium',
        launchOptions: { args: ['--autoplay-policy=no-user-gesture-required'] },
      },
      metadata: { autoplayAllowed: true },
    },
  ],
  webServer: [
    {
      command: `uv run python tests/fake_audible_alerts_device.py`
        + ` --indi-port ${INDI_PORT} --control-port ${CONTROL_PORT} --cache-root ${CACHE_ROOT}`,
      url: `http://127.0.0.1:${CONTROL_PORT}/health`,
      cwd: repoRoot,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
    },
    {
      command: `uv run sup indi.port=${INDI_PORT} bind_port=${SUP_PORT}`
        + ` audible_alerts_cache_root=${CACHE_ROOT}`
        + ` instgraph_file_path=${path.join(CACHE_ROOT, 'magaox.drawio')}`
        + ` log_unit=`
        // Small, so the log history tests can overflow it quickly.
        + ` log_history_per_level=5`,
      url: `http://127.0.0.1:${SUP_PORT}/config`,
      cwd: repoRoot,
      reuseExistingServer: !process.env.CI,
      stdout: 'pipe',
    },
  ],
});
