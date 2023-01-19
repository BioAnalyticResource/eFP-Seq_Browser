# eFP-Seq-Browser

The eFP-Seq Browser is an RNA-Seq data exploration tool that shows read map coverage of a gene of interest along with an "electronic fluorescent pictographic" (eFP) image. This web-tool also allows the generation of new datasets if provided with SAM/BAM (with their index files) to allow visualization of any RNA-Seq mapping coverage. Gene expression levels and the similarity is also shown by calculating the Reads per Kilobase per Million reads mapped (RPKM) expression levels and Point Biserial Correlation Coefficient (r<sub>pb</sub>) scores amongst its different splice variants.

Official publication of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) can be found at [https://doi.org/10.1111/tpj.14468](https://doi.org/10.1111/tpj.14468).

[![Maintainability](https://api.codeclimate.com/v1/badges/0a119cf04831e18922ed/maintainability)](https://codeclimate.com/github/BioAnalyticResource/eFP-Seq_Browser/maintainability)
[![Follow on Twitter](https://img.shields.io/twitter/follow/BAR_PlantBio?style=social)](https://twitter.com/BAR_PlantBio)
[![GitHub repo size](https://img.shields.io/github/repo-size/BioAnalyticResource/eFP-Seq-Browser)](https://github.com/BioAnalyticResource/eFP-Seq-Browser)
[![GitHub](https://img.shields.io/github/license/BioAnalyticResource/eFP-Seq-Browser)](https://github.com/BioAnalyticResource/eFP-Seq-Browser)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fbar.utoronto.ca%2FeFP-Seq_Browser%2F)](https://bar.utoronto.ca/eFP-Seq_Browser/)

## Getting Started

It is recommended that you use the web version available at https://bar.utoronto.ca/eFP-Seq_Browser/ but if you want to download and run the eFP-Seq Browser locally, it is possible though it may require an internet connection to reach our webservices and Araport's APIs.

## Browser Compatibilities

| Chrome | Firefox | IE  | Edge | Safari | Opera | Tor | Mobile |
| ------ | ------- | --- | ---- | ------ | ----- | --- | ------ |
| ✔      | ✔       | X   | ✔    | ✔      | ✔     | ✔   | ✔      |

## Installation/Open

Clone the repository with git by running the following command:

```
git clone https://github.com/BioAnalyticResource/eFP-Seq-Browser.git
```

If you wish to modify the code, all .CGI files use [Python 3](https://www.python.org) as well as there are a few [Perl](https://www.perl.org/) scripts. The primary webservice ([rnaSeqMapCoverage.cgi](cgi-bin/rnaSeqMapCoverage.cgi)) requires [SAMTools](https://github.com/samtools/samtools) and [bcftools](https://samtools.github.io/bcftools/bcftools.html).

There are also some JavaScript packages that are optional to install. To install these, ensure you have Node version 16.18.0 or higher installed and run the following commands:

```
npm install
```

Outside of that, there is nothing to install, just download all the files and have your server host the [index.html](index.html) file and change all the Python scripts from our server to yours.

## Known issues

We aim to make the eFP-Seq Browser as perfect as possible but unfortunately, there may be some unforeseen bugs. If you manage to find one that is not here, feel free to create a [bug report](https://github.com/BioAnalyticResource/eFP-Seq_Browser/issues/new?template=bug_report.md) so we can fix it.

Current known issues:

-   The IGB links do not work with Google Drive repositories
-   If the web service timeouts, the eFP-Seq Browser will load continuously

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## License

SVG images are [CC-BY SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
For rest: [GPL-2.0](LICENSE.md)

## Authors

-   Alexander Sullivan - [GitHub](https://github.com/AlexJSully), [Twitter](https://twitter.com/alexjsully), [ORCiD](https://orcid.org/0000-0002-4463-4473), [LinkedIn](https://www.linkedin.com/in/alexanderjsullivan/), [Website](https://alexjsully.me/)
-   Priyank Purohit - [GitHub](https://github.com/priyank-purohit)
-   Nowlan H. Freese
-   Asher Pasha - [Github](https://github.com/asherpasha), [Twitter](https://twitter.com/AsherPasha), [ORCiD](https://orcid.org/0000-0002-9315-0520)
-   Eddi Esteban - [ORCiD](https://orcid.org/0000-0001-9016-9202)
-   Jamie Waese - [GitHub](https://github.com/jamiewaese), [Twitter](https://twitter.com/JamieWaese), [Website](https://www.waese.com/#)
-   Alison Wu
-   Michelle Chen
-   Chih Ying Chin
-   Richard Song
-   Sneha Ramesh Watharkar
-   Agnes P. Chan
-   Vivek Krishnakumar
-   Matthew W. Vaughn
-   Chris Town
-   Ann E. Loraine - [Twitter](https://twitter.com/igbbioviz), [Website](https://lorainelab.org/)
-   Nicholas J. Provart - [Github](https://github.com/BioAnalyticResource), [Twitter](https://twitter.com/BAR_PlantBio), [Website](https://bar.utoronto.ca)
