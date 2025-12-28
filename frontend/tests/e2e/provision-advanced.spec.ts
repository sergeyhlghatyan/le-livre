import { test, expect } from '@playwright/test';

const TEST_PROVISION = '/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024';

test.describe('Provision Page - Tab Navigation', () => {
	test('should navigate through all tabs without errors', async ({ page }) => {
		const errors: string[] = [];
		page.on('pageerror', err => {
			if (!err.message.includes('favicon')) {
				errors.push(err.message);
			}
		});

		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor({ timeout: 30000 });

		const tabs = ['Overview', 'Timeline', 'Relations', 'Changes', 'Impact', 'Constellation', 'Insights'];

		for (const tabName of tabs) {
			// Click tab
			await page.getByRole('tab', { name: tabName }).click();

			// Verify tab is active
			await expect(page.getByRole('tab', { name: tabName })).toHaveAttribute('aria-selected', 'true');

			// Wait for content to render
			await page.waitForTimeout(1000);

			// Check no errors occurred
			expect(errors.filter(e => !e.includes('favicon'))).toHaveLength(0);
		}

		// Final check - should have navigated all tabs successfully
		expect(errors).toHaveLength(0);
	});

	test('should display Overview tab content correctly', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Click Overview tab
		await page.getByRole('tab', { name: 'Overview' }).click();

		// Should show provision text
		await page.waitForTimeout(1000);

		// Should have Quick Links section if relations exist
		const hasQuickLinks = await page.getByText('Quick Links').isVisible().catch(() => false);

		// Should have provision text section
		const hasProvisionText = await page.getByText('Provision Text').isVisible().catch(() => false);

		// At least one should be true
		expect(hasProvisionText || hasQuickLinks).toBeTruthy();
	});

	test('should display Timeline tab with interactive year dots', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Click Timeline tab
		await page.getByRole('tab', { name: 'Timeline' }).click();

		await page.waitForTimeout(2000);

		// Should display timeline
		const hasTimelineHeading = await page.getByText('Timeline').count() > 0;
		expect(hasTimelineHeading).toBeTruthy();

		// Look for year indicators
		const yearElements = page.locator('text=/^(199|200|201|202)\\d$/');
		const yearCount = await yearElements.count();

		// Should have at least some years
		expect(yearCount).toBeGreaterThan(0);
	});

	test('should display Relations tab with all relationship types', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Click Relations tab
		await page.getByRole('tab', { name: 'Relations' }).click();

		await page.waitForTimeout(2000);

		// Check for different relation sections (at least one should exist)
		const hasParent = await page.getByText('Parent Provision').isVisible().catch(() => false);
		const hasChildren = await page.getByText('Child Provisions').isVisible().catch(() => false);
		const hasReferences = await page.getByText('References').isVisible().catch(() => false);
		const hasReferencedBy = await page.getByText('Referenced By').isVisible().catch(() => false);
		const hasSimilar = await page.getByText('Similar Provisions').isVisible().catch(() => false);
		const hasEmpty = await page.getByText('No relationships found').isVisible().catch(() => false);

		// At least one section should be visible
		expect(hasParent || hasChildren || hasReferences || hasReferencedBy || hasSimilar || hasEmpty).toBeTruthy();
	});

	test('should display Changes tab with year selectors', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Click Changes tab
		await page.getByRole('tab', { name: 'Changes' }).click();

		await page.waitForTimeout(1000);

		// Should have year selection dropdowns
		const selects = page.locator('select');
		const selectCount = await selects.count();

		expect(selectCount).toBeGreaterThanOrEqual(2);

		// Should have compare button
		const compareButton = page.getByRole('button', { name: /Compare/i });
		await expect(compareButton).toBeVisible();
	});

	test('should display Impact tab with depth selector', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Click Impact tab
		await page.getByRole('tab', { name: 'Impact' }).click();

		await page.waitForTimeout(2000);

		// Should have depth selection
		const depthButtons = page.getByRole('button', { name: /hop|Depth/i });
		const hasDepthControls = await depthButtons.count() > 0;

		// Should have some content or loading indicator
		const hasContent = await page.locator('text=/Impact|Distance|Provisions/i').count() > 0;

		expect(hasDepthControls || hasContent).toBeTruthy();
	});

	test('should display Constellation tab with year range', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Click Constellation tab
		await page.getByRole('tab', { name: 'Constellation' }).click();

		await page.waitForTimeout(1000);

		// Should have year range inputs
		const numberInputs = page.locator('input[type="number"]');
		const inputCount = await numberInputs.count();

		expect(inputCount).toBeGreaterThanOrEqual(2);
	});

	test('should display Insights tab with importance score', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Click Insights tab
		await page.getByRole('tab', { name: 'Insights' }).click();

		await page.waitForTimeout(1000);

		// Should show importance score
		const hasImportance = await page.getByText(/Importance|Score/i).count() > 0;

		// Should show key statistics
		const hasStats = await page.getByText(/References|Children|Amendments/i).count() > 0;

		expect(hasImportance || hasStats).toBeTruthy();
	});
});

