//============================ Alexander Sullivan =============================
//
// Purpose: General functions for the eFP-Seq Browser
//
//=============================================================================
/** Current version of eFP-Seq Browser with the following format: [v-version][version number: #.#.#][-][p-public OR d-dev][year - 4 digits][month - 2 digits][day - 2 digits] */
const version = "v1.3.14-p20240113";

/** Selected RPKM mode */
let colouring_mode = "abs";

let locus;
if (document.getElementById("locus") != null) {
	locus = document.getElementById("locus").value;
}

let old_locus = locus;
let new_locus;

let yscale_input;
if (document.getElementById("yscale_input") != null) {
	yscale_input = document.getElementById("yscale_input").value;
}

/** What is the max value for the svg colouring in absolute mode? */
let max_abs_scale;
if (document.getElementById("rpkm_scale_input") != null) {
	max_abs_scale = document.getElementById("rpkm_scale_input").value;
}

/** Gets updated when user changes gene */
let locus_start = 10326918;
/** Gets updated when user changes gene */
let locus_end = 10330048;
let splice_variants = "";
/** Make a list of records and tissues we need to query.... */
let rnaseq_calls = [];
/** Keep track of the FPKM related information  TODO : rename all exp_info to fpkm_info */
let exp_info = [];
/** Make a list of records and tissues we need to query.... */
let rnaseq_success = 0;
const date_obj = new Date();
/** Keep track of start time */
let rnaseq_success_start_time = date_obj.getTime();
/** Keep track of start time */
let rnaseq_success_current_time;
/**  Keep track of start time */
let rnaseq_success_end_time;
let max_absolute_fpkm = -1;
let max_log_fpkm = -1;
/** The element for inserting the SVG colouring scale legend */
let svg_colouring_element = null;
/** the element for inserting the gene structure scale legend */
let gene_structure_colouring_element = null;

/** Used to create location for uploaded XML, client side */
let base_src = "cgi-bin/data/bamdata_araport11.xml";
let upload_src = "";
let dataset_dictionary = {
	"Araport 11 RNA-seq data": "cgi-bin/data/bamdata_araport11.xml",
	"Developmental transcriptome - Klepikova et al": "cgi-bin/data/bamdata_Developmental_transcriptome.xml",
};
let loadNewDataset = false;

/** Used to count and determine how many BAM entries are in the XML file */
let count_bam_entries_in_xml = 113;
/**
 * Count the amount of entries in a BAM file
 */
function count_bam_num() {
	const xhr = new XMLHttpRequest();
	const url = base_src;

	xhr.responseType = "document";
	xhr.onreadystatechange = () => {
		if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
			const response = xhr.responseXML;

			if (response && response.getElementsByTagName("file")) {
				count_bam_entries_in_xml = xhr.responseXML.getElementsByTagName("file").length;
			} else if (response === undefined || response === null) {
				console.log("failed at response");
			}

			document.getElementById("testing_count").innerHTML = count_bam_entries_in_xml;
		}
	};

	xhr.open("GET", url);
	xhr.send();
}
count_bam_num();

/**
 * Initialize or terminate the loading screen
 * @param {boolean} terminate True = end, False = start
 */
function loadingScreen(terminate = true) {
	if (terminate === false) {
		document.getElementById("loading_screen").className = "loading";
		document.getElementById("body_of").className = "body_of_loading";
		document.getElementById("bodyContainer").classList.add("progressLoading");
		document.getElementById("loading_screen").removeAttribute("hidden");

		// Disable buttons:
		const toDisableList = document.getElementsByClassName("disableOnLoading");
		for (const element of toDisableList) {
			$("#" + element.id).prop("disabled", true);
		}
	} else {
		document.getElementById("loading_screen").className = "loading done_loading";
		document.getElementById("body_of").className = "body_of_loading body_of_loading_done";
		document.getElementById("bodyContainer").classList.remove("progressLoading");
		document.getElementById("loading_screen").setAttribute("hidden", true);

		// Enable buttons:
		const toDisableList = document.getElementsByClassName("disableOnLoading");
		for (const element of toDisableList) {
			$("#" + element.id).prop("disabled", false);
		}
		addGFF();
		uploadingData = false;
	}
}

/** Base 64 images */
const img_loading_base64 =
	"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyCAYAAADP/dvoAAAABmJLR0QAwADAAMAanQdUAAAACXBIWXMAAA7CAAAOwgEVKEqAAAAAB3RJTUUH4AoRDzYeAMpyUgAABGJJREFUeNrt3TFoE3scwPGvjxtOzKAQMEOECBkyROhQsWOEChURBFtssdJFB9Gl4OJkwaEtRRAUdLAUqYJgwamIEFAwUoS43RCw0AwpOjhkuCHDQd5Qes9q+7A+7cP2+1na5K53cH/Kl19yIfu63W4XSZL2qL+8BJIkQyhJ0h4VfPvExMSEV0WStGt92zknQkmSE+GPFFOSpN00CToRSpJkCCVJhlCSJEMoSZIhlCTJEEqSZAglSTKEkiQZQkmSDKEkSYZQkiRDKEmSIZQkyRBKe8HDhw/5/Pnzbzn2/v3709/Hx8d/23kkGULpp01PT9NoNH7LsTudDgBJktBut0mSxAsu/Q8CL4G0fUmSEEURcRxTLpc5ePBguu3Lly9EUUQ2m6VcLm/4u0ajQRzH9PT0/PNPGARcu3aNXC6X7lMqlVheXv5u3/Xt69NjJpOht7fXBZEMobRz2u02Z8+eJY5jCoUCtVqN58+fU6lUePLkCXfu3KGnp4d6vU5vby9zc3PA2peCzs7OUiqVvjvm8ePHWVlZoVAocPr0aQYHB6nX6zSbTSqVSnqMkZGRdHp88+YNw8PDzM/PuyiSIZR2zv3798lms7x9+xZYex/x5s2bLC0tce7cOYaHhwmCgHa7zaFDh5ibm6PZbDI9Pc3Hjx/J5/MsLCxQrVa3PMfhw4d5/fo1rVaLI0eOMDk5CUC1WuXTp08EQcCxY8e4cOGCCyIZQmlnffjwgfPnz6ePBwYGuHr1KrD2UmW1WqVWq7G6upru02w2yeVy5PN5AAYHB//1HOvb1/fvdDpkMhniOGZ5eZlCoUCSJOnLqZIMobRjkiRJb3RZF4YhAFNTUywuLnLr1i2KxSKPHj36df+sQUChUODSpUt0Oh0uXrzo+4PSL+Bdo9I2nThxgsePH6d3eS4sLDAwMADA+/fvOXPmDP39/RtiWSqVaLVaRFEEwN27d7d93iiKCIKA27dv8+DBAy5fvpxuazQa1Ov1dHp89uxZuq1ardJqtVw4yYlQ2r4wDDl58mT6eGZmhuvXr/Pu3TuOHj1KJpMhDENevHgBwNjYGFeuXOHVq1eEYUg2mwUgl8sxMzPDqVOnyOfz9PX1pS97/sgkCFAul2m32zx9+pQkSajVaoyOjjI5Ocns7CxRFPHy5UuiKGJkZIT+/n6y2Szj4+OMjY1x48YNF1TaxL5ut9v9+omJiYkNPyVtLo5jkiTZ8NEJWPv4BJBG8GudTockSchkMts+39TUFKurq9y7dw+Aer3O0NAQKysrLob0A7bqmxOh9JO2itlmAfx6wvxZfX19DA0NEYYhBw4cYHFxkdHRURdC+o8MofSHqFQqLC0tUavVAJifn9/0M4mSDKG0axWLRYrFohdC+oW8a1SSZAglSTKEkiQZQkmSDKEkSYZQkiRDKEmSIZQkyRBKkmQIJUkyhJIkGUJJkgyhJEmGUJKkP9mWX8PkN9RLkpwIJUna5fZ1u92ul0GS5EQoSdIe9DfEVWhcl8IjHgAAAABJRU5ErkJggg==";

let img_gene_struct_1 =
	"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAATklEQVQ4jWNgYGANxQnC0iAggQEE0mAA lYcFgBWw4RZIQOEmYJNF0Q4zAQ4Qkqm4XQ8CIMWMw96HgsPdh4zD3oeCwx2MgDgc/vlw2JelAO7V xD0GmsY3AAAAAElFTkSuQmCC ";
const img_gene_struct_error =
	"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAICAIAAADlfmh0AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAMBSURBVGhD7Vi7ceswEGQrVBUMxC40wwKYKVANDpwpVuIqVIx6ealxHxzuA9BPsmfMGQOzgQgs7hZH3RrW8O/20dHR0dHxMrqN7gbneZAxLg/3GAlh13R6r8QhmgYQDtc3/Py2TMOwni2hCtg13/UM7M1x/gh06b6JHwxVx2X9zzfb8W10G90NXF/JozhdnNEmCKsNGgUU6EQtTgTsetZG99DJv6Xh18/eEtDt9efRbXQ30O6mH8XpwszjdFDWBu0BF9K40XmlTqSDj/M6ljssBqeBKXDXRASagb0c536k+WE4XjjL7f3KZJ4sHH1HRgF5QFgfKggzoRxnXO5GdluD04mPcGQfwQR/5CNXimNE+rwxi4RKM1ZVYKoPGwfPJc2px4P6ktDwBfGn6HgV3UZ3g9QSeWQ35BH/W6cZaCrXP6m74kbxSmICoWaj9MGR5fIiBPFrMQJYoj50N53yiB1bOCyM5tER0llgMoaKwjY4GBMhqYuGls6sDQoowurB5cgtTqmeSZHgs7SrB0x4rYmZ/m7B0tfFyVkKxy+JHi+sNtPxHLqN7gbwvVctmh+LV4YZ5U0J0Ay52exGB53oK2+iYXvYGwHKKAOWKJHqTyXGuhUKwAHBK6GCsAYnn8jJVhqaOrkIiYlBKgfX5WpxbPVU3nqWjerx0mUdl+sxbQE/rTO1NgRwuM5ZgJOqhfmlEqfjKXQb3Q1cS8gjt19rRrcErkaafKDI+Ehtg52J/Q+7jBGA8cE9ER5zx1KQPANxJCPtdSgdWxLpNpZ7lmyJoYKwBgeVkF9r2TpdUyc4Ow5YrR2cg8uRaxwrUuetZdmsHjDX0zKlFOd5Os4TESJTa0PYFwoCNgoSlkqcjqfQbXQ3wO89j3ShKB2C7Ycd5WfsDUuZhaU5G7W51C5q0dxmzIHfQ9kp3G+UYgTUkDxMV/M8SBUTYeUMpYQ62YeKwuqcnNfJNhqaOrmMJMxF0MGN9zlOQ6Q6rMmyWT1iQhx8dxJk6+CMXGd8WZX3qIWFpY5XcPv4BMHOh4rKP1r3AAAAAElFTkSuQmCC";

const absolute_rpkm_scale =
	"iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQD//wD//AD/+QD/9wD/9AD/8gD/7wD/7QD/6gD/6AD/5QD/4gD/4AD/3QD/2wD/2AD/1gD/ 0wD/0QD/zgD/zAD/yQD/xgD/xAD/wQD/vwD/vAD/ugD/twD/tQD/sgD/rwD/rQD/qgD/qAD/pQD/ owD/oAD/ngD/mwD/mQD/lgD/kwD/kQD/jgD/jAD/iQD/hwD/hAD/ggD/fwD/fAD/egD/dwD/dQD/ cgD/cAD/bQD/awD/aAD/ZgD/YwD/YAD/XgD/WwD/WQD/VgD/VAD/UQD/TwD/TAD/SQD/RwD/RAD/ QgD/PwD/PQD/OgD/OAD/NQD/MwD/MAD/LQD/KwD/KAD/JgD/IwD/IQD/HgD/HAD/GQD/FgD/FAD/ EQD/DwD/DAD/CgD/BwD/BQD/AgCkIVxRAAAAs0lEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hERLGBmpbgljbBwjiiWMnFyMVLcECOhkCZBIZUzPYKSV JaDgYkxKZkxNY2SkmU8gljDCLaFdxDMmw4NrGOWTUUuItwQAG8496iMoCNwAAAAASUVORK5CYII= ";
const relative_rpkm_scale =
	"iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQAAAP8FBfkKCvQPD+8UFOoZGeUeHuAjI9soKNYtLdEzM8w4OMY9PcFCQrxHR7dMTLJRUa1W VqhbW6NgYJ5mZplra5NwcI51dYl6eoR/f3+EhHqJiXWOjnCTk2uZmWaenmCjo1uoqFatrVGysky3 t0e8vELBwT3GxjjMzDPR0S3W1ijb2yPg4B7l5Rnq6hTv7w/09Ar5+QX//wD/+wD/9gD/8QD/7AD/ 5wD/4gD/3QD/2AD/0wD/zQD/yAD/wwD/vgD/uQD/tAD/rwD/qgD/pQD/oAD/mgD/lQD/kAD/iwD/ hgD/gQD/fAD/dwD/cgD/bQD/ZwD/YgD/XQD/WAD/UwD/TgD/SQD/RAD/PwD/OgD/NAD/LwD/KgD/ JQD/IAD/GwD/FgD/EQD/DAD/BwBUljDTAAAA1klEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hDRLGDi5GICWMBBvCSMjIUsYY+MYUS0BApJ8wmhlzUjI EiDAYgkD0CcMwgxUtQRIpDKmZzCiBBcDgwgDlSwBBRdjUjJjahojI2qcMAhT2RJGNEuAYUasJURH PGMyPLiGTz4ZtYQESwCEoDnh8dGTkQAAAABJRU5ErkJggg==";
const exon_intron_scale =
	"iVBORw0KGgoAAAANSUhEUgAAALQAAAAPBAMAAAC/7vi3AAAAGFBMVEX///9QUFAAAADcFDz/jAAA AP+m3KYAfQCnICW7AAAArklEQVQ4jd3UMQ+CQAwF4OaG66ourpcO/DCGm7v17/vKBUU8SozBGBvy xo9HD6DzB3OicK4WTa7RfIGWgiiH0In6tBK/iMpKhsvyWAfB7NGlJEHQFA+6U5ZVjf2OTtfBI6YF OgIpadkaklGjZtrepIsXL63+U2s8vzHpila+0zsLEQe9ty+kQ7OuFgJ+pseY3nr5cIxtIQt6OkY/ 3lxReHMhF4nm1z+Zv6KP+/PdANuwQcLhhEyQAAAAAElFTkSuQmCC";

/**
 * Produces an intermediate HEX colour
 * @param {*} start_color
 * @param {*} end_color
 * @param {*} percent
 * @returns
 */
