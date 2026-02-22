import { test, expect } from "@playwright/test";

test.describe("Generate Data flow", () => {
	test("fills form in iframe and generates XML", async ({ page }) => {
		await page.goto("http://localhost:3030/index.html");
		await page.waitForLoadState("load");

		// Open the Generate Data modal
		await page.getByRole("button", { name: "Generate Data" }).click();
		await page.waitForSelector("#SubmissionModal", { state: "visible", timeout: 10000 });

		// Ensure iframe has a src (lazy-loaded via data-src)
		const iframeElement = page.locator("#submissioniframe");
		const currentSrc = await iframeElement.getAttribute("src");
		if (!currentSrc || currentSrc === "") {
			const dataSrc = (await iframeElement.getAttribute("data-src")) || "cgi-bin/Submission_page.html";
			await iframeElement.evaluate((node, value) => {
				node.setAttribute("src", value);
			}, dataSrc);
		}

		// Wait for iframe content to load
		const frameHandle = await iframeElement.elementHandle();
		const frame = await frameHandle?.contentFrame();
		expect(frame).not.toBeNull();
		await frame?.waitForSelector("#GenerateButton", { state: "visible" });

		// Fill required inputs (including hidden ones) directly to satisfy form validation
		await frame.evaluate(() => {
			const setVal = (id, value) => {
				const el = document.getElementById(id);
				if (el) {
					el.value = value;
					el.dispatchEvent(new Event("input", { bubbles: true }));
				}
			};

			setVal("reqxml", "Test Dataset Title");
			setVal("reqauthor", "Test Author");
			setVal("contectinfo", "author@example.com");
			setVal("reqtitle", "Entry One Title");
			setVal("reqdesc", "Entry description for testing.");
			setVal("rec", "SRR99999999");
			setVal("filename", "test-file.bam");
			setVal("reqread", "1000000");
			setVal("readmapmethod", "STAR");
			setVal("tissue1_subunit", "Root");
			setVal("hexID_num1", "#53f442");
			setVal("foregroundID_num1", "#000000");
			setVal("svg1", "ath-rosettePlusRoot.svg");

			const bamInput = document.getElementById("bam_input");
			if (bamInput) {
				bamInput.value = "https://s3.amazonaws.com/test-bucket/test-file.bam";
				bamInput.dispatchEvent(new Event("input", { bubbles: true }));
			}

			const bamType = document.getElementById("bamType");
			if (bamType) {
				bamType.value = "Amazon AWS";
				bamType.dispatchEvent(new Event("change", { bubbles: true }));
			}

			const species = document.getElementById("reqspecies");
			if (species) {
				species.value = "Arabidopsis thaliana";
				species.dispatchEvent(new Event("change", { bubbles: true }));
			}
		});

		// Generate XML
		await frame.click("#GenerateButton");
		await frame.waitForSelector("#DownloadLink[href^='data:text/xml;base64']", { timeout: 15000 });

		// Validate generated XML content includes our inputs
		const xmlData = await frame.evaluate(() => {
			const href = document.getElementById("DownloadLink")?.getAttribute("href") || "";
			const base64 = href.replace("data:text/xml;base64,", "");
			try {
				return atob(base64);
			} catch (e) {
				return "";
			}
		});

		expect(xmlData).toContain("Test Dataset Title");
		expect(xmlData).toContain("Entry One Title");
		expect(xmlData).toContain("https://s3.amazonaws.com/test-bucket/test-file.bam");
		expect(xmlData).toContain("test-file.bam");
		expect(xmlData).toContain("SRR99999999");
		expect(xmlData).toContain("Root");
	});
});
