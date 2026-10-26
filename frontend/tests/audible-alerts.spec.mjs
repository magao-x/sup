// End-to-end coverage for browser-side audible alerts.
//
// Runs against a real sup and a fake maggieo_x (tests/fake_audible_alerts_device.py),
// both started by playwright.config.mjs. Two projects cover the two states a
// browser can be in: audio allowed only after an interaction, which is what a
// first-time visitor sees, and audio allowed outright, which is what someone
// who granted the site permission sees.
import { test, expect } from '@playwright/test';
import { ports } from '../playwright.config.mjs';

const CONTROL = `http://127.0.0.1:${ports.CONTROL_PORT}`;
const STATIC_CLIP = 'a1b2c3d4e5.wav';
const OTHER_CLIP = 'walkup_example.wav';
const TEMP_CLIP = 'temp/f6e5d4c3b2.wav';

/** Make the fake device announce a clip, the way a real reaction would. */
async function emit(request, file) {
  const response = await request.post(`${CONTROL}/emit?file=${encodeURIComponent(file)}`);
  expect(response.ok()).toBeTruthy();
  return response.json();
}

/**
 * Watch clip traffic and playback attempts.
 *
 * play() is patched before any page script runs so the count includes the
 * silent probe the player uses at startup to find out whether it is allowed to
 * make noise.
 */
async function instrument(page) {
  const clipRequests = [];
  const pageErrors = [];
  page.on('request', (r) => {
    const url = r.url();
    if (url.includes('/audible-alerts/clip/')) {
      clipRequests.push(decodeURIComponent(url.split('/clip/')[1]));
    }
  });
  page.on('pageerror', (e) => pageErrors.push(String(e)));
  await page.addInitScript(() => {
    window.__playAttempts = [];
    const play = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () {
      window.__playAttempts.push(this.src.startsWith('blob:') ? 'generated-tone' : this.src.split('/clip/')[1]);
      return play.call(this);
    };
  });
  return { clipRequests, pageErrors };
}

const alertState = (page) => page.evaluate(() => ({
  ...document.querySelector('#app').__vue_app__.config.globalProperties.$store.state.audibleAlerts,
}));

const playedClips = (page) => page.evaluate(
  () => window.__playAttempts.filter((s) => s !== 'generated-tone')
);

const control = (page) => page.locator('.audible-alerts').first();

// Each test runs in a fresh browser context, so localStorage starts empty on
// its own. Resist clearing it in a beforeEach: an init script re-runs on every
// navigation, which would wipe the preference the reload tests exist to check.


test('the control appears once the device is publishing', async ({ page }) => {
  await instrument(page);
  await page.goto('/');
  await expect(control(page)).toBeVisible();
});

test('alerts are off until asked for, and stay silent until then', async ({ page, request }) => {
  const { clipRequests } = await instrument(page);
  await page.goto('/');
  await expect(control(page)).toBeVisible();
  expect(await alertState(page)).toMatchObject({ enabled: false });

  await emit(request, STATIC_CLIP);
  await page.waitForTimeout(800);
  expect(clipRequests).toEqual([]);
});

test('enabling confirms audibly, then plays what the device announces', async ({ page, request }) => {
  const { clipRequests, pageErrors } = await instrument(page);
  await page.goto('/');
  await control(page).locator('.toggle').click();

  // The confirmation tone doubles as a check that the right output device is
  // selected, so enabling must make a sound of its own.
  await expect.poll(() => page.evaluate(() => window.__playAttempts)).toContain('generated-tone');
  expect(await alertState(page)).toMatchObject({ enabled: true, blocked: false });

  await emit(request, STATIC_CLIP);
  await expect.poll(() => playedClips(page)).toEqual([STATIC_CLIP]);
  expect(clipRequests).toEqual([STATIC_CLIP]);
  expect(pageErrors).toEqual([]);
});

test('a repeated clip is played from cache without fetching it again', async ({ page, request }) => {
  // This is the payoff of content-addressed clip URLs: the utterance pool is
  // fixed, so most of what plays has played before.
  const { clipRequests } = await instrument(page);
  await page.goto('/');
  await control(page).locator('.toggle').click();
  await page.waitForTimeout(400);

  for (let i = 0; i < 3; i++) {
    await emit(request, STATIC_CLIP);
    await page.waitForTimeout(900);
  }

  await expect.poll(() => playedClips(page)).toEqual([STATIC_CLIP, STATIC_CLIP, STATIC_CLIP]);
  expect(clipRequests).toEqual([STATIC_CLIP]);
});