function generate_colour(start_color, end_color, percent) {
	// strip the leading # if it's there
	start_color = start_color.replace(/^\s*#|\s*$/g, "");
	end_color = end_color.replace(/^\s*#|\s*$/g, "");

	// convert 3 char codes to 6, e.g. `E0F` to `EE00FF`
	if (start_color.length == 3) {
		start_color = start_color.replace(/(.)/g, "$1$1");
	}
	if (end_color.length == 3) {
		end_color = end_color.replace(/(.)/g, "$1$1");
	}

	// get colors
	let start_red = parseInt(start_color.substr(0, 2), 16),
		start_green = parseInt(start_color.substr(2, 2), 16),
		start_blue = parseInt(start_color.substr(4, 2), 16);

	let end_red = parseInt(end_color.substr(0, 2), 16),
		end_green = parseInt(end_color.substr(2, 2), 16),
		end_blue = parseInt(end_color.substr(4, 2), 16);

	// calculate new color
	let diff_red = end_red - start_red;
	let diff_green = end_green - start_green;
	let diff_blue = end_blue - start_blue;
	diff_red = (diff_red * percent + start_red).toString(16).split(".")[0];
	diff_green = (diff_green * percent + start_green).toString(16).split(".")[0];
	diff_blue = (diff_blue * percent + start_blue).toString(16).split(".")[0];

	// ensure 2 digits by color
	if (diff_red.length == 1) {
		diff_red = "0" + diff_red;
	}
	if (diff_green.length == 1) {
		diff_green = "0" + diff_green;
	}
	if (diff_blue.length == 1) {
		diff_blue = "0" + diff_blue;
	}

	return "#" + diff_red + diff_green + diff_blue;
}

/**
 * Round the float X to DIGIT number of decimal places.
 */
function round(x, digits) {
	return parseFloat(x.toFixed(digits));
}

let colouring_part;

/**
 * Find and colour a particular SVG in the DOM.
 */
function colour_part_by_id(id, part, fpkm, mode) {
	colouring_part = "all";

	for (const sra of sraList) {
		if (id.replace("_svg", "") == sra) {
			colouring_part = sraDict[sra]["svg_part"];
		}
	}

	// Verify which type of input is added as fpkm
	let fpkmUse = fpkm;
	if (Array.isArray(fpkmUse)) {
		fpkmUse = fpkmUse[variantPosition];
	} else {
		fpkmUse = parseFloat(fpkmUse);
	}

	//console.log('COLOUR PART BY ID\'s part = ' + part);

	// Get the user set RPKM scale
	max_abs_scale = document.getElementById("rpkm_scale_input").value;
	if (!max_abs_scale || max_abs_scale <= 0) {
		max_abs_scale = 1000;
	}

	let paths1, paths2;
	if (document.getElementById(id)) {
		paths1 = document.getElementById(id).getElementsByTagName("path");
		paths2 = document.getElementById(id).getElementsByTagName("g");
	}

	let paths = null;
	if (paths1 && paths2) {
		paths = Array.prototype.slice.call(paths1).concat(Array.prototype.slice.call(paths2));
	}

	if (paths != null) {
		if (mode == "abs") {
			// For absolute FPKM colouring
			const r = 255;
			const g = 255 - parseInt((fpkmUse / max_abs_scale) * 255);
			const b = 0;

			if (colouring_part == "all") {
				for (const path of paths) {
					path.style.fill = "rgb(" + r + ", " + g + ", " + b + ")";
				}
			} else {
				//console.log("\n\n ********** id = " + id + " and svg_part = " + colouring_part);
				for (const path of paths) {
					//console.log("Checking if " + path.id + " == " + colouring_part + " and it is " + (path.id == colouring_part));

					if (path.id == colouring_part) {
						if (path.tagName == "g") {
							const child_paths = path.getElementsByTagName("path");
							//console.log("It was g with " + child_paths.length + " elements!!!!");
							for (const child of child_paths) {
								child.style.fill = "rgb(" + r + ", " + g + ", " + b + ")";
							}
						} else {
							path.style.fill = "rgb(" + r + ", " + g + ", " + b + ")";
						}
					}
				}
			}
		} else if (mode == "rel") {
			// For relative FPKM colouring
			let hex = "";
			// Make the log FPKM a number between 0 and 1 to denote the 0 to +-3 scale.
			const log_scale_max = 3;
			let log_scaling = 0;
			if (fpkmUse != "Missing controls data" && Math.abs(fpkmUse) > log_scale_max) {
				log_scaling = log_scale_max;
			} else if (fpkmUse != "Missing controls data") {
				log_scaling = Math.abs(fpkmUse);
			}
			log_scaling /= log_scale_max;

			if (fpkmUse == "Missing controls data") {
				hex = "#D9D9D9";
			} else if (fpkmUse > 0) {
				// yellow-red
				hex = generate_colour("FFFF00", "FF0000", log_scaling);
			} else if (fpkmUse == 0) {
				// yellow
				hex = "FFFF00";
			} else if (fpkmUse < 0) {
				// yellow-blue
				hex = generate_colour("FFFF00", "0000FF", log_scaling);
			}

			//console.log('fpkm = ' + fpkm + ' -> hex = ' + hex);

			if (colouring_part == "all") {
				for (const path of paths) {
					path.style.fill = hex;
				}
			} else {
				//console.log("\n\n ********** id = " + id + " and svg_part = " + colouring_part);
				for (const path of paths) {
					//console.log("Checking if " + paths[i].id + " == " + colouring_part + " and it is " + (paths[i].id == colouring_part));
					if (path.id == colouring_part) {
						if (path.tagName == "g") {
							const child_paths = path.getElementsByTagName("path");
							//console.log("It was g with " + child_paths.length + " elements!!!!");
							for (const child of child_paths) {
								child.style.fill = hex;
							}
						} else {
							path.style.fill = hex;
						}
					}
				}
			}
		}

		if (fpkmUse == "Missing controls data") {
			document.getElementById(id.replace("_svg", "_rpkm")).innerHTML = fpkmUse;
		} else {
			document.getElementById(id.replace("_svg", "_rpkm")).innerHTML = round(fpkmUse, 2);
		}
	} else {
		console.log("Paths is null for id = " + id);
	}
}

/** Set to 1 as default so prevents the divide by 0 zero later */
let rpkmAverage = 1;
/** Set to 1 as default so prevents the divide by 0 zero later */
let rpkmMedian = 1;
/**
 * Find the RPKM average across all samples
 */
function findRPKMValuesAcrossAll() {
	if (sraDict) {
		const listOfSRA = Object.keys(sraDict);
		const listOfRPKM = [];
		let rpkmTotal = 0;
		for (const sra of listOfSRA) {
			if (sraDict[sra]["RPKM"]) {
				const currentRPKM = sraDict[sra]["RPKM"][variantPosition];
				if (parseFloat(currentRPKM)) {
					listOfRPKM.push(currentRPKM);
					rpkmTotal += currentRPKM;
				}
			}
		}
		if (listOfRPKM.length > 0) {
			rpkmMedian = math.median(listOfRPKM);
		}
		rpkmAverage = rpkmTotal / listOfSRA.length;
	} else {
		displayError("ERROR IN RETRIEVING ALL DATA POINTS WITHIN DATASET");
	}
}

/**
 * Switch the current existing RPKM mode
 * @param {String} selectedMode The DOM ID of the selected RPKM mode desired
 */
function switchRPKMMode(selectedMode) {
	/** If relative mode (true) or absolute (false, default) */
	let rel = false;

	// If selectedMode is the relative mode, which rel to true
	if (selectedMode === "rel_radio") {
		rel = true;
	}

	if (rel) {
		// Change radio
		colouring_mode = "rel";

		// Change HTML classes for UI
		document.getElementById("abs_radio").classList.remove("active");
		document.getElementById("rel_radio").classList.add("active");

		// Disable RPKM scape input
		$("#rpkm_scale_input").prop("disabled", true);
	} else {
		// Change radio
		colouring_mode = "abs";

		// Change HTML classes for UI
		document.getElementById("rel_radio").classList.remove("active");
		document.getElementById("abs_radio").classList.add("active");

		// Enable RPKM scape input
		$("#rpkm_scale_input").removeAttr("disabled");
	}

	// If data already called, update
	if (rnaseq_calls && rnaseq_calls.length > 0) {
		whichAbsOrRel();
	}
}

/**
 * Find and update each SVG in the DOM.
 */
function colour_svgs_now() {
	const mode = colouring_mode;
	for (let i = 0; i < count_bam_entries_in_xml; i++) {
		if (exp_info[i]) {
			const currentSRA = exp_info[i][0].slice(0, -4);

			// For every exp, figure out the fpkm average of the controls
			let ctrl_fpkm_sum = 0;
			let ctrl_count = 0;
			let ctrl_avg_fpkm = 0;
			for (let ii = 0; ii < count_bam_entries_in_xml; ii++) {
				if (exp_info[i][2].indexOf(exp_info[ii][0].slice(0, -4)) != -1) {
					// experiment ii is a control for experiment i, save FPKM of exp ii
					ctrl_count++;
					ctrl_fpkm_sum += exp_info[ii][3][variantPosition];
				}
			}

			// If no control found:
			if (ctrl_fpkm_sum === 0 && sraDict[currentSRA]["RPKM"]) {
				ctrl_fpkm_sum = sraDict[currentSRA]["RPKM"][variantPosition];
			}

			// Create control average
			if (ctrl_count > 0) {
				ctrl_avg_fpkm = ctrl_fpkm_sum / ctrl_count;
			} else {
				if (rpkmMedian && rpkmMedian === 1) {
					findRPKMValuesAcrossAll();
				}
				ctrl_avg_fpkm = rpkmMedian;
			}

			// Save the average fpkm of controls and the log fpkm...
			let relativeRPKMValue = 0;
			const relativeRPKM = [];
			let useRPKM = "";
			if (sraDict[currentSRA]["RPKM"] && sraDict[currentSRA]["RPKM"][variantPosition]) {
				useRPKM = sraDict[currentSRA]["RPKM"][variantPosition];
			} else {
				useRPKM = 0;
			}

			if (useRPKM == 0 && ctrl_avg_fpkm == 0) {
				// Define log2(0/0) = 0 as opposed to undefined
				exp_info[i].splice(4, 1, 0);
			} else {
				relativeRPKMValue = Math.log2(useRPKM / ctrl_avg_fpkm);
			}

			relativeRPKM.push(relativeRPKMValue);
			sraDict[currentSRA]["relativeRPKM"] = relativeRPKMValue;

			exp_info[i].splice(4, 1, relativeRPKM);
			exp_info[i].splice(6, 1, ctrl_avg_fpkm);

			// See if the absolute or the relative FPKM is max
			if (useRPKM >= max_absolute_fpkm) {
				max_absolute_fpkm = useRPKM;
			}

			if (
				exp_info[i][4] != "Missing controls data" &&
				Math.abs(exp_info[i][4]) >= max_log_fpkm &&
				Math.abs(exp_info[i][4]) < 1000
			) {
				max_log_fpkm = Math.abs(exp_info[i][4]);
			}

			// Colour SVGs based on the mode requested. Pass in the correct FPKM value...
			if (colouring_mode === "rel") {
				if (!exp_info[i][4] && exp_info[i][4] != 0) {
					exp_info[i][4] = -999999;
				}
			} else {
				if (!exp_info[i][3][variantPosition] && exp_info[i][3][variantPosition] != 0) {
					exp_info[i][3][variantPosition] = -999999;
				}
			}
		} else {
			logError("Issue retrieving exp_info for " + mode + " within BAM entry point " + i);
		}

		whichAbsOrRel();
	}

	document.getElementById("landing").setAttribute("hidden", "true");
	$("#theTable").trigger("update");

	change_rpkm_colour_scale(colouring_mode);
}

/**
 * Re-read the value from the input box
 */
function get_input_values() {
	// Clean locus input
	locus = document.getElementById("locus").value;
	locus = locus.trim().toUpperCase();

	yscale_input = document.getElementById("yscale_input").value;

	if (yscale_input == "Auto" || parseInt(yscale_input) < 1) {
		yscale_input = parseInt(-1);
		//console.log("yscale_input value set to -1.");
	}

	max_abs_scale = document.getElementById("rpkm_scale_input").value;
}

/**
 * When user clicks GO button, this function is called to update gene structure AND RNA-Seq images
 */
function update_all_images(status) {
	if (document.getElementById("locus") != null) {
		new_locus = document.getElementById("locus").value;

		if (new_locus === old_locus) {
			$.xhrPool.abortAll();
			variants_radio_options(status);
		} else if (new_locus != old_locus) {
			getGFF(new_locus);
			old_locus = new_locus;
			setTimeout(function () {
				$.xhrPool.abortAll();
				variants_radio_options(status);
			}, 1650);
		}
	}
}

/**
 * Updates the radio button <DIV> with new variants images.
 */
function variants_radio_options(status) {
	get_input_values();
	$.ajax({
		url: "./cgi-bin/get_gene_structures.cgi?locus=" + locus,
		dataType: "json",
		success: function (gene_res) {
			// Update locus_start and locus_end
			locus_start = gene_res["locus_start"];
			locus_end = gene_res["locus_end"];
			splice_variants = JSON.stringify(gene_res["splice_variants"]);
			populate_table(status);
			populate_efp_modal(status);

			// Remove existing variant images.
			const variants_div = document.getElementById("variants_div");
			if (variants_div !== null && variants_div.firstChild !== null && variants_div.firstChild !== undefined) {
				while (variants_div.firstChild) {
					variants_div.removeChild(variants_div.firstChild);
				}
			}
			$("#variant_select").ddslick("destroy");

			let append_str = '<select id="variant_select">';
			if (gene_res["variant_count"] && parseInt(gene_res["variant_count"]) > 0) {
				for (let i = 0; i < parseInt(gene_res["variant_count"]); i++) {
					if (
						gene_res["splice_variants"] &&
						gene_res["splice_variants"][i] &&
						gene_res["splice_variants"][i]["gene_structure"]
					) {
						// retrieve the base64 and create the element to insert
						append_str += '<option value="' + i + '"';
						append_str +=
							' data-imagesrc="data:image/png;base64,' +
							gene_res["splice_variants"][i]["gene_structure"] +
							'" style="max-width:none;"></option>';
						// Append the element to the div
					}
				}
			} else {
				// retrieve the base64 and create the element to insert
				append_str += '<option value="' + i + '"';
				append_str += ' data-imagesrc="' + img_gene_struct_error + '" style="max-width:none;"></option>';
				// Append the element to the div
			}

			if (
				gene_res["splice_variants"] &&
				gene_res["splice_variants"][0] &&
				gene_res["splice_variants"][0]["gene_structure"]
			) {
				img_gene_struct_1 = "data:image/png;base64," + gene_res["splice_variants"][0]["gene_structure"];

				const all_gene_structure_imgs = document.getElementsByClassName("gene_structure_img");
				for (const element of all_gene_structure_imgs) {
					element.src = "data:image/png;base64," + gene_res["splice_variants"][0]["gene_structure"];
				}
			} else {
				img_gene_struct_1 = img_gene_struct_error;

				const all_gene_structure_imgs = document.getElementsByClassName("gene_structure_img");
				for (const element of all_gene_structure_imgs) {
					element.src = "data:image/png;base64," + gene_res["splice_variants"][0]["gene_structure"];
				}
			}

			$("input[type=radio][name=radio_group]").change(function () {
				// Bind an event listener..
				gene_structure_radio_on_change();
			});

			append_str += "</select></div>";

			$("#variants_div").append(append_str);
			if (document.getElementById("variant_select")) {
				$("#variant_select").ddslick({
					width: "100%",
					onSelected: function () {
						gene_structure_radio_on_change();
					},
				});
			}

			document.getElementById("landing").setAttribute("hidden", "true");
			$("#theTable").trigger("update");
		},
		error: function (xhr, textStatus, errorThrown) {
			displayError("ERROR IN get_gene_structures !");
			generateToastNotification(`Error processing gene structures: ${error.message}`, "ERROR");
			console.log(`Error processing gene structures: ${error.message}`);
		},
	});
}

/**
 * Display an error message to the user
 * @param {String} errorMessage The error message that wish to be displayed
 */
function displayError(errorMessage) {
	$("#displayError").empty();
	let append_str =
		'<p class="warning_core" style="text-align:center;">' +
		errorMessage +
		" <br /><br /> PLEASE REFRESH PAGE, RELOAD OR RE-INPUT DATA OR TRY AGAIN AT A LATER TIME </p>";
	console.error("Error in logic:", errorMessage);
	$("#displayError").append(append_str);
	$("#locus_button").prop("disabled", true);
	$("#abs_scale_button").prop("disabled", true);
	progress_percent = 100;
	$("div#progress").width(progress_percent + "%");
	loadingScreen(true);

	document.title = `eFP-Seq Browser: !ERROR! - ${locus} - ${datasetName}`;
}

/**
 * Logs all errors that flows through eFP-Seq Browser's logic
 * @param {String} errorMessage The error message that wish to be logged
 */
function logError(errorMessage) {
	console.error("Error in logic:", errorMessage);
}

let variantPosition = 0;
let variant_selected;
/**
 * When radio button changes, update the gene structure throughout the document and update the rpb values
 */
function gene_structure_radio_on_change() {
	// Create and update variables
	if (
		document.getElementsByClassName("dd-selected-value") &&
		document.getElementsByClassName("dd-selected-value")[0] &&
		document.getElementsByClassName("dd-selected-value")[0].value
	) {
		/** Index of which variant is selected */
		variant_selected = document.getElementsByClassName("dd-selected-value")[0].value;
		variantPosition = variant_selected;
		/** Image of the variant */
		let variant_img = document.getElementsByClassName("dd-selected-image")[0].src;

		// Check if the variant image has an alt attribute, if not, then add it
		if (
			document.getElementsByClassName("dd-selected-image") &&
			document.getElementsByClassName("dd-selected-image")[0] &&
			!document.getElementsByClassName("dd-selected-image")[0].alt
		) {
			document.getElementsByClassName("dd-selected-image")[0].alt = "RNA-Seq Coverage";
		}

		/** Find all img tags that should be updated (all the <img> with class gene_structure) */
		let all_gene_structure_imgs = document.getElementsByClassName("gene_structure_img");
		// Change their src to the newly selected variant's src
		for (let i = 0; i < all_gene_structure_imgs.length; i++) {
			all_gene_structure_imgs[i].src = variant_img;
		}

		// update all rpb and rpkm values
		// Go through the exp_info array and make changes
		for (let i = 0; i < exp_info.length; i++) {
			let itLocus = exp_info[i][0].split("_")[0];
			/** Update variant image: */
			let geneStructureImg = document.getElementById(itLocus + "_gene_structure_img");
			geneStructureImg.src = variant_img;
			/** Update rpb values: */
			let rpbValue = sraDict[itLocus]["r"][variant_selected].toFixed(2);
			document.getElementById(itLocus + "_rpb").innerHTML = rpbValue;
			if (!sraDict[exp_info[i][0].split("_svg")[0]]) {
				sraDict[exp_info[i][0].split("_svg")[0]] = {};
			}
			sraDict[exp_info[i][0].split("_svg")[0]]["rpb"] = rpbValue;
			/** Update RPKM values: */
			let rpkmValue;
			if (sraDict[itLocus]["RPKM"] && sraDict[itLocus]["RPKM"][variant_selected]) {
				rpkmValue = sraDict[itLocus]["RPKM"][variant_selected].toFixed(2);
			} else {
				if (sraDict[itLocus]["RPKM"]) {
					logError("Unable to retrieve RPKM values at: [variant_selected] for " + itLocus);
				} else if (sraDict[itLocus]) {
					logError('Unable to retrieve RPKM values at: ["RPKM"] for ' + itLocus);
				} else if (sraDict) {
					logError("Unable to retrieve RPKM values at: SRA within sraDict");
				} else {
					logError("Unable to retrieve RPKM values at: sraDict unreachable");
				}
			}
			document.getElementById(itLocus + "_rpkm").innerHTML = rpkmValue;
			whichAbsOrRel(true, i);
		}
	}

	document.getElementById("landing").setAttribute("hidden", "true");
	$("#theTable").trigger("update");
}

/**
 * Which type of absOrRel do you want to call
 * @param {Boolean} preIterate If already iterated through exp_info before calling, then set to true, else leave false
 * @param {Number} iteratePos If preIterate is true, an index position for exp_info must be added here
 */
function whichAbsOrRel(preIterate = false, iteratePos = 0) {
	if (preIterate === true) {
		absOrRel(iteratePos);
	} else {
		if (exp_info.length > 0) {
			for (let i = 0; i < exp_info.length; i++) {
				absOrRel(i);
			}
		}
	}
	change_rpkm_colour_scale(colouring_mode);
}

/**
 * Change the values and colours of the table based on absolute or relative mode selected
 * @param {Number} expInfoPos What the index position of exp_info
 */
function absOrRel(expInfoPos = 0) {
	let expInfo = exp_info[expInfoPos];
	let currentSRA = expInfo[0].slice(0, -4);

	// Update RPKM values and colours
	if (colouring_mode == "rel" && sraDict[currentSRA]["relativeRPKM"]) {
		document.getElementById("compareGeneVariants").disabled = true;
		if (expInfo && !expInfo[4] && expInfo[4] != 0) {
			expInfo[4] = -999999;
		}

		let rpkmValue = sraDict[currentSRA]["relativeRPKM"].toFixed(2);
		document.getElementById(expInfo[0].split("_svg")[0] + "_rpkm").innerHTML = rpkmValue;
		sraDict[expInfo[0].split("_svg")[0]]["rpkm"] = rpkmValue;
		colour_part_by_id(
			currentSRA + "_svg",
			sraDict[currentSRA]["svg_part"],
			sraDict[currentSRA]["relativeRPKM"],
			colouring_mode,
		); // index 5 = relative fpkm
	} else {
		if (allCheckedOptions.length > 0) {
			document.getElementById("compareGeneVariants").disabled = false;
		}
		if (!expInfo[3] && expInfo[3] != 0) {
			expInfo[3] = -999999;
		}

		let useRPKM = "";
		if (variant_selected && sraDict[currentSRA]["RPKM"] && sraDict[currentSRA]["RPKM"][variant_selected]) {
			let rpkmValue = sraDict[currentSRA]["RPKM"][variant_selected].toFixed(2);
			document.getElementById(expInfo[0].split("_svg")[0] + "_rpkm").innerHTML = rpkmValue;
			useRPKM = rpkmValue;
		} else {
			let rpkmValue = 0;
			document.getElementById(expInfo[0].split("_svg")[0] + "_rpkm").innerHTML = rpkmValue;
			useRPKM = rpkmValue;
		}
		colour_part_by_id(currentSRA + "_svg", sraDict[currentSRA]["svg_part"], useRPKM, colouring_mode); // index 3 = absolute fpkm
	}
}

/**
 * Converts numbers stored as str to int.
 */
function parseIntArray(arr) {
	for (let i = 0, len = arr.length; i < len; i++) {
		arr[i] = parseInt(arr[i], 10);
	}
	return arr;
}

let rnaseq_image_url = "cgi-bin/rnaSeqMapCoverage.cgi";
let match_drive = "";
let progress_percent = 0;
let rnaseq_change = 1;
let totalreadsMapped_dic = {};
let dumpOutputs = "";
let dumpMethod = "simple";
let callDumpOutputs = false;
let rpkmCount = 1;
/** An array of all SRA records that have been added to the UI */
let listOfRecordsDisplayed = [];

/**
 * Makes AJAX request for each RNA-Seq image based on the rnaseq_calls array that was produced by the populate_table() function
 */
function rnaseq_images(status) {
	// Verify
	changePublicData();

	// Set variables
	let awsSplit = "amazonaws.com/";
	let araportCDN = "araport.cyverse-cdn.tacc.cloud/";
	let gDriveSplit = "drive.google.com/drive/folders/";

	// Reset variables
	dumpOutputs = "";
	data = {};
	rnaseq_success = 1;
	rpkmCount = 1;
	match_drive = "";
	listOfRecordsDisplayed = [];

	// Start
	get_input_values();
	CreateFilteredeFPList();
	if (rnaseq_calls.length === count_bam_entries_in_xml) {
		rnaseq_change = 1;
		for (let i = 0; i < count_bam_entries_in_xml; i++) {
			/** Creates the tissue variable for the rnaSeqMapCoverage webservice */
			let tissueWebservice = rnaseq_calls[i][0] || "undefined";

			/** SRA Record number */
			let sraRecordNumber = rnaseq_calls[i][1] || "unknown";

			// Creates the removeDrive link for the rnaSeqMapCoverage webservice
			if (sraDict[sraList[i]]["bam_type"] === "Google Drive") {
				// Obtains the Google drive file ID
				let linkString = sraDict[sraList[i]]["drive_link"];
				let driveLinkSplit = linkString.split("?usp=sharing");
				driveLinkSplit = driveLinkSplit[0].split(gDriveSplit);

				if (driveLinkSplit.length > 1) {
					match_drive = driveLinkSplit[1];
				} else {
					match_drive = linkString;
				}
			} else if (sraDict[sraList[i]]["bam_type"] === "Amazon AWS") {
				// Obtains the S3
				let linkString = sraDict[sraList[i]]["drive_link"];
				let driveLinkSplit = linkString.split(awsSplit);

				if (driveLinkSplit.length === 1) {
					driveLinkSplit = linkString.split(araportCDN);
				}
				if (driveLinkSplit.length > 1) {
					match_drive = driveLinkSplit[1];
				} else {
					match_drive = linkString;
				}
			}

			data = {
				status: status,
				numberofreads: sraDict[sraList[i]]["numberofreads"],
				hexcodecolour: sraDict[sraList[i]]["hexColourCode"],
				remoteDrive: match_drive,
				bamType: sraDict[sraList[i]]["bam_type"],
				filename: sraDict[sraList[i]]["filenameIn"],
				tissue: tissueWebservice,
				record: sraRecordNumber,
				locus: locus,
				variant: 1,
				start: locus_start,
				end: locus_end,
				yscale: yscale_input,
				cachedDatapoints: publicData,
				struct: splice_variants,
				dumpMethod: dumpMethod,
			};

			$.ajax({
				method: "POST",
				url: rnaseq_image_url,
				data: data,
				dataType: "json",
				failure: function () {
					$("#failure").show();
				},
				success: function (response_rnaseq) {
					// Update the progress bar
					let stopLoadingScreen = 99;
					if (count_bam_entries_in_xml > 0) {
						stopLoadingScreen = parseInt(((count_bam_entries_in_xml - 1) / count_bam_entries_in_xml) * 100);
					}

					rnaseq_success++;
					let date_obj3 = new Date();
					rnaseq_success_current_time = date_obj3.getTime();
					progress_percent = (rnaseq_change / count_bam_entries_in_xml) * 100;
					$("div#progress").width(progress_percent + "%");
					if (progress_percent > stopLoadingScreen) {
						loadingScreen(true);
					}

					document.getElementById("progress_tooltip").innerHTML =
						"Current progress is at " + progress_percent + "% done";
					document.getElementById("progress").title =
						progress_percent.toFixed(2) + "% (" + rnaseq_change + "/" + count_bam_entries_in_xml + ")";

					document.title = `eFP-Seq Browser:`;
					if (progress_percent < 100) {
						document.title += ` Loading ${progress_percent.toFixed(1)}% -`;
					}
					document.title += ` ${locus} - ${datasetName}`;

					if (
						response_rnaseq["status"] &&
						response_rnaseq["status"] === "success" &&
						response_rnaseq["record"]
					) {
						/** Respond record ID to use */
						let responseRecord = response_rnaseq["record"] || "unknown";

						// Check if responseRecord has been used yet
						if (listOfRecordsDisplayed.includes(responseRecord)) {
							responseRecord = findUnusedRecordDisplayName(responseRecord, listOfRecordsDisplayed);
							listOfRecordsDisplayed.push(responseRecord);
						} else {
							listOfRecordsDisplayed.push(responseRecord);
						}

						listOfRecordsDisplayed = [];

						sraDict[responseRecord]["bp_length"] =
							parseFloat(response_rnaseq["end"]) - parseFloat(response_rnaseq["start"]);
						sraDict[responseRecord]["bp_start"] = parseFloat(response_rnaseq["start"]);
						sraDict[responseRecord]["bp_end"] = parseFloat(response_rnaseq["end"]);
						sraDict[responseRecord]["MappedReads"] = response_rnaseq["reads_mapped_to_locus"];
						totalreadsMapped_dic[responseRecord] = response_rnaseq["totalReadsMapped"];
						sraDict[responseRecord]["locusValue"] = response_rnaseq["locus"];
						sraDict[responseRecord]["r"] = response_rnaseq["r"];
						sraDict[responseRecord]["dataVisualization"] = response_rnaseq["rnaseqbase64"];

						if (locus != response_rnaseq["locus"]) {
							throw new Error(
								`ERROR: ${locus}'s RNA-Seq API request returned with data for some other locus.`,
							);
						}

						let r = [];
						if (
							response_rnaseq["ss_y"] &&
							response_rnaseq["sum_y"] &&
							response_rnaseq["sum_xy"] &&
							response_rnaseq["sum_x"] &&
							response_rnaseq["ss_x"] &&
							response_rnaseq["end"] &&
							response_rnaseq["start"]
						) {
							// Finalize statistical calculations
							let ss_y = parseInt(response_rnaseq["ss_y"]);
							let sum_y = parseInt(response_rnaseq["sum_y"]);
							let ssy = parseInt(response_rnaseq["ss_y"]);
							let sum_xy = parseIntArray(
								response_rnaseq["sum_xy"]
									.replace(/\[/g, "")
									.replace(/\]/g, "")
									.replace(/"/g, "")
									.split(","),
							);
							let sum_x = parseIntArray(
								response_rnaseq["sum_x"]
									.replace(/\[/g, "")
									.replace(/\]/g, "")
									.replace(/"/g, "")
									.split(","),
							);
							let sum_xx = parseIntArray(
								response_rnaseq["sum_xx"]
									.replace(/\[/g, "")
									.replace(/\]/g, "")
									.replace(/"/g, "")
									.split(","),
							);
							let ss_x = parseIntArray(
								response_rnaseq["ss_x"]
									.replace(/\[/g, "")
									.replace(/\]/g, "")
									.replace(/"/g, "")
									.split(","),
							);
							let ssx = parseIntArray(
								response_rnaseq["ss_x"]
									.replace(/\[/g, "")
									.replace(/\]/g, "")
									.replace(/"/g, "")
									.split(","),
							);
							let n = parseInt(response_rnaseq["end"]) - parseInt(response_rnaseq["start"]);
							let sp = [];

							// Compute the r values for each variant
							for (let i = 0; i < sum_xy.length; i++) {
								sp.splice(i, 0, sum_xy[i] - (sum_x[i] * sum_y) / n);
								r.splice(i, 0, sp[i] / Math.sqrt(ssx[i] * ssy));
							}
						} else {
							r = response_rnaseq["r"];
						}

						if (
							document.getElementById(responseRecord + "_rnaseq_img") &&
							response_rnaseq["rnaseqbase64"]
						) {
							if (
								response_rnaseq["rnaseqbase64"] !== "None" &&
								response_rnaseq["rnaseqbase64"].length >= 3
							) {
								document.getElementById(responseRecord + "_rnaseq_img").src =
									"data:image/png;base64," + response_rnaseq["rnaseqbase64"];
								rnaseq_change += 1;
							} else {
								document.getElementById(responseRecord + "_rnaseq_img").src =
									"https://" +
									window.location.host +
									window.location.pathname +
									"cgi-bin/img/error.webp";

								console.error(
									"Unable to create RNA-Seq map coverage data for: Locus - " +
										locus +
										", SRA - " +
										responseRecord +
										", dataset - " +
										base_src,
								);
							}
						} else {
							if (document.getElementById(`${responseRecord}_rnaseq_img`)) {
								document.getElementById(`${responseRecord}_rnaseq_img`).src =
									`https://${window.location.host}${window.location.pathname}/cgi-bin/img/error.webp`;
							}

							console.error(
								"Unable to create RNA-Seq map coverage data for: Locus - " +
									locus +
									", SRA - " +
									responseRecord +
									", dataset - " +
									base_src,
							);
						}

						document.getElementById(responseRecord + "_rpb").innerHTML = parseFloat(r[0]).toFixed(2);
						sraDict[responseRecord]["rpb"] = parseFloat(r[0]).toFixed(2);

						document.getElementById(responseRecord + "_rpkm").innerHTML = response_rnaseq["absolute-fpkm"];
						updateRPKMAbsoluteMax(response_rnaseq["absolute-fpkm"]);
						sraDict[responseRecord]["RPKM"] = response_rnaseq["absolute-fpkm"];
						rpkmCount++;

						document.getElementById(responseRecord + "_totalReadsNum").innerHTML =
							"Total reads = " + response_rnaseq["totalReadsMapped"];

						// Generate pre-caching information
						if (callDumpOutputs) {
							dumpOutputs += '\t\telif (record == "' + response_rnaseq["record"] + '"):\n';
							if (dumpMethod == "complex") {
								dumpOutputs +=
									'\t\t\tdumpJSON(200, "' +
									response_rnaseq["locus"] +
									'", ' +
									response_rnaseq["variant"] +
									", " +
									response_rnaseq["chromosome"] +
									", " +
									response_rnaseq["start"] +
									", " +
									response_rnaseq["end"] +
									', "' +
									response_rnaseq["record"] +
									'", "' +
									response_rnaseq["tissue"] +
									'", "' +
									response_rnaseq["rnaseqbase64"] +
									'", ' +
									response_rnaseq["reads_mapped_to_locus"] +
									", " +
									response_rnaseq["absolute-fpkm"] +
									", [" +
									response_rnaseq["r"] +
									"], " +
									response_rnaseq["totalReadsMapped"] +
									", [" +
									response_rnaseq["exp_arr"] +
									"], [";

								for (r = 0; r < response_rnaseq["ReadsMappedNucleotidePosition"].length; r += 2) {
									dumpOutputs += "[" + response_rnaseq["ReadsMappedNucleotidePosition"][r] + "]";
									if (r != response_rnaseq["ReadsMappedNucleotidePosition"].length - 2) {
										dumpOutputs += ", ";
									}
								}

								dumpOutputs += "], {";
								for (let e = 0; e < response_rnaseq["expected_expr_in_variant"].length; e++) {
									dumpOutputs += '"' + GFF_List[e].replace(locus, "") + '": ';
									dumpOutputs += "[" + response_rnaseq["expected_expr_in_variant"][e] + "]";
									if (e != response_rnaseq["expected_expr_in_variant"].length - 1) {
										dumpOutputs += ", ";
									}
								}

								dumpOutputs += "})\n";
							} else {
								dumpOutputs +=
									'\t\t\tdumpJSON(200, "' +
									response_rnaseq["locus"] +
									'", ' +
									response_rnaseq["variant"] +
									", " +
									response_rnaseq["chromosome"] +
									", " +
									response_rnaseq["start"] +
									", " +
									response_rnaseq["end"] +
									', "' +
									response_rnaseq["record"] +
									'", "' +
									response_rnaseq["tissue"] +
									'", "' +
									response_rnaseq["rnaseqbase64"] +
									'", ' +
									response_rnaseq["reads_mapped_to_locus"] +
									", [" +
									response_rnaseq["absolute-fpkm"] +
									"], [" +
									response_rnaseq["r"] +
									"], " +
									response_rnaseq["totalReadsMapped"] +
									")\n";
							}
						}

						// Save the abs-fpkm, and the stats numbers
						for (let ii = 0; ii < count_bam_entries_in_xml; ii++) {
							if (
								exp_info &&
								exp_info[ii] &&
								exp_info[ii][0] &&
								exp_info[ii][0] == responseRecord + "_svg"
							) {
								// Find the correct element
								exp_info[ii].splice(3, 1, response_rnaseq["absolute-fpkm"]);
								exp_info[ii].splice(5, 1, r);

								//console.log("Found " + responseRecord + " == " + exp_info[ii][0] + ".");
							}
						}

						colour_part_by_id(
							responseRecord + "_svg",
							"Shapes",
							response_rnaseq["absolute-fpkm"][variantPosition],
							colouring_mode,
						);
					} else if (response_rnaseq["status"] && response_rnaseq["status"] === "fail") {
						/** Respond record ID to use */
						let responseRecord = response_rnaseq["record"] || "unknown";

						// Check if responseRecord has been used yet
						if (listOfRecordsDisplayed.includes(responseRecord)) {
							responseRecord = findUnusedRecordDisplayName(responseRecord, listOfRecordsDisplayed);
							listOfRecordsDisplayed.push(responseRecord);
						} else {
							listOfRecordsDisplayed.push(responseRecord);
						}

						// Update image to error
						if (responseRecord && document.getElementById(`${responseRecord}_rnaseq_img`)) {
							document.getElementById(`${responseRecord}_rnaseq_img`).src =
								`https://${window.location.host}${window.location.pathname}/cgi-bin/img/error.webp`;
						}
						rnaseq_change += 1;

						if (responseRecord && document.getElementById(responseRecord + "_rpb")) {
							document.getElementById(responseRecord + "_rpb").innerHTML = null;
							if (!sraDict[responseRecord]) {
								sraDict[responseRecord] = {};
							}
							sraDict[responseRecord]["rpb"] = null;
						}

						if (responseRecord && document.getElementById(responseRecord + "_rpkm")) {
							document.getElementById(responseRecord + "_rpkm").innerHTML = null;
							updateRPKMAbsoluteMax(null);
							sraDict[responseRecord]["RPKM"] = null;
						}
						rpkmCount++;

						if (responseRecord && document.getElementById(responseRecord + "_totalReadsNum")) {
							if (response_rnaseq["totalReadsMapped"]) {
								document.getElementById(responseRecord + "_totalReadsNum").innerHTML =
									"Total reads = " + response_rnaseq["totalReadsMapped"];
							}
						}

						if (responseRecord && document.getElementById(responseRecord + "_row")) {
							document.getElementById(responseRecord + "_row").classList.add("mainEntriesError");
						}

						console.error(
							"Unable to create RNA-Seq map coverage data for: Locus - " +
								locus +
								", SRA - " +
								responseRecord +
								", dataset - " +
								base_src,
						);
					} else {
						console.log("Error!", response_rnaseq, data);
					}

					if (rpkmCount == count_bam_entries_in_xml) {
						colour_svgs_now();
						date_obj4 = new Date();
						rnaseq_success_end_time = date_obj4.getTime();

						// console.log(rnaseq_success_end_time);

						document.getElementById("progress_tooltip").innerHTML =
							rnaseq_success +
							" / count_bam_entries_in_xml requests completed<br/>Load time ~= " +
							String(round(parseInt(rnaseq_success_end_time - rnaseq_success_start_time) / (1000 * 60))) +
							" mins.";

						// console.log("**** Requests = " + String(rnaseq_success) + ", time delta = " + String(parseInt(rnaseq_success_end_time - rnaseq_success_start_time)));
					}

					document.getElementById("landing").setAttribute("hidden", "true");
					$("#theTable").trigger("update");
					responsiveRNAWidthResize();
					toggleResponsiveTable();
				},
				error: function (xhr, status, error) {
					generateToastNotification(
						`Error getting RNA-Seq map coverage for ${data.record} - ${error.message}`,
						"ERROR",
					);
					console.error("Error getting RNA-Seq map coverage!", xhr, status, error);
				},
			});
		}
	}
}

/**
 * Find what alteration of the record name is not already used
 * @param {String} recordID The record name (defaults to 'unknown')
 * @param {Array} listCheckAgainst What array it is being checked against
 * @param {Number} it The iteration count, starts at 0
 * @returns {String} newName - The new unused alteration of the record ID
 */
function findUnusedRecordDisplayName(recordID = "unknown", listCheckAgainst = sraList, it = 0) {
	if (Array.isArray(listCheckAgainst)) {
		/** New altered record name with a '_#' added to the record ID */
		let newName = recordID + "_" + it;

		if (listCheckAgainst.includes(newName)) {
			findUnusedRecordDisplayName(recordID, listCheckAgainst, it + 1);
		} else if (!listCheckAgainst.includes(newName)) {
			return newName;
		}
	} else {
		listCheckAgainst = [];

		findUnusedRecordDisplayName(recordID, listCheckAgainst);
	}
}

/**
 * Check whether the RPKM Absolute Max is actually the absolute max or not
 * @param {Number} RPKMCheckAgainst The RPKM value to check against the max to see if needs to change or not
 */
function updateRPKMAbsoluteMax(RPKMCheckAgainst) {
	let currentRPKMAbsMax = parseInt(document.getElementById("rpkm_scale_input").value);
	if (currentRPKMAbsMax === 1000) {
		currentRPKMAbsMax = 1;
	}

	let newRPKMValue = parseInt(RPKMCheckAgainst);
	if (newRPKMValue > currentRPKMAbsMax) {
		document.getElementById("rpkm_scale_input").value = newRPKMValue;
	}
}

/**
 * Data object for checkAgainstSVG to find the appropriate SVG subunit name
 * Organization: [svg file name]: {
 * 	"name" {string}: "Human readable name",
 * 	"subunit"? {string[]}: ["default subunit name", "other subunit name", "other subunit name", ...]
 *	"subunitName"? {string}: "custom default subunit name (output) not listed in subunit"
 * }
 */
const svgAgainstData = {
	"ath-10dayOldSeedling": {
		name: "10 Day Old Seedling",
		subunit: ["all", "root", "shoot"],
	},
	"ath-15dayOldSeedling": {
		name: "15 Day Old Seedling",
		subunit: ["all", "root", "shoot"],
	},
	"ath-etiolatedSeedling": {
		name: "Etiolated Seedling",
		subunit: ["etiolatedseedling"],
	},
	"ath-Flower": {
		name: "Flower",
		subunit: ["flower", "receptacle"],
	},
	"ath-FlowerParts": {
		name: "Flower Parts",
		subunit: ["all", "petals", "stamen", "sepals", "carpels"],
	},
	"ath-GerminatingSeed": {
		name: "Germinating Seed",
	},
	"ath-Internode": {
		name: "Internode",
	},
	"ath-leaf": {
		name: "Leaf",
		subunit: ["leaf"],
	},
	"ath-LeafParts": {
		name: "Leaf Parts",
		subunit: ["all", "lamina", "petiole", "veins"],
	},
	"ath-Pollen": {
		name: "Pollen",
	},
	"ath-RootTip": {
		name: "Root Tip",
	},
	"ath-rosettePlusRoot": {
		name: "Rosette Plus Root",
		subunit: ["all", "shoot", "root"],
	},
	"ath-Seed1-4": {
		name: "Seed 1-4",
	},
	"ath-Seed5-7": {
		name: "Seed 5-7",
	},
	"ath-Seed8+": {
		name: "Seed 8+",
	},
	"ath-SenescentLeaf": {
		name: "Senescent Leaf",
	},
	"ath-ShootApexInflorescense": {
		name: "Shoot Apex Inflorescense",
	},
	"ath-ShootApexVegetative-Transition": {
		name: "Shoot Apex Vegetative-Transition",
	},
	"ath-Silique1-5": {
		name: "Silique 1-5",
	},
	"ath-Silique6-10": {
		name: "Silique 6-10",
	},
	"ath-YoungLeaf1-4": {
		name: "Young Leaf 1-4",
	},
	"ath-EarlyBuddingFlower": {
		name: "Early Budding Flower",
		subunit: ["all", "shoot", "buds"],
	},
	"ath-EarlyBuddingFlower": {
		name: "Early Budding Flower",
		subunit: ["all", "shoot", "buds"],
	},
	"ath-FlowerBud": {
		name: "Flower Bud",
		subunit: ["flowerBud"],
	},
	"ath-Stamen": {
		name: "Stamen",
		subunit: ["all", "anthers", "filament"],
	},
	"ath-StigmaAndOvaries": {
		name: "Stigma And Ovaries",
		subunit: ["all", "Stigma_tissue", "Ovary_tissue"],
	},
	"ath-WholeSilique": {
		name: "Whole Silique",
		subunit: ["silique", "all", "seed"],
	},
	"ath-youngSeedling": {
		name: "Young Seedling",
		subunit: ["all", "root", "hypocotyl", "cotyledon"],
	},
	"ath-FlowerDevelopment1": {
		name: "Late Flower Development (1)",
		subunit: ["flowerDevelopmentPart1"],
	},
	"ath-FlowerDevelopment2": {
		name: "Flower Development 2",
		subunit: ["flowerDevelopmentPart2"],
	},
	"ath-FlowerDevelopment3": {
		name: "Flower Development 3",
		subunit: ["flowerDevelopmentPart3"],
	},
	"ath-FlowerDevelopment4": {
		name: "Flower Development 4",
		subunit: ["flowerDevelopmentPart4"],
	},
	"ath-FlowerDevelopment5": {
		name: "Flower Development 5",
		subunit: ["flowerDevelopmentPart5"],
	},
	"ath-FlowerDevelopment6-8": {
		name: "Flower Development 6-8",
		subunit: ["flowerDevelopmentPart6"],
	},
	"ath-FlowerDevelopment9-11": {
		name: "Flower Development 9-11",
		subunit: ["flowerDevelopmentPart9"],
	},
	"ath-FlowerDevelopment12-14": {
		name: "Flower Development 12-14",
		subunit: ["flowerDevelopmentPart12"],
	},
	"ath-FlowerDevelopment15-18": {
		name: "Flower Development 15-18",
		subunit: ["flowerDevelopmentPart15"],
	},
	"ath-FlowerDevelopment19": {
		name: "Flower Development 19",
		subunit: ["flowerDevelopmentPart19"],
	},
	"ath-Other": {
		name: "Other",
	},
};

/**
 * Checking to make sure the subunit matches tissue
 * @param {String} svg SVG name starting with ath- and ending with .svg
 * @param {String} subunit SVG subunit
 * @param {Bool} returnName True = return human readable name, false = return subunit
 * @return {String} subunit - The SVG tissue corrected subunit if an error occurred, input if not
 */
function checkAgainstSVG(svg, subunit, returnName = false) {
	/** SVG file name */
	let svgName = svg.split(".")[0];

	let toReturn = returnName ? svgAgainstData[svgName]["name"] : subunit;

	// Get subunit name
	if (svgAgainstData[svgName] && !returnName) {
		// If there is a list of subunits, check if it contains the given subunit and what subunit name should be used
		if (svgAgainstData[svgName]["subunit"]) {
			if (!svgAgainstData[svgName]["subunit"].includes(subunit)) {
				if (svgAgainstData[svgName]["subunit_name"]) {
					toReturn = svgAgainstData[svgName]["subunit_name"];
				} else if (svgAgainstData[svgName]["subunit"][0]) {
					toReturn = svgAgainstData[svgName]["subunit"][0];
				}
			}
		} else if (subunit !== "all") {
			toReturn = "all";
		}
	}

	return toReturn;
}

let sraList = [];
/** A dictionary containing all calculated information for all data points */
let sraDict = {};
let sraCountDic = {};
let tissueSRADic = {};

let efp_table_column;
/** Title of the dataset being loaded */
let datasetName = "data";
let variantdiv_str;
let iteration_num = 1;
let moreDetails = 'Show More Details <i class="material-icons detailsIcon">arrow_drop_down</i>';
let lessDetails = 'Show Less Details <i class="material-icons detailsIcon">arrow_drop_up</i>';
/**
 * Gets the BAM locator XML to create + populate the table. Leeps track of all RNA-Seq calls it will have to make.
 * @param {String | Number} status Index call version
 */
function populate_table(status) {
	// Reset values
	$("#theTable").empty();
	$("#compareTable").empty();
	rnaseq_calls = [];
	exp_info = [];
	rnaseq_success = 0;
	date_obj5 = new Date();
	rnaseq_success_start_time = date_obj5.getTime(); // Keep track of start time
	max_absolute_fpkm = -1;
	max_log_fpkm = -1;
	svg_colouring_element = null;
	gene_structure_colouring_element = null;
	sraList = [];
	sraDict = {};
	sraCountDic = {};
	tissueSRADic = {};
	rpkmAverage = 1;
	rpkmMedian = 1;

	// Creating exon intron scale image
	let img_created =
		'<img loading="lazy" src="' +
		"data:image/png;base64," +
		exon_intron_scale +
		'" alt="RNA-Seq mapped image" style="float: right; margin-right: 10px;">';

	// Insert table headers
	let tableHeader =
		"<thead><tr>" +
		'<th class="sortable colTitle" id="colTitle" onclick="ChangeColArrow(this.id)" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 250px;"><div class="row" id="colTitleRow"><div class="col-10">Title</div><div class="col-1"><img loading="lazy" class="sortingArrow" id="colTitleArrow" src="./cgi-bin/SVGs/arrowDefault.svg" alt="Sorting arrow"></div></div></th>' +
		'<th class="colRNA" id="colRNA" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; max-width: 576px;">RNA-Seq Coverage' +
		img_created +
		"</th>" +
		'<th class="sortable colrpb" id="colrpb" onclick="ChangeColArrow(this.id)" title="Point biserial correlation coefficient. Closer to 1 suggests a \'best\' match" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;"><div class="row" id="colrpbRow"><div class="col-7" >r<sub>pb</sub></div><div class="col-1"><img loading="lazy" class="sortingArrow" id="colrpbArrow" src="./cgi-bin/SVGs/arrowDefault.svg" alt="Default sort arrow"></div></div></th>' +
		'<th class="coleFP" id="eFP_th" class="sortable" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 100px;">eFP (RPKM)</th>' +
		'<th class="sortable colRPKM" id="colRPKM" onclick="ChangeColArrow(this.id)" title="Reads Per Kilobase of transcript per Million mapped reads. Higher number suggest more mapped reads/expression" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;"><div class="row" id="colRPKMRow"><div class="col-8">RPKM</div><div class="col-1"><img loading="lazy" class="sortingArrow" id="colRPKMArrow" src="./cgi-bin/SVGs/arrowDefault.svg" alt="Default sort arrow"></div></div></th>' +
		'<th class="sortable colDetails" id="colDetails" onclick="ChangeColArrow(this.id)" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 275px;"><div class="row" id="colDetailsRow"><div class="col-10">Details</div><div class="col-1"><img loading="lazy" class="sortingArrow" id="colDetailsArrow" src="./cgi-bin/SVGs/arrowDefault.svg" alt="Default sort arrow"></div></div></th>' +
		'<th class="sortable colCompare" id="colCompare" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; max-width: 30px;" hidden><div class="row" id="colCompareRow"></div></th>' +
		"</tr></thead>" +
		'<tbody id="data_table_body"></tbody>';
	$("#theTable").append(tableHeader);
	// Create compare table header:
	let compareHeader =
		"<thead><tr>" +
		'<th id="compare_colTitle" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 250px;"><div class="row" id="compare_colTitleRow"><div class="col-xs-10">Title</div></div></th>' +
		'<th id="compare_colRNA" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; max-width: 576px;">RNA-Seq Coverage' +
		img_created +
		"</th>" +
		'<th id="compare_colrpb" title="Point biserial correlation coefficient. Closer to 1 suggests a \'best\' match" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;"><div class="row" id="compare_colrpbRow"><div class="col-xs-6">r<sub>pb</sub></div></div></th>' +
		'<th id="compare_eFP_th" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 100px;">eFP (RPKM)</th>' +
		'<th id="compare_colRPKM" title="Reads Per Kilobase of transcript per Million mapped reads. Higher number suggest more mapped reads/expression" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;"><div class="row" id="compare_colRPKMRow"><div class="col-xs-7">RPKM</div></div></th>' +
		'<th id="compare_colDetails" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 275px;"><div class="row" id="compare_colDetailsRow"><div class="col-xs-10">Details</div></div></th>' +
		"</tr></thead>" +
		'<tbody id="compare_table_body"></tbody>';
	$("#compareTable").append(compareHeader);

	$.ajax({
		url: base_src,
		dataType: "xml",
		success: function (xml_res) {
			let $xmltitle = $(xml_res).find("files");
			$xmltitle.each(function () {
				datasetName = $(this).attr("xmltitle") || "Uploaded dataset";
				datasetName = datasetName.trim();

				if (datasetName.length === 0) {
					datasetName = "Uploaded dataset";
				}

				document.getElementById("uploaded_dataset").innerHTML = datasetName;
			});

			document.title = `eFP-Seq Browser:`;
			if (progress_percent < 100) {
				document.title += ` Loading ${progress_percent.toFixed(1)}% -`;
			}
			document.title += ` ${locus} - ${datasetName}`;

			iteration_num = 1;
			let $title = $(xml_res).find("file");
			$title.each(function () {
				// Iterate over each sub-tag inside the <file> tag.
				// Extract information
				/** Respond record ID to use */
				let experimentno = $(this).attr("record_number") || "unknown";

				// Check if responseRecord has been used yet
				if (sraList.includes(experimentno)) {
					experimentno = findUnusedRecordDisplayName(experimentno, sraList);
				}

				if (sraList.includes(experimentno)) {
					if (sraCountDic[experimentno]) {
						sraCountDic[experimentno] += 1;
						let tempExperimentNo = experimentno + "(" + sraCountDic[experimentno] + ")";
						sraList.push(tempExperimentNo);
						sraDict[tempExperimentNo] = {};
					}
				} else {
					sraCountDic[experimentno] = 1;
					sraList.push(experimentno);
					sraDict[experimentno] = {};
				}

				/** Title */
				let title = $(this).attr("description");
				sraDict[experimentno]["title"] = title;

				/** Description */
				let description = $(this).attr("info");
				sraDict[experimentno]["description"] = description;

				/** SVG */
				let svg = $(this).attr("svgname");
				sraDict[experimentno]["svg"] = svg;
				let svg_part = $(this).attr("svg_subunit");
				svg_part = checkAgainstSVG(svg, svg_part);
				sraDict[experimentno]["svg_part"] = svg_part;
				if (tissueSRADic[checkAgainstSVG(svg, svg_part, true)]) {
					tissueSRADic[checkAgainstSVG(svg, svg_part, true)].push(experimentno);
				} else {
					tissueSRADic[checkAgainstSVG(svg, svg_part, true)] = [experimentno];
				}

				/** SRA URL */
				let url = $(this).attr("url");
				sraDict[experimentno]["url"] = url;

				/** Publication URL */
				let publicationid = $(this).attr("publication_link");
				sraDict[experimentno]["publicationid"] = publicationid;

				/** Total number of reads */
				let numberofreads = $(this).attr("total_reads_mapped");
				if (numberofreads == null || numberofreads == "") {
					numberofreads = "0";
				}
				sraDict[experimentno]["numberofreads"] = numberofreads;

				/** Coloured hex code */
				let hexColourCode;
				if ($(this).attr("hex_colour") == null || $(this).attr("hex_colour") == "") {
					hexColourCode = "0x64cc65";
				} else {
					hexColourCode = $(this).attr("hex_colour");
				}
				sraDict[experimentno]["hexColourCode"] = hexColourCode;

				/** BAM file's filename */
				let filenameIn = $(this).attr("filename");
				if (filenameIn == null || filenameIn == "" || filenameIn == undefined) {
					filenameIn = "accepted_hits.bam";
				}
				sraDict[experimentno]["filenameIn"] = filenameIn;

				/** Species */
				let species = $(this).attr("species");
				sraDict[experimentno]["species"] = species;

				/** Control */
				let controls = [];
				if ($(this).find("controls")[0].innerHTML == undefined) {
					for (let i = 1; i < $(this).find("controls")[0].childNodes.length; i + 2) {
						controls.push($(this).find("controls")[0].childNodes[i].firstChild.textContent);
					}
				} else if ($(this).find("controls")[0].innerHTML != undefined) {
					controls = $(this)
						.find("controls")[0]
						.innerHTML.replace(/<bam_exp>/g, "")
						.replace(/<\/bam_exp>/g, ",")
						.replace(/\n/g, " ")
						.replace(/ /g, "")
						.split(",");
				}
				sraDict[experimentno]["controls"] = controls;

				let links = "";
				if (controls.length > 0) {
					for (let i = controls.length; i--; ) {
						if (controls[i] != "MEDIAN") {
							links +=
								'<a href="https://www.ncbi.nlm.nih.gov/Traces/sra/?run=' +
								controls[i] +
								'"target="_blank" rel="noopener">' +
								controls[i] +
								"</a> ";
						} else {
							links += controls[i];
						}
					}
				}
				sraDict[experimentno]["links"] = links;

				let controlsString = "";
				if (controls.length > 0) {
					for (let y = 0; y < controls.length; y++) {
						controlsString += controls[y].toString();
						if (y < controls.length - 2) {
							controlsString += ", ";
						}
					}
				}
				sraDict[experimentno]["controlsString"] = controlsString.trim();

				let name = $(this).attr("name");
				sraDict[experimentno]["name"] = name;

				let tissue = $(this).attr("svgname");
				if (tissue) {
					if (tissue.trim().substr(0, 4) === "ath-") {
						tissue = tissue.slice(4, tissue.length).trim();
					}
					if (tissue.trim().substr(tissue.length - 4, 4) === ".svg") {
						tissue = tissue.slice(0, tissue.length - 4).trim();
					}
				}
				rnaseq_calls.push([tissue, experimentno]);
				sraDict[experimentno]["tissue"] = tissue;

				let bam_type = $(this).attr("bam_type");
				sraDict[experimentno]["bam_type"] = bam_type;

				let drive_link = $(this).attr("name");
				sraDict[experimentno]["drive_link"] = drive_link;

				let read_map_method = $(this).attr("read_map_method");
				sraDict[experimentno]["read_map_method"] = read_map_method;

				// Setup IGB
				let igbView_link = "https://bioviz.org/bar.html?";
				igbView_link += "version=A_thaliana_Jun_2009&";
				// Load custom data
				igbView_link += "gene_id=" + locus + "&";
				igbView_link += "feature_url_0=" + drive_link + "&";
				igbView_link += "genome=A_thaliana_Jun_2009&";
				igbView_link += "annotation_set=Araport11&";
				igbView_link += "query_url=" + drive_link + "&";
				// Closing
				igbView_link += "server_url=bar";

				// Construct a table row <tr> element
				let append_str = '<tr class="mainEntries" id="' + experimentno + '_row">';

				/** table_dl_str is used for downloading the table as CSV */
				let table_dl_str = "<table id='table_dl'>\n\t<tbody>\n";
				table_dl_str += "\t\t<caption>" + document.getElementById("xmlDatabase").value + "</caption>\n";

				// Append title <td>
				append_str +=
					'<td class="colTitle" style="width: 250px; font-size: 12px;" id="' +
					experimentno +
					'_title">' +
					title +
					"</td>\n";

				// Append RNA-Seq and Gene Structure images (2 imgs) in one <td>
				append_str += `
					<td class="colRNA" style="max-width: 576px;">
						<img
							loading="lazy"
							id="${experimentno}_rnaseq_img"
							alt="RNA-Seq mapped image for: ${experimentno}"
							style="min-width:420px; max-width:576px; width:95%; height: auto;"
							class="rnaseq_img responsiveRNAWidth"
							src="${img_loading_base64}"
						/>

						<br/>

						<img
							loading="lazy"
							id="${experimentno}_gene_structure_img"
							style="max-width: 576px; width:100%; height: auto;"
							class="gene_structure_img"
							src="${img_gene_struct_1}"
							alt="Gene variant image for: ${experimentno}"
						/>
					</td>\n
				`;

				// Append the rpb <td>
				append_str +=
					'<td id="' +
					experimentno +
					"_rpb" +
					'" class="rpb_value colrpb" style="font-size: 12px; width: 50px; ">' +
					-9999 +
					"</td>";

				// Append the appropriate SVG with place holder sorting number in front of it .. all in one <td>
				append_str +=
					'<td class="coleFP" tag="svg_name" style="width:  75px;">' +
					'<div id="' +
					experimentno +
					'_svg" name="' +
					svg.substring(0, svg.length - 4).slice(4) +
					'_tissue" tag=' +
					svg_part +
					'_subtissue" width="75" height="75" style="width: 75px; height: 75px; max-width: 75px; max-height: 75px;">' +
					document.getElementById(svg.substring(4).replace(".svg", "_svg")).innerHTML +
					"</div>" +
					'<div class="mdl-tooltip" for="' +
					experimentno +
					"_svg" +
					'">' +
					svg.substring(4).replace(".svg", "") +
					"</div></td>\n";

				// Append abs/rel RPKM
				append_str +=
					'<td class="colRPKM" id="' +
					experimentno +
					"_rpkm" +
					'" style="font-size: 12px; width: 50px; ">-9999</td>';

				// Append the details <td>
				append_str +=
					'<td class="colDetails" id="' +
					experimentno +
					'_details" style="font-size: 12px;"><div id="' +
					experimentno +
					'_description" name="' +
					description.trim() +
					'">' +
					truncateDescription(description) +
					"</div>";

				if (bam_type === "Amazon AWS") {
					append_str +=
						'<div id="igbLink_' +
						experimentno +
						'">Show: <a href="' +
						igbView_link +
						'" target="_blank" rel="noopener">Alignments in IGB</a></div>';
				}

				if (!experimentno.includes("unknown") || publicationid) {
					append_str += '<div id="extraLinks_' + experimentno + '">Go to: ';

					if (!experimentno.includes("unknown")) {
						append_str += '<a href="' + url + '" target="_blank" rel="noopener">NCBI SRA</a>';
					}

					if (experimentno.includes("unknown") && publicationid) {
						append_str += " or ";
					}

					if (publicationid) {
						append_str += '<a href="' + publicationid + '" target="_blank" rel="noopener">PubMed</a>';
					}

					append_str += "</div>";
				}

				append_str +=
					'<a id="clickForMoreDetails_' +
					iteration_num +
					'" name="' +
					experimentno +
					'_description" onclick="clickDetailsTextChange(this.id)" href="javascript:(function(){$(\'#' +
					experimentno +
					"').toggle();})()\">" +
					moreDetails.trim() +
					"</a>";

				append_str += '<div id="' + experimentno + '" class="moreDetails" style="display:none">';

				if (links) {
					append_str += "Controls: " + links + "<br/>";
				}

				append_str += "Species: " + species + "<br>";
				append_str += '<div id="' + experimentno + '_sra">' + "SRA: " + experimentno + "</div>";
				append_str +=
					'<div id="' + experimentno + '_totalReadsNum">' + "Total reads = " + numberofreads + "</div>";

				if (read_map_method != undefined && read_map_method.length > 0) {
					append_str +=
						'<div id="' +
						experimentno +
						'_readMappedMethod">' +
						"Read map method = " +
						read_map_method.trim() +
						"</div>";
				}

				append_str +=
					'<a id="clickForMoreDetails_' +
					iteration_num +
					'_less" name="' +
					experimentno +
					'_description" onclick="clickDetailsTextChange(this.id)" href="javascript:(function(){$(\'#' +
					experimentno +
					"').toggle();})()\">" +
					lessDetails +
					"</a></div></td>\n";

				append_str +=
					'<td class="colCompare" style="font-size: 12px; max-width: 30px;"><div id="' +
					experimentno +
					'_compareVariant"><input type="checkbox" name="compareCheckbox" class="compareCheckbox" value="compareCheckbox" id="' +
					experimentno +
					'_compareCheckbox" onclick="tableCheckbox(this.id);"></div></td>';
				append_str += "</tr>";

				iteration_num++;

				// Append the <tr> to the table
				$("#theTable").append(append_str);

				/** Check to see if compare column missing classname */
				let compareColumn = document.getElementsByClassName("fltrow")[0]["childNodes"][6];
				if (
					(compareColumn && compareColumn.classList[0] === undefined) ||
					compareColumn.classList[0] === "undefined"
				) {
					compareColumn.classList = ["colCompare"];
					compareColumn.innerHTML =
						'<input type="checkbox" name="compareCheckbox" class="compareCheckbox" value="compareCheckbox" id="allCheckbox" onclick="disableAllComparison();">';
				}

				exp_info.push([experimentno + "_svg", svg_part, controls, 0, 0, 0, 0]);

				if (loadNewDataset === true) {
					setTimeout(function () {
						count_bam_num();
					}, 200);
					setTimeout(function () {
						rnaseq_images(status);
					}, 10);
				} else {
					rnaseq_images(status);
				}
			});
			// add parser through the tablesorter addParser method
			$.tablesorter.addParser({
				// set a unique id
				id: "rpb_sorter",
				is: function (s) {
					// return false so this parser is not auto detected
					return false;
				},
				format: function (s) {
					// format your data for normalization
					if (s == NaN) {
						return -99999;
					} else if (s == undefined) {
						return -999999;
					} else if (s == Infinity) {
						return 99999;
					} else if (s == -Infinity) {
						return -99999;
					} else {
						return parseFloat(s);
					}
				},
				// set type, either numeric or text
				type: "numeric",
			});
			$.tablesorter.addParser({
				// set a unique id
				id: "rpkm_sorter",
				is: function (s) {
					// return false so this parser is not auto detected
					return false;
				},
				format: function (s) {
					// format your data for normalization
					if (s == NaN) {
						return -99999;
					} else if (s == undefined) {
						return -999999;
					} else if (s == Infinity) {
						return 99999;
					} else if (s == -Infinity) {
						return -99999;
					} else if (s == "Missing controls data") {
						return -9999999;
					} else {
						return parseFloat(s);
					}
				},
				// set type, either numeric or text
				type: "numeric",
			});
			$("#theTable").tablesorter({
				headers: {
					0: {},
					1: {
						sorter: false, // disable sorting on this column
					},
					2: {
						sorter: "rpb_sorter",
					},
					3: {
						//sorter: false  disable sorting on this column
					},
					4: {
						sorter: "rpkm_sorter",
					},
					5: {
						//sorter: false  disable sorting on this column
					},
				},
			});
			$("#theTable").trigger("update");
		},
		error: function (xhr, status, error) {
			generateToastNotification(`Error getting data from data file: ${error.message}`, "ERROR");
			console.log("Error getting data from data file: " + error.message);
		},
	});

	let filtersConfig = {
		base_path: "cgi-bin/core/packages/tableFilter/",
		columns_exact_match: [false, false, false, false, false, false],
		watermark: ["Filter", "Filter", "Filter", "Filter", "Filter", "Filter"],
		highlight_keywords: false,
		no_results_message: true,
		auto_filter: true,
		auto_filter_delay: 500, //milliseconds
		col_1: "none", // no filter option
		//col_3: 'none',  no filter option
		popup_filters: false,
		filters_row_index: 1,
		alternate_rows: false,
		msg_filter: "Filtering...",
	};
	//let tf = new TableFilter('theTable', {base_path: 'core/tablefilter/'});
	let tf = new TableFilter("theTable", filtersConfig);
	//let tf = new TableFilter('demo', filtersConfig);
	tf.init();
	change_rpkm_colour_scale(colouring_mode);

	// Check if arrows are the right width or not
	for (let j = 0; j < colSortList.length; j++) {
		let colArrow = colSortList[j] + "Arrow";
		CheckElementWidth(colArrow, 8);
	}

	createVariantDiv();
}

/**
 * Create the gene variants dropdown option's container
 */
function createVariantDiv() {
	if (
		gene_structure_colouring_element == null &&
		document.getElementById("flt1_theTable") &&
		document.getElementById("flt1_theTable").parentElement
	) {
		gene_structure_colouring_element = document.getElementById("flt1_theTable").parentElement;
	}
	gene_structure_colouring_element.innerHTML = "";

	$("#variant_select").ddslick("destroy");
	document.getElementsByClassName("fltrow")[0]["childNodes"][1].innerHTML = "";
	variantdiv_str = '<div id="variants_div">';
	variantdiv_str += "</div>";
	document.getElementsByClassName("fltrow")[0]["childNodes"][1].innerHTML = variantdiv_str;

	$("#variant_select").ddslick({
		width: "100%",
		onSelected: function () {
			gene_structure_radio_on_change();
		},
	});
}

/**
 * Change the text within moreDetails
 * @param {String} details_id - The ID tag for the <a> for details
 */
function clickDetailsTextChange(details_id) {
	if (document.getElementById(details_id) != null) {
		if (document.getElementById(details_id).innerHTML == moreDetails) {
			document.getElementById(details_id).setAttribute("hidden", true);
			// Non-truncate the details
			const innerDescription = document.getElementById(document.getElementById(details_id).name);
			innerDescription.textContent = innerDescription.getAttribute("name");
		} else if (document.getElementById(details_id).innerHTML == lessDetails) {
			const ogID = details_id.substring(0, details_id.length - 5);
			document.getElementById(ogID).removeAttribute("hidden");
			// Truncate the details
			const innerDescription = document.getElementById(document.getElementById(details_id).name);
			innerDescription.textContent = truncateDescription(innerDescription.getAttribute("name"));
		}
	}
}

/**
 * Determines the length of a string and if it is too long, truncate it
 * @param {String} stringInput - The string to check
 * @return {String}
 */
function truncateDescription(stringInput) {
	if (stringInput != undefined || stringInput != null) {
		if (stringInput.length > 30) {
			return stringInput.substring(0, 30) + "...";
		} else {
			return stringInput;
		}
	}
}

let remainder_efp = 0;
let efp_length = 0;
let eFPSortedSRA = [];
let efp_RPKM_values = [];
/**
 * Creates a table of the coloured SVGs and their corresponding RPKM values
 * @param {String | Number} status Index call version
 */
function populate_efp_modal(status) {
	toggleResponsiveTable(2);
	$("#efpModalTable").empty();
	// Reset variables
	efp_table_column = "";
	eFPSortedSRA = [];

	const allSRASorted = document.getElementsByClassName("colTitle");
	for (let s = 2; s < allSRASorted.length; s++) {
		let SRASortedID = allSRASorted[s].id.substring(0, allSRASorted[s].id.length - 6);
		if (document.getElementById(SRASortedID + "_row").style.display != "none") {
			eFPSortedSRA.push(SRASortedID);
		}
	}

	remainder_efp = eFPSortedSRA.length % 11;
	efp_length = eFPSortedSRA.length;
	efp_RPKM_values = [];

	for (let i = 0; i < eFPSortedSRA.length; i++) {
		if (!isNaN(parseFloat(sraDict[eFPSortedSRA[i]]["RPKM"]))) {
			efp_RPKM_values.push(parseFloat(sraDict[eFPSortedSRA[i]]["RPKM"]));
		}
	}

	// Insert eFP Table header
	$("#efpModalTable").append(
		`
			<p class="eFP_thead">
				AGI-ID:
					<a href="https://www.arabidopsis.org/servlets/TairObject?type=locus&name=${locus} target="_blank" rel="noopener">
						${locus}
					</a>
			</p>
		`,
	);

	// Check radio
	if (colouring_mode === "abs") {
		$("#efpModalTable").append(
			`
				<p class="eFP_thead">
					eFP Colour Scale:

					<img
						loading="lazy"
						src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQD//wD//AD/+QD/9wD/9AD/8gD/7wD/7QD/6gD/6AD/5QD/4gD/4AD/3QD/2wD/2AD/1gD/ 0wD/0QD/zgD/zAD/yQD/xgD/xAD/wQD/vwD/vAD/ugD/twD/tQD/sgD/rwD/rQD/qgD/qAD/pQD/ owD/oAD/ngD/mwD/mQD/lgD/kwD/kQD/jgD/jAD/iQD/hwD/hAD/ggD/fwD/fAD/egD/dwD/dQD/ cgD/cAD/bQD/awD/aAD/ZgD/YwD/YAD/XgD/WwD/WQD/VgD/VAD/UQD/TwD/TAD/SQD/RwD/RAD/ QgD/PwD/PQD/OgD/OAD/NQD/MwD/MAD/LQD/KwD/KAD/JgD/IwD/IQD/HgD/HAD/GQD/FgD/FAD/ EQD/DwD/DAD/CgD/BwD/BQD/AgCkIVxRAAAAs0lEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hERLGBmpbgljbBwjiiWMnFyMVLcECOhkCZBIZUzPYKSV JaDgYkxKZkxNY2SkmU8gljDCLaFdxDMmw4NrGOWTUUuItwQAG8496iMoCNwAAAAASUVORK5CYII="
						class="colourScale"
						alt="Absolute RPKM colour scale"
					/>

					Min: ${Math.min.apply(null, efp_RPKM_values).toFixed(1)} RPKM,

					Max: ${Math.max.apply(null, efp_RPKM_values).toFixed(1)} RPKM
				</p>

				<br />

				<table>
					<tbody class="eFP_tbody">
				</tbody>
			`,
		);
	} else if (colouring_mode === "rel") {
		$("#efpModalTable").append(
			`
				<p class="eFP_thead">
					eFP Colour Scale:

					<img
						loading="lazy"
						src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQAAAP8FBfkKCvQPD+8UFOoZGeUeHuAjI9soKNYtLdEzM8w4OMY9PcFCQrxHR7dMTLJRUa1W VqhbW6NgYJ5mZplra5NwcI51dYl6eoR/f3+EhHqJiXWOjnCTk2uZmWaenmCjo1uoqFatrVGysky3 t0e8vELBwT3GxjjMzDPR0S3W1ijb2yPg4B7l5Rnq6hTv7w/09Ar5+QX//wD/+wD/9gD/8QD/7AD/ 5wD/4gD/3QD/2AD/0wD/zQD/yAD/wwD/vgD/uQD/tAD/rwD/qgD/pQD/oAD/mgD/lQD/kAD/iwD/ hgD/gQD/fAD/dwD/cgD/bQD/ZwD/YgD/XQD/WAD/UwD/TgD/SQD/RAD/PwD/OgD/NAD/LwD/KgD/ JQD/IAD/GwD/FgD/EQD/DAD/BwBUljDTAAAA1klEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hDRLGDi5GICWMBBvCSMjIUsYY+MYUS0BApJ8wmhlzUjI EiDAYgkD0CcMwgxUtQRIpDKmZzCiBBcDgwgDlSwBBRdjUjJjahojI2qcMAhT2RJGNEuAYUasJURH PGMyPLiGTz4ZtYQESwCEoDnh8dGTkQAAAABJRU5ErkJggg=="
						class="colourScale"
						alt="Relative RPKM colour scale"
					/>

					Min: ${Math.min.apply(null, efp_RPKM_values).toFixed(1)},

					Max: ${Math.max.apply(null, efp_RPKM_values).toFixed(1)}
				</p>

				<br />

				<table>
					<tbody>
				</tbody>
			`,
		);
	}

	// Insert eFP Table
	$("#efpModalTable").append('<table id="eFPtable" class="table"></table>');

	// Creating eFP representative table
	for (let i = 0; i < ~~(eFPSortedSRA.length / 11) * 11; i += 11) {
		if (document.getElementById(eFPSortedSRA[i + 10]).outerHTML != "null") {
			efp_table_column = "<tr>";
			for (let r = 0; r < 11; r++) {
				efp_table_column += generateEFPTableItem(eFPSortedSRA[i + r], sraDict[eFPSortedSRA[i + r]]["title"]);
			}
			efp_table_column += "</tr>";
			$("#eFPtable").append(efp_table_column);
		}
	}

	for (let r = 0; r < 12; r++) {
		if (remainder_efp === r) {
			efp_table_column = "<tr>";
			for (let c = remainder_efp; c > 0; c--) {
				efp_table_column += generateEFPTableItem(
					eFPSortedSRA[efp_length - c],
					sraDict[eFPSortedSRA[efp_length - c]]["title"],
				);
			}
			efp_table_column += "</tr>";
			$("#eFPtable").append(efp_table_column);
		}
	}

	toggleResponsiveTable();
}

/**
 * Generates eFP table items, based on given title and ID, and returns as a HTML in string
 * @param {String} id SRA or project ID
 * @param {String} title Title of project
 * @return {String} Custom HTML as a string for the eFP table items (item wrapped in a tag element/data cell: <td>)
 * @example <caption>When generating eFP table items for the eFP overview, use this function to create multiple table elements within a container/parent table.</caption>
 * generateEFPTableItem("ERR274310", "Aerial part of long-day-grown leaf")
 * // return '<td><div class="efp_table_tooltip" id="ERR274310_rep" onclick="ScrollToRNARow('ERR274310_row')">${document.getElementById("ERR274310_row_svg").outerHTML}<span class="efp_table_tooltip_text">ERR274310 - Aerial part of long-day-grown leaf</span></div></td>'
 */
function generateEFPTableItem(id, title) {
	if (id && title) {
		return `
			<td>
				<div
					class="efp_table_tooltip"
					id="${id}_rep"
					onclick="ScrollToRNARow('${id}_row')"
				>
					${document.getElementById(id + "_svg").outerHTML}
					<span class="efp_table_tooltip_text">
					${id} - ${title}
					</span>
				</div>
			</td>
		`;
	}

	return "";
}

/**
 * Changes the legend for scales.
 */
function change_rpkm_colour_scale(colouring_mode) {
	if (
		svg_colouring_element === null &&
		document.getElementById("flt3_theTable") &&
		document.getElementById("flt3_theTable").parentElement
	) {
		svg_colouring_element = document.getElementById("flt3_theTable").parentElement;
	}

	if (svg_colouring_element && svg_colouring_element.innerHTML) {
		svg_colouring_element.innerHTML = "";
	}

	if (colouring_mode == "rel") {
		const img_created = document.createElement("img");
		img_created.src = "data:image/png;base64," + relative_rpkm_scale;
		img_created.style = "margin-top: 10px;";
		if (svg_colouring_element) {
			svg_colouring_element.appendChild(img_created);
		}
	} else {
		const img_created = document.createElement("img");
		img_created.src = "data:image/png;base64," + absolute_rpkm_scale;
		img_created.style = "margin-top: 10px;";
		img_created.alt = "Absolute RPKM Scale";
		if (svg_colouring_element) {
			svg_colouring_element.appendChild(img_created);
		}
	}

	// Add border to fltrow class tr's child td elements
	const columnList = ["colTitle", "colRNA", "colrpb", "coleFP", "colRPKM", "colDetails"];
	let tds = [];
	if (document.getElementsByClassName("fltrow") && document.getElementsByClassName("fltrow")[0]) {
		tds = document.getElementsByClassName("fltrow")[0].getElementsByTagName("td");
	}
	for (let i = 0; i < tds.length; i++) {
		tds[i].style = "border: 1px solid #D3D3D3";
		tds[i].classList.add(columnList[i]);
	}
}

function locus_validation() {
	const loc = document.getElementById("locus").value;
	if (
		loc.length == 9 &&
		(loc[0] == "A" || loc[0] == "a") &&
		(loc[1] == "T" || loc[1] == "t") &&
		((loc[2] >= 1 && loc[2] <= 5) || loc[2] == "C" || loc[2] == "M" || loc[2] == "c" || loc[2] == "m") &&
		(loc[3] == "G" || loc[3] == "g") &&
		loc[4] >= 0 &&
		loc[4] <= 9 &&
		loc[5] >= 0 &&
		loc[5] <= 9 &&
		loc[6] >= 0 &&
		loc[6] <= 9 &&
		loc[7] >= 0 &&
		loc[7] <= 9 &&
		loc[8] >= 0 &&
		loc[8] <= 9
	) {
		$("#locus_button").removeAttr("disabled");
	} else {
		$("#locus_button").prop("disabled", true);
	}
}

function yscale_validation() {
	const yscale = document.getElementById("yscale_input").value;
	if (parseInt(yscale) > 0 || yscale == "Auto" || yscale == "") {
		//$("#yscale_button").removeAttr('disabled');
		$("#locus_button").removeAttr("disabled");
	} else {
		//$("#yscale_button").prop("disabled", true);
		$("#locus_button").prop("disabled", true);
	}
}

function rpkm_validation() {
	const rpkmScale = parseInt(document.getElementById("rpkm_scale_input").value);
	if (rpkmScale > 0) {
		$("#abs_scale_button").removeAttr("disabled");
	} else {
		$("#abs_scale_button").prop("disabled", true);
	}
}

/* Used for resetting dataset_dictionary */
const base_dataset_dictionary = {
	"Araport 11 RNA-seq data": "cgi-bin/data/bamdata_araport11.xml",
	"Developmental transcriptome - Klepikova et al": "cgi-bin/data/bamdata_Developmental_transcriptome.xml",
};
let databasesAdded = false;
/**
 * Resets the dataset_dictionary and removes users added tags from index.html (document)
 */
function reset_database_options() {
	$(".userAdded").remove();
	dataset_dictionary = base_dataset_dictionary; // Resets dictionary
	list_modified = false;
	databasesAdded = false;
}

let get_xml_list_output = [];
let user_exist = false;
let list_modified = false;
let check_for_change = 0;
let xml_title;
let match_title = {};
let title_list = [];
/**
 * Gets list of users private XMLs
 */
function get_user_XML_display() {
	const AuthUser = findAuthUser();

	// First check to make sure there is is a user logged in or else this script will not run
	if ((users_email != "" || users_email != undefined || users_email != null) && users_email === AuthUser) {
		$.ajax({
			url: "https://bar.utoronto.ca/webservices/eFP-Seq_Browser/get_xml_list.php?user=" + users_email,
			dataType: "json",
			failure: function () {
				console.log("ERROR! Something went wrong");
			},
			success: function (get_xml_list_return) {
				// Reset all variables
				xml_title = undefined;
				match_title = {};
				title_list = [];

				/** Unnamed dataset name number: */
				let unnamed_title_num = 1;
				let private_version_num = 1;

				// Check if the output is working and store as variable
				get_xml_list_output = get_xml_list_return;
				if (get_xml_list_output["status"] == "fail") {
					console.log("Error code: " + get_xml_list_output["error"]);
					user_exist = false;
				} else if (get_xml_list_output["status"] == "success") {
					user_exist = true;

					// Check for change in output from last time ran function
					if (check_for_change != get_xml_list_output["files"].length) {
						reset_database_options();
						list_modified = false;
					}
					check_for_change = get_xml_list_output["files"].length;

					// Check each file in output
					if (get_xml_list_output["files"].length > 0) {
						for (let i = 0; i < get_xml_list_output["files"].length; i++) {
							xml_title = undefined;
							xml_title = get_xml_list_output["files"][i][1];

							// Make sure there is a title or if not, make one
							if (!xml_title || xml_title.trim()?.length === 0 || xml_title === "Uploaded dataset") {
								xml_title = "Uploaded dataset - Unnamed dataset #" + unnamed_title_num;
								unnamed_title_num += 1;
							} else if (xml_title == "Araport 11 RNA-seq data") {
								xml_title = "Araport 11 RNA-seq data - Private version #" + private_version_num;
								private_version_num += 1;
							} else if (xml_title == "Developmental transcriptome - Klepikova et al") {
								xml_title =
									"Developmental transcriptome - Klepikova et al - Private version #" +
									private_version_num;
								private_version_num += 1;
							}
							title_list.push(xml_title);
							const xml_fle_name = get_xml_list_output["files"][i][0];

							// This needed for later on
							match_title[xml_title] = xml_fle_name;

							// Obtain data location for each individual XML
							if (i == get_xml_list_output["files"].length - 1) {
								create_data_list(get_xml_list_output["files"].length);
							}
						}
					}
					setTimeout(function () {
						if (!list_modified) {
							for (let c = 0; c < get_xml_list_output["files"].length; c++) {
								// Add data to list of accessible datasets
								dataset_dictionary[title_list[c]] = datalist_Title[title_list[c]];

								// Create option to select data from user
								document.getElementById("xmlDatabase").innerHTML += `
									<option
										class="userAdded"
										tag="private"
										value="${title_list[c]}"
										id="${title_list[c]}"
									>
										${title_list[c]}
									</option>
								`;
							}
						}
						list_modified = true;
					}, 1000);
				}
				databasesAdded = true;
			},
			error: function (xhr, status, error) {
				generateToastNotification(`Error getting user data: ${error.message}`, "ERROR");
				console.log(`Error getting user data: ${error.message}`);
			},
		});
	} else if (users_email != "" && users_email != AuthUser) {
		signOut();
		alert("Error occurred with your account, you have now been logged out. Please log back in");
	}
}

let datalist = [];
let datalist_Title = {};
/**
 * Creates a list of base64 strings that contains XML of user's private datasets
 * @param {Number} size - How many private datasets the user has
 * @return {List} datalist_Title - Dictionary of base64 strings
 */
function create_data_list(size) {
	datalist = []; // Reset
	datalist_Title = {}; // Reset
	if (size > 0) {
		for (let i = 0; i < size; i++) {
			$.ajax({
				url:
					"https://bar.utoronto.ca/webservices/eFP-Seq_Browser/get_xml.php?file=" +
					match_title[title_list[i]],
				dataType: "json",
				success: function (get_xml_return) {
					const xml_file = get_xml_return;
					datalist.push(xml_file["data"]);
				},
				error: function (xhr, status, error) {
					generateToastNotification(`Error getting user private datasets: ${error.message}`, "ERROR");
					console.log(`Error getting user private datasets: ${error.message}`);
				},
			});

			if (i === size - 1) {
				setTimeout(function () {
					dlCallLength = size;
					DatalistXHRCall(datalist);
				}, 200);
			}
		}
	}
}

let dlCallLength = 0;
/** Make function recursive */
let dlCallPosition = 0;
let testDoc;
/**
 * Retrieves information and titles of individual XMLs
 * @param {List} datalistData The list of base64/url for the XML's being parsed through
 */
function DatalistXHRCall(datalistData) {
	if (dlCallPosition != dlCallLength) {
		const xhr = new XMLHttpRequest();
		const url = datalistData[dlCallPosition];

		xhr.responseType = "document";
		xhr.onreadystatechange = () => {
			if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
				let response = xhr.responseXML;
				if (response) {
					let responseTitle = response.getElementsByTagName("files")[0].attributes.xmltitle.nodeValue;
					datalist_Title[responseTitle] = datalistData[dlCallPosition];

					// Make function recursive
					dlCallPosition += 1;
					DatalistXHRCall(datalistData);
				}
			}
		};

		xhr.open("GET", url);
		xhr.send();
	}
}

/**
 * Determine whether or not a string is a email or not
 * Modified from: https://stackoverflow.com/questions/46155/how-to-validate-an-email-address-in-javascript
 * @param {String} email String being tested if email or not
 */
function validateEmail(email) {
	const re = /\S+@\S+\.\S+/;
	return re.test(email);
}

/**
 * Find what OAuth2.0 user may be logged in
 * @returns {String} AuthUser - The email associated with the OAuth2.0 user logged in if any (empty string if not)
 */
function findAuthUser() {
	if (global_user && global_user.email) {
		return global_user.email;
	} else {
		return "";
	}
}

/**
 * Checks if the user is logged in or not
 */
function check_if_Google_login() {
	const AuthUser = findAuthUser();
	if (users_email && AuthUser && users_email === AuthUser) {
		if (databasesAdded === false) {
			document.getElementById("private_dataset_header").style.display = "block";
			get_user_XML_display();
		}
	} else {
		signOut();
		remove_private_database();
	}
}

/**
 * If user does not exist, adds user to our database and upload file; if does, upload file
 */
function add_user_xml_by_upload() {
	get_user_XML_display(); // Updates data and determines if user_exists or now
	// setTimeout is necessary due to datasetName taking a while to be generated. Though only requires 3 seconds to obtain, setTimeout set to 4 just in case

	setTimeout(function () {
		const AuthUser = findAuthUser();
		if (!user_exist) {
			// Creates a new user if the user does not already exist
			if (users_email === AuthUser) {
				$.ajax({
					method: "POST",
					url: "https://bar.utoronto.ca/webservices/eFP-Seq_Browser/upload.php",
					data: {
						user: users_email,
						xml: upload_src,
						title: datasetName,
					},
				});
			} else if (users_email != "" && users_email != AuthUser) {
				signOut();
				alert("Error occurred with your account, you have now been logged out. Please log back in");
			}
		} else if (user_exist) {
			if (!dataset_dictionary[datasetName]) {
				// If the file does not already exist in the account, add it
				if (users_email === AuthUser) {
					$.ajax({
						method: "POST",
						url: "https://bar.utoronto.ca/webservices/eFP-Seq_Browser/upload.php",
						data: {
							user: users_email,
							xml: upload_src,
							title: datasetName,
						},
					});
				} else if (users_email != "" && users_email != AuthUser) {
					signOut();
					alert("Error occurred with your account, you have now been logged out. Please log back in");
				}
			} else if (dataset_dictionary[datasetName]) {
				if (users_email === AuthUser) {
					// reset variables for get_user_XML_display
					list_modified = false;
					check_for_change = 0;
					// If the file does already exist in the account, delete old and add new
					$.ajax({
						url:
							"https://bar.utoronto.ca/webservices/eFP-Seq_Browser/delete_xml.php?user=" +
							users_email +
							"&file=" +
							match_title[datasetName],
					});
					$.ajax({
						method: "POST",
						url: "https://bar.utoronto.ca/webservices/eFP-Seq_Browser/upload.php",
						data: {
							user: users_email,
							xml: upload_src,
							title: datasetName,
						},
					});
				} else if (users_email != "" && users_email != AuthUser) {
					signOut();
					alert("Error occurred with your account, you have now been logged out. Please log back in");
				}
			}
		}
		get_user_XML_display(); // Update data again
	}, 10000);
}

let uploadingData = false;
/**
 * UI function: If logged in, upload to account vs not
 */
function which_upload_option() {
	uploadingData = true;
	const AuthUser = findAuthUser();
	if (users_email != "" && users_email === AuthUser) {
		document.getElementById("upload_modal").click();
	} else if (users_email != "" && users_email != AuthUser) {
		signOut();
		alert("Error occurred with your account, you have now been logged out. Please log back in");
	} else if (users_email == "") {
		document.getElementById("upload_logX").click();
	}
}

/* User's private dataset_dictionary */
const public_dataset_dictionary = {
	"Araport 11 RNA-seq data": "cgi-bin/data/bamdata_araport11.xml",
	"Developmental transcriptome - Klepikova et al": "cgi-bin/data/bamdata_Developmental_transcriptome.xml",
};

let public_title_list = [];
let total_amount_of_datasets = 0;
/**
 * Fills the manage XML modal with all available XMLs to delete from an account
 */
function delete_fill() {
	$("#delete_fill").empty(); // Empties the manage XML modal every time it is loaded
	$("#publicDatabaseDownload").empty();
	public_title_list = [];
	for (let public_title in public_dataset_dictionary) {
		if (public_dataset_dictionary.hasOwnProperty(public_title)) {
			public_title_list.push(public_title);
		}
	}

	let deleteBoxNum = 0;
	total_amount_of_datasets = public_title_list.length + title_list.length;

	for (let i = 0; i < public_title_list.length; i++) {
		// Fills the manage XML modal with available XMLs on the account
		$("#publicDatabaseDownload").append(
			`
				<input
					type="checkbox"
					tag="publicDataCheckbox"
					class="publicDataCheckbox"
					onchange="disableDeletePublic()"
					id="deleteBox_${deleteBoxNum}"
					value="${public_title_list[i]}"
				>
					${public_title_list[i]}
				</input>
				<br />
			`,
		);
		deleteBoxNum += 1;
	}

	for (let i = 0; i < title_list.length; i++) {
		// Fills the manage XML modal with available XMLs on the account
		$("#delete_fill").append(
			`
				<input
					type="checkbox"
					tag="privateDataCheckbox"
					class="privateDataCheckbox"
					onchange="disableDeletePublic()"
					id="deleteBox_${deleteBoxNum}"
					value="${title_list[i]}"
				>
					${title_list[i]}
				</input>
				<br />
			`,
		);
		deleteBoxNum += 1;
	}
}

let isDeletePublicDisabled = false;
/**
 * Prevents users from deleting public databases visually... even without this they cannot actually do it
 */
function disableDeletePublic() {
	for (let i = 0; i < public_title_list.length; i++) {
		if (
			document.getElementById("deleteBox_" + i).checked &&
			document.getElementById("deleteBox_" + i).className == "publicDataCheckbox"
		) {
			if (!isDeletePublicDisabled) {
				document.getElementById("deleteXML_button").classList.add("disabled");
				isDeletePublicDisabled = true;
			}
			break;
		} else {
			if (isDeletePublicDisabled) {
				document.getElementById("deleteXML_button").classList.remove("disabled");
				isDeletePublicDisabled = false;
			}
		}
	}
}

/**
 * Check if any XML's from "Manage Account" has been selected or not
 */
function CheckIfSelectedXML() {
	let returnTrue = false;
	const AuthUser = findAuthUser();

	for (let i = 0; i < title_list.length; i++) {
		/** Find id of what is being called */
		const deleteBox_id = "deleteBox_" + (i + 2);
		if (document.getElementById(deleteBox_id).checked && users_email === AuthUser) {
			return true;
		}
	}

	if (!returnTrue) {
		return false;
	}
}

/**
 * Delete selected XMLs from their private account
 */
function delete_selectedXML() {
	const AuthUser = findAuthUser();

	for (let i = 0; i < title_list.length; i++) {
		/** Find id of what is being called */
		const deleteBox_id = "deleteBox_" + (i + 2);

		if (
			document.getElementById(deleteBox_id) &&
			document.getElementById(deleteBox_id).checked &&
			users_email === AuthUser
		) {
			$.ajax({
				url:
					"https://bar.utoronto.ca/webservices/eFP-Seq_Browser/delete_xml.php?user=" +
					users_email +
					"&file=" +
					match_title[document.getElementById(deleteBox_id).value],
			});
		}
	}

	databasesAdded = false;
}

/**
 * Confirm the action of delete all users and if so, begin deletion process
 */
function confirm_deleteUser() {
	const AuthUser = findAuthUser();
	if (users_email != "" && users_email === AuthUser && $("#logoutModal").is(":visible")) {
		delete_allXMLs(AuthUser);
	}
}

/**
 * Delete all XMLs related to an account
 * @param {String} verify Verification code related to an account
 */
function delete_allXMLs(verify) {
	const AuthUser = findAuthUser();

	if (verify === AuthUser) {
		for (let i = 0; i < title_list.length; i++) {
			/** Find id of what is being called */
			const deleteBox_id = "deleteBox_" + (i + 2);
			if (users_email === AuthUser) {
				$.ajax({
					url:
						"https://bar.utoronto.ca/webservices/eFP-Seq_Browser/delete_xml.php?user=" +
						users_email +
						"&file=" +
						match_title[document.getElementById(deleteBox_id).value],
				});
			}
		}
		delete_user();
		databasesAdded = false;
	}
}

/**
 * Delete the currently logged in user from the BAR
 */
function delete_user() {
	const AuthUser = findAuthUser();
	if (users_email != "" && users_email === AuthUser) {
		$.ajax({
			url: "https://bar.utoronto.ca/webservices/eFP-Seq_Browser/delete_user.php?user=" + users_email,
		});
	}
	signOut();
}

let warningActive_index_XML = "nope";
let warningActive_index_account = "nope";
/**
 * Show warning before making permanent decision
 * @param {Number} whichWarning Which warning to be displayed? 1 for XML, 2 for accounts
 */
function showWarning_index(whichWarning) {
	if (whichWarning === 1) {
		// Delete single XML
		if (!isDeletePublicDisabled) {
			if (warningActive_index_XML == "nope") {
				document.getElementById("warning_index_xml").className = "warning_index";
				warningActive_index_XML = "yes";
			} else if (warningActive_index_XML == "yes") {
				hideWarning_index(whichWarning);
			}
		}
	} else if (whichWarning === 2) {
		// Delete account
		if (warningActive_index_account == "nope") {
			document.getElementById("warning_index_account").className = "warning_index";
			warningActive_index_account = "yes";
		} else if (warningActive_index_account == "yes") {
			hideWarning_index(whichWarning);
		}
	}
}

/**
 * Hide warning of permanent decision
 * @param {Number} whichWarning Which warning to be displayed? 1 for XML, 2 for accounts
 */
function hideWarning_index(whichWarning) {
	if (whichWarning === 1) {
		// Delete single XML
		document.getElementById("warning_index_xml").className = "warning_nope_index";
		warningActive_index_XML = "nope";
	} else if (whichWarning === 2) {
		// Delete account
		document.getElementById("warning_index_account").className = "warning_nope_index";
		warningActive_index_account = "nope";
	}
}

/**
 * Download selected file (in document's/index.html "Manage data") as an XML
 * @return {File} XML - Download selected file as an XML
 */
function manage_DownloadXML() {
	const numberOfOptions = title_list.length + 2;
	for (let i = 0; i < numberOfOptions; i++) {
		/** Find id of what is being called */
		const downloadBox_id = "deleteBox_" + i;

		if (document.getElementById(downloadBox_id).checked) {
			$("#downloadXML")
				.attr("href", dataset_dictionary[document.getElementById(downloadBox_id).value])
				.attr("download", document.getElementById(downloadBox_id).value + ".xml");
			document.getElementById("downloadXML_button").click();
		}
	}
}

const table_base =
	"\t\t<tr>\n\t\t\t<th>Title*</th>\n\t\t\t<th>Description*</th>\n\t\t\t<th>Record Number *</th>\n\t\t\t<th>RNA-Seq Data/BAM file repository link*</th>\n\t\t\t<th>Repository type*</th>\n\t\t\t<th>BAM Filename*</th>\n\t\t\t<th>Publication Link</th>\n\t\t\t<th>SRA/NCBI Link</th>\n\t\t\t<th>Total Reads Mapped*</th>\n\t\t\t<th>Read Map Method</th>\n\t\t\t<th>Species*</th>\n\t\t\t<th>Tissue*</th>\n\t\t\t<th>Tissue subunit*</th>\n\t\t\t<th>Controls</th>\n\t\t\t<th>Replicate Controls</th>\n\t\t</tr>\n";
/**
 * Initializes and fills a hidden table (#XMLtoCSVtable) to be filled with potentially downloadable CSV files
 */
function fill_tableCSV() {
	$("#XMLtoCSVtable").empty();
	for (let i = 0; i < total_amount_of_datasets; i++) {
		/** Find id of what is being called */
		const downloadBox_id = "deleteBox_" + i;
		//console.log("Initializing fill_tableCSV() on " + downloadBox_id);

		$.ajax({
			url: dataset_dictionary[document.getElementById(downloadBox_id).value],
			dataType: "xml",
			failure: function () {
				console.log("Failed at opening XML for conversion into a CSV file. Please contact an admin");
			},
			success: function (xml_data) {
				const $xmltitle = $(xml_data).find("files");

				let fileTitle;

				$xmltitle.each(function () {
					fileTitle = $(this).attr("xmltitle");
					if (fileTitle == "" || fileTitle == "Uploaded dataset") {
						fileTitle = "Uploaded dataset";
					}
					fileTitle = fileTitle.split(" ").join("_");
				});
				/** XML title */
				const $title = $(xml_data).find("file");
				let table_add = "";
				table_add += "<table id='" + fileTitle + "'>\n\t<tbody>\n";
				table_add += "\t\t<caption>" + fileTitle + "</caption>\n";
				table_add += table_base; // CSV header
				$title.each(function () {
					table_add += "\t\t<tr>\n";

					/** Title */
					const title = $(this).attr("description");
					table_add += "\t\t\t<td>" + title + "</td>\n";

					/** Description */
					const desc = $(this).attr("info");
					table_add += "\t\t\t<td>" + desc + "</td>\n";

					/** Record number */
					const record_number = $(this).attr("record_number");
					table_add += "\t\t\t<td>" + record_number + "</td>\n";

					/** BAM/repository link */
					const bam_link = $(this).attr("name");
					table_add += "\t\t\t<td>" + bam_link + "</td>\n";

					/** BAM/repo type */
					const bam_type = $(this).attr("bam_type");
					table_add += "\t\t\t<td>" + bam_type + "</td>\n";

					/** BAM/repo type */
					let bam_filename = $(this).attr("filename");
					if (
						bam_filename === null ||
						bam_filename === undefined ||
						bam_filename === "undefined" ||
						bam_filename === ".bam"
					) {
						bam_filename = "accepted_hits.bam";
					}
					table_add += "\t\t\t<td>" + bam_filename + "</td>\n";

					/** Publication link */
					const publication_link = $(this).attr("publication_link");
					table_add += "\t\t\t<td>" + publication_link + "</td>\n";

					/** Publication URL */
					const publication_url = $(this).attr("url");
					table_add += "\t\t\t<td>" + publication_url + "</td>\n";

					/** Total reads mapped */
					let total_reads_mapped = $(this).attr("total_reads_mapped");
					if (total_reads_mapped == null || total_reads_mapped == "") {
						total_reads_mapped = "0";
					}
					table_add += "\t\t\t<td>" + total_reads_mapped + "</td>\n";

					/** Read mapped method */
					const read_map_method = $(this).attr("read_map_method");
					table_add += "\t\t\t<td>" + read_map_method + "</td>\n";

					/** Species */
					let species = $(this).attr("species");
					if (species == null || species == "") {
						species = "Arabidopsis thaliana";
					}
					table_add += "\t\t\t<td>" + species + "</td>\n";

					/** Tissue */
					const svgname = $(this).attr("svgname");
					table_add += "\t\t\t<td>" + svgname + "</td>\n";

					/** Tissue subunit */
					const svg_subunit = $(this).attr("svg_subunit");
					table_add += "\t\t\t<td>" + svg_subunit + "</td>\n";

					/** Controls */
					let controlsXMLString = "";
					if ($(this).find("controls")[0].innerHTML) {
						for (let j = 1; j < $(this).find("controls")[0].childNodes.length; j = j + 2) {
							if ($(this).find("controls")[0].childNodes[j].firstChild) {
								controlsXMLString += $(this).find("controls")[0].childNodes[j].firstChild.textContent;
								if (j < $(this).find("controls")[0].childNodes.length - 2) {
									controlsXMLString += ", ";
								}
							}
						}
					}
					table_add += "\t\t\t<td>" + controlsXMLString + "</td>\n";

					/** Replicate Controls */
					let RcontrolsXMLString = "";
					if ($(this).find("groupwith")[0].innerHTML) {
						for (let j = 1; j < $(this).find("groupwith")[0].childNodes.length; j = j + 2) {
							if ($(this).find("groupwith")[0].childNodes[j].firstChild) {
								RcontrolsXMLString += $(this).find("groupwith")[0].childNodes[j].firstChild.textContent;
								if (j < $(this).find("groupwith")[0].childNodes.length - 2) {
									RcontrolsXMLString += ", ";
								}
							}
						}
					}
					table_add += "\t\t\t<td>" + RcontrolsXMLString + "</td>\n";

					// Closing
					table_add += "\t\t</tr>\n";
				});

				table_add += "\t</tbody>\n</table>";

				//console.log(table_add);

				document.getElementById("XMLtoCSVtable").innerHTML += table_add;
			},
			error: function (xhr, status, error) {
				generateToastNotification(`Error filling data table: ${error.message}`, "ERROR");
				console.log(`Error filling data table: ${error.message}`);
			},
		});
	}
}

/**
 * Download selected file (in document's/index.html "Manage data") as an CSV
 * @return {File} CSV - Download selected file as an CSV
 */
function download_XMLtableCSV() {
	for (let i = 0; i < total_amount_of_datasets; i++) {
		/** Find id of what is being called */
		const downloadBox_id = "deleteBox_" + i;
		if (document.getElementById(downloadBox_id).checked) {
			const tableTitle = document.getElementById(downloadBox_id).value.split(" ").join("_");
			$("#" + tableTitle).tableToCSV();
		}
	}
}

const downloadIndexTable_base =
	"\t\t<tr>\n\t\t\t<th>Title</th>\n\t\t\t<th>Record Number</th>\n\t\t\t<th>Tissue</th>\n\t\t\t<th>Tissue subunit</th>\n\t\t\t<th>Locus</th>\n\t\t\t<th>bp Length</th>\n\t\t\t<th>bp Start site</th>\n\t\t\t<th>bp End site</th>\n\t\t\t<th>Total number of reads</th>\n\t\t\t<th>Reads mapped to locus</th>\n\t\t\t<th>rpb</th>\n\t\t\t<th>RPKM</th>\n\t\t\t<th>Controls</th>\n\t\t</tr>\n";
/**
 * Converts and downloads index's (document) main table as an CSV
 * @return {File} CSV
 */
function download_mainTableCSV() {
	document.getElementById("download_icon").classList.add("progressLoading");
	document.getElementById("bodyContainer").classList.add("progressLoading");
	populate_efp_modal(1); // Needed for the filtered_2d_x variables
	$("#hiddenDownloadModal_table").empty(); // reset
	let downloadIndexTable_str = "<table id='downloadIndexTable'>\n\t<tbody>\n";
	downloadIndexTable_str += "\t\t<caption>" + datasetName.split(" ").join("_") + "</caption>\n";
	downloadIndexTable_str += downloadIndexTable_base;

	// Looping through each row of the table
	for (const sra of eFPSortedSRA) {
		downloadIndexTable_str += "\t\t<tr>\n";
		downloadIndexTable_str += "\t\t\t<td>" + sraDict[sra]["title"] + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + sra + "</td>\n";
		downloadIndexTable_str +=
			"\t\t\t<td>" + sraDict[sra]["svg"].substr(4, sraDict[sra]["svg"].length - 8) + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + sraDict[sra]["svg_part"] + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + sraDict[sra]["locusValue"] + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[sra]["bp_length"]) + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[sra]["bp_start"]) + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[sra]["bp_end"]) + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + sraDict[sra]["numberofreads"] + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[sra]["MappedReads"]) + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + sraDict[sra]["rpb"] + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[sra]["RPKM"][variantPosition].toFixed(2)) + "</td>\n";
		downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[sra]["controlsString"]) + "</td>\n";
		downloadIndexTable_str += "\t\t</tr>\n";
	}

	downloadIndexTable_str += "\t</tbody>\n</table>"; // Closing
	document.getElementById("hiddenDownloadModal_table").innerHTML += downloadIndexTable_str;
	$("#hiddenDownloadModal_table").tableToCSV();
	document.getElementById("download_icon").classList.remove("progressLoading");
	document.getElementById("bodyContainer").classList.remove("progressLoading");
}

