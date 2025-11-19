import { test, expect } from "@playwright/test";

// Basic test to check if the main page loads and renders

test.describe("eFP-Seq Browser main page", () => {
	test("should load and render index.html", async ({ page }) => {
		// Use the correct port for the static server
		await page.goto("http://localhost:3030/index.html");
		await expect(page).toHaveTitle(/eFP-Seq Browser/i);

		// Check for a main container element
		await expect(page.locator("#mainContainer")).toBeVisible();
	});
});