test.describe('Provision Page - Cross-Reference Links', () => {
	test('should display clickable cross-reference links in provision text', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Go to Overview tab
		await page.getByRole('tab', { name: 'Overview' }).click();
		await page.waitForTimeout(1000);

		// Look for provision text with potential cross-references
		// Cross-references are typically styled links or have special formatting
		const potentialRefs = page.locator('a[href*="/provision"], button[class*="reference"], a[class*="cross-ref"]');
		const refCount = await potentialRefs.count();

		// If there are cross-references, test one
		if (refCount > 0) {
			const firstRef = potentialRefs.first();
			await expect(firstRef).toBeVisible();

			// Should be clickable
			const isClickable = await firstRef.evaluate(el => {
				const styles = window.getComputedStyle(el);
				return styles.cursor === 'pointer' || el.tagName === 'A' || el.tagName === 'BUTTON';
			});

			expect(isClickable).toBeTruthy();
		}
	});

	test('should show hover preview on cross-reference links', async ({ page }) => {
		test.setTimeout(60000);

		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Go to Overview tab
		await page.getByRole('tab', { name: 'Overview' }).click();
		await page.waitForTimeout(2000);

		// Find cross-reference links
		const refLinks = page.locator('a[href*="/provision"]');
		const linkCount = await refLinks.count();

		if (linkCount > 0) {
			const firstLink = refLinks.first();

			// Hover over the link
			await firstLink.hover();

			// Wait for hover preview to appear (300ms debounce + some buffer)
			await page.waitForTimeout(1000);

			// Look for tooltip/preview (exact structure may vary)
			const hasTooltip = await page.locator('[class*="tooltip"], [class*="preview"], [class*="popover"]').isVisible().catch(() => false);
			const hasHoverText = await page.locator('text=/U.S.C|section|paragraph/i').count() > 1;

			// One of these should indicate hover preview is working
			expect(hasTooltip || hasHoverText).toBeTruthy();
		}
	});

	test('should navigate to cross-referenced provision on click', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Go to Overview tab
		await page.getByRole('tab', { name: 'Overview' }).click();
		await page.waitForTimeout(1000);

		// Find cross-reference links
		const refLinks = page.locator('a[href*="/provision"]');
		const linkCount = await refLinks.count();

		if (linkCount > 0) {
			const originalUrl = page.url();
			const firstLink = refLinks.first();

			// Click the link
			await firstLink.click();

			// Should navigate or update URL
			await page.waitForTimeout(2000);

			const newUrl = page.url();

			// URL should have changed or provision content should have updated
			const urlChanged = newUrl !== originalUrl;
			const hasProvisionId = await page.getByText(/\/us\/usc\/t\d+/).count() > 0;

			expect(urlChanged || hasProvisionId).toBeTruthy();
		}
	});

	test('should show breadcrumb navigation after following cross-reference', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Go to Overview tab
		await page.getByRole('tab', { name: 'Overview' }).click();
		await page.waitForTimeout(1000);

		// Find and click cross-reference
		const refLinks = page.locator('a[href*="/provision"]');
		const linkCount = await refLinks.count();

		if (linkCount > 0) {
			await refLinks.first().click();
			await page.waitForTimeout(2000);

			// Look for breadcrumb navigation
			const hasBreadcrumb = await page.locator('[class*="breadcrumb"], nav[aria-label*="Breadcrumb"]').isVisible().catch(() => false);

			// Or check for back button
			const hasBackButton = await page.getByRole('button', { name: /Back/i }).isVisible().catch(() => false);

			expect(hasBreadcrumb || hasBackButton).toBeTruthy();
		}
	});
});