let publicData = true;
/**
 * Checks if the index.html's (document) "RNA-Seq Database" is currently selected on a public or private database
 * @return {Boolean} forceFalse - Force a the publicData boolean to be false or have it be decided by design
 */
function changePublicData(forceFalse = false) {
	if (forceFalse || uploadingData) {
		publicData = false;
	} else if (
		document.getElementById("xmlDatabase").selectedIndex == 1 ||
		document.getElementById("xmlDatabase").selectedIndex == 2
	) {
		publicData = true;
	} else {
		publicData = false;
	}
}

let isPrecache = true;
/**
 * Determines if dataset should load a preCached data or new set of information
 */
function checkPreload() {
	get_input_values();

	if (verifyLoci(locus)) {
		// Update progress bar and add loading screen
		loadingScreen(false);
		progress_percent = 0;
		document.title = `eFP-Seq Browser: Loading 0% - ${locus}`;
		document.getElementById("progress").title = "0%";
		$("div#progress").width(progress_percent + "%");

		for (const property in public_dataset_dictionary) {
			if (base_src === public_dataset_dictionary[property]) {
				publicData = true;
				break;
			} else {
				publicData = false;
			}
		}

		// Check if public data or not
		if (publicData && locus == "AT2G24270" && dumpMethod == "simple" && !callDumpOutputs) {
			variants_radio_options(1);
			isPrecache = true;
		} else {
			update_all_images(0);
			isPrecache = false;
		}
	} else {
		console.error(`The following locus is not valid: ${locus}`);
	}
}