test('a burst of alerts is queued and played one at a time', async ({ page, request }) => {
  await instrument(page);
  await page.goto('/');
  await control(page).locator('.toggle').click();
  await page.waitForTimeout(400);

  // Spaced wider than sup's batch_update_interval_sec (0.2s by default) but
  // closer together than the clips are long, so the player really does have to
  // queue. Updates landing inside a single batch window would collapse --- the
  // batcher sends each property's current state once per batch, not every
  // value it passed through --- which the real device cannot provoke, since it
  // sleeps for the length of each clip before announcing the next one.
  for (const clip of [STATIC_CLIP, OTHER_CLIP, TEMP_CLIP]) {
    await emit(request, clip);
    await page.waitForTimeout(300);
  }

  await expect.poll(() => playedClips(page), { timeout: 10000 })
    .toEqual([STATIC_CLIP, OTHER_CLIP, TEMP_CLIP]);
});

test('turning alerts off silences them again', async ({ page, request }) => {
  const { clipRequests } = await instrument(page);
  await page.goto('/');
  await control(page).locator('.toggle').click();
  await page.waitForTimeout(400);
  await emit(request, STATIC_CLIP);
  await expect.poll(() => playedClips(page)).toEqual([STATIC_CLIP]);

  await control(page).locator('.toggle').click();
  expect(await alertState(page)).toMatchObject({ enabled: false });

  await emit(request, OTHER_CLIP);
  await page.waitForTimeout(800);
  expect(clipRequests).toEqual([STATIC_CLIP]);
  expect(await playedClips(page)).toEqual([STATIC_CLIP]);
});

test('an alert that arrived while alerts were off is not replayed on enabling', async ({ page, request }) => {
  // The device leaves the last utterance sitting in the property and INDI
  // re-sends it on connect, so "newest value" is not the same as "news".
  const { clipRequests } = await instrument(page);
  await page.goto('/');
  await expect(control(page)).toBeVisible();
  await emit(request, OTHER_CLIP);
  await page.waitForTimeout(600);

  await control(page).locator('.toggle').click();
  await page.waitForTimeout(800);
  expect(clipRequests).toEqual([]);
});

test('a fresh page does not blurt out the utterance already in the property', async ({ page, request }) => {
  await emit(request, OTHER_CLIP);
  const { clipRequests } = await instrument(page);
  await page.goto('/');
  await control(page).locator('.toggle').click();
  await page.waitForTimeout(800);
  // The clip named in the property on arrival is history, not news.
  expect(clipRequests).toEqual([]);
});

test.describe('across a reload', () => {
  test('the opt-in is remembered', async ({ page }) => {
    await instrument(page);
    await page.goto('/');
    await control(page).locator('.toggle').click();
    await page.waitForTimeout(400);

    await page.reload();
    await expect(control(page)).toBeVisible();
    expect(await alertState(page)).toMatchObject({ enabled: true });
  });

  test('alerts resume by themselves where the browser allows audio', async ({ page, request }, testInfo) => {
    test.skip(!testInfo.project.metadata.autoplayAllowed,
      'needs a browser that allows audio without an interaction');
    await instrument(page);
    await page.goto('/');
    await control(page).locator('.toggle').click();
    await page.waitForTimeout(400);

    await page.reload();
    await expect(control(page)).toBeVisible();
    expect(await alertState(page)).toMatchObject({ enabled: true, blocked: false });

    await emit(request, STATIC_CLIP);
    await expect.poll(() => playedClips(page)).toEqual([STATIC_CLIP]);
  });

  test('the control reports when the browser is withholding audio', async ({ page }, testInfo) => {
    test.skip(testInfo.project.metadata.autoplayAllowed,
      'only meaningful where audio needs an interaction first');
    await instrument(page);
    await page.goto('/');
    await control(page).locator('.toggle').click();
    await page.waitForTimeout(400);

    await page.reload();
    await expect(control(page)).toBeVisible();
    // The silent probe should have found out before any alert depended on it.
    await expect.poll(() => alertState(page).then((s) => s.blocked)).toBe(true);
    await expect(control(page).locator('.needs-permission')).toBeVisible();
  });

  test('clicking the speaker recovers from a withheld-audio state', async ({ page, request }, testInfo) => {
    test.skip(testInfo.project.metadata.autoplayAllowed,
      'only meaningful where audio needs an interaction first');
    await instrument(page);
    await page.goto('/');
    await control(page).locator('.toggle').click();
    await page.waitForTimeout(400);
    await page.reload();
    await expect.poll(() => alertState(page).then((s) => s.blocked)).toBe(true);

    await control(page).locator('button').click();
    await expect.poll(() => alertState(page).then((s) => s.blocked)).toBe(false);

    await emit(request, STATIC_CLIP);
    await expect.poll(() => playedClips(page)).toEqual([STATIC_CLIP]);
  });
});