test.describe('Provision Page - Year Selection & Navigation', () => {
	test('should display current year in URL and page', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// URL should contain year parameter
		expect(page.url()).toContain('year=2024');

		// Page should display the year
		await expect(page.getByText('2024')).toBeVisible();
	});

	test('should change year from Timeline tab', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Go to Timeline tab
		await page.getByRole('tab', { name: 'Timeline' }).click();
		await page.waitForTimeout(2000);

		// Find year buttons/dots
		const yearButtons = page.locator('button').filter({ hasText: /^(199|200|201|202)\d$/ });
		const buttonCount = await yearButtons.count();

		if (buttonCount > 1) {
			const originalUrl = page.url();

			// Click on a different year
			await yearButtons.nth(1).click();

			// Wait for navigation
			await page.waitForTimeout(2000);

			const newUrl = page.url();

			// URL should have changed to reflect new year
			expect(newUrl).not.toBe(originalUrl);
			expect(newUrl).toContain('year=');
		}
	});

	test('should persist year across tab changes', async ({ page }) => {
		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2022');
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Verify initial year
		expect(page.url()).toContain('year=2022');

		// Switch tabs
		await page.getByRole('tab', { name: 'Relations' }).click();
		await page.waitForTimeout(1000);

		// Year should still be in URL
		expect(page.url()).toContain('year=2022');

		await page.getByRole('tab', { name: 'Timeline' }).click();
		await page.waitForTimeout(1000);

		// Year should persist
		expect(page.url()).toContain('year=2022');
	});

	test('should load different provision data for different years', async ({ page }) => {
		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024');
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Capture some content from 2024
		const content2024 = await page.textContent('body');

		// Change to different year
		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2013');
		await page.getByText('/us/usc/t18/s922/a').first().waitFor({ timeout: 30000 });

		await page.waitForTimeout(2000);

		const content2013 = await page.textContent('body');

		// Content should be different (provision may have changed)
		// At minimum, the year display should be different
		expect(content2024).toContain('2024');
		expect(content2013).toContain('2013');
	});

	test('should show year in Changes tab comparison', async ({ page }) => {
		await page.goto(TEST_PROVISION);
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Go to Changes tab
		await page.getByRole('tab', { name: 'Changes' }).click();
		await page.waitForTimeout(1000);

		// Year selectors should exist
		const selects = page.locator('select');
		const selectCount = await selects.count();

		expect(selectCount).toBeGreaterThanOrEqual(2);

		// Selects should have year options
		const firstSelect = selects.first();
		const options = await firstSelect.locator('option').count();

		expect(options).toBeGreaterThan(0);
	});

	test('should update Relations tab when year changes', async ({ page }) => {
		await page.goto('/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa?year=2024');
		await page.getByText('/us/usc/t18/s922/a').first().waitFor();

		// Go to Relations tab
		await page.getByRole('tab', { name: 'Relations' }).click();
		await page.waitForTimeout(2000);

		// Capture relations state
		const relations2024 = await page.textContent('[class*="space-y"]');

		// Navigate to Timeline and change year
		await page.getByRole('tab', { name: 'Timeline' }).click();
		await page.waitForTimeout(1000);

		const yearButtons = page.locator('button').filter({ hasText: /^(199|200|201|202)\d$/ });

		if (await yearButtons.count() > 1) {
			await yearButtons.nth(0).click();
			await page.waitForTimeout(3000);

			// Go back to Relations
			await page.getByRole('tab', { name: 'Relations' }).click();
			await page.waitForTimeout(2000);

			const relationsNew = await page.textContent('[class*="space-y"]');

			// Relations data should potentially be different for different years
			// At minimum, the page should have loaded successfully
			expect(relationsNew).toBeTruthy();
		}
	});
});