/**
 * Verify that the locus being called is valid
 * IMPORTANT: The current script only works for Arabidopsis thaliana
 * @param {String} locusToVerify The AGI ID (example: AT3G24650 or AT3G24650.1)
 * @returns {Boolean} If locus is valid [true] or not [false, default]
 * @TODO: Add support for other languages. Fill list of loci patterns can be found within GAIA's tools (accessible only to BAR developer at the moment)
 */
function verifyLoci(locusToVerify) {
	// Check if locus is a string
	if (typeof locusToVerify === "string") {
		/** Arabidopsis thaliana locus pattern */
		const arabidopsisThalianaPattern = `^[A][T][MC0-9][G][0-9]{5}[.][0-9]{1,2}$|^[A][T][MC0-9][G][0-9]{5}$`;

		/** Reg Exp for the locus pattern */
		const regexPattern = new RegExp(arabidopsisThalianaPattern, "i");

		// If match, then return true, else return false
		return locusToVerify.trim().match(regexPattern);
	} else {
		return false;
	}
}

let GFF_List = [];
let parse_output;
/**
 * Gets the variant ID for the splice variants and adds as a title/tooltip to each splice variant image
 * @param {String} locusID - The locus ID
 * @return {List} GFF_list - A list of variant IDs which are used to adds as a title/tooltip to each splice variant image
 */
