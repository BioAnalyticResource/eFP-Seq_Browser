// @ts-check
import { defineConfig, devices } from "@playwright/test";

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */

/** Android Devices to test on */
const androidDeviceList = [
	"Nexus 6P",
	"Nexus 6P landscape",
	"Pixel 3",
	"Pixel 3 landscape",
	"Pixel 7",
	"Pixel 7 landscape",
];

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
	testDir: "./tests/playwright/",
	// Run tests serially to reduce flakiness
	fullyParallel: false,
	// Fail the build on CI if you accidentally left test.only in the source code.
	forbidOnly: !!process.env.CI,
	// Retry on CI only
	retries: process.env.CI ? 2 : 0,
	// Limit workers to 1 in CI to avoid resource contention; allow parallelism locally
	workers: process.env.CI ? 1 : undefined,
	// Reporter to use. See https://playwright.dev/docs/test-reporters
	reporter: [["list"], ["html"], ["json", { outputFile: "test-results/results.json" }]],
	// Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions.
	use: {
		// baseURL: 'http://localhost:3030',
		trace: "on-first-retry",
		screenshot: "only-on-failure",
		video: "retain-on-failure",
		actionTimeout: 15000,
		navigationTimeout: 45000,
	},

	// Configure projects for major browsers
	projects: [
		// Desktop Browsers - Chromium
		{
			name: "chromium",
			use: {
				...devices["Desktop Chrome"],
			},
		},
		{
			name: "chromium:hiDPI",
			use: {
				...devices["Desktop Chrome HiDPI"],
			},
		},
		// Desktop Browsers - Firefox
		{
			name: "firefox",
			use: {
				...devices["Desktop Firefox"],
			},
		},
		// Desktop Browsers - WebKit (Safari)
		{
			name: "webkit",
			use: { ...devices["Desktop Safari"] },
		},
		// Microsoft Edge
		{
			name: "edge",
			use: {
				...devices["Desktop Edge"],
			},
		},
		// iOS
		{
			name: "iOS:iPad Pro 11 landscape",
			use: {
				...devices["iPad Pro 11 landscape"],
			},
		},
		// Android
		...androidDeviceList.map((deviceName) => ({
			name: `Android:${deviceName}`,
			use: {
				...devices[deviceName],
			},
		})),
	],

	// Run your local dev server before starting the tests
	webServer: {
		command: "npm run start",
		url: "http://localhost:3030",
		reuseExistingServer: !process.env.CI,
		timeout: 180000, // Increase timeout for slow server startup
	},
});
