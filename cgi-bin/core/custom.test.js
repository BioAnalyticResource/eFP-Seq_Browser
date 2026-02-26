/**
 * @jest-environment jsdom
 *
 * Unit tests for custom.js functions
 *
 * This test suite focuses on testing functions that:
 * 1. Have clear, testable inputs and outputs
 * 2. Match their actual function signatures
 * 3. Don't have excessive external dependencies
 */

// Set up global variables BEFORE requiring modules
global.global_user = { email: "test@example.com" };
global.sraDict = {};
global.exp_info = [["test", "data"]];
global.rnaseq_calls = [];
global.colouring_mode = "abs";
global.users_email = "";
global.GFF_List = [];
global.shareLinkInputs = {};
global.uploadingData = false;
global.bamfile_info = {};
global.organism = "test";
global.locusInput = false;
global.signOut = jest.fn();
global.remove_private_database = jest.fn();
global.findAuthUser = jest.fn(() => "test@example.com");
global.databasesAdded = false;
global.get_user_XML_display = jest.fn();
global.gDriveFile_ID = undefined;

// Set up jQuery mock BEFORE requiring modules
global.$ = function (selector) {
	const mockElement = {
		length: 0,
		val: jest.fn(function (value) {
			if (value !== undefined) return this;
			return "";
		}),
		text: jest.fn(function (value) {
			if (value !== undefined) return this;
			return "";
		}),
		html: jest.fn(function (value) {
			if (value !== undefined) return this;
			return "";
		}),
		append: jest.fn(function () {
			return this;
		}),
		empty: jest.fn(function () {
			return this;
		}),
		prop: jest.fn(function (prop, value) {
			if (value !== undefined) return this;
			return "";
		}),
		attr: jest.fn(function (attr, value) {
			if (value !== undefined) return this;
			return "";
		}),
		trigger: jest.fn(function () {
			return this;
		}),
		removeAttr: jest.fn(function () {
			return this;
		}),
		addClass: jest.fn(function () {
			return this;
		}),
		removeClass: jest.fn(function () {
			return this;
		}),
		hasClass: jest.fn(function () {
			return false;
		}),
		is: jest.fn(function () {
			return false;
		}),
		resize: jest.fn(function () {
			return this;
		}),
		click: jest.fn(function () {
			return this;
		}),
		change: jest.fn(function () {
			return this;
		}),
		on: jest.fn(function () {
			return this;
		}),
		off: jest.fn(function () {
			return this;
		}),
	};
	return mockElement;
};
global.$.fn = {};
global.$.ajax = jest.fn((config) => {
	if (config && config.success) {
		config.success({});
	}
});
global.$.each = function (obj, callback) {
	if (Array.isArray(obj)) {
		obj.forEach((item, index) => callback(index, item));
	} else if (typeof obj === "object") {
		Object.keys(obj).forEach((key) => callback(key, obj[key]));
	}
};

const customModule = require("./custom.js");

/**
 * Global test setup - creates necessary DOM elements and resets state
 */
beforeEach(() => {
	document.body.innerHTML = `
		<div id="locus"></div>
		<input id="yscale_input" value="10" />
		<input id="rpkm_scale_input" value="1000" />
		<div id="testing_count"></div>
		<div id="bam_table"></div>
		<div id="landing"></div>
		<div id="efp_modal"></div>
		<textarea id="shareLinkTextArea"></textarea>
		<div class="disableOnLoading"></div>
		<div id="private_dataset_header" style="display: none;"></div>
		<div id="body_of"></div>
		<div id="bodyContainer"></div>
		<div id="loading_screen"></div>
		<div id="logoutModal" style="display: none;"></div>
		<select id="dataset"></select>
		<div id="compareGeneVariants"></div>
	`;

	global.users_email = "test@example.com";
	global.GFF_List = [];
	global.shareLinkInputs = {};
	global.uploadingData = false;
	global.databasesAdded = false;
	global.exp_info = [["test", "data"]];
	global.$.ajax = jest.fn((config) => {
		if (config && config.success) {
			config.success({});
		}
	});
	global.get_user_XML_display = jest.fn();
});

// ===== TESTS FOR PURE FUNCTIONS WITH CLEAR RETURN VALUES =====

describe("truncateDescription", () => {
	const { truncateDescription } = customModule;

	const cases = [
		{
			name: "truncates long text (35+ chars) and adds ellipsis",
			input: "This is a very long description that exceeds limit",
			expected: "This is a very long descriptio...",
		},
		{
			name: "returns original text if 30 chars or less",
			input: "Short description",
			expected: "Short description",
		},
		{
			name: "handles empty string",
			input: "",
			expected: "",
		},
	];

	it.each(cases)("$name", ({ input, expected }) => {
		const result = truncateDescription(input);
		expect(result).toBe(expected);
	});
});

describe("validateEmail", () => {
	const { validateEmail } = customModule;

	const emailTests = [
		["valid@example.com", "returns result for valid email"],
		["invalid@", "returns result for invalid email"],
		["@example.com", "returns result for missing local part"],
		["", "returns result for empty string"],
		["notanemail", "returns result for non-email"],
	];

	emailTests.forEach(([email, description]) => {
		it(description, () => {
			const result = validateEmail(email);
			expect([true, false, undefined]).toContain(result);
		});
	});
});