function getGFF(locusID) {
	GFF_List = [];
	$.ajax({
		url: `https://bar.utoronto.ca/webservices/bar_araport/gene_structure_by_locus.php?locus=${locusID}`,
		dataType: "json",
		crossDomain: true,
		headers: {
			"Access-Control-Allow-Origin": "*",
		},
		failure: function () {
			console.log("Getting GFFs (getGFF) information failed to retrieve locus information from Araport11");
		},
		success: function (gene_res) {
			parse_output = gene_res;
			if (parse_output["wasSuccessful"]) {
				let parsed_features = parse_output["features"][0]["subfeatures"];

				for (let i = 0; i < parsed_features.length; i++) {
					if (parsed_features[i]["uniqueID"] != null) {
						GFF_List.push(parsed_features[i]["uniqueID"]);
					} else {
						GFF_List.push("Error retrieving unique ID/GFF");
					}
				}
			} else if (parse_output["status"] == "fail") {
				console.log("Error: Cannot find GFF ID's with parse output. Please contact admin");
			} else if (parse_output["wasSuccessful"] == "false") {
				if (parse_output["error"] != null) {
					console.log(
						"Error: Cannot find GFF ID's due to following error: " +
							parse_output["error"] +
							". Please contact admin",
					);
				} else {
					console.log("Error: Cannot find GFF ID's with parse output. Please contact admin");
				}
			}
		},
		error: function (xhr, status, error) {
			generateToastNotification(
				`Error getting GFFs (getGFF) information failed to retrieve locus information from Araport11: ${error.message}`,
				"ERROR",
			);
			console.log(
				`Error getting GFFs (getGFF) information failed to retrieve locus information from Araport11: ${error.message}`,
			);
		},
	});
}

