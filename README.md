# eFP-Seq-Browser

The eFP-Seq Browser is a RNA-Seq data exploration tool that shows read map coverage of a gene of interest along with a "electronic fluorescent pictopgrahic" (eFP) image. This web-tool also allows generation of new datasets if provided with SAM/BAM (with their index files) to allow visualization of any RNA-Seq mapping coverage. Gene expression levels and similarity is also shown by calculating the Reads per Kilobase per Million reads mapped (RPKM) expression levels and Pearson Correlation Coefficient (PCC) scores amongst its different splice variants.

## Getting Started

It is recommended that you use the web-version available at https://bar.utoronto.ca/eFP-Seq_Browser/ but if you want to download and run the eFP-Seq Browser locally, it is possible though it may require internet connection to reach our webservers and Araport's APIs. 

## Browser Compatibilities 

Chrome | Firefox | IE | Edge | Safari | Opera
--- | --- | --- | --- | --- | --- |
✔ |  ✔ | X |  ✔ | ? |  ✔ |

## Installation/Open

If you wish to modify the code, all .CGI files uses [Python 2](https://www.python.org) as well as there are a few [Perl](https://www.perl.org/) scripts. If you are running webservice (or webservice_gdrive) locally, you will also need to install [SAMTools](https://github.com/samtools/samtools).

Outside of that, there is nothing to install, just download all the files and open "[index.html](index.html)" ([legacy.html](legacy.html) is no longer supported).

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## License

SVG images are [CC-BY SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
For rest: [GPL-3.0](LICENSE.md)

## Authors

* Alexander Sullivan - [GitHub](https://github.com/ASully), [Twitter](https://twitter.com/alexjsully), [LinkedIn](https://www.linkedin.com/in/alexanderjsullivan/)
* Priyank Purohit - [GitHub](https://github.com/priyank-purohit)
* Asher Pasha - [Github](https://github.com/asherpasha), [ORCiD](https://orcid.org/0000-0002-9315-0520)
* Eddi Esteban - [ORCiD](https://orcid.org/0000-0001-9016-9202)
* Jamie Waese - [GitHub](https://github.com/jamiewaese), [Website](http://www.waese.com/#)
* Alison Wu
* Michelle Chen
* Chih Ying Chin
* Richard Song
* Sneha Ramesh Watharkar
* Nowlan Freese
* Agnes Chan
* Vivek Krishnakumar
* Chris Town
* Ann E. Loraine - [Website](http://lorainelab.org/)
* Nicholas J. Provart - [Github](https://github.com/BioAnalyticResource), [Twitter](https://twitter.com/BAR_PlantBio), [Website](http://bar.utoronto.ca)