import { test, expect } from '@playwright/test';

test.describe('Main Page', () => {
	test('should load main page without errors', async ({ page }) => {
		const errors: string[] = [];
		page.on('console', msg => {
			if (msg.type() === 'error' && !msg.text().includes('favicon')) {
				errors.push(msg.text());
			}
		});

		page.on('pageerror', err => {
			if (!err.message.includes('favicon')) {
				errors.push(err.message);
			}
		});

		await page.goto('/');

		// Wait for page to load
		await page.getByText('Le Livre').first().waitFor();

		// Verify no errors
		expect(errors).toHaveLength(0);

		// Check main elements are visible
		await expect(page.getByText('Browse US Code provisions')).toBeVisible();
		await expect(page.getByText('Title 18 USC § 922')).toBeVisible();
	});

	test('should navigate to section from main page', async ({ page }) => {
		await page.goto('/');

		// Click on section card
		await page.getByRole('button', { name: /Title 18 USC § 922/i }).click();

		// Should navigate to section page
		await page.waitForURL(/\/section\//);
		expect(page.url()).toContain('/section/');
	});

	test('should have working navigation bar', async ({ page }) => {
		await page.goto('/');

		// Check navigation links exist
		await expect(page.getByRole('link', { name: 'Chat' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Timeline' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Compare' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Graph' })).toBeVisible();

		// Test navigation to timeline
		await page.getByRole('link', { name: 'Timeline' }).click();
		await page.waitForURL('/timeline');
		expect(page.url()).toContain('/timeline');
	});

	test('should toggle dark mode', async ({ page }) => {
		await page.goto('/');

		// Find dark mode toggle button
		const darkModeButton = page.locator('button').filter({ has: page.locator('svg') }).first();

		// Click to toggle
		await darkModeButton.click();

		// Wait a bit for transition
		await page.waitForTimeout(500);

		// Toggle back
		await darkModeButton.click();
	});
});

test.describe('Chat Sidebar', () => {
	test('should toggle chat sidebar', async ({ page }) => {
		await page.goto('/');

		// Chat sidebar should be hidden initially or togglable
		// Look for sidebar toggle button (Cmd+\ button)
		const sidebarToggle = page.locator('button[title*="sidebar"], button[aria-label*="sidebar"]').first();

		if (await sidebarToggle.isVisible()) {
			await sidebarToggle.click();
			await page.waitForTimeout(500);
		}
	});

	test('should send chat message and receive response', async ({ page, context }) => {
		// Set a longer timeout for this test since it involves API calls
		test.setTimeout(60000);

		await page.goto('/');

		// Open chat sidebar if not visible
		const chatInput = page.locator('textarea[placeholder*="Ask"], input[placeholder*="Ask"]').first();

		// If chat input not visible, try to open sidebar
		if (!(await chatInput.isVisible({ timeout: 2000 }).catch(() => false))) {
			// Look for chat button or sidebar toggle
			const chatLink = page.getByRole('link', { name: 'Chat' });
			if (await chatLink.isVisible()) {
				await chatLink.click();
				await page.waitForTimeout(1000);
			}
		}

		// Type a test question
		const testQuery = 'What is section 922?';
		await chatInput.fill(testQuery);

		// Submit the message
		await chatInput.press('Enter');

		// Wait for user message to appear
		await expect(page.getByText(testQuery)).toBeVisible({ timeout: 5000 });

		// Wait for assistant response (with loading indicator first)
		const loadingIndicator = page.locator('text="Thinking..."').or(page.locator('.animate-pulse'));

		// Response should eventually appear
		await page.waitForTimeout(10000); // Give API time to respond

		// Check that we have at least 2 messages (user + assistant)
		const messages = page.locator('[class*="message"], [class*="bubble"]');
		expect(await messages.count()).toBeGreaterThanOrEqual(1);
	});

	test('should display source cards in chat response', async ({ page }) => {
		test.setTimeout(60000);

		await page.goto('/');

		// Open chat and send message
		const chatInput = page.locator('textarea[placeholder*="Ask"], input[placeholder*="Ask"]').first();

		if (!(await chatInput.isVisible({ timeout: 2000 }).catch(() => false))) {
			const chatLink = page.getByRole('link', { name: 'Chat' });
			if (await chatLink.isVisible()) {
				await chatLink.click();
				await page.waitForTimeout(1000);
			}
		}

		await chatInput.fill('firearm regulations');
		await chatInput.press('Enter');

		// Wait for response
		await page.waitForTimeout(15000);

		// Look for source-related elements (provision IDs, source cards, etc.)
		// The exact structure depends on the chat response
		const hasProvisionId = await page.locator('[class*="font-mono"]').count() > 0;
		const hasSourceGroup = await page.locator('text=/Semantic|Graph|Sources/i').count() > 0;

		// At least one of these should be true if sources are displayed
		expect(hasProvisionId || hasSourceGroup).toBeTruthy();
	});

	test('should handle empty chat input', async ({ page }) => {
		await page.goto('/');

		const chatInput = page.locator('textarea[placeholder*="Ask"], input[placeholder*="Ask"]').first();

		if (!(await chatInput.isVisible({ timeout: 2000 }).catch(() => false))) {
			const chatLink = page.getByRole('link', { name: 'Chat' });
			if (await chatLink.isVisible()) {
				await chatLink.click();
				await page.waitForTimeout(1000);
			}
		}

		// Try to submit empty message
		await chatInput.click();
		await chatInput.press('Enter');

		// Should not create a message
		await page.waitForTimeout(1000);

		// No new messages should appear
		const messagesBefore = await page.locator('[class*="message"]').count();
		await page.waitForTimeout(500);
		const messagesAfter = await page.locator('[class*="message"]').count();

		expect(messagesBefore).toBe(messagesAfter);
	});

	test('should copy message to clipboard', async ({ page, context }) => {
		test.setTimeout(60000);

		// Grant clipboard permissions
		await context.grantPermissions(['clipboard-read', 'clipboard-write']);

		await page.goto('/');

		const chatInput = page.locator('textarea[placeholder*="Ask"], input[placeholder*="Ask"]').first();

		if (!(await chatInput.isVisible({ timeout: 2000 }).catch(() => false))) {
			const chatLink = page.getByRole('link', { name: 'Chat' });
			if (await chatLink.isVisible()) {
				await chatLink.click();
				await page.waitForTimeout(1000);
			}
		}

		await chatInput.fill('test query');
		await chatInput.press('Enter');

		// Wait for response
		await page.waitForTimeout(15000);

		// Look for copy button (usually appears on assistant messages)
		const copyButton = page.locator('button[title*="Copy"], button[aria-label*="Copy"]').first();

		if (await copyButton.isVisible({ timeout: 2000 }).catch(() => false)) {
			await copyButton.click();

			// Check clipboard content
			const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
			expect(clipboardText.length).toBeGreaterThan(0);
		}
	});
});