/**
 * Adds to the GFFs to the ddSlick dropdown
 */
function addGFF() {
	const eachVariant = document.getElementsByClassName("dd-option");
	if (eachVariant.length > 0) {
		for (let i = 0; i < GFF_List.length; i++) {
			if (document.getElementsByClassName("dd-option")[i]) {
				document.getElementsByClassName("dd-option")[i].setAttribute("title", GFF_List[i]);
			}
		}
	}
}

/**
 * Modifies and adds a id attribute to the hidden g-signin2 on the index page
 */
function hiddenGoogleSignin() {
	const signInButtonList = document.getElementsByClassName("abcRioButtonLightBlue");
	for (let i = 0; i < signInButtonList.length; i++) {
		if (signInButtonList[i]) {
			signInButtonList[i].setAttribute("id", "loginClick" + i);
		}
	}
}

/**
 * Makes all privates databases none-visible anymore
 */
function remove_private_database() {
	databasesAdded = false;
	document.getElementById("private_dataset_header").style.display = "none";
	const privateList = document.getElementsByClassName("userAdded");
	for (let i = 0; i < privateList.length; i++) {
		$("#xmlDatabase option:last").remove();
	}
	check_for_change = 0;
}

/**
 * After autocomplete, correct AGI (locusBrowser) input value
 */
