// Build the frontend before the suite runs.
//
// These tests drive a real sup, which serves the *built* assets out of
// sup/static/. Without this, editing a component and running the tests would
// silently exercise whatever was built last --- which looks exactly like a
// passing or failing test about the new code, and is neither.
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export default function build() {
  const frontend = fileURLToPath(new URL('..', import.meta.url));
  process.stdout.write('Building frontend so the tests run against current source...\n');
  execFileSync('npm', ['run', 'build'], { cwd: frontend, stdio: 'inherit' });
}
