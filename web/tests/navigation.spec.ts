import { test, expect } from '@playwright/test';
import { resetFixtureDb } from './helpers/seed.js';

test.beforeEach(() => resetFixtureDb());

// ─── Global nav ───────────────────────────────────────────────────────────────

test.describe('Global nav — desktop', () => {
  test('shows EARMARK wordmark linking to /accounts', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.goto('/accounts');
    const wordmark = page.getByRole('link', { name: 'EARMARK' });
    await expect(wordmark).toBeVisible();
    await expect(wordmark).toHaveAttribute('href', '/accounts');
  });

  test('shows Accounts link as active on accounts pages', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.goto('/accounts');
    const link = page.getByRole('navigation', { name: 'Global' }).getByRole('link', { name: 'Accounts' });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('aria-current', 'page');
  });

  test('shows Settings link', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.goto('/accounts');
    await expect(page.getByRole('navigation', { name: 'Global' }).getByRole('link', { name: 'Settings' })).toBeVisible();
  });

  test('hamburger button is hidden on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.goto('/accounts');
    await expect(page.getByRole('button', { name: 'Open menu' })).toBeHidden();
  });
});

test.describe('Global nav — mobile', () => {
  // The Earmark header is a fixed 440px mobile frame with inline nav — there is
  // no hamburger; the two short links always show.
  test('shows inline nav links on mobile (no hamburger)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/accounts');
    const nav = page.getByRole('navigation', { name: 'Global' });
    await expect(nav).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Accounts' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Open menu' })).toHaveCount(0);
  });

  test('shows EARMARK wordmark on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/accounts');
    const wordmark = page.getByRole('link', { name: 'EARMARK' });
    await expect(wordmark).toBeVisible();
    await expect(wordmark).toHaveAttribute('href', '/accounts');
  });
});

// ─── Account tab bar ──────────────────────────────────────────────────────────

test.describe('Account tab bar', () => {
  test('shows account name on account page', async ({ page }) => {
    await page.goto('/accounts');
    await page.getByTestId('account-card').first().click();
    await expect(page.getByTestId('account-tab-bar')).toBeVisible();
    await expect(page.getByTestId('account-tab-bar')).toContainText('Personal');
  });

  test('Envelopes tab is active on account page', async ({ page }) => {
    await page.goto('/accounts');
    await page.getByTestId('account-card').first().click();
    await expect(page.getByTestId('tab-envelopes')).toHaveAttribute('aria-current', 'page');
  });
});
