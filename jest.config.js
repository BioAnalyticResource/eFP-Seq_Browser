/**
 * For a detailed explanation regarding each configuration property, visit:
 * https://jestjs.io/docs/configuration
 */

/** @type {import('jest').Config} */
const config = {
	clearMocks: true,
	collectCoverage: true,
	coverageDirectory: "coverage",
	coverageProvider: "v8",
	verbose: true,
	testPathIgnorePatterns: ["/node_modules/", "/tests/playwright/", "cgi-bin/core/packages/"],
};

module.exports = config;
