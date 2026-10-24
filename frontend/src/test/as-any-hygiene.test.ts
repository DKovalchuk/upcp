import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * `as any` budget enforcement — TASK-0155 (parent TASK-0097 AC §6.9:
 * "as any count in test files reduced by >=80%").
 *
 * Baseline at audit 2026-10-24/25: 90 occurrences in 15 test files.
 * Budgets: tests <= 18 (>=80% reduction); production src <= 4 (the
 * documented TanStack-router search escapes in use-filters.ts and
 * ProjectSelector.tsx — see TASK-0155; tighten to 0 if typed).
 *
 * This file is excluded from the scan (it names the needle).
 * Path base: vitest runs with cwd = frontend/ (import.meta.url is not
 * a file: scheme under the jsdom environment).
 */

const SRC_DIR = join(process.cwd(), 'src');
const SELF = 'as-any-hygiene.test.ts';

const TEST_BUDGET = 18;
const PROD_BUDGET = 4;

const NEEDLE = 'as any';

interface Counts {
  testFiles: number;
  production: number;
  perFile: Record<string, number>;
}

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...walk(path));
    } else if (/\.(ts|tsx)$/.test(entry.name)) {
      out.push(path);
    }
  }
  return out;
}

function isTestPath(path: string): boolean {
  return /\.test\.(ts|tsx)$/.test(path) || path.includes(`${'__'}tests__`);
}

function countOccurrences(): Counts {
  const counts: Counts = { testFiles: 0, production: 0, perFile: {} };
  for (const path of walk(SRC_DIR)) {
    if (path.endsWith(SELF)) continue;
    const hits = readFileSync(path, 'utf-8').split(NEEDLE).length - 1;
    if (hits === 0) continue;
    const relative = path.slice(SRC_DIR.length);
    counts.perFile[relative] = hits;
    if (isTestPath(path)) counts.testFiles += hits;
    else counts.production += hits;
  }
  return counts;
}

describe('as any hygiene budget (TASK-0155)', () => {
  it(`test files stay within budget (<={TEST_BUDGET}, was 90 at audit)`, () => {
    const { testFiles, perFile } = countOccurrences();
    expect(
      testFiles,
      `test-file "as any" count ${testFiles} exceeds budget ${TEST_BUDGET}; ` +
        `offenders: ${JSON.stringify(perFile, null, 2)}`
    ).toBeLessThanOrEqual(TEST_BUDGET);
  });

  it(`production src stays within documented budget (<={PROD_BUDGET})`, () => {
    const { production, perFile } = countOccurrences();
    expect(
      production,
      `production "as any" count ${production} exceeds budget ${PROD_BUDGET}; ` +
        `offenders: ${JSON.stringify(perFile, null, 2)}`
    ).toBeLessThanOrEqual(PROD_BUDGET);
  });
});
