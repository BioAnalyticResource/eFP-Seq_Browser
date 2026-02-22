/**
 * @jest-environment jsdom
 */

const elementValueMap = {
	reqxml: { value: "TestXML" },
	reqauthor: { value: "Author" },
	contectinfo: { value: "contact@email.com" },
};

// Lightweight jQuery stub to satisfy update()
global.$ = function () {
	const valueMap = {
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

	return {
		find: (childSelector) => ({ val: () => valueMap[childSelector] || "" }),
	};
};
global.$.fn = {};

// Mock document.getElementById before requiring modules
global.document = {
	...global.document,
	getElementById: (id) => elementValueMap[id] || { value: "" },
};

const xmlGeneratorModule = require("./XMLgenerator.js");

describe("XMLgenerator", () => {
	const { update, check_links, check_amazon_for_bam } = xmlGeneratorModule;

	beforeEach(() => {
		global.document.getElementById = (id) => elementValueMap[id] || { value: "" };
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

	describe("update", () => {
		const cases = [
			{
				name: "includes all substituted values",
				want: [
					"desc",
					'record_number="42"',
					'hex_colour="#ff0000"',
					'bam_type="Google Drive"',
					'name="https://drive.google.com/file/d/abc"',
					'filename="file1.bam"',
					"<bam_exp>ctrl1</bam_exp>",
					"<bam_exp>rep2</bam_exp>",
					'total_reads_mapped="12345"',
					'read_map_method="STAR"',
					'species="Arabidopsis"',
					'svg_subunit="Leaf"',
				],
			},
		];

		it.each(cases)("$name", ({ want }) => {
			const result = update("", {});
			want.forEach((expected) => expect(result).toContain(expected));
			expect(result).toContain("</file>");
		});
	});

	describe("check_amazon_for_bam", () => {
		const cases = [
			{ name: "accepts .bam extension", input: "https://s3.amazonaws.com/bucket/file.bam", expected: true },
			{ name: "accepts local .bam", input: "file.bam", expected: true },
			{ name: "rejects non-bam extension", input: "https://s3.amazonaws.com/bucket/file.txt", expected: false },
			{ name: "rejects alternate extension", input: "https://example.com/path/to/file.bed", expected: false },
		];

		it.each(cases)("$name", ({ input, expected }) => {
			expect(check_amazon_for_bam(input)).toBe(expected);
		});
	});

	describe("check_links", () => {
		const buildDom = (bamType, bamLink) => {
			const bamInput = { id: "bam_input", value: bamLink, style: {} };
			const bamTypeNode = { value: bamType };
			global.document.getElementById = (id) => {
				if (id === "Entries_all") {
					return {
						querySelectorAll: (selector) => {
							if (selector === ".bam_link") return [bamInput];
							if (selector === ".channelbamType") return [bamTypeNode];
							return [];
						},
					};
				}
				return elementValueMap[id] || { value: "" };
			};
		};

		const cases = [
			{
				name: "valid Amazon S3 bam link",
				bamType: "Amazon AWS",
				link: "https://s3.amazonaws.com/test/file.bam",
				expected: true,
			},
			{
				name: "valid Cyverse bam link",
				bamType: "Amazon AWS",
				link: "https://araport.cyverse-cdn.tacc.cloud/rnaseq/file.bam",
				expected: true,
			},
			{
				name: "Amazon link missing .bam",
				bamType: "Amazon AWS",
				link: "https://s3.amazonaws.com/test/file.txt",
				expected: false,
			},
			{
				name: "valid Google Drive link",
				bamType: "Google Drive",
				link: "https://drive.google.com/file/d/123456/view",
				expected: true,
			},
			{
				name: "invalid Google host",
				bamType: "Google Drive",
				link: "https://invalid.google.com/file/d/123456/view",
				expected: false,
			},
			{
				name: "unknown bam type",
				bamType: "Unknown",
				link: "https://example.com/file.bam",
				expected: false,
			},
		];

		it.each(cases)("$name", ({ bamType, link, expected }) => {
			buildDom(bamType, link);
			expect(check_links(".channelbamType", ".bam_link")).toBe(expected);
		});
	});
});
