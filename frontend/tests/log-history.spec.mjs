// End-to-end coverage for the log history the browser keeps for the log viewer.
//
// The viewer filters by level, so history is kept per level, both by sup (for
// pages that load later) and by the page itself (as messages keep arriving).
// sup runs here with log_history_per_level=5 (see playwright.config.mjs). The
// viewer itself is only on screen once the telescope reports in, which the
// fake device doesn't, so these check the logs the viewer filters rather than
// the rendered table.
import { test, expect } from '@playwright/test';
import { ports } from '../playwright.config.mjs';

const CONTROL = `http://127.0.0.1:${ports.CONTROL_PORT}`;
const PER_LEVEL = 5;

/** Have the fake device send an INDI log message. */
async function sendLog(request, text) {
  const response = await request.post(`${CONTROL}/log?text=${encodeURIComponent(text)}`);
  expect(response.ok()).toBeTruthy();
}

const keptLogs = (page) => page.evaluate(
  () => document.querySelector('#app')._vnode.component.proxy.systemLogs.map((l) => l.message)
);

// Messages from earlier tests (and the other project's run) stay in sup's
// history, so each test tags its own and looks only at those.
const tagged = (logs, tag) => logs.filter((m) => m.includes(tag));

test('a page that loads later is sent the history', async ({ page, request }) => {
  const tag = `load-${Date.now()}`;
  await sendLog(request, `WARN  ${tag} earlier warning`);
  await sendLog(request, `INFO ${tag} earlier info`);
  // Into the history once a batch has carried them out
  await page.waitForTimeout(600);

  await page.goto('/');
  await expect.poll(async () => tagged(await keptLogs(page), tag)).toEqual([
    `WARN  ${tag} earlier warning`,
    `INFO ${tag} earlier info`,
  ]);
});

test('a flood at one level does not push out the others', async ({ page, request }) => {
  const tag = `flood-${Date.now()}`;
  await sendLog(request, `ERR  ${tag} the only error`);
  for (let i = 0; i < 3 * PER_LEVEL; i++) {
    await sendLog(request, `INFO ${tag} chatter ${i}`);
  }
  await page.waitForTimeout(600);

  await page.goto('/');
  const expected = [
    `ERR  ${tag} the only error`,
    ...Array.from({ length: PER_LEVEL }, (_, k) => `INFO ${tag} chatter ${2 * PER_LEVEL + k}`),
  ];
  await expect.poll(async () => tagged(await keptLogs(page), tag)).toEqual(expected);

  // And the page keeps them per level too, as more arrive while it's open.
  for (let i = 0; i < 2 * PER_LEVEL; i++) {
    await sendLog(request, `INFO ${tag} later ${i}`);
  }
  await expect.poll(async () => tagged(await keptLogs(page), tag)).toEqual([
    `ERR  ${tag} the only error`,
    ...Array.from({ length: PER_LEVEL }, (_, k) => `INFO ${tag} later ${PER_LEVEL + k}`),
  ]);
});

test('a reconnect does not repeat what the page already had', async ({ page, request }) => {
  const tag = `reconnect-${Date.now()}`;
  await page.goto('/');
  await sendLog(request, `NOTE ${tag} before the drop`);
  await expect.poll(async () => tagged(await keptLogs(page), tag)).toEqual([`NOTE ${tag} before the drop`]);

  // Drop the websocket; the page reconnects on its own and is sent the history.
  await page.evaluate(() => document.querySelector('#app')._vnode.component.proxy.ws.close());
  await sendLog(request, `NOTE ${tag} while away`);
  await expect.poll(async () => tagged(await keptLogs(page), tag), { timeout: 10000 }).toEqual([
    `NOTE ${tag} before the drop`,
    `NOTE ${tag} while away`,
  ]);
});
