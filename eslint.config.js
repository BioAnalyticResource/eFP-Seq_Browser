const eslintPluginPrettier = require("eslint-plugin-prettier");
const globals = require("globals");

module.exports = [
	{
		ignores: [
			"**/*.min.js",
			"node_modules/**/*",
			"coverage/**/*",
			"playwright-report/**/*",
			"cgi-bin/core/packages/**/*",
			"cgi-bin/core/serviceWorker/**/*",
			"eslint.config.js",
			"workbox-config.js",
		],
	},
	{
		languageOptions: {
			ecmaVersion: "latest",
			globals: {
				...globals.browser,
			},
			parserOptions: {
				ecmaFeatures: {
					modules: true,
				},
			},
		},
		plugins: {
			prettier: eslintPluginPrettier,
		},
		rules: {
			"class-methods-use-this": "off",
			"consistent-return": "off",
			indent: ["error", "tab"],
			"no-console": "off",
			"no-continue": "off",
			"no-param-reassign": "off",
			"no-restricted-syntax": "off",
			"no-unused-vars": "off",
			"prettier/prettier": "warn",
			radix: "off",
			semi: ["error", "always"],
		},
	},
];
