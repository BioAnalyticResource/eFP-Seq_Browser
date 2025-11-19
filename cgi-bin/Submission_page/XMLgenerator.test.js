/**
 * @jest-environment jsdom
 */

const fs = require("fs");
const path = require("path");

describe("update (XMLgenerator.js)", () => {
	let update;
	let $;

	beforeAll(() => {
		// Minimal jQuery mock
		$ = () => ({
			find: (selector) => ({
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
					return map[selector] || "dummy";
				},
			}),
		});

		// Robust document.getElementById mock for all ids
		const getElementByIdMock = (id) => {
			const values = {
				reqxml: { value: "TestXML" },
				reqauthor: { value: "Author" },
				contectinfo: { value: "contact@email.com" },
			};
			return values[id] || { value: "dummy" };
		};
		if (global.document) {
			global.document.getElementById = getElementByIdMock;
		} else {
			global.document = { getElementById: getElementByIdMock };
		}
		global.$ = $;

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

		// Load the update function from XMLgenerator.js
		const code = fs.readFileSync(path.join(__dirname, "../Submission_page/XMLgenerator.js"), "utf8");
		const fnMatch = code.match(/function update\s*\(([^)]*)\)\s*{([\s\S]*?)^}/m);
		if (!fnMatch) throw new Error("update function not found in XMLgenerator.js");
		const args = fnMatch[1];
		const body = fnMatch[2];

		update = new Function(args, body);
	});

	it("generates correct XML for given form values", () => {
		const v = {}; // dummy, not used in our $ mock
		const result = update("", v);
		// Check for key XML elements and values
		expect(result).toContain('info="desc"');
		expect(result).toContain('record_number="42"');
		expect(result).toContain('hex_colour="#ff0000"');
		expect(result).toContain('bam_type="Google Drive"');
		expect(result).toContain('name="https://drive.google.com/file/d/abc"');
		expect(result).toContain('filename="file1.bam"');
		expect(result).toContain("<bam_exp>ctrl1</bam_exp>");
		expect(result).toContain("<bam_exp>ctrl2</bam_exp>");
		expect(result).toContain("<bam_exp>rep1</bam_exp>");
		expect(result).toContain("<bam_exp>rep2</bam_exp>");
	});
});
