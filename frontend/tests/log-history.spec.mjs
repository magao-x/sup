// End-to-end coverage for the log viewer on the observation page, and the
// history behind it.
//
// The viewer filters by level, so history is kept per level, both by sup (for
// pages that load later) and by the page itself (as messages keep arriving).
// sup runs here with log_history_per_level=5 (see playwright.config.mjs).
import { test, expect } from '@playwright/test';
import { ports } from '../playwright.config.mjs';

const CONTROL = `http://127.0.0.1:${ports.CONTROL_PORT}`;
const PER_LEVEL = 5;
const LEVELS = ['EMER', 'ALRT', 'CRIT', 'ERR', 'WARN', 'NOTE', 'INFO'];

/** Have the fake device send an INDI log message. */
async function sendLog(request, text) {
  const response = await request.post(`${CONTROL}/log?text=${encodeURIComponent(text)}`);
  expect(response.ok()).toBeTruthy();
}

/** Tick exactly these level filters in the viewer. */
async function showOnly(page, levels) {
  for (const level of LEVELS) {
    await page.locator(`.levels input[id="${level}"]`).setChecked(levels.includes(level));
  }
}

// Messages from earlier tests (and the other project's run) stay in sup's
// history, so each test tags its own and reads back only those: the message
// text of each row the viewer shows, as it shows them, newest first.
const shown = (page, tag) => page.locator('.logs .short tbody tr td.msg').allTextContents()
  .then((texts) => texts.map((t) => t.trim()).filter((t) => t.includes(tag)));

test('a page that loads later shows the history', async ({ page, request }) => {
  const tag = `load-${Date.now()}`;
  await sendLog(request, `WARN ${tag} earlier warning`);
  await sendLog(request, `INFO ${tag} earlier info`);
  // Into the history once a batch has carried them out
  await page.waitForTimeout(600);

  await page.goto('/');
  await expect.poll(() => shown(page, tag)).toEqual([
    `${tag} earlier info`,
    `${tag} earlier warning`,
  ]);
  await showOnly(page, ['WARN']);
  await expect.poll(() => shown(page, tag)).toEqual([`${tag} earlier warning`]);
});

test('filtering to a quiet level still finds its messages after a flood at another', async ({ page, request }) => {
  const tag = `flood-${Date.now()}`;
  await sendLog(request, `ERR  ${tag} the only error`);
  for (let i = 0; i < 3 * PER_LEVEL; i++) {
    await sendLog(request, `INFO ${tag} chatter ${i}`);
  }
  await page.waitForTimeout(600);

  await page.goto('/');
  await showOnly(page, ['ERR']);
  await expect.poll(() => shown(page, tag)).toEqual([`${tag} the only error`]);
  await showOnly(page, ['INFO']);
  const newestInfo = (prefix, from) =>
    Array.from({ length: PER_LEVEL }, (_, k) => `${tag} ${prefix} ${from + PER_LEVEL - 1 - k}`);
  await expect.poll(() => shown(page, tag)).toEqual(newestInfo('chatter', 2 * PER_LEVEL));

  // And the page keeps them per level too, as more arrive while it's open.
  for (let i = 0; i < 2 * PER_LEVEL; i++) {
    await sendLog(request, `INFO ${tag} later ${i}`);
  }
  await expect.poll(() => shown(page, tag)).toEqual(newestInfo('later', PER_LEVEL));
  await showOnly(page, ['ERR']);
  await expect.poll(() => shown(page, tag)).toEqual([`${tag} the only error`]);
});

test('a reconnect does not repeat what the page already showed', async ({ page, request }) => {
  const tag = `reconnect-${Date.now()}`;
  await page.goto('/');
  await sendLog(request, `NOTE ${tag} before the drop`);
  await expect.poll(() => shown(page, tag)).toEqual([`${tag} before the drop`]);

  // Drop the websocket; the page reconnects on its own and is sent the history.
  await page.evaluate(() => document.querySelector('#app')._vnode.component.proxy.ws.close());
  await sendLog(request, `NOTE ${tag} while away`);
  await expect.poll(() => shown(page, tag), { timeout: 10000 }).toEqual([
    `${tag} while away`,
    `${tag} before the drop`,
  ]);
});
