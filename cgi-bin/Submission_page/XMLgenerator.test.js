/**
 * @jest-environment jsdom
 */
// Set up jQuery and document mocks BEFORE requiring modules
// to prevent errors from module-level code execution
global.$ = function (selector) {
	return {
		click: function () {
			return this;
		},
		find: (childSelector) => ({
			val: () => {
				const map = {
					".channelcontrols": "ctrl1, ctrl2",
					".channelgroupwidtho": "rep1, rep2",
					".channeldescription": "desc",
					".channelrecordnumber": "42",
					".channelhexcolor": "#ff0000",
					".channelbamType": "Google Drive",
					".channelbamlink": "https://drive.google.com/file/d/abc",
					".channeltotalreadsmapped": "12345",
					".channelreadmapmethod": "STAR",
					".channelpublicationlink": "https://pub.com/xyz",
					".channeltissue": "Leaf",
					".channelsvgname": "ath-leaf.svg",
					".channeltitle": "Test Title",
					".channelsralink": "SRR000001",
					".channelspecies": "Arabidopsis",
					".channelforeground": "#000000",
					".channelfilename": "file1.bam",
				};
				return map[childSelector] || "dummy";
			},
		}),
	};
};
global.$.fn = {};

// Mock document.getElementById before requiring modules
const elementValueMap = {
	reqxml: { value: "TestXML" },
	reqauthor: { value: "Author" },
	contectinfo: { value: "contact@email.com" },
};
global.document = {
	...global.document,
	getElementById: (id) => elementValueMap[id] || { value: "dummy" },
};

const xmlGeneratorModule = require("./XMLgenerator.js");

describe("XMLGenerator", () => {
	const { update } = xmlGeneratorModule;

	beforeAll(() => {
		// Ensure document.getElementById is properly mocked
		global.document.getElementById = (id) => elementValueMap[id] || { value: "dummy" };

		// Required top-level variables for update()
		global.topXML = [
			'\t\t<file info="<?channeldescription?>" record_number="<?channelrecordnumber?>" foreground="<?channelforeground?>" hex_colour="<?channelhexcolor?>" bam_type="<?channelbamType?>" name="<?channelbamlink?>" filename="<?channelfilename?>" total_reads_mapped="<?channeltotalreadsmapped?>" read_map_method="<?channelreadmapmethod?>" publication_link="<?channelpublicationlink?>" svg_subunit="<?channeltissue?>" svgname="<?channelsvgname?>" description="<?channeltitle?>" url="<?channelsralink?>" species="<?channelspecies?>" title="<?channeligbtitle?>">',
			"\t\t\t<controls>\n",
		].join("\r\n");
		global.controlsXML = "";
		global.replicatesXML = ["\t\t\t</controls>", "\t\t\t<groupwith>\n"].join("\r\n");
		global.endingXML = ["\t\t\t</groupwith>", "\t\t</file>", "\n"].join("\r\n");
		global.existingXML = "";
		global.all_controls = "";
		global.all_replicates = "";
	});

	/**
	 * Test case structure:
	 * @property {string} name - Test description
	 * @property {*} input - Input to update() function
	 * @property {Object} want - Expected output checks
	 * @property {string[]} want.contains - Strings that should appear in result
	 * @property {string[]} [want.notContains] - Strings that should NOT appear
	 */
	const cases = [
		{
			name: "generates correct XML with proper field values",
			input: {}, // dummy form element
			want: {
				contains: [
					'info="desc"',
					'record_number="42"',
					'hex_colour="#ff0000"',
					'bam_type="Google Drive"',
					'name="https://drive.google.com/file/d/abc"',
					'filename="file1.bam"',
					"<bam_exp>ctrl1</bam_exp>",
					"<bam_exp>ctrl2</bam_exp>",
					"<bam_exp>rep1</bam_exp>",
					"<bam_exp>rep2</bam_exp>",
					'total_reads_mapped="12345"',
					'read_map_method="STAR"',
					'species="Arabidopsis"',
					'svg_subunit="Leaf"',
					'svgname="ath-leaf.svg"',
				],
			},
		},
	];

	it.each(cases)("$name", ({ input, want }) => {
		const result = update("", input);

		// Check all expected strings are present
		want.contains.forEach((expectedStr) => {
			expect(result).toContain(expectedStr);
		});

		// Check strings that should NOT be present (if specified)
		if (want.notContains) {
			want.notContains.forEach((unexpectedStr) => {
				expect(result).not.toContain(unexpectedStr);
			});
		}

		// Verify result is valid XML-like string
		expect(typeof result).toBe("string");
		expect(result.length).toBeGreaterThan(0);
	});
});
