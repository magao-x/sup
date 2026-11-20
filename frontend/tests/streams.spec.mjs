// End-to-end coverage for the streams tab, which lists what sup can stream
// and opens each in a camera window of its own.
//
// sup runs here with the rtimv configs in tests/fixtures/rtimv and no shmims
// (see playwright.config.mjs), so it lists exactly camsim, camwfs and dm00disp.
import { test, expect } from '@playwright/test';

test('lists the streams the rtimv configs define, with their darks and masks', async ({ page }) => {
  await page.goto('/streams');
  const rows = page.locator('.listing tbody tr');
  await expect(rows).toHaveCount(3);
  await expect(rows.nth(1)).toContainText('camwfs');
  await expect(rows.nth(1)).toContainText('camwfs_dark');
  await expect(rows.nth(1)).toContainText('16383');
  await expect(rows.nth(2)).toContainText('dm00disp00');
  await expect(rows.nth(2)).toContainText('dm00dispST');

  await page.locator('.filter').fill('dm');
  await expect(rows).toHaveCount(1);
  await expect(page.locator('.streams-header .count')).toHaveText('1 of 3 streams');
});

test('clicking a stream opens it in a popup with only the camera in it', async ({ page }) => {
  await page.goto('/streams');
  const [popup] = await Promise.all([
    page.waitForEvent('popup'),
    page.getByRole('link', { name: 'dm00disp' }).click(),
  ]);
  const url = new URL(popup.url());
  expect(url.pathname).toBe('/camera.html');
  expect(url.searchParams.get('name')).toBe('dm00disp');
  expect(url.searchParams.get('popup')).toBe('1');
  await expect(popup.locator('.feed-name').first()).toHaveText('dm00disp');
  await expect(popup.locator('.viewer-toolbar')).toHaveCount(0);
  await expect(page.locator('.blocked-hint')).toHaveCount(0);
});

test('a blocked popup says how to allow it, and offers a tab instead', async ({ page }) => {
  // What window.open returns when the browser blocks the window.
  await page.addInitScript(() => { window.open = () => null; });
  await page.goto('/streams');
  await page.getByRole('link', { name: 'camwfs' }).click();
  const hint = page.locator('.blocked-hint');
  await expect(hint).toContainText('allow pop-ups for this site');
  await expect(hint.getByRole('link')).toHaveAttribute('href', /\/camera\.html\?name=camwfs$/);
  await hint.locator('.dismiss').click();
  await expect(hint).toHaveCount(0);
});

test('the camera page outside a popup takes companions from the catalog', async ({ page }) => {
  await page.goto('/camera.html?name=camwfs');
  await expect(page.locator('.viewer-toolbar')).toBeVisible();
  await expect(page.locator('#known-streams option')).toHaveCount(3);
});

/** The viewcam feeds a page opens, by stream name. */
function feedsOf(page) {
  const names = [];
  page.on('websocket', (ws) => {
    const match = ws.url().match(/\/ws\/viewcam\/(.+)$/);
    if (match) names.push(decodeURIComponent(match[1]));
  });
  return names;
}

test('a camera opens the dark and mask its rtimv config names', async ({ page }) => {
  const feeds = feedsOf(page);
  await page.goto('/camera.html?name=dm00disp');
  await expect.poll(() => feeds.slice().sort()).toEqual(['dm00disp', 'dm00disp00', 'dm00dispST']);
});

test('a stream without an rtimv config opens no dark or mask', async ({ page }) => {
  const feeds = feedsOf(page);
  await page.goto('/camera.html?name=acc000_psds');
  await expect.poll(() => feeds).toEqual(['acc000_psds']);
  // Give any stray feeds time to open.
  await page.waitForTimeout(500);
  expect(feeds).toEqual(['acc000_psds']);
});

/** The window of each ack a page sends on a feed, as they go. */
function windowsSentOn(page, name) {
  const windows = [];
  page.on('websocket', (ws) => {
    if (!ws.url().endsWith(`/ws/viewcam/${name}`)) return;
    ws.on('framesent', ({ payload }) => {
      if (typeof payload !== 'string') windows.push(payload.readUInt32LE(24));
    });
  });
  return windows;
}

test('a camera starts capped at one frame a second, and turbo lifts the cap', async ({ page }) => {
  const windows = windowsSentOn(page, 'camwfs');
  await page.goto('/camera.html?name=camwfs');
  // Acks for the opening and for the "no image" frame, as there's no shmim here.
  await expect.poll(() => windows.length).toBeGreaterThan(0);
  expect(new Set(windows)).toEqual(new Set([1]));
  const turbo = page.getByRole('button', { name: 'turbo off' });
  await turbo.click();
  await expect(page.getByRole('button', { name: 'turbo on' })).toBeVisible();
  await expect.poll(() => windows.at(-1)).toBe(6);
  await page.getByRole('button', { name: 'turbo on' }).click();
  await expect.poll(() => windows.at(-1)).toBe(1);
});
