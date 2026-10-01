import {test, expect} from '@playwright/test';

test('Supabase sign-in fixture rejects invalid credentials without opening the workspace', async ({page}) => {
  await page.route('**/api/v1/config', route => route.fulfill({json: {
    auth_mode: 'supabase', supabase_url: 'https://test.supabase.co',
    supabase_publishable_key: 'public-fixture-key', demo_enabled: false,
  }}));
  await page.route('https://test.supabase.co/**', route => route.fulfill({status: 400, json: {
    error_code: 'invalid_credentials', msg: 'Invalid login credentials',
  }}));
  await page.goto('/workspace');
  await expect(page.getByRole('heading', {name: 'Your packing workspace.'})).toBeVisible();
  await page.getByLabel('Email', {exact: true}).fill('software-test@example.invalid');
  await page.getByLabel('Password', {exact: true}).fill('not-a-real-password');
  await page.getByRole('button', {name: 'Sign in', exact: true}).click();
  await expect(page.getByRole('alert')).toContainText('Unable to sign in');
  await expect(page.getByLabel('Password', {exact: true})).toHaveValue('');
  await expect(page.getByRole('button', {name: 'Sign out', exact: true})).toHaveCount(0);
});
