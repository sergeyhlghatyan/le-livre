import { test, expect } from '@playwright/test';

test.describe('Provision Page', () => {
	test('should load provision without errors', async ({ page }) => {
		// Collect console errors
		const errors: string[] = [];
		page.on('console', msg => {
			if (msg.type() === 'error' && !msg.text().includes('favicon')) {
				errors.push(msg.text());
			}
		});

		// Collect page errors
		const pageErrors: string[] = [];
		page.on('pageerror', err => {
			if (!err.message.includes('favicon')) {
				pageErrors.push(err.message);
			}
		});

		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024');

		// Wait for content to load - check for provision ID which always appears
		await page.getByText('/us/usc/t18/s922/a').first().waitFor({ timeout: 30000 });

		// Verify no TypeError errors (especially truncateText)
		const truncateErrors = [...errors, ...pageErrors].filter(e =>
			e.includes('truncateText') || e.includes('Cannot read properties of undefined')
		);
		expect(truncateErrors).toHaveLength(0);

		// Check Overview tab exists and is active
		const overviewTab = page.getByRole('tab', { name: 'Overview' });
		await expect(overviewTab).toBeVisible();
		await expect(overviewTab).toHaveAttribute('aria-selected', 'true');
	});

	test('should navigate between tabs', async ({ page }) => {
		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024');

		// Wait for initial load
		await page.waitForSelector('h1');

		// Overview tab should be active by default
		await expect(page.getByRole('tab', { name: 'Overview' })).toHaveAttribute('aria-selected', 'true');

		// Click Timeline tab
		await page.getByRole('tab', { name: 'Timeline' }).click();
		await expect(page.getByRole('tab', { name: 'Timeline' })).toHaveAttribute('aria-selected', 'true');

		// Click Relations tab
		await page.getByRole('tab', { name: 'Relations' }).click();
		await expect(page.getByRole('tab', { name: 'Relations' })).toHaveAttribute('aria-selected', 'true');

		// Click Changes tab
		await page.getByRole('tab', { name: 'Changes' }).click();
		await expect(page.getByRole('tab', { name: 'Changes' })).toHaveAttribute('aria-selected', 'true');

		// Click Impact tab
		await page.getByRole('tab', { name: 'Impact' }).click();
		await expect(page.getByRole('tab', { name: 'Impact' })).toHaveAttribute('aria-selected', 'true');

		// Click Constellation tab
		await page.getByRole('tab', { name: 'Constellation' }).click();
		await expect(page.getByRole('tab', { name: 'Constellation' })).toHaveAttribute('aria-selected', 'true');

		// Click Insights tab
		await page.getByRole('tab', { name: 'Insights' }).click();
		await expect(page.getByRole('tab', { name: 'Insights' })).toHaveAttribute('aria-selected', 'true');
	});

	test('should handle Relations tab with null text_content gracefully', async ({ page }) => {
		// Track errors
		const truncateErrors: string[] = [];
		page.on('pageerror', err => {
			if (err.message.includes('truncateText') || err.message.includes('Cannot read properties of undefined')) {
				truncateErrors.push(err.message);
			}
		});

		page.on('console', msg => {
			if (msg.type() === 'error' && !msg.text().includes('favicon')) {
				const text = msg.text();
				if (text.includes('truncateText') || text.includes('Cannot read properties of undefined')) {
					truncateErrors.push(text);
				}
			}
		});

		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024');

		// Wait for page to load
		await page.getByText('/us/usc/t18/s922/a').first().first().waitFor();

		// Click Relations tab
		await page.getByRole('tab', { name: 'Relations' }).click();

		// Wait for Relations tab to be active
		await expect(page.getByRole('tab', { name: 'Relations' })).toHaveAttribute('aria-selected', 'true');

		// Wait a bit for content to render
		await page.waitForTimeout(1000);

		// Verify no truncateText errors occurred
		expect(truncateErrors).toHaveLength(0);
	});

	test('should display provision metadata', async ({ page }) => {
		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024');

		// Wait for page load
		await page.getByText('/us/usc/t18/s922/a').first().first().waitFor();

		// Check that provision ID is displayed
		await expect(page.getByText('/us/usc/t18/s922/a').first()).toBeVisible();

		// Check year is displayed
		await expect(page.locator('text=2024')).toBeVisible();
	});

	test('should display current year', async ({ page }) => {
		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024');

		// Wait for page load
		await page.getByText('/us/usc/t18/s922/a').first().first().waitFor();

		// Check year is displayed in the URL and page
		expect(page.url()).toContain('year=2024');
		await expect(page.locator('text=2024')).toBeVisible();
	});

	test('should show Timeline tab', async ({ page }) => {
		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024');

		// Wait for page to load
		await page.getByText('/us/usc/t18/s922/a').first().first().waitFor();

		// Click Timeline tab
		await page.getByRole('tab', { name: 'Timeline' }).click();

		// Verify Timeline tab is now active
		await expect(page.getByRole('tab', { name: 'Timeline' })).toHaveAttribute('aria-selected', 'true');

		// Wait for content
		await page.waitForTimeout(1000);
	});

	test('should show Changes tab', async ({ page }) => {
		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024');

		// Wait for page to load
		await page.getByText('/us/usc/t18/s922/a').first().first().waitFor();

		// Click Changes tab
		await page.getByRole('tab', { name: 'Changes' }).click();

		// Verify Changes tab is now active
		await expect(page.getByRole('tab', { name: 'Changes' })).toHaveAttribute('aria-selected', 'true');

		// Wait for content
		await page.waitForTimeout(1000);
	});

	test('should handle missing provision gracefully', async ({ page }) => {
		// Navigate to non-existent provision
		await page.goto('/provision/invalid-provision-id?year=2024');

		// Should show error message or redirect, not crash
		await page.waitForLoadState('networkidle');

		// Page should not have JavaScript errors
		const errors: string[] = [];
		page.on('pageerror', err => errors.push(err.message));

		await page.waitForTimeout(1000);

		// Should handle gracefully without runtime errors
		expect(errors.filter(e => !e.includes('favicon'))).toHaveLength(0);
	});
});