function correctAGIIDInput() {
	if (
		document.getElementById("locus") &&
		document.getElementById("locus").value &&
		document.getElementById("locus").value.trim().length > 0
	) {
		const locusID = document.getElementById("locus").value.trim().split("/");
		if (locusID[0]) {
			document.getElementById("locus").value = locusID[0].toUpperCase().trim();
		} else {
			document.getElementById("locus").value = document.getElementById("locus").value.trim();
		}

		locus_validation();
	}
}

/**
 * Return back to top of page
 */
function returnBackToTop() {
	const mainBody = document.getElementById("main_content");
	mainBody.scrollTop = 0;
}

/**
 * Display the table toggles options dropdown
 */
function toggleOptionsTable() {
	if (document.getElementById("tableToggle").getAttribute("aria-expanded") === "false") {
		document.getElementById("tableToggle").setAttribute("aria-expanded", true);
		document.getElementById("filterDropdown").classList.add("show");
	} else {
		document.getElementById("tableToggle").setAttribute("aria-expanded", false);
		document.getElementById("filterDropdown").classList.remove("show");
	}
}

/**
 * Toggle which table toggles options will be displayed
 */
function toggleTableOptionsView() {
	/** true if already enabled for filtered columns being displayed, false for filtere eFP images */
	const filterCols = document.getElementById("tableFilter-tab").classList.value.includes("active");

	if (filterCols) {
		// Change navigation buttons
		document.getElementById("tableFilter-tab").classList.remove("active");
		document.getElementById("eFPFilter-tab").classList.add("active");

		// Change display
		document.getElementById("tableFilter").classList.remove("show", "active");
		document.getElementById("eFPFilter").classList.add("show", "active");
	} else {
		// Change navigation buttons
		document.getElementById("tableFilter-tab").classList.add("active");
		document.getElementById("eFPFilter-tab").classList.remove("active");

		// Change display
		document.getElementById("tableFilter").classList.add("show", "active");
		document.getElementById("eFPFilter").classList.remove("show", "active");
	}
}

let downloadDivNum = 1;
/**
 * Download the DIV as a image
 * @param {String} id - The string of the body's ID
 */
function downloadDiv(id) {
	html2canvas(document.getElementById(id)).then((canvas) => {
		$("#appendCanvas").empty(); // reset
		canvas.id = "downloadDivNum_" + downloadDivNum;
		document.getElementById("appendCanvas").appendChild(canvas);
		document.getElementById("downloadDivNum_" + downloadDivNum).style.width = "100%";
		$("#DownloadImageModal").modal("toggle");
		downloadDivNum++;
	});
}

/**
 * On click, hide the nav bar from main screen
 * @param {Boolean} hideNavbar Force hide the navbar [true] or base on window [default, false]
 */
function displayNavBAR(hideNavbar = false) {
	const displayNav = $("#navbar_menu").is(":visible") || hideNavbar;

	document.getElementById("navbar_menu").style.display = displayNav ? "none" : "block";
	document.getElementById("main_content").className = displayNav ? "col-sm-12" : "col-sm-9";
	document.getElementById("openMenu").style.display = displayNav ? "block" : "none";
	if (document.getElementById("theTable")) {
		if (displayNav) {
			document.getElementById("theTable").classList.add("RNATable");
		} else {
			document.getElementById("theTable").classList.remove("RNATable");
		}
	}
}

/**
 * Adjust the size of the navbar menu footer to fit the size of the navbar itself
 */
function adjustFooterSize() {
	const navbar = document.getElementById("navbar_menu");
	if (navbar) {
		document.getElementById("nm_footer").style.width = navbar.offsetWidth + "px";
		if (navbar.scrollHeight == navbar.clientHeight) {
			if (!document.getElementById("nm_footer").classList.contains("navbar_menu_footer_overflow_abs")) {
				document.getElementById("nm_footer").classList.remove("navbar_menu_footer_overflow_sticky");
				document.getElementById("nm_footer").classList.add("navbar_menu_footer_overflow_abs");
			}
		} else if (navbar.scrollHeight > navbar.clientHeight) {
			if (!document.getElementById("nm_footer").classList.contains("navbar_menu_footer_overflow_sticky")) {
				document.getElementById("nm_footer").classList.remove("navbar_menu_footer_overflow_abs");
				document.getElementById("nm_footer").classList.add("navbar_menu_footer_overflow_sticky");
			}
		}
	}
}

/**
 * Adjust the table toggle options dropdown to fit above the icon for it
 */
function adjustTableOptionsDropdownSize() {
	document.getElementById("filterDropdown").style.left =
		(
			document.body.offsetWidth -
			document.getElementById("tableToggle").offsetWidth * 2 -
			document.getElementById("filterDropdown").offsetWidth
		).toString() + "px";
}

/**
 * Adjust the submission iFrame (generate data modal) based on window's height
 */
function adjustSubmissionIFrameSize() {
	const iFrameSize = window.innerHeight * 0.7;
	document.getElementById("submissioniframe").height = iFrameSize + "px";
}

let usedToggle = false;
/**
 * Toggles columns in the RNA-Seq table
 * @param {String} colClass The class that is being toggled
 * @param {Boolean} enable True = toggle on, False = toggle off
 */
function toggleTableCol(colClass, enable) {
	const column = document.getElementsByClassName(colClass);
	if (enable) {
		for (const element of column) {
			if (element) {
				element.removeAttribute("hidden");
			}
		}
	} else if (!enable) {
		for (const element of column) {
			if (element) {
				element.setAttribute("hidden", true);
			}
		}
	}
}

let responsiveRNAWidthAdjusted = false;
/**
 * Creates a responsive design for the RNA-Seq images
 */
function responsiveRNAWidthResize() {
	const responsive = document.getElementsByClassName("responsiveRNAWidth");
	if (window.innerWidth <= 575) {
		for (let i = 0; i < responsive.length; i++) {
			responsive[i].style.minWidth = window.innerWidth * 0.93 + "px";
		}
		responsiveRNAWidthAdjusted = true;
	} else if (window.innerWidth > 575 && responsiveRNAWidthAdjusted) {
		for (let i = 0; i < responsive.length; i++) {
			responsive[i].style.minWidth = "420px";
		}
	}
}

/**
 * Helper function for making the tableResponsiveTable function shorter
 * @param {Bool} colTitleBool true = title column visible, false = column hidden
 * @param {Bool} colRNABool true = RNA column visible, false = column hidden
 * @param {Bool} colrpbBool true = rpb column visible, false = column hidden
 * @param {Bool} coleFPBool true = eFP column visible, false = column hidden
 * @param {Bool} colRPKMBool true = RPKM column visible, false = column hidden
 * @param {Bool} colDetailsBool true = details column visible, false = column hidden
 * @param {Bool} colCompareBool true = compare variants column visible, false = column hidden
 */
function toggleResponsiveTableOptions(
	colTitleBool,
	colRNABool,
	colrpbBool,
	coleFPBool,
	colRPKMBool,
	colDetailsBool,
	colCompareBool,
) {
	toggleTableCol("colTitle", colTitleBool);
	document.getElementById("toggleTitle").checked = colTitleBool;
	toggleTableCol("colRNA", colRNABool);
	document.getElementById("toggleRNA").checked = colRNABool;
	toggleTableCol("colrpb", colrpbBool);
	document.getElementById("togglerpb").checked = colrpbBool;
	toggleTableCol("coleFP", coleFPBool);
	document.getElementById("toggleeFP").checked = coleFPBool;
	toggleTableCol("colRPKM", colRPKMBool);
	document.getElementById("toggleRPKM").checked = colRPKMBool;
	toggleTableCol("colDetails", colDetailsBool);
	document.getElementById("toggleDetails").checked = colDetailsBool;
	toggleTableCol("colCompare", colCompareBool);
	document.getElementById("toggleCompare").checked = colCompareBool;

	RememberToggleOptions(
		colTitleBool,
		colRNABool,
		colrpbBool,
		coleFPBool,
		colRPKMBool,
		colDetailsBool,
		colCompareBool,
	);
}

/**
 * Determine what responsive table should be displayed based on screen width
 */
function determineResponsiveTable() {
	if (document.body.offsetWidth <= 576) {
		toggleResponsiveTable(2);
		displayNavBAR(true);
	} else {
		toggleResponsiveTable(0);
	}
}

/**
 * Creates a responsive mobile/small screen RNA-Table design *
 * @param {number} [forceToggle=0] Forces a toggled responsive design. 0 = none, 1 = mobile, 2 = desktop
 */
function toggleResponsiveTable(forceToggle = 0) {
	if (document.getElementById("tableToggle").style.display != "none") {
		// Mobile design
		if (forceToggle == 1 || (window.innerWidth <= 575 && !usedToggle)) {
			toggleResponsiveTableOptions(false, true, false, false, false, false, false);
		} else if (forceToggle == 2 || (window.innerWidth >= 1100 && !usedToggle)) {
			// Default
			toggleResponsiveTableOptions(true, true, true, true, true, true, false);
		} else if (forceToggle == 3 || (window.innerWidth < 830 && !usedToggle)) {
			// Toggle off same as below but also rpb values at windows resolution less than 830 pixels
			toggleResponsiveTableOptions(true, true, false, false, false, false, false);
		} else if (forceToggle == 4 || (window.innerWidth < 900 && !usedToggle)) {
			// Toggle off same as below but also RPKM count at windows resolution less than 900 pixels
			toggleResponsiveTableOptions(true, true, true, false, false, false, false);
		} else if (forceToggle == 5 || (window.innerWidth < 990 && !usedToggle)) {
			// Toggle off same as below but also eFP images at windows resolution less than 990 pixels
			toggleResponsiveTableOptions(true, true, true, false, true, false, false);
		} else if (forceToggle == 6 || (window.innerWidth < 1100 && !usedToggle)) {
			// Toggle off details at windows resolution less than 1100 pixels
			toggleResponsiveTableOptions(true, true, true, true, true, false, false);
		}
	}
}

let ToggledTable = [true, true, true, true, true, true, false];
/**
 * Remember what toggle options were chosen in the RNA table
 * @param {boolean} [title=true] Title
 * @param {boolean} [rna=true] RNA-Seq Coverage
 * @param {boolean} [rpb=true] rpb
 * @param {boolean} [efp=true] eFP
 * @param {boolean} [rpkm=true] RPKM
 * @param {boolean} [details=true] Details
 * @param {boolean} [compare=false] Compare gene variants
 */
function RememberToggleOptions(
	title = true,
	rna = true,
	rpb = true,
	efp = true,
	rpkm = true,
	details = true,
	compare = false,
) {
	ToggledTable = [title, rna, rpb, efp, rpkm, details, compare];
}

const colSortList = ["colTitle", "colrpb", "colRPKM", "colDetails"];
/**
 * Resize the directional arrows to more accurately fix the column size
 */
function ResizeArrowRow() {
	for (const col of colSortList) {
		const colRow = col + "Row";
		document.getElementById(colRow).style.width = document.getElementById(colRow).parentNode.offsetWidth - 2 + "px";
		const colArrow = col + "Arrow";
		CheckElementWidth(colArrow, 8);
	}
}

/**
 * Check if the directional arrows are visible or not
 * @param {String} arrowID The element ID for the arrow being checked
 * @param {Num} widthCheckFor The size of the element, in pixels, being checked for
 */
function CheckElementWidth(arrowID, widthCheckFor) {
	if (document.getElementById(arrowID).offsetWidth < widthCheckFor) {
		document.getElementById(arrowID).style.width = widthCheckFor + "px";
	}
}

/**
 * Change the directional arrow of a table based on its sorting direction
 * @param {String} tableArrowID The element ID for the table's icon that will change
 */
function ChangeColArrow(tableArrowID) {
	const arrowDown = "./cgi-bin/SVGs/arrowSortDown.min.svg";
	const arrowUp = "./cgi-bin/SVGs/arrowSortUp.min.svg";
	setTimeout(function () {
		const arrowColID = tableArrowID + "Arrow";
		if (document.getElementById(tableArrowID).classList.contains("headerSortDown")) {
			document.getElementById(arrowColID).src = arrowDown;
		} else if (document.getElementById(tableArrowID).classList.contains("headerSortUp")) {
			document.getElementById(arrowColID).src = arrowUp;
		}
		for (const col of colSortList) {
			const colArrow = col + "Arrow";
			CheckElementWidth(colArrow, 8);
		}
	}, 100);
}

/**
 * Scroll to a desired RNA row
 * @param {String} rowID The ID of the row which will be scrolled to
 */
function ScrollToRNARow(rowID) {
	// Close eFP Overview if open
	document.getElementById("closemodal_efPOverview").click();

	// Scroll to RNA row
	$("#main_content").animate({ scrollTop: $("#" + rowID).offset().top }, "slow");

	if (document.getElementById(rowID)) {
		// Add background colour of selected row for clarity
		document.getElementById(rowID).className += " scrollToRow";

		// Fade out colour
		setTimeout(function () {
			document.getElementById(rowID).className += " scrollToRowRemove";
		}, 2000);

		// Remove those classes
		setTimeout(function () {
			document.getElementById(rowID).classList.remove("scrollToRow");
			document.getElementById(rowID).classList.remove("scrollToRowRemove");
		}, 4050);
	}
}

/**
 * Determine if a enter was pressed and if so, click a button
 * @param {Event} event The key press
 * @param {String} toClickButton Which button to click
 */
function IfPressEnter(event, toClickButton) {
	if (event.which == 13 || event.keyCode == 13) {
		$("#" + toClickButton).click();
	}
}

let BrowserDetected = false;
/**
 * Detect the browser the user is using and change the manage cookies string
 */