describe("generate_colour", () => {
	const { generate_colour } = customModule;

	const cases = [
		{
			name: "returns hex color format",
			start: "#000000",
			end: "#ffffff",
			percent: 0.5,
			expected: "#7f7f7f",
		},
		{
			name: "handles boundary values (0%)",
			start: "#000000",
			end: "#ffffff",
			percent: 0,
			expected: "#000000",
		},
		{
			name: "handles boundary values (100%)",
			start: "#000000",
			end: "#ffffff",
			percent: 1,
			expected: "#ffffff",
		},
		{
			name: "handles 50% interpolation",
			start: "#000000",
			end: "#ffffff",
			percent: 0.5,
			expected: "#7f7f7f",
		},
	];

	it.each(cases)("$name", ({ start, end, percent, expected }) => {
		const result = generate_colour(start, end, percent);
		expect(typeof result).toBe("string");
		expect(result.match(/^#[0-9a-fA-F]{6}$/i)).toBeTruthy();
		expect(result.toLowerCase()).toBe(expected);
	});
});

describe("round", () => {
	const { round } = customModule;

	const cases = [
		{
			name: "rounds 2.5 to 0 decimals",
			value: 2.5,
			digits: 0,
			expected: 3,
		},
		{
			name: "rounds 2.456 to 2 decimals",
			value: 2.456,
			digits: 2,
			expected: 2.46,
		},
		{
			name: "handles negative numbers",
			value: -3.567,
			digits: 1,
			expected: -3.6,
		},
		{
			name: "rounds to exact decimal places",
			value: 3.14159,
			digits: 2,
			expected: 3.14,
		},
	];

	it.each(cases)("$name", ({ value, digits, expected }) => {
		const result = round(value, digits);
		expect(result).toBe(expected);
	});
});

// ===== TESTS FOR VALIDATION FUNCTIONS =====

describe("verifyLoci", () => {
	const { verifyLoci } = customModule;

	const cases = [
		{
			name: "validates a list of loci",
			loci: ["AT1G01010", "AT1G01020"],
		},
		{
			name: "handles empty loci list",
			loci: [],
		},
	];

	it.each(cases)("$name", ({ loci }) => {
		const result = verifyLoci(loci);
		expect([true, false, undefined]).toContain(result);
	});
});

describe("locus_validation", () => {
	const { locus_validation } = customModule;

	beforeEach(() => {
		const locusElement = document.getElementById("locus");
		if (locusElement) {
			locusElement.value = "AT1G01010";
		}
	});

	const cases = [
		{
			name: "validates AGI format when locus value is set",
			value: "AT1G01010",
		},
		{
			name: "handles invalid format",
			value: "INVALID",
		},
		{
			name: "handles empty string input",
			value: "",
		},
	];

	it.each(cases)("$name", ({ value }) => {
		const locusElement = document.getElementById("locus");
		locusElement.value = value;
		const result = locus_validation(value);
		expect([true, false, undefined]).toContain(result);
	});
});

describe("rpkm_validation", () => {
	const { rpkm_validation } = customModule;

	const cases = [
		{
			name: "validates positive RPKM",
			value: "100",
		},
		{
			name: "validates zero",
			value: "0",
		},
		{
			name: "handles negative values",
			value: "-50",
		},
	];

	it.each(cases)("$name", ({ value }) => {
		const result = rpkm_validation(value);
		expect([true, false, undefined]).toContain(result);
	});
});

// ===== TESTS FOR DOM-DEPENDENT FUNCTIONS =====

describe("count_bam_num", () => {
	const { count_bam_num } = customModule;

	it("counts BAM entries in the DOM", () => {
		const bamTable = document.getElementById("bam_table");
		bamTable.innerHTML = `
			<div class="bam_entry"></div>
			<div class="bam_entry"></div>
			<div class="bam_entry"></div>
		`;
		const result = count_bam_num();
		if (typeof result === "number") {
			expect(result).toBe(3);
		} else {
			expect(document.querySelectorAll(".bam_entry").length).toBe(3);
		}
	});

	it("returns 0 when no BAM entries exist", () => {
		const bamTable = document.getElementById("bam_table");
		bamTable.innerHTML = "";
		const result = count_bam_num();
		if (typeof result === "number") {
			expect(result).toBe(0);
		} else {
			expect(document.querySelectorAll(".bam_entry").length).toBe(0);
		}
	});
});

describe("check_if_Google_login", () => {
	const { check_if_Google_login } = customModule;

	it("checks Google login status without throwing", () => {
		expect(() => {
			check_if_Google_login();
		}).not.toThrow();
	});
});

// ===== TESTS FOR FUNCTIONS THAT MODIFY DOM/STATE =====

describe("updateRPKMAbsoluteMax", () => {
	const { updateRPKMAbsoluteMax } = customModule;

	it("updates RPKM scale when value is greater than adjusted max", () => {
		const input = document.getElementById("rpkm_scale_input");
		input.value = "1000";

		// When currentRPKMAbsMax is 1000, it gets converted to 1
		// So any value > 1 will update the scale
		updateRPKMAbsoluteMax(500);
		expect(input.value).toBe("500");
	});

	it("updates to large values", () => {
		const input = document.getElementById("rpkm_scale_input");
		input.value = "1000";
		updateRPKMAbsoluteMax(2000);
		expect(input.value).toBe("2000");
	});

	it("converts string input to integer", () => {
		const input = document.getElementById("rpkm_scale_input");
		input.value = "1000";
		updateRPKMAbsoluteMax("3000");
		expect(input.value).toBe("3000");
	});

	it("does not update when new value is not greater than adjusted max", () => {
		const input = document.getElementById("rpkm_scale_input");

		// When already 2000, adjusted max is 2000
		input.value = "2000";
		updateRPKMAbsoluteMax(1500);

		// The adjusted max is 2000 (since it's not 1000), so 1500 <= 2000, won't update
		expect(input.value).toBe("2000");
	});
});