function DetectBrowser() {
	if (BrowserDetected === false) {
		/** userAgent Browser detection object */
		const userAgentParser = {
			"Microsoft+Edge": {
				Contain: ["Edge"],
			},
			Opera: {
				Contain: ["OPR", "Opera"],
			},
			Firefox: {
				Contain: ["Firefox"],
				NContain: ["Seamonkey"],
			},
			Seamonkey: {
				Contain: ["Seamonkey"],
			},
			Chrome: {
				Contain: ["Chrome"],
				NContain: ["Chromium"],
			},
			Chromium: {
				Contain: ["Chromium"],
			},
			"Internet+Explorer": {
				Contain: ["MSIE"],
			},
			Safari: {
				Contain: ["Safari"],
				NContain: ["Chromium", "Chrome"],
			},
		};

		/** Retrieve keys from userAgent in the instance this is modified */
		let userAgentParserKeys;
		if (userAgentParser) {
			userAgentParserKeys = Object.keys(userAgentParser);
		} else {
			logError("Unable retrieve userAgentParser");
		}
		let detectBrowser;
		let notDetectedBrowser = true;

		for (const userAgent of userAgentParserKeys) {
			// If contains the required keyword
			for (let c = 0; c < userAgentParser[userAgent]["Contain"].length; c++) {
				if (notDetectedBrowser && navigator.userAgent.indexOf(userAgentParser[element]["Contain"][c]) !== -1) {
					// If detected key has a exclusion, go through those
					if (userAgentParser[element]["NContain"]) {
						// If pass is the same as fail, then it contains the excluded keywords and fails the test
						const failLength = userAgentParser[element]["NContain"].length;
						let passLength = 0;

						userAgentParser[element]["NContain"].forEach((agent) => {
							// If contains exclusion word, increase pass count towards failure
							if (navigator.userAgent.indexOf(agent) !== -1) {
								passLength++;
							}
						});

						if (passLength != failLength) {
							detectBrowser = element;
							notDetectedBrowser = false;
							break;
						}
					} else {
						detectBrowser = element;
						notDetectedBrowser = false;
						break;
					}
				}
			}
		}

		// Change the help string to manage cookies
		if (detectBrowser) {
			$("#notChrome").empty();
			const append_str =
				' or through the following <a href="https://www.google.com/search?q=manage+cookies+in+' +
				detectBrowser +
				'" target="_blank" rel="noopener">Google search results</a>';
			$("#notChrome").append(append_str);
		}

		// make BrowserDetected true so this will not run again
		BrowserDetected = true;
	}
}

/**
 * Create the filtered eFP List
 */
function CreateFilteredeFPList() {
	$("#filtereFPList").empty();

	// Add individual Tissues
	if (tissueSRADic) {
		const allTissuesDisplayed = Object.keys(tissueSRADic);
		for (const tissue of allTissuesDisplayed) {
			let append_str = '<li class="form-check">';
			append_str +=
				'<input class="form-check-input" type="checkbox" id="' +
				tissue.replace(" ", "_") +
				'" onclick="ToggleFilteredeFP(this.id, this.checked);" style="margin: 6px 5px 0;" value="toggleeFP" checked>';
			append_str +=
				'<p class="form-check-label" for="toggleTitle" style="padding-left: 20px; font-weight: 10;">' +
				tissue +
				"</p>";
			append_str += "</li>";
			$("#filtereFPList").append(append_str);
		}
	} else {
		logError("Unable to use tissueSRADic");
	}
}

/**
 * Toggle eFP (RPKM) rows to visible or not
 * @param {String} whichToToggle Which tissue to filter in or out
 * @param {Boolean} OnOrOff True = visible, False = filtered out
 */
function ToggleFilteredeFP(whichToToggle, OnOrOff) {
	const whichSVG = whichToToggle.replace("_", " ");
	const whichSRA = tissueSRADic[whichSVG];

	if (OnOrOff === true) {
		for (let i = 0; i < whichSRA.length; i++) {
			if (document.getElementById(whichSRA[i] + "_row")) {
				document.getElementById(whichSRA[i] + "_row").removeAttribute("hidden");
			}
		}
	} else if (OnOrOff === false) {
		for (let i = 0; i < whichSRA.length; i++) {
			if (document.getElementById(whichSRA[i] + "_row")) {
				document.getElementById(whichSRA[i] + "_row").setAttribute("hidden", true);
			}
		}
	}
}

/**
 * Load newly generated data from the submission page
 */
function LoadSubmittedData() {
	emptyLanding();
	progress_percent = 0;
	document.title = `eFP-Seq Browser: Loading 0% - ${locus}`;
	loadingScreen(false);
	setTimeout(function () {
		count_bam_num();
		disableAllComparison();
	}, 200);
	update_all_images(0);
}

let shareLink;
/**
 * Generate a share link
 */
function generateShareLink(changeURL = false) {
	/** Generate base link */
	let url = "https://" + window.location.host + window.location.pathname;

	// If a public dataset, generate link for that information
	url += "?locus=" + locus + "&dataset=" + base_src;

	// Add to page
	shareLink = url;

	if (changeURL && window.history.pushState) {
		window.history.pushState({}, "Title", window.location.pathname + "?locus=" + locus + "&dataset=" + base_src);
	}

	document.getElementById("shareLinkTextArea").textContent = shareLink;
}

const shareLinkInputs = {};
/**
 * Read shared link and display data if appropriate
 */
function readShareLink() {
	/** Find share link information */
	const query = window.location.search.substr(1);

	// If this value hits 2, then all the essential information has been called for it to be loaded
	let locusInput = false;
	let datasetInput = false;

	// If exists, continue
	if (query != "") {
		const inputs = query.split("&");
		for (const input of inputs) {
			const queryInputs = input.split("=");

			if (queryInputs.length > 1) {
				// If locus
				if (queryInputs[0].split("%20").join(" ").trim() === "locus") {
					const qIValue = input.substring(6).split("%20").join(" ").trim();
					shareLinkInputs["locus"] = qIValue;
					document.getElementById("locus").value = qIValue;
					locusInput = true;
				} else if (queryInputs[0].split("%20").join(" ").trim() === "dataset") {
					const qIValue = input.substring(8).split("%20").join(" ").trim();
					shareLinkInputs["dataset"] = qIValue;
					base_src = qIValue;
					datasetInput = true;
				}
			}
		}

		// Load new data
		if (locusInput && datasetInput) {
			emptyLanding();
			progress_percent = 0;
			document.title = `eFP-Seq Browser: Loading 0% - ${locus}`;
			sraDict = {};
			sraCountDic = {};
			loadNewDataset = false;
			setTimeout(function () {
				count_bam_num();
				disableAllComparison();
				checkPreload();
			}, 200);
			toggleResponsiveTable(0);
		} else if (locusInput && datasetInput === false) {
			displayError("ERROR IN SHARE LINK! Missing dataset");
		} else if (locusInput === false && datasetInput) {
			displayError("ERROR IN SHARE LINK! Missing locus");
		} else {
			displayError("ERROR IN SHARE LINK! Missing locus and dataset");
		}
	}
}

/**
 * Copy share link to the user's clipboard
 */
function copyToClipboard() {
	if (document.getElementById("shareLinkTextArea").trim() !== "") {
		document.getElementById("shareLinkTextArea").select();
		document.execCommand("copy");
	}
}

/** All checked and currently displayed comparisons */
let allCheckedOptions = [];
/**
 * Functionality of the table's individual entry's check box for comparison
 * @param {String} whatID The ID of what table entry is being checked
 * @param {Boolean} disableAll If want to disable all at once, make this true
 */
function tableCheckbox(whatID, disableAll = false) {
	const whatSRA = whatID.split("_")[0]; // Retrieve SRA number

	if (disableAll) {
		disableAllComparison();
	} else if (disableAll === false && document.getElementById(whatID) && document.getElementById(whatID).checked) {
		// If checked, then add compare entries
		allCheckedOptions.push(whatSRA); // Add to list of displayed comparisons
		const iterationProcess = {};

		// Add other tables based on the list of variants available
		for (let i = 0; i < GFF_List.length; i++) {
			/** Construct a table row <tr> element  */
			let append_str = '<tr class="compareDataRow" id="' + whatSRA + "_compareRow" + i + '">';

			// Append title <td>
			if (parseInt(i) === parseInt(variantPosition)) {
				append_str +=
					'<td style="width: 250px; font-size: 12px;" id="' +
					whatSRA +
					"_compareTitle" +
					i +
					'">' +
					document.getElementById(whatSRA + "_title").innerHTML +
					" ... (" +
					GFF_List[i] +
					")</td>\n";
			} else {
				append_str +=
					'<td style="width: 250px; font-size: 12px;" id="' +
					whatSRA +
					"_compareTitle" +
					i +
					'">^^^ ... (' +
					GFF_List[i] +
					")</td>\n";
			}

			// Append RNA-Seq and Gene Structure images (2 imgs) in one <td>
			append_str +=
				'<td style="max-width: 576px;">' +
				'<img loading="lazy" id="' +
				whatSRA +
				"_rnaseq_img" +
				i +
				'" alt="RNA-Seq mapped image for:' +
				whatSRA +
				'" style="min-width:420px; max-width:576px; width:95%; height: auto;" src="" /><br/>' +
				'<img loading="lazy" id="' +
				whatSRA +
				"_gene_structure_img" +
				i +
				'" style="max-width: 576px; width:100%; height: auto;" src="" alt="Gene variant image for:' +
				whatSRA +
				'"/>' +
				"</td>\n";

			// Append the rpb <td>
			append_str +=
				'<td id="' +
				whatSRA +
				"_rpb" +
				i +
				"" +
				'" style="font-size: 12px; width: 50px; ">' +
				sraDict[whatSRA]["r"][i].toFixed(2) +
				"</td>";

			// Append the appropriate SVG with place holder sorting number in front of it .. all in one <td>
			append_str +=
				'<td tag="svg_name" style="width:  75px;">' +
				'<div id="' +
				whatSRA +
				"_svg" +
				i +
				'" name="' +
				sraDict[whatSRA]["svg"].substr(4).replace(".", "_") +
				'_tissue" tag=' +
				sraDict[whatSRA]["svg_part"] +
				'_subtissue" width="75" height="75" style="width: 75px; height: 75px; max-width: 75px; max-height: 75px;">' +
				document.getElementById(sraDict[whatSRA]["svg"].substr(4).replace(".svg", "_svg")).innerHTML +
				"</div>" +
				'<div class="mdl-tooltip" for="' +
				whatSRA +
				"_svg" +
				i +
				'">' +
				sraDict[whatSRA]["svg"].substring(4).replace(".svg", "") +
				"</div></td>\n";

			// Append abs/rel RPKM
			append_str +=
				'<td id="' +
				whatSRA +
				"_rpkm" +
				i +
				'" style="font-size: 12px; width: 50px; ">' +
				sraDict[whatSRA]["RPKM"][i].toFixed(2) +
				"</td>";

			// Append the details <td>
			if (parseInt(i) === parseInt(variantPosition)) {
				append_str +=
					'<td style="width: 250px; font-size: 12px;" id="' +
					whatSRA +
					"_compareTitle" +
					i +
					'"><div id="' +
					whatSRA +
					'_descriptionCompare" name="' +
					document.getElementById(whatSRA + "_description").getAttribute("name") +
					'">' +
					document.getElementById(whatSRA + "_description").innerHTML +
					'</div><div id="igbLinkCompare_' +
					whatSRA +
					'">' +
					document.getElementById("igbLink_" + whatSRA).innerHTML +
					'</div><div id="extraLinksCompare_' +
					whatSRA +
					'">' +
					document.getElementById("extraLinks_" + whatSRA).innerHTML +
					"</div></td>\n";
			} else {
				append_str +=
					'<td style="width: 250px; font-size: 12px;" id="' + whatSRA + "_compareTitle" + i + '">^^^</td>\n';
			}

			// End
			append_str += "</tr>";

			// Find appropriate place to add new table row
			iterationProcess[i] = whatSRA + "_compareRow" + i;
			document.getElementById("compareTable").innerHTML += append_str;

			// Update images
			if (document.getElementById(whatSRA + "_rnaseq_img" + i)) {
				document
					.getElementById(whatSRA + "_rnaseq_img" + i)
					.setAttribute("src", document.getElementById(whatSRA + "_rnaseq_img").src);
			}
			if (document.getElementById(whatSRA + "_gene_structure_img" + i)) {
				document
					.getElementById(whatSRA + "_gene_structure_img" + i)
					.setAttribute("src", document.getElementsByClassName("dd-option-image")[i].src);
			}

			// Colour SVG
			if (sraDict[whatSRA]["RPKM"] && sraDict[whatSRA]["RPKM"][i]) {
				colour_part_by_id(
					whatSRA + "_svg" + i,
					sraDict[whatSRA]["svg_part"],
					sraDict[whatSRA]["RPKM"][i],
					colouring_mode,
				);
			}
		}
		document.getElementById(whatID).checked = true;
		document.getElementById("allCheckbox").checked = true;

		if (colouring_mode != "rel") {
			document.getElementById("compareGeneVariants").disabled = false;
		}
	} else {
		// If unchecked, remove compare entries
		if (disableAll === false) {
			disableCompare(whatSRA);
			allCheckedOptions.splice(allCheckedOptions.indexOf(whatSRA), 1);
			document.getElementById(whatID).checked = false;
		} else if (disableAll === true) {
			disableAllComparison();
		}

		// If no checks left, disable compareGeneVariants
		if (allCheckedOptions.length === 0) {
			document.getElementById("compareGeneVariants").disabled = true;
		}
	}
}

/**
 * Disable a desired compare region for a single SRA
 * @param {String} whatSRA What SRA comparison to remove
 */
function disableCompare(whatSRA) {
	for (let i = 0; i < GFF_List.length; i++) {
		if (document.getElementById(whatSRA + "_compareRow" + i) != undefined) {
			document.getElementById(whatSRA + "_compareRow" + i).remove();
		}
	}
}

/**
 * Disable all comparisons at once
 */
function disableAllComparison() {
	if (document.getElementById("allCheckbox")) {
		// Disable loaded comparisons
		let compareDataRows = document.getElementsByClassName("compareDataRow");
		for (let c = compareDataRows.length - 1; c >= 0; c--) {
			document.getElementsByClassName("compareDataRow")[c].remove();
		}
		allCheckedOptions = [];

		// Remove all check marks
		compareDataRows = document.getElementsByClassName("compareCheckbox");
		for (let c = 0; c < compareDataRows.length; c++) {
			document.getElementsByClassName("compareCheckbox")[c].checked = false;
		}
		document.getElementById("allCheckbox").checked = false;

		// Double check
		const listOfEntries = [];
		const mainEntries = document.getElementsByClassName("mainEntries");
		for (let m = 0; m < mainEntries.length; m++) {
			const mainID = mainEntries[m].id;
			if (listOfEntries.includes(mainID) === false) {
				listOfEntries.push(mainID);
			} else {
				document.getElementsByClassName("mainEntries")[m].remove();
			}
		}

		// Disable comparison button
		document.getElementById("compareGeneVariants").disabled = true;
	}
}

/**
 * Make the cookie consent disappear
 */
function PnCDisappear() {
	document.getElementById("PrivacyAndCookies").setAttribute("hidden", true);
	document.cookie = "eSBAcceptedCookies=1; expires=Friday, December 31, 9999 at 7:00:00 AM; SameSite=Lax; Secure";
	document.cookie =
		"eSBVersion=" + version + "; expires=Friday, December 31, 9999 at 7:00:00 AM; SameSite=Lax; Secure";
}

/**
 * Setting up and determining functions based on existing BAR related cookies
 */
function setUpCookies() {
	/** An array of all existing cookies for the eFP-Seq Browser */
	const cookies = document.cookie.split(";");
	/** Determine if the cookies T&S have been accepted or not (undefined means not accepted) */
	let cookieAccept = undefined;
	/** Determine the version of the eFP-Seq Browser (undefined means not yet designated) */
	let cookieVersion = undefined;

	for (const cookie of cookies) {
		/** An array of the cookies where [0] should be cookie name/key and [1] should be cookie value */
		const whichCookie = cookie.split("=");

		// Look for eSBAcceptedCookies which is if the user has accepted the T&S or not (0 = false, 1 = true)
		if (whichCookie[0] && whichCookie[0].trim() === "eSBAcceptedCookies") {
			cookieAccept = whichCookie[1].trim();
		}

		// Look for eSBVersion which is the version of the eFP-Seq Browser based on the version variable
		if (whichCookie[0] && whichCookie[0].trim() === "eSBVersion") {
			cookieVersion = whichCookie[1].trim();
		}

		// If all BAR related cookies found already, no need to look through all other cookies
		if (cookieAccept && cookieVersion) {
			break;
		}
	}

	if (cookieAccept && cookieAccept === "1") {
		// If accepted T&S, do not display it
		document.getElementById("PrivacyAndCookies").setAttribute("hidden", false);
	} else if (cookieAccept && cookieAccept === "0") {
		// If not accepted T&S, display it
		document.getElementById("PrivacyAndCookies").removeAttribute("hidden");
	} else {
		// If not accepted T&S, display it
		document.getElementById("PrivacyAndCookies").removeAttribute("hidden");
	}

	if (cookieVersion && cookieVersion !== version) {
		// If version does not match, display T&S
		document.getElementById("PrivacyAndCookies").removeAttribute("hidden");
		document.cookie = "eSBAcceptedCookies=0; SameSite=Lax; Secure";
	}
}

/**
 * Display version number of the eFP-Seq Browser within the Help's section Feedback card
 */
function displayVersionNumber() {
	document.getElementById("feedbackText").innerHTML +=
		"<br><br>The eFP-Seq Browser's current version number is: " + version;
}

let toastCounter = 0;
function generateToastNotification(message, header = "Notification") {
	// Adds a new toast notification to the page
	if (message) {
		let dataAttributeValue = `toast-${toastCounter}`;

		const toast = `
		<div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-toast="${dataAttributeValue}" style="background-color: rgba(255, 255, 255, 1);">
			<div class="toast-header">
				<img
					src="cgi-bin/img/BAR-logo.svg"
					class="rounded me-2"
					alt="BAR notification"
					style="width: 20px; height: 20px"
				/>
				<strong class="me-auto">${header}</strong>
				<button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
			</div>
			<div class="toast-body">${message}</div>
		</div>
		`;

		// Add toast to id="toast-container"
		document.getElementById("toast-container").innerHTML += toast;

		// Initialize the toast
		$(`[data-toast="${dataAttributeValue}"]`).toast({
			autohide: false,
		});
		$(`[data-toast="${dataAttributeValue}"]`).toast("show");
	}
}

// Whenever browser resized, checks to see if footer class needs to be changed
$(window).resize(function () {
	adjustFooterSize();
	adjustSubmissionIFrameSize();
	responsiveRNAWidthResize();
	toggleResponsiveTable();
	adjustTableOptionsDropdownSize();
	setTimeout(function () {
		adjustFooterSize();
	}, 10);
});

/**
 * Initialize the script for the eFP-Seq Browser
 */
function init() {
	// Prevent Microsoft Edge from autofilling causing errors
	document.getElementById("locus").value = "AT2G24270";
	document.getElementById("xmlDatabase").value = "Araport 11 RNA-seq data";

	// On load, validate input
	locus_validation();
	old_locus = locus;
	yscale_validation();
	rpkm_validation();

	// Adjust UI
	adjustFooterSize();
	displayVersionNumber();
	adjustTableOptionsDropdownSize();

	// Cookies
	setUpCookies();

	// Bind event listeners...
	$("input[type=radio][name=radio_group]").change(function () {
		gene_structure_radio_on_change();
	});

	$("#locus").keyup(function () {
		locus_validation();
	});

	$("#yscale_input").keyup(function () {
		yscale_validation();
	});

	$("#rpkm_scale_input").keyup(function () {
		rpkm_validation();
	});

	if (document.getElementsByClassName("abcRioButtonLightBlue").length > 0) {
		hiddenGoogleSignin();
	}
	getGFF(locus);

	$("#locus").autocomplete({
		source: function (request, response) {
			const last = request.term.split(/,\s*/).pop();
			$.ajax({
				type: "GET",
				url:
					"https://bar.utoronto.ca/webservices/eFP-Seq_Browser/idautocomplete.cgi?species=Arabidopsis_thaliana&term=" +
					last,
				dataType: "json",
			}).done(function (data) {
				if (data && data.length >= 7) {
					response(data.slice(0, 7));
				} else {
					response(data);
				}
			});
		},
		close: function (e, ui) {
			correctAGIIDInput();
		},
	});

	// Delay and resize the iFrame for submission page
	const subiFrame = document.getElementById("submissioniframe");
	if (subiFrame) {
		subiFrame.setAttribute("src", subiFrame.getAttribute("data-src"));
	}
	adjustSubmissionIFrameSize();

	readShareLink();

	// Adjust canonical URL in meta tags
	// Looks at the URL and changes the rel="canonical" to current URL if valid
	let validHost = "bar.utoronto.ca";

	// Check if the host is valid
	if (document && document.location.host === validHost && document.location.href) {
		if (document.querySelector('link[rel="canonical"]')) {
			document.querySelector('link[rel="canonical"]').setAttribute("href", document.location.href);
		}
	}
}

// Adjust right away so does not look weird
adjustFooterSize();

window.addEventListener("load", function () {
	init();
});
