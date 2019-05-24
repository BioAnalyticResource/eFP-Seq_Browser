//============================ Alexander Sullivan =============================
//
// Purpose: General functions for the eFP-Seq Browser
//
//=============================================================================
var legacy = false;

var colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();

var locus; 
if (document.getElementById("locus") != null) {
  locus = document.getElementById("locus").value;
};

var old_locus = locus;
var new_locus;

var yscale_input;
if (document.getElementById("yscale_input") != null) {
  yscale_input = document.getElementById("yscale_input").value;
};

var max_abs_scale; // What is the max value for the svg colouring in absolute mode?
if (document.getElementById("rpkm_scale_input") != null) {
  max_abs_scale = document.getElementById("rpkm_scale_input").value;
};

var locus_start = 10326918; // Gets updated when user changes gene
var locus_end = 10330048; // Gets updated when user changes gene
var splice_variants = '';
var rnaseq_calls = []; // Make a list of records and tissues we need to query....
var exp_info = []; // Keep track of the FPKM related information  TODO : rename all exp_info to fpkm_info
var rnaseq_success = 0; // Make a list of records and tissues we need to query....
var date_obj = new Date();
var rnaseq_success_start_time = date_obj.getTime(); // Keep track of start time
var rnaseq_success_current_time;
var rnaseq_success_end_time;
var max_absolute_fpkm = -1;
var max_log_fpkm = -1;
var svg_colouring_element = null; // the element for inserting the SVG colouring scale legend
var gene_structure_colouring_element = null; // the element for inserting the gene structure scale legend

//Used to create location for uploaded XML, client side
var base_src = 'cgi-bin/data/bamdata_amazon_links.xml';
var upload_src = '';
var dataset_dictionary = {
  "Araport 11 RNA-seq data": 'cgi-bin/data/bamdata_amazon_links.xml',
  "Developmental transcriptome - Klepikova et al": 'cgi-bin/data/bamdata_Developmental_transcriptome.xml'
};
let loadNewDataset = false;

//Following lines are used to count and determine how many BAM entries are in the XML file
var count_bam_entries_in_xml = 113;
/**
* Count the amount of entries in a BAM file
*/
function count_bam_num() {
  const xhr = new XMLHttpRequest();
  let url = base_src;

  xhr.responseType = 'document';
  xhr.onreadystatechange = () => {
    if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
      var response = xhr.responseXML;

      if (response != undefined && response.getElementsByTagName('file') != undefined) {
        count_bam_entries_in_xml = xhr.responseXML.getElementsByTagName("file").length;
      } else if (response === undefined || response === null) {
        console.log('failed at response');
      };

      document.getElementById("testing_count").innerHTML = count_bam_entries_in_xml;
    };
  };

  xhr.open('GET', url);
  xhr.send();
};
count_bam_num();

/**
* Changes UI of index.html (document) based on width of navigator.userAgent
*/
function checkMobile() {
  if (legacy == true) {
    if (($(window).width() < 598) || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
      //Creating mobile UI:
      document.getElementById("correctSpacing").style.display = "none";
      document.getElementById("barBoarder").style.display = "none";
      document.getElementById("uploadData").style.display = "none";
      document.getElementById("google_iden_login_button").style.display = "none";
      document.getElementById("google_iden_logout_button").style.display = "none";
      document.getElementById("generateData").style.display = "none";
      $("#publicDatabase").removeClass("col-md-6");
      $("#publicDatabase").removeClass("col-xs-3");
      document.getElementById("eFP_button").style.display = "none";
      document.getElementById("locusBrowser").className = "col-xs-6";
      document.getElementById("locus").style.width = "100%";
      document.getElementById("yscale_input").style.width = "100%";
      document.getElementById("mobileSpacing").style.display = "inline";
      document.getElementById("default_radio").className = "col-xs-6";
      document.getElementById("rpkm_scale_input").style.width = "100%";
      document.getElementById("mobileNavbar").style.display = "block";
    }
    else {
      // Restoring default UI:
      document.getElementById("correctSpacing").style.display = "block";
      document.getElementById("barBoarder").style.display = "block";
      document.getElementById("uploadData").style.display = "block";
      if (users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
        if (users_email != "") {
          document.getElementById("google_iden_login_button").style.display = 'none';
          document.getElementById("google_iden_logout_button").style.display = '';
        }
        else if (users_email == "") {
          document.getElementById("google_iden_login_button").style.display = '';
          document.getElementById("google_iden_logout_button").style.display = 'none';
        }
      }
      else if (users_email != "") {
        signOut();
        alert("Error occurred with your account, you have now been logged out. Please log back in");
      }
      document.getElementById("generateData").style.display = "block";
      document.getElementById("publicDatabase").className = "col-md-6 col-xs-3 dropdown";
      document.getElementById("eFP_button").style.display = "block";
      document.getElementById("locusBrowser").className = "col-xs-4";
      document.getElementById("locus").style.width = "175px";
      document.getElementById("yscale_input").style.width = "175px";
      document.getElementById("mobileSpacing").style.display = "none";
      document.getElementById("default_radio").className = "col-xs-4";
      document.getElementById("rpkm_scale_input").style.width = "175px";
      document.getElementById("mobileNavbar").style.display = "none";
    }
  }
};

/**
* Initialize or terminate the loading screen
* @param {boolean} terminate True = end, False = start
*/
function loadingScreen(terminate = true) {
  if (terminate === false) {
    document.getElementById("loading_screen").className = "loading";
    document.getElementById("body_of").className = "body_of_loading";
    // Disable buttons:
    let toDisableList = document.getElementsByClassName('disableOnLoading');
    for (var i = 0; i < toDisableList.length; i++) {
      $('#' + toDisableList[i].id).prop('disabled', true);
    };
  }
  else {
    document.getElementById("loading_screen").className = "loading done_loading";
    document.getElementById("body_of").className = "body_of_loading body_of_loading_done";
    // Enable buttons:
    let toDisableList = document.getElementsByClassName('disableOnLoading');
    for (var i = 0; i < toDisableList.length; i++) {
      $('#' + toDisableList[i].id).prop('disabled', false);
    };
    addGFF();
    uploadingData = false;
  }
}

// Base 64 images
var img_loading_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyCAYAAADP/dvoAAAABmJLR0QAwADAAMAanQdUAAAACXBIWXMAAA7CAAAOwgEVKEqAAAAAB3RJTUUH4AoRDzYeAMpyUgAABGJJREFUeNrt3TFoE3scwPGvjxtOzKAQMEOECBkyROhQsWOEChURBFtssdJFB9Gl4OJkwaEtRRAUdLAUqYJgwamIEFAwUoS43RCw0AwpOjhkuCHDQd5Qes9q+7A+7cP2+1na5K53cH/Kl19yIfu63W4XSZL2qL+8BJIkQyhJ0h4VfPvExMSEV0WStGt92zknQkmSE+GPFFOSpN00CToRSpJkCCVJhlCSJEMoSZIhlCTJEEqSZAglSTKEkiQZQkmSDKEkSYZQkiRDKEmSIZQkyRBKe8HDhw/5/Pnzbzn2/v3709/Hx8d/23kkGULpp01PT9NoNH7LsTudDgBJktBut0mSxAsu/Q8CL4G0fUmSEEURcRxTLpc5ePBguu3Lly9EUUQ2m6VcLm/4u0ajQRzH9PT0/PNPGARcu3aNXC6X7lMqlVheXv5u3/Xt69NjJpOht7fXBZEMobRz2u02Z8+eJY5jCoUCtVqN58+fU6lUePLkCXfu3KGnp4d6vU5vby9zc3PA2peCzs7OUiqVvjvm8ePHWVlZoVAocPr0aQYHB6nX6zSbTSqVSnqMkZGRdHp88+YNw8PDzM/PuyiSIZR2zv3798lms7x9+xZYex/x5s2bLC0tce7cOYaHhwmCgHa7zaFDh5ibm6PZbDI9Pc3Hjx/J5/MsLCxQrVa3PMfhw4d5/fo1rVaLI0eOMDk5CUC1WuXTp08EQcCxY8e4cOGCCyIZQmlnffjwgfPnz6ePBwYGuHr1KrD2UmW1WqVWq7G6upru02w2yeVy5PN5AAYHB//1HOvb1/fvdDpkMhniOGZ5eZlCoUCSJOnLqZIMobRjkiRJb3RZF4YhAFNTUywuLnLr1i2KxSKPHj36df+sQUChUODSpUt0Oh0uXrzo+4PSL+Bdo9I2nThxgsePH6d3eS4sLDAwMADA+/fvOXPmDP39/RtiWSqVaLVaRFEEwN27d7d93iiKCIKA27dv8+DBAy5fvpxuazQa1Ov1dHp89uxZuq1ardJqtVw4yYlQ2r4wDDl58mT6eGZmhuvXr/Pu3TuOHj1KJpMhDENevHgBwNjYGFeuXOHVq1eEYUg2mwUgl8sxMzPDqVOnyOfz9PX1pS97/sgkCFAul2m32zx9+pQkSajVaoyOjjI5Ocns7CxRFPHy5UuiKGJkZIT+/n6y2Szj4+OMjY1x48YNF1TaxL5ut9v9+omJiYkNPyVtLo5jkiTZ8NEJWPv4BJBG8GudTockSchkMts+39TUFKurq9y7dw+Aer3O0NAQKysrLob0A7bqmxOh9JO2itlmAfx6wvxZfX19DA0NEYYhBw4cYHFxkdHRURdC+o8MofSHqFQqLC0tUavVAJifn9/0M4mSDKG0axWLRYrFohdC+oW8a1SSZAglSTKEkiQZQkmSDKEkSYZQkiRDKEmSIZQkyRBKkmQIJUkyhJIkGUJJkgyhJEmGUJKkP9mWX8PkN9RLkpwIJUna5fZ1u92ul0GS5EQoSdIe9DfEVWhcl8IjHgAAAABJRU5ErkJggg==";

var img_gene_struct_1 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAATklEQVQ4jWNgYGANxQnC0iAggQEE0mAA lYcFgBWw4RZIQOEmYJNF0Q4zAQ4Qkqm4XQ8CIMWMw96HgsPdh4zD3oeCwx2MgDgc/vlw2JelAO7V xD0GmsY3AAAAAElFTkSuQmCC ";
var absolute_rpkm_scale = "iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQD//wD//AD/+QD/9wD/9AD/8gD/7wD/7QD/6gD/6AD/5QD/4gD/4AD/3QD/2wD/2AD/1gD/ 0wD/0QD/zgD/zAD/yQD/xgD/xAD/wQD/vwD/vAD/ugD/twD/tQD/sgD/rwD/rQD/qgD/qAD/pQD/ owD/oAD/ngD/mwD/mQD/lgD/kwD/kQD/jgD/jAD/iQD/hwD/hAD/ggD/fwD/fAD/egD/dwD/dQD/ cgD/cAD/bQD/awD/aAD/ZgD/YwD/YAD/XgD/WwD/WQD/VgD/VAD/UQD/TwD/TAD/SQD/RwD/RAD/ QgD/PwD/PQD/OgD/OAD/NQD/MwD/MAD/LQD/KwD/KAD/JgD/IwD/IQD/HgD/HAD/GQD/FgD/FAD/ EQD/DwD/DAD/CgD/BwD/BQD/AgCkIVxRAAAAs0lEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hERLGBmpbgljbBwjiiWMnFyMVLcECOhkCZBIZUzPYKSV JaDgYkxKZkxNY2SkmU8gljDCLaFdxDMmw4NrGOWTUUuItwQAG8496iMoCNwAAAAASUVORK5CYII= ";
var relative_rpkm_scale = "iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQAAAP8FBfkKCvQPD+8UFOoZGeUeHuAjI9soKNYtLdEzM8w4OMY9PcFCQrxHR7dMTLJRUa1W VqhbW6NgYJ5mZplra5NwcI51dYl6eoR/f3+EhHqJiXWOjnCTk2uZmWaenmCjo1uoqFatrVGysky3 t0e8vELBwT3GxjjMzDPR0S3W1ijb2yPg4B7l5Rnq6hTv7w/09Ar5+QX//wD/+wD/9gD/8QD/7AD/ 5wD/4gD/3QD/2AD/0wD/zQD/yAD/wwD/vgD/uQD/tAD/rwD/qgD/pQD/oAD/mgD/lQD/kAD/iwD/ hgD/gQD/fAD/dwD/cgD/bQD/ZwD/YgD/XQD/WAD/UwD/TgD/SQD/RAD/PwD/OgD/NAD/LwD/KgD/ JQD/IAD/GwD/FgD/EQD/DAD/BwBUljDTAAAA1klEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hDRLGDi5GICWMBBvCSMjIUsYY+MYUS0BApJ8wmhlzUjI EiDAYgkD0CcMwgxUtQRIpDKmZzCiBBcDgwgDlSwBBRdjUjJjahojI2qcMAhT2RJGNEuAYUasJURH PGMyPLiGTz4ZtYQESwCEoDnh8dGTkQAAAABJRU5ErkJggg==";
var exon_intron_scale = "iVBORw0KGgoAAAANSUhEUgAAALQAAAAPBAMAAAC/7vi3AAAAGFBMVEX///9QUFAAAADcFDz/jAAA AP+m3KYAfQCnICW7AAAArklEQVQ4jd3UMQ+CQAwF4OaG66ourpcO/DCGm7v17/vKBUU8SozBGBvy xo9HD6DzB3OicK4WTa7RfIGWgiiH0In6tBK/iMpKhsvyWAfB7NGlJEHQFA+6U5ZVjf2OTtfBI6YF OgIpadkaklGjZtrepIsXL63+U2s8vzHpila+0zsLEQe9ty+kQ7OuFgJ+pseY3nr5cIxtIQt6OkY/ 3lxReHMhF4nm1z+Zv6KP+/PdANuwQcLhhEyQAAAAAElFTkSuQmCC";

/**
 * Produces an intermediate HEX colour
 * @param {*} start_color
 * @param {*} end_color
 * @param {*} percent
 * @returns
 */
function generate_colour(start_color, end_color, percent) {
  // strip the leading # if it's there
  start_color = start_color.replace(/^\s*#|\s*$/g, '');
  end_color = end_color.replace(/^\s*#|\s*$/g, '');
  // convert 3 char codes to 6, e.g. `E0F` to `EE00FF`
  if (start_color.length == 3) {
    start_color = start_color.replace(/(.)/g, '$1$1');
  }
  if (end_color.length == 3) {
    end_color = end_color.replace(/(.)/g, '$1$1');
  }
  // get colors
  var start_red = parseInt(start_color.substr(0, 2), 16),
    start_green = parseInt(start_color.substr(2, 2), 16),
    start_blue = parseInt(start_color.substr(4, 2), 16);

  var end_red = parseInt(end_color.substr(0, 2), 16),
    end_green = parseInt(end_color.substr(2, 2), 16),
    end_blue = parseInt(end_color.substr(4, 2), 16);
  // calculate new color
  var diff_red = end_red - start_red;
  var diff_green = end_green - start_green;
  var diff_blue = end_blue - start_blue;
  diff_red = ((diff_red * percent) + start_red).toString(16).split('.')[0];
  diff_green = ((diff_green * percent) + start_green).toString(16).split('.')[0];
  diff_blue = ((diff_blue * percent) + start_blue).toString(16).split('.')[0];
  // ensure 2 digits by color
  if (diff_red.length == 1)
    diff_red = '0' + diff_red
  if (diff_green.length == 1)
    diff_green = '0' + diff_green
  if (diff_blue.length == 1)
    diff_blue = '0' + diff_blue
  return '#' + diff_red + diff_green + diff_blue;
};

/**
* Round the float X to DIGIT number of decimal places.
*/
function round(x, digits) {
  return parseFloat(x.toFixed(digits))
}

var colouring_part;

/**
* Find and colour a particular SVG in the DOM.
*/
function colour_part_by_id(id, part, fpkm, mode) {
  colouring_part = "all";
  for (var i = 0; i < sraList.length; i++) {
    if (id.replace("_svg", "") == sraList[i]) {
      colouring_part = sraDict[sraList[i]]["svg_part"];
    }
  }

  // Verify which type of input is added as fpkm
  let fpkmUse = fpkm
  if (Array.isArray(fpkmUse)) {
    fpkmUse = fpkmUse[variantPosition];
  }
  else {
    fpkmUse = parseFloat(fpkmUse);
  }

  //console.log('COLOUR PART BY ID\'s part = ' + part);
  // Get the user set RPKM scale
  max_abs_scale = document.getElementById("rpkm_scale_input").value;
  if ((!max_abs_scale) || max_abs_scale <= 0)
    max_abs_scale = 1000;

  var paths1 = document.getElementById(id).getElementsByTagName("path");
  var paths2 = document.getElementById(id).getElementsByTagName("g");

  var paths = Array.prototype.slice.call(paths1).concat(Array.prototype.slice.call(paths2));

  if (paths != null) {
    if (mode == "abs") { // For absolute FPKM colouring
      var r = 255;
      var g = 255 - parseInt(fpkmUse / max_abs_scale * 255);
      var b = 0;
      if (colouring_part == "all") {
        for (i = 0; i < paths.length; i++) {
          paths[i].style.fill = 'rgb(' + r + ', ' + g + ', ' + b + ')';
        }
      }
      else {
        //console.log("\n\n ********** id = " + id + " and svg_part = " + colouring_part);
        for (i = 0; i < paths.length; i++) {
          //console.log("Checking if " + paths[i].id + " == " + colouring_part + " and it is " + (paths[i].id == colouring_part));
          if (paths[i].id == colouring_part) {
            if (paths[i].tagName == "g") {
              var child_paths = paths[i].getElementsByTagName("path");
              //console.log("It was g with " + child_paths.length + " elements!!!!");
              for (ii = 0; ii < child_paths.length; ii++) {
                child_paths[ii].style.fill = 'rgb(' + r + ', ' + g + ', ' + b + ')';
              }
            }
            else {
              paths[i].style.fill = 'rgb(' + r + ', ' + g + ', ' + b + ')';
            }
          }
        }
      }
    }
    else if (mode == "rel") { // For relative FPKM colouring
      var hex = "";
      // Make the log FPKM a number between 0 and 1 to denote the 0 to +-3 scale.
      var log_scale_max = 3;
      var log_scaling = 0;
      if (fpkmUse != "Missing controls data" && Math.abs(fpkmUse) > log_scale_max)
        log_scaling = log_scale_max;
      else if (fpkmUse != "Missing controls data")
        log_scaling = Math.abs(fpkmUse);
      log_scaling /= log_scale_max;

      if (fpkmUse == "Missing controls data") {
        hex = "#D9D9D9"
      }
      else if (fpkmUse > 0) { // yellow-red
        hex = generate_colour("FFFF00", "FF0000", log_scaling);
      }
      else if (fpkmUse == 0) { // yellow
        hex = "FFFF00";
      }
      else if (fpkmUse < 0) { // yellow-blue
        hex = generate_colour("FFFF00", "0000FF", log_scaling);
      }
      //console.log('fpkm = ' + fpkm + ' -> hex = ' + hex);
      if (colouring_part == "all") {
        for (i = 0; i < paths.length; i++) {
          paths[i].style.fill = hex;
        }
      }
      else {
        //console.log("\n\n ********** id = " + id + " and svg_part = " + colouring_part);
        for (i = 0; i < paths.length; i++) {
          //console.log("Checking if " + paths[i].id + " == " + colouring_part + " and it is " + (paths[i].id == colouring_part));
          if (paths[i].id == colouring_part) {
            if (paths[i].tagName == "g") {
              var child_paths = paths[i].getElementsByTagName("path");
              //console.log("It was g with " + child_paths.length + " elements!!!!");
              for (ii = 0; ii < child_paths.length; ii++) {
                child_paths[ii].style.fill = hex;
              }
            }
            else {
              paths[i].style.fill = hex;
            }
          }
        }
      }
    }
    if (fpkmUse == "Missing controls data") {
      document.getElementById(id.replace('_svg', '_rpkm')).innerHTML = fpkmUse;
    }
    else {
      document.getElementById(id.replace('_svg', '_rpkm')).innerHTML = round(fpkmUse, 2);
    }
  } else {
    console.log("Paths is null for id = " + id);
  }
}

var current_radio = "abs";
/**
* Find and update each SVG in the DOM.
*/
function colour_svgs_now(mode) {  
  colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();
  mode = colouring_mode
  current_radio = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();
  for (var i = 0; i < count_bam_entries_in_xml; i++) {
    // For every exp, figure out the fpkm average of the controls
    var ctrl_fpkm_sum = 0;
    var ctrl_count = 0;
    var ctrl_avg_fpkm = 0;
    for (var ii = 0; ii < count_bam_entries_in_xml; ii++) {
      if (exp_info[i][2].indexOf(exp_info[ii][0].slice(0, -4)) != -1) {
        // experiment ii is a control for experiment i, save FPKM of exp ii
        ctrl_count++;
        ctrl_fpkm_sum += exp_info[ii][3];
      }
    }
    if (ctrl_count > 0)
      ctrl_avg_fpkm = ctrl_fpkm_sum / ctrl_count;

    // Save the average fpkm of controls and the log fpkm...
    var relativeRPKM = [];
    if (ctrl_count > 0) {
      for (var v = 0; v < exp_info[0][3].length; v++) {
        if (exp_info[i][3][variantPosition] == 0 && ctrl_avg_fpkm == 0) {
          // Define log2(0/0) = 0 as opposed to undefined
          relativeRPKM.push(0);
          exp_info[i].splice(4, 1, 0);
        }
        else {
          relativeRPKM.push(Math.log2(exp_info[i][3][variantPosition] / ctrl_avg_fpkm))
        }
      }      
    }
    else {
      for (var v = 0; v < exp_info[0][3].length; v++) {
        relativeRPKM.push("Missing controls data");
      }      
    }
    exp_info[i].splice(4, 1, relativeRPKM);
    exp_info[i].splice(6, 1, ctrl_avg_fpkm);

    // See if the absolute or the relative FPKM is max
    if (exp_info[i][3][variantPosition] >= max_absolute_fpkm)
      max_absolute_fpkm = exp_info[i][3][variantPosition];
    if (exp_info[i][4] != "Missing controls data" && Math.abs(exp_info[i][4]) >= max_log_fpkm && Math.abs(exp_info[i][4]) < 1000)
      max_log_fpkm = Math.abs(exp_info[i][4]);

    // Colour SVGs based on the mode requested. Pass in the correct FPKM value...
    if (colouring_mode === "rel") {
      if (!exp_info[i][4] && exp_info[i][4] != 0)
        exp_info[i][4] = -999999;
      colour_part_by_id(exp_info[i][0], exp_info[i][1], exp_info[i][4], colouring_mode); // index 5 = relative fpkm
    }
    else {
      if (!exp_info[i][3][variantPosition] && exp_info[i][3][variantPosition] != 0)
        exp_info[i][3][variantPosition] = -999999;
      colour_part_by_id(exp_info[i][0], exp_info[i][1], exp_info[i][3], colouring_mode); // index 3 = absolute fpkm
    }
  }

  $("#theTable").trigger("update");

  change_rpkm_colour_scale(colouring_mode);
}

/**
* Re-read the value from the input box
*/
function get_input_values() {
  colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();
  locus = document.getElementById("locus").value;
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
      send_null_count = 0;
    } else if (new_locus != old_locus) {
      getGFF(new_locus);
      old_locus = new_locus;
      setTimeout(function() {
        $.xhrPool.abortAll();
        variants_radio_options(status);
        send_null_count = 0;
      }, 1650);
    }
  };
}

/**
* Updates the radio button <DIV> with new variants images.
*/
function variants_radio_options(status) {
  get_input_values();
  $.ajax({
    url: 'cgi-bin/get_gene_structures.cgi?locus=' + locus, 
    dataType: 'json',
    success: function(gene_res) {
      // Update locus_start and locus_end
      locus_start = gene_res['locus_start'];
      locus_end = gene_res['locus_end'];
      splice_variants = JSON.stringify(gene_res['splice_variants']);
      populate_table(status);
      populate_efp_modal(status);

      // Remove existing variant images.
      testList = [];
      var variants_div = document.getElementById("variants_div");
      if (variants_div.firstChild != null || variants_div.firstChild != undefined || variants_div != null) {
        while (variants_div.firstChild) {
          variants_div.removeChild(variants_div.firstChild);
        }
      }      
      $('#variant_select').ddslick('destroy');
      var append_str = '<select id="variant_select">';
      for (var i = 0; i < parseInt(gene_res['variant_count']); i++) {
        // retrieve the base64 and create the element to insert
        append_str += '<option value="' + i + "\"";
        append_str += " data-imagesrc=\"data:image/png;base64," + gene_res['splice_variants'][i]['gene_structure'] + '" style="max-width:none;"></option>';
        // Append the element to the div
      }
      img_gene_struct_1 = "data:image/png;base64," + gene_res['splice_variants'][0]['gene_structure'];
      testList.push("data:image/png;base64," + gene_res['splice_variants'][0]['gene_structure']);
      var all_gene_structure_imgs = document.getElementsByClassName('gene_structure_img');
      for (var i = 0; i < all_gene_structure_imgs.length; i++) {
        all_gene_structure_imgs[i].src = "data:image/png;base64," + gene_res['splice_variants'][0]['gene_structure'];
      }
      $('input[type=radio][name=radio_group]').change(function() { // Bind an event listener..
        gene_structure_radio_on_change();
      });
      append_str += '</select></div>';
      $("#variants_div").append(append_str);
      $('#variant_select').ddslick({
        width: "100%",
        onSelected: function(selectedData){
          setData = selectedData;
          callVariantChange(selectedData);
        }
      });
      $("#theTable").trigger("update");
    },
    error: function() {
      $("tbody").empty();
      var variants_div = document.getElementById("variants_div");
      if (variants_div.firstChild != null || variants_div.firstChild != undefined || variants_div != null) {
        while (variants_div.firstChild) {
          variants_div.removeChild(variants_div.firstChild);
        }
      }  
      var append_str = "<p class=\"warning_core\" style=\"text-align:center;\"> ERROR IN get_gene_structures ! PLEASE REFRESH PAGE AND UPLOAD DATA AGAIN OR CONTACT AN ADMIN </p>"
      $("#variants_div").append(append_str);
      $('#locus_button').prop('disabled', true);
      $('#abs_scale_button').prop('disabled', true);
    }
  })
}

var variantPosition = 0;
/**
* When radio button changes, update the gene structure throughout the document and update the rpb values
*/
function gene_structure_radio_on_change() {
  // Create and update variables
  variant_selected = document.getElementsByClassName('dd-selected-value')[0].value; // Index of which variant is selected
  variantPosition = variant_selected;
  variant_img = document.getElementsByClassName('dd-selected-image')[0].src; // Image of the variant
  // Find all img tags that should be updated (all the <img> with class gene_structure)
  var all_gene_structure_imgs = document.getElementsByClassName('gene_structure_img');
  // Change their src to the newly selected variant's src
  for (var i = 0; i < all_gene_structure_imgs.length; i++) {
    all_gene_structure_imgs[i].src = variant_img;
  }
  // update all rpb and rpkm values 
  // Go through the exp_info array and make changes
  for (var i = 0; i < exp_info.length; i++) {
    // Update rpb values:
    var rpbValue = exp_info[i][5][variant_selected].toFixed(2);
    document.getElementById(exp_info[i][0].split("_svg")[0] + '_rpb').innerHTML = rpbValue;
    sraDict[exp_info[i][0].split("_svg")[0]]["rpb"] = rpbValue;
    // Update RPKM values:
    absOrRel();
  }

  $("#theTable").trigger("update");
}

/**
 * Change the values and colours of the table based on absolute or relative mode selected
 */
function absOrRel() {
  if (exp_info.length > 0) {
    for (var i = 0; i < exp_info.length; i++) {
      // Update RPKM values and colours
      if (colouring_mode == "rel") {
        if (!exp_info[i][4] && exp_info[i][4] != 0) {
          exp_info[i][4] = -999999;
        }
        var rpkmValue = exp_info[i][5][variant_selected].toFixed(2);
        document.getElementById(exp_info[i][0].split("_svg")[0] + '_rpkm').innerHTML = rpkmValue;
        sraDict[exp_info[i][0].split("_svg")[0]]["rpkm"] = rpkmValue;
        colour_part_by_id(exp_info[i][0], exp_info[i][1], exp_info[i][5], colouring_mode); // index 5 = relative fpkm
      }
      else {
        if (!exp_info[i][3] && exp_info[i][3] != 0) {
          exp_info[i][3] = -999999;
        }
        var rpkmValue = exp_info[i][3][variant_selected].toFixed(2);
        document.getElementById(exp_info[i][0].split("_svg")[0] + '_rpkm').innerHTML = rpkmValue;
        sraDict[exp_info[i][0].split("_svg")[0]]["rpkm"] = rpkmValue;
        colour_part_by_id(exp_info[i][0], exp_info[i][1], exp_info[i][3], colouring_mode); // index 3 = absolute fpkm
      }
    }
    change_rpkm_colour_scale(colouring_mode);
  }  
}

/**
* Converts numbers stored as str to int.
*/
function parseIntArray(arr) {
  for (var i = 0, len = arr.length; i < len; i++) {
    arr[i] = parseInt(arr[i], 10);
  }
  return arr;
}

var rnaseq_image_url = "cgi-bin/rnaSeqMapCoverage.cgi";
var match_drive = "";
var progress_percent = 0;
var sraList_check = [];
var rnaseq_change = 1;
var totalreadsMapped_dic = {};
var dumpOutputs = "";
var dumpMethod = "simple";
var callDumpOutputs = false;
/**
* Makes AJAX request for each RNA-Seq image based on the rnaseq_calls array that was produced by the populate_table() function
*/
function rnaseq_images(status) {
  // Verify
  changePublicData();
  // Set variables
  var awsSplit = "amazonaws.com/";
  var araportCDN = 'araport.cyverse-cdn.tacc.cloud/';
  var gDriveSplit = 'drive.google.com/drive/folders/';
  var myRegexp = /^https:\/\/drive.google.com\/drive\/folders\/(.+)/g;
  // Reset variables
  dumpOutputs = "";
  data = {};
  rnaseq_success = 1;
  match_drive = "";
  // Start
  get_input_values();
  CreateFilteredeFPList();
  if (rnaseq_calls.length === count_bam_entries_in_xml) {
    sraList_check = [];
    rnaseq_change = 1;
    for (var i = 0; i < count_bam_entries_in_xml; i++) {
      // Creates the tissue variable for the rnaSeqMapCoverage webservice
      var tissueWebservice;
      if (rnaseq_calls[i][0] == undefined || rnaseq_calls[i][0] == "None" || rnaseq_calls[i][0] == null) {
        tissueWebservice = "undefined"; // If no "tissue" variable, create an undefined one
      }
      else {
        tissueWebservice = rnaseq_calls[i][0];
      }
      // Creates the removeDrive link for the rnaSeqMapCoverage webservice 
      if (sraDict[sraList[i]]["bam_type"] === "Google Drive") {        
        // Obtains the Google drive file ID
        var linkString = sraDict[sraList[i]]["drive_link"];
        var driveLinkSplit = linkString.split('?usp=sharing');
        driveLinkSplit = driveLinkSplit[0].split(gDriveSplit);
        if (driveLinkSplit.length > 1) {
          match_drive = driveLinkSplit[1];
        }
        else {
          match_drive = linkString;
        }
      }
      else if (sraDict[sraList[i]]["bam_type"] === "Amazon AWS") {
        // Obtains the S3 
        var linkString = sraDict[sraList[i]]["drive_link"];
        var driveLinkSplit = linkString.split(awsSplit);
        if (driveLinkSplit.length === 1) {
          driveLinkSplit = linkString.split(araportCDN);
        }
        if (driveLinkSplit.length > 1) {
          match_drive = driveLinkSplit[1];
        }
        else {
          match_drive = linkString;
        }
      }
      data = {status: status, numberofreads: sraDict[sraList[i]]["numberofreads"], hexcodecolour: sraDict[sraList[i]]["hexColourCode"], remoteDrive: match_drive, bamType: sraDict[sraList[i]]["bam_type"], filename: sraDict[sraList[i]]["filenameIn"], tissue: tissueWebservice, record: rnaseq_calls[i][1], locus: locus, variant: 1, start: locus_start, end: locus_end, yscale: yscale_input, cachedDatapoints: publicData, struct: splice_variants, dumpMethod: dumpMethod};

      $.ajax({
        method: 'POST',
        url: rnaseq_image_url,
        data: data,
        dataType: 'json',
        failure: function(failure_response) {
          $('#failure').show();
        },
        success: function(response_rnaseq) {
          sraList_check.push(response_rnaseq['record']);
          sraDict[response_rnaseq['record']]["bp_length"] = (parseFloat(response_rnaseq['end']) - parseFloat(response_rnaseq['start']));
          sraDict[response_rnaseq['record']]["bp_start"] = (parseFloat(response_rnaseq['start']));
          sraDict[response_rnaseq['record']]["bp_end"] = (parseFloat(response_rnaseq['end']));
          sraDict[response_rnaseq['record']]["MappedReads"] = response_rnaseq['reads_mapped_to_locus'];
          totalreadsMapped_dic[response_rnaseq['record']] = response_rnaseq['totalReadsMapped'];
          sraDict[response_rnaseq['record']]["locusValue"] = response_rnaseq['locus'];
          if (locus != response_rnaseq['locus']) {
            console.log("ERROR: " + locus + "'s RNA-Seq API request returned with data for some other locus.");
          }
          // Update the progress bar
          if (response_rnaseq['status'] == 200) {
            rnaseq_success++;
            date_obj3 = new Date();
            rnaseq_success_current_time = date_obj3.getTime(); // Keep track of start time
            progress_percent = rnaseq_change / count_bam_entries_in_xml * 100;
            $('div#progress').width(progress_percent + '%');
            if (progress_percent >= 96) {
              loadingScreen(true);
            }
            document.getElementById('progress_tooltip').innerHTML = rnaseq_success + " / count_bam_entries_in_xml requests completed<br/>Load time <= " + String(round(parseInt(rnaseq_success_current_time - rnaseq_success_start_time) / (1000 * 60))) + " mins.";
            document.getElementById('progress').title = progress_percent.toFixed(2) + '%';
            //console.log("Requests = " + String(rnaseq_success) + ", time delta = " + String(parseInt(rnaseq_success_current_time - rnaseq_success_start_time)));
          }
          else {
            $('#failure').show();
            console.log("ERROR CODE = " + response_rnaseq['status'] + " returned for " + locus + " RNA-Seq data on " + response_rnaseq['record'] + ".");
          }

          var r = [];
          if (status == 2) { // Used to be 1
            // Finalize statistical calculations
            var ss_y = parseInt(response_rnaseq['ss_y']);
            var sum_y = parseInt(response_rnaseq['sum_y']);
            var ssy = parseInt(response_rnaseq['ss_y']);
            var sum_xy = parseIntArray(response_rnaseq['sum_xy'].replace(/\[/g, "").replace(/\]/g, "").replace(/"/g, "").split(','));
            var sum_x = parseIntArray(response_rnaseq['sum_x'].replace(/\[/g, "").replace(/\]/g, "").replace(/"/g, "").split(','));
            var sum_xx = parseIntArray(response_rnaseq['sum_xx'].replace(/\[/g, "").replace(/\]/g, "").replace(/"/g, "").split(','));
            var ss_x = parseIntArray(response_rnaseq['ss_x'].replace(/\[/g, "").replace(/\]/g, "").replace(/"/g, "").split(','));
            var ssx = parseIntArray(response_rnaseq['ss_x'].replace(/\[/g, "").replace(/\]/g, "").replace(/"/g, "").split(','));
            var n = parseInt(response_rnaseq['end']) - parseInt(response_rnaseq['start']);
            var sp = [];
            // Compute the r values for each variant
            for (var i = 0; i < sum_xy.length; i++) {
              sp.splice(i, 0, sum_xy[i] - ((sum_x[i] * sum_y) / n));
              r.splice(i, 0, sp[i] / (Math.sqrt(ssx[i] * ssy)));
            }
          }
          else {
            r = response_rnaseq['r'];
          }
          document.getElementById(response_rnaseq['record'] + '_rnaseq_img').src = 'data:image/png;base64,' + response_rnaseq['rnaseqbase64'];
          rnaseq_change += 1;
          document.getElementById(response_rnaseq['record'] + '_rpb').innerHTML = parseFloat(r[0]).toFixed(2);
          sraDict[response_rnaseq['record']]["rpb"] = parseFloat(r[0]).toFixed(2);
          document.getElementById(response_rnaseq['record'] + '_rpkm').innerHTML = response_rnaseq['absolute-fpkm'];
          sraDict[response_rnaseq['record']]["RPKM"] = response_rnaseq['absolute-fpkm'];
          document.getElementById(response_rnaseq['record'] + '_totalReadsNum').innerHTML = "Total reads = " + response_rnaseq['totalReadsMapped'];

          // Generate pre-caching information
          if (callDumpOutputs == true) {
            dumpOutputs += '\t\telif (record == "' + response_rnaseq["record"] + '"):\n';
            if (dumpMethod == "complex") {
              dumpOutputs += '\t\t\tdumpJSON(200, "' + response_rnaseq["locus"] + '", ' + response_rnaseq["variant"] + ', ' + response_rnaseq["chromosome"] + ', ' + response_rnaseq["start"] + ', ' + response_rnaseq["end"] + ', "' + response_rnaseq["record"] + '", "' + response_rnaseq["tissue"] + '", "' + response_rnaseq["rnaseqbase64"] + '", ' + response_rnaseq["reads_mapped_to_locus"] + ', ' + response_rnaseq["absolute-fpkm"] + ', [' + response_rnaseq["r"] + '], ' + response_rnaseq["totalReadsMapped"] + ', [' + response_rnaseq["exp_arr"] + '], [';
              for (r = 0; r < response_rnaseq["ReadsMappedNucleotidePosition"].length; r += 2) {
                dumpOutputs += '[' + response_rnaseq["ReadsMappedNucleotidePosition"][r] + ']';
                if (r != (response_rnaseq["ReadsMappedNucleotidePosition"].length - 2)) {
                  dumpOutputs += ", "
                };
              }
              dumpOutputs += '], {';
              for (e = 0; e < response_rnaseq["expected_expr_in_variant"].length; e++) {
                dumpOutputs += '"' + GFF_List[e].replace(locus, '') + '": ';
                dumpOutputs += '[' + response_rnaseq["expected_expr_in_variant"][e] + ']';
                if (e != response_rnaseq["expected_expr_in_variant"].length - 1) {
                  dumpOutputs += ', ';
                }
              }               
              dumpOutputs += '})\n'
            }
            else {
              dumpOutputs += '\t\t\tdumpJSON(200, "' + response_rnaseq["locus"] + '", ' + response_rnaseq["variant"] + ', ' + response_rnaseq["chromosome"] + ', ' + response_rnaseq["start"] + ', ' + response_rnaseq["end"] + ', "' + response_rnaseq["record"] + '", "' + response_rnaseq["tissue"] + '", "' + response_rnaseq["rnaseqbase64"] + '", ' + response_rnaseq["reads_mapped_to_locus"] + ', [' + response_rnaseq["absolute-fpkm"] + '], [' + response_rnaseq["r"] + '], ' + response_rnaseq["totalReadsMapped"] + ')\n';
            }
          }          

          // Save the abs-fpkm, and the stats numbers
          for (var ii = 0; ii < count_bam_entries_in_xml; ii++) {
            if (exp_info[ii][0] == response_rnaseq['record'] + '_svg') { // Find the correct element
              exp_info[ii].splice(3, 1, response_rnaseq['absolute-fpkm']);
              exp_info[ii].splice(5, 1, r);
              //console.log("Found " + response_rnaseq['record'] + " == " + exp_info[ii][0] + ".");
            }
          }

          colour_part_by_id(response_rnaseq['record'] + '_svg', 'Shapes', response_rnaseq['absolute-fpkm'][variantPosition], colouring_mode);

          if (rnaseq_success == count_bam_entries_in_xml || rnaseq_success % 10 == 0) {
            // Execute the colour_svgs_now() function
            colour_svgs_now();
            // Change the input box value to max absolute fpkm
            document.getElementById("rpkm_scale_input").value = parseInt(round(max_absolute_fpkm));
            // Execute the colour_svgs_now() function and use the new max absolute fpkm
            colour_svgs_now();
            if (rnaseq_success == count_bam_entries_in_xml) {
              date_obj4 = new Date();
              rnaseq_success_end_time = date_obj4.getTime(); // Keep track of start time
              //console.log(rnaseq_success_end_time);
              document.getElementById('progress_tooltip').innerHTML = rnaseq_success + " / count_bam_entries_in_xml requests completed<br/>Load time ~= " + String(round(parseInt(rnaseq_success_end_time - rnaseq_success_start_time) / (1000 * 60))) + " mins.";
              //console.log("**** Requests = " + String(rnaseq_success) + ", time delta = " + String(parseInt(rnaseq_success_end_time - rnaseq_success_start_time)));
            }
          }

          $("#theTable").trigger("update");
          responsiveRNAWidthResize();
          toggleResponsiveTable();
        }
      });
    }
  }
}

/**
 * Checking to make sure the subunit matches tissue
 * @param {String} svg SVG name starting with ath- and ending with .svg
 * @param {String} subunit SVG's subunit
 * @param {Bool} returnName True = return human readable name, false = return subunit
 * @return {String} subunit - The SVG tissue corrected subunit if an error occurred, input if not
 */
function checkAgainstSVG(svg, subunit, returnName = false) {
  var toReturn = subunit;
  if (svg === "ath-10dayOldSeedling.svg" || svg === "ath-10dayOldSeedling.min.svg") {
    if (returnName === true) {
      toReturn = "10 Day Old Seedling";
    }
    else if (subunit != "all" && subunit != "root" && subunit != "shoot") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-15dayOldSeedling.svg" || svg === "ath-15dayOldSeedling.min.svg") {
    if (returnName === true) {
      toReturn = "15 Day Old Seedling";
    }
    else if (subunit != "all" && subunit != "root" && subunit != "shoot") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-etiolatedSeedling.svg" || svg === "ath-etiolatedSeedling.min.svg") {
    if (returnName === true) {
      toReturn = "Etiolated Seedling";
    }
    else if (subunit != "etiolatedseedling") {
      toReturn = "etiolatedseedling";
    }
  }
  else if (svg === "ath-Flower.svg" || svg === "ath-Flower.min.svg") {
    if (returnName === true) {
      toReturn = "Flower";
    }
    else if (subunit != "flower" && subunit != "receptacle") {
      toReturn = "flower";
    }
  }
  else if (svg === "ath-FlowerParts.svg" || svg === "ath-FlowerParts.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Parts";
    }
    else if (subunit != "all" && subunit != "petals" && subunit != "stamen" && subunit != "sepals" && subunit != "carpels") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-GerminatingSeed.svg" || svg === "ath-GerminatingSeed.min.svg") {
    if (returnName === true) {
      toReturn = "Germinating Seed";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-Internode.svg" || svg === "ath-Internode.min.svg") {
    if (returnName === true) {
      toReturn = "Internode";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-leaf.svg" || svg === "ath-leaf.min.svg") {
    if (returnName === true) {
      toReturn = "Leaf";
    }
    else if (subunit != "leaf") {
      toReturn = "leaf";
    }
  }
  else if (svg === "ath-LeafParts.svg" || svg === "ath-LeafParts.min.svg") {
    if (returnName === true) {
      toReturn = "Leaf Parts";
    }
    else if (subunit != "all" && subunit != "lamina" && subunit != "petiole" && subunit != "veins") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-Pollen.svg" || svg === "ath-Pollen.min.svg") {
    if (returnName === true) {
      toReturn = "Pollen";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-RootTip.svg" || svg === "ath-RootTip.min.svg") {
    if (returnName === true) {
      toReturn = "Root Tip";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-rosettePlusRoot.svg" || svg === "ath-rosettePlusRoot.min.svg") {
    if (returnName === true) {
      toReturn = "Rosette Plus Root";
    }
    else if (subunit != "all" && subunit != "shoot" && subunit != "root") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-Seed1-4.svg" || svg === "ath-Seed1-4.min.svg") {
    if (returnName === true) {
      toReturn = "Seed 1-4";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-Seed5-7.svg" || svg === "ath-Seed5-7.min.svg") {
    if (returnName === true) {
      toReturn = "Seed 5-7";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-Seed8+.svg" || svg === "ath-Seed8+.min.svg") {
    if (returnName === true) {
      toReturn = "Seed 8+";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-SenescentLeaf.svg" || svg === "ath-SenescentLeaf.min.svg") {
    if (returnName === true) {
      toReturn = "Senescent Leaf";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-ShootApexInflorescense.svg" || svg === "ath-ShootApexInflorescense.min.svg") {
    if (returnName === true) {
      toReturn = "Shoot Apex Inflorescense";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-ShootApexVegetative-Transition.svg" || svg === "ath-ShootApexVegetative-Transition.min.svg") {
    if (returnName === true) {
      toReturn = "Shoot Apex Vegetative-Transition";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-Silique1-5.svg" || svg === "ath-Silique1-5.min.svg") {
    if (returnName === true) {
      toReturn = "Silique 1-5";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-Silique6-10.svg" || svg === "ath-Silique6-10.min.svg") {
    if (returnName === true) {
      toReturn = "Silique 6-10";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-YoungLeaf1-4.svg" || svg === "ath-YoungLeaf1-4.min.svg") {
    if (returnName === true) {
      toReturn = "Young Leaf 1-4";
    }
    else if (subunit != "all") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-EarlyBuddingFlower.svg" || svg === "ath-EarlyBuddingFlower.min.svg") {
    if (returnName === true) {
      toReturn = "Early Budding Flower";
    }
    else if (subunit != "all" && subunit != "shoot" && subunit != "buds") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-FlowerBud.svg" || svg === "ath-FlowerBud.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Bud";
    }
    else if (subunit != "flowerBud" || svg === "ath-10dayOldSeedling.min.svg") {
      toReturn = "flowerBud";
    }
  }
  else if (svg === "ath-Stamen.svg" || svg === "ath-Stamen.min.svg") {
    if (returnName === true) {
      toReturn = "Stamen";
    }
    else if (subunit != "all" && subunit != "anthers" && subunit != "filament") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-StigmaAndOvaries.svg" || svg === "ath-StigmaAndOvaries.min.svg") {
    if (returnName === true) {
      toReturn = "Stigma And Ovaries";
    }
    else if (subunit != "all" && subunit != "Stigma_tissue" && subunit != "Ovary_tissue") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-WholeSilique.svg" || svg === "ath-WholeSilique.min.svg") {
    if (returnName === true) {
      toReturn = "Whole Silique";
    }
    else if (subunit != "all" && subunit != "silique" && subunit != "seed") {
      toReturn = "silique";
    }
  }
  else if (svg === "ath-youngSeedling.svg" || svg === "ath-youngSeedling.min.svg") {
    if (returnName === true) {
      toReturn = "Young Seedling";
    }
    else if (subunit != "all" && subunit != "root" && subunit != "hypocotyl" && subunit != "cotyledon") {
      toReturn = "all";
    }
  }
  else if (svg === "ath-FlowerDevelopment1.svg" || svg === "ath-FlowerDevelopment1.min.svg") {
    if (returnName === true) {
      toReturn = "Late Flower Development (1)";
    }
    else if (subunit != "flowerDevelopmentPart1") {
      toReturn = "flowerDevelopmentPart1";
    }
  }
  else if (svg === "ath-FlowerDevelopment2.svg" || svg === "ath-FlowerDevelopment2.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Development 2";
    }
    else if (subunit != "flowerDevelopmentPart2") {
      toReturn = "flowerDevelopmentPart2";
    }
  }
  else if (svg === "ath-FlowerDevelopment3.svg" || svg === "ath-FlowerDevelopment3.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Development 3";
    }
    else if (subunit != "flowerDevelopmentPart3") {
      toReturn = "flowerDevelopmentPart3";
    }
  }
  else if (svg === "ath-FlowerDevelopment4.svg" || svg === "ath-FlowerDevelopment4.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Development 4";
    }
    else if (subunit != "flowerDevelopmentPart4") {
      toReturn = "flowerDevelopmentPart4";
    }
  }
  else if (svg === "ath-FlowerDevelopment5.svg" || svg === "ath-FlowerDevelopment5.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Development 5";
    }
    else if (subunit != "flowerDevelopmentPart5") {
      toReturn = "flowerDevelopmentPart5";
    }
  }
  else if (svg === "ath-FlowerDevelopment6-8.svg" || svg === "ath-FlowerDevelopment6-8.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Development 6-8";
    }
    else if (subunit != "flowerDevelopmentPart6") {
      toReturn = "flowerDevelopmentPart6";
    }
  }
  else if (svg === "ath-FlowerDevelopment9-11.svg" || svg === "ath-FlowerDevelopment9-11.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Development 9-11";
    }
    else if (subunit != "flowerDevelopmentPart9") {
      toReturn = "flowerDevelopmentPart9";
    }
  }
  else if (svg === "ath-FlowerDevelopment12-14.svg" || svg === "ath-FlowerDevelopment12-14.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Development 12-14";
    }
    else if (subunit != "flowerDevelopmentPart12") {
      toReturn = "flowerDevelopmentPart12";
    }
  }
  else if (svg === "ath-FlowerDevelopment15-18.svg" || svg === "ath-FlowerDevelopment15-18.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Development 15-18";
    }
    else if (subunit != "flowerDevelopmentPart15") {
      toReturn = "flowerDevelopmentPart15";
    }
  }  
  else if (svg === "ath-FlowerDevelopment19.svg" || svg === "ath-FlowerDevelopment19.min.svg") {
    if (returnName === true) {
      toReturn = "Flower Development 19";
    }
    else if (subunit != "flowerDevelopmentPart19") {
      toReturn = "flowerDevelopmentPart19";
    }
  }  
  else if (svg === "ath-Other.svg" || svg === "ath-Other.min.svg") {
    if (returnName === true) {
      toReturn = "Other";
    }
    else if (subunit != "all") {
      return "all";
    }
  }
  return toReturn;
}

var sraList = [];
var sraDict = {};
var sraCountDic = {};
var tissueSRADic = {};

var efp_table_column;
var xmlTitleName = "";
var variantdiv_str;
var iteration_num = 1;
var moreDetails = 'Show More Details <i class="material-icons detailsIcon">arrow_drop_down</i>';
var lessDetails = 'Show Less Details <i class="material-icons detailsIcon">arrow_drop_up</i>';
/**
* Gets the BAM locator XML to create + populate the table. Leeps track of all RNA-Seq calls it will have to make.
* @param {String | Number} status Index call version
*/
function populate_table(status) {
  // Reset values
  $("#theTable").empty();
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

  // Creating exon intron scale image
  var img_created = '<img src="' + 'data:image/png;base64,' + exon_intron_scale + '" alt="RNA-Seq mapped image" style="float: right; margin-right: 10px;">';
  // Insert table headers
  $("#theTable").append(
    '<thead><tr>' +
    '<th class="sortable colTitle" id="colTitle" onclick="ChangeColArrow(this.id)" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 250px;"><div class="row" id="colTitleRow"><div class="col-xs-10">Title</div><div class="col-xs-0.5"><img class="sortingArrow" id="colTitleArrow" src="./cgi-bin/SVGs/arrowDefault.min.svg"></div></div></th>' +
    '<th class="colRNA" id="colRNA" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; max-width: 576px;">RNA-Seq Coverage' +
    img_created +
    '</th>' +
    '<th class="sortable colrpb" id="colrpb" onclick="ChangeColArrow(this.id)" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;"><div class="row" id="colrpbRow"><div class="col-xs-6">r<sub>pb</sub></div><div class="col-xs-1"><img class="sortingArrow" id="colrpbArrow" src="./cgi-bin/SVGs/arrowDefault.min.svg"></div></div></th>' +
    '<th class="coleFP" id="eFP_th" class="sortable" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 100px;">eFP (RPKM)</th>' +
    '<th class="sortable colRPKM" id="colRPKM" onclick="ChangeColArrow(this.id)" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;"><div class="row" id="colRPKMRow"><div class="col-xs-7">RPKM</div><div class="col-xs-1"><img class="sortingArrow" id="colRPKMArrow" src="./cgi-bin/SVGs/arrowDefault.min.svg"></div></div></th>' +
    '<th class="sortable colDetails" id="colDetails" onclick="ChangeColArrow(this.id)" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 275px;"><div class="row" id="colDetailsRow"><div class="col-xs-10">Details</div><div class="col-xs-0.5"><img class="sortingArrow" id="colDetailsArrow" src="./cgi-bin/SVGs/arrowDefault.min.svg"></div></div></th>' +
    '</tr></thead>' +
    '<tbody id="data_table_body"></tbody>');

  $.ajax({
    url: base_src,
    dataType: 'xml',
    success: function(xml_res) {
      var $xmltitle = $(xml_res).find("files");
      $xmltitle.each(function() {
        xmlTitleName = $(this).attr('xmltitle');
        if (xmlTitleName != "" || xmlTitleName != "Uploaded dataset") {
          document.getElementById("uploaded_dataset").innerHTML = xmlTitleName;
        } else if (xmlTitleName == "" || xmlTitleName == "Uploaded dataset") {
          document.getElementById("uploaded_dataset").innerHTML = "Uploaded dataset";
        }
      });
      iteration_num = 1;
      var $title = $(xml_res).find("file");
      $title.each(function() { // Iterate over each sub-tag inside the <file> tag.
        // Extract information
        var experimentno = $(this).attr('record_number');
        if (sraList.includes(experimentno)) {
          if (sraCountDic[experimentno]) {
            sraCountDic[experimentno] += 1;
            var tempExperimentNo = experimentno + "(" + sraCountDic[experimentno] + ")";
            sraList.push(tempExperimentNo);
            sraDict[tempExperimentNo] = {};
          }
        }
        else {
          sraCountDic[experimentno] = 1;
          sraList.push(experimentno);
          sraDict[experimentno] = {};
        }

        // Title
        var title = $(this).attr('description');
        sraDict[experimentno]["title"] = title;
        // Description
        var description = $(this).attr('info');
        sraDict[experimentno]["description"] = description;
        // SVG
        var svg = $(this).attr('svgname');
        sraDict[experimentno]["svg"] = svg;
        var svg_part = $(this).attr('svg_subunit');
        svg_part = checkAgainstSVG(svg, svg_part);
        sraDict[experimentno]["svg_part"] = svg_part;
        if (tissueSRADic[checkAgainstSVG(svg, svg_part, true)]) {
          tissueSRADic[checkAgainstSVG(svg, svg_part, true)].push(experimentno);
        }
        else {
          tissueSRADic[checkAgainstSVG(svg, svg_part, true)] = [experimentno];
        }

        // SRA URL
        var url = $(this).attr('url');
        sraDict[experimentno]["url"] = url;
        // Publication URL
        var publicationid = $(this).attr('publication_link');
        sraDict[experimentno]["publicationid"] = publicationid;
        // Total number of reads
        var numberofreads = $(this).attr('total_reads_mapped');
        if (numberofreads == null || numberofreads == "") {
          numberofreads = "0";
        }
        sraDict[experimentno]["numberofreads"] = numberofreads;
        // Coloured hex code
        var hexColourCode;
        if ($(this).attr('hex_colour') == null || $(this).attr('hex_colour') == "") {
          hexColourCode = '0x64cc65';
        } else {
          hexColourCode = $(this).attr('hex_colour');
        }
        sraDict[experimentno]["hexColourCode"] = hexColourCode;
        // BAM file's filename
        var filenameIn =  ($(this).attr('filename'));
        if (filenameIn == null || filenameIn == "" || filenameIn == undefined) {
          filenameIn = "accepted_hits.bam"
        }
        sraDict[experimentno]["filenameIn"] = filenameIn;
        // Species
        var species = $(this).attr('species');    
        sraDict[experimentno]["species"] = species;
        // Control
        var controls = [];
        if ($(this).find("controls")[0].innerHTML == undefined) {
          for (i = 1; i < $(this).find("controls")[0].childNodes.length; i+2) {
            controls.push($(this).find("controls")[0].childNodes[i].firstChild.textContent);
          }
        }
        else if ($(this).find("controls")[0].innerHTML != undefined) {
          controls = $(this).find("controls")[0].innerHTML.replace(/<bam_exp>/g, "").replace(/<\/bam_exp>/g, ",").replace(/\n/g, " ").replace(/ /g, "").split(",");
        }
        sraDict[experimentno]["controls"] = controls;
        var links = "";
        if (controls.length > 0) {
          for (var i = controls.length; i--;) {
            if (controls[i] != "MEDIAN") {
              links += '<a href="https://www.ncbi.nlm.nih.gov/Traces/sra/?run=' + controls[i] + '"target="_blank" rel="noopener">' + controls[i] + '</a> ';
            } else {
              links += controls[i];
            }
          }
        }        
        sraDict[experimentno]["links"] = links;
        var controlsString = "";
        if (controls.length > 0) {
          for (var y = 0; y < controls.length; y++) {
            controlsString += controls[y].toString();
            if (y < (controls.length - 2)) {
              controlsString += ", ";
            }
          }
        }
        sraDict[experimentno]["controlsString"] = controlsString.trim();
        var name = $(this).attr('name');
        sraDict[experimentno]["name"] = name;
        if ($(this).attr('bam_type') == "Amazon AWS") {        
          var bamTissueLink = $(this).attr('name').split('/');
          var bamTissuePos = bamTissueLink.indexOf(experimentno);
          var tissue = bamTissueLink[bamTissuePos-1];
        };
        rnaseq_calls.push([tissue, experimentno]);
        sraDict[experimentno]["tissue"] = tissue;
        var bam_type = $(this).attr('bam_type');
        sraDict[experimentno]["bam_type"] = bam_type;
        var drive_link = $(this).attr('name');
        sraDict[experimentno]["drive_link"] = drive_link;
        var read_map_method = $(this).attr('read_map_method');
        sraDict[experimentno]["read_map_method"] = read_map_method;

        // Setup IGB
        var igbView_link = 'https://bioviz.org/bar.html?';
        igbView_link += 'version=A_thaliana_Jun_2009&';
        // Load custom data
        igbView_link += 'gene_id=' + locus + '&';
        igbView_link += 'feature_url_0=' + drive_link + '&'
        igbView_link += 'genome=A_thaliana_Jun_2009&';
        igbView_link += 'annotation_set=Araport11&';
        igbView_link += 'query_url=' + drive_link + '&';
        // Closing
        igbView_link += 'server_url=bar';
        
        // Construct a table row <tr> element
        var append_str = '<tr id="' + experimentno + '_row">';
        // table_dl_str is used for downloading the table as CSV
        var table_dl_str = "<table id='table_dl'>\n\t<tbody>\n";
        table_dl_str += "\t\t<caption>" + document.getElementById("xmlDatabase").value + "</caption>\n";
        // Append title <td>
        append_str += '<td class="colTitle" style="width: 250px; font-size: 12px;" id="' + experimentno + '_title">' + title + '</td>\n';
        // Append RNA-Seq and Gene Structure images (2 imgs) in one <td>
        append_str += '<td class="colRNA" style="max-width: 576px;">' + '<img id="' + experimentno + '_rnaseq_img" alt="RNA-Seq mapped image for:' + experimentno + '" style="min-width:420px; max-width:576px; width:95%; height: auto;" class="rnaseq_img responsiveRNAWidth" src="' + img_loading_base64 + '" /><br/>' + '<img id="' + experimentno + '_gene_structure_img" style="max-width: 576px; width:100%; height: auto;" class="gene_structure_img" src="' + img_gene_struct_1 + '" alt="Gene variant image for:' + experimentno + '"/>' + '</td>\n';
        // Append the rpb <td>
        append_str += '<td id="' + experimentno + '_rpb' + '" class="rpb_value colrpb" style="font-size: 12px; width: 50px; ">' + -9999 + '</td>';
        // Append the appropriate SVG with place holder sorting number in front of it .. all in one <td>
        append_str += '<td class="coleFP" tag="svg_name" style="width:  75px;">' + '<div id="' + experimentno + '_svg" name="' + svg.substring(0, svg.length - 4).slice(4) + '_tissue" tag=' + svg_part + '_subtissue" width="75" height="75" style="width: 75px; height: 75px; max-width: 75px; max-height: 75px;">' + document.getElementById(svg.substring(4).replace(".svg", "_svg")).innerHTML + '</div>' + '<div class="mdl-tooltip" for="' + experimentno + '_svg' + '">' + svg.substring(4).replace(".svg", "") + '</div></td>\n';
        // Append abs/rel RPKM
        append_str += '<td class="colRPKM" id="' + experimentno + '_rpkm' + '" style="font-size: 12px; width: 50px; ">-9999</td>';
        // Append the details <td>
        append_str += '<td class="colDetails" style="font-size: 12px;"><div id="' + experimentno + '_description" name="' + description.trim() + '">' + truncateDescription(description) + '</div>';  
        if (bam_type === "Amazon AWS") {
            append_str += '<div id="igbLink_' + experimentno + '">Show: <a href="' + igbView_link + '" target="_blank" rel="noopener">Alignments in IGB</a></div>';
        }
        append_str += '<div id="extraLinks_' + experimentno + '">Go to: <a href="' + url + '" target="_blank" rel="noopener">NCBI SRA</a> or <a href="' + publicationid + '" target="_blank" rel="noopener">PubMed</a></div>';
        append_str += '<a id="clickForMoreDetails_' + iteration_num + '" name="' + experimentno + '_description" onclick="clickDetailsTextChange(this.id)" href="javascript:(function(){$(\'#' + experimentno + '\').toggle();})()">' + moreDetails.trim() + '</a>';
        append_str += '<div id="' + experimentno + '" class="moreDetails" style="display:none">Controls: ' + links + '<br/>Species: ' + species + '<br>';
        append_str += '<div id="' + experimentno + '_totalReadsNum">' + 'Total reads = ' + numberofreads + '</div>';
        if (read_map_method != undefined && read_map_method.length > 0) {
          append_str += '<div id="' + experimentno + '_readMappedMethod">' + 'Read map method = ' + read_map_method.trim() + '</div>';
        }
        append_str += '<a id="clickForMoreDetails_' + iteration_num + '_less" name="' + experimentno + '_description" onclick="clickDetailsTextChange(this.id)" href="javascript:(function(){$(\'#' + experimentno + '\').toggle();})()">' + lessDetails + '</a></div></td>\n';
        append_str += '</tr>';

        iteration_num++;

        // Append the <tr> to the table
        $("#theTable").append(append_str);

        exp_info.push([experimentno + '_svg', svg_part, controls, 0, 0, 0, 0]);
        if (loadNewDataset === true) {
          setTimeout(function() {
            count_bam_num();
          }, 200);
          setTimeout(function() {
            rnaseq_images(status);
          }, 10);  
        } else {
          rnaseq_images(status);
        };              
      });
      // add parser through the tablesorter addParser method
      $.tablesorter.addParser({
        // set a unique id
        id: 'rpb_sorter',
        is: function(s) {
          // return false so this parser is not auto detected
          return false;
        },
        format: function(s) {
          // format your data for normalization
          if (s == NaN) {
            return -99999;
          }
          else if (s == undefined) {
            return -999999;
          }
          else if (s == Infinity) {
            return 99999;
          }
          else if (s == -Infinity) {
            return -99999;
          }
          else {
            return parseFloat(s);
          }
        },
        // set type, either numeric or text
        type: 'numeric'
      });
      $.tablesorter.addParser({
        // set a unique id
        id: 'rpkm_sorter',
        is: function(s) {
          // return false so this parser is not auto detected
          return false;
        },
        format: function(s) {
          // format your data for normalization
          if (s == NaN) {
            return -99999;
          }
          else if (s == undefined) {
            return -999999;
          }
          else if (s == Infinity) {
            return 99999;
          }
          else if (s == -Infinity) {
            return -99999;
          }
          else if (s == "Missing controls data") {
            return -9999999;
          }
          else {
            return parseFloat(s);
          }
        },
        // set type, either numeric or text
        type: 'numeric'
      });
      $('#theTable').tablesorter({
        headers: {
          0: {},
          1: {
            sorter: false // disable sorting on this column
          },
          2: {
            sorter: 'rpb_sorter'
          },
          3: {
            //sorter: false  disable sorting on this column
          },
          4: {
            sorter: 'rpkm_sorter'
          },
          5: {
            //sorter: false  disable sorting on this column
          }
        }
      });
      $("#theTable").trigger("update");
    }
  });

  var filtersConfig = {
    base_path: 'cgi-bin/core/tablefilter/',
    columns_exact_match: [false, false, false, false, false, false],
    watermark: ["Filter", "Filter", "Filter", "Filter", "Filter", "Filter"],
    highlight_keywords: false,
    no_results_message: true,
    auto_filter: true,
    auto_filter_delay: 500, //milliseconds
    col_1: 'none', // no filter option
    //col_3: 'none',  no filter option
    popup_filters: false,
    filters_row_index: 1,
    alternate_rows: false,
    msg_filter: 'Filtering...'
  };
  //var tf = new TableFilter('theTable', {base_path: 'core/tablefilter/'});
  var tf = new TableFilter('theTable', filtersConfig);
  //var tf = new TableFilter('demo', filtersConfig);
  tf.init();
  colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();
  change_rpkm_colour_scale(colouring_mode);

  // Check if arrows are the right width or not
  for (i = 0; i < colSortList.length; i++) {
    var colArrow = colSortList[i] + "Arrow";
    CheckElementWidth(colArrow, 8);
  }

  if (gene_structure_colouring_element == null) {
    gene_structure_colouring_element = document.getElementById("flt1_theTable").parentElement;
  }
  gene_structure_colouring_element.innerHTML = "";
  document.getElementsByClassName("fltrow")[0]["childNodes"][1].innerHTML = "";
  if (isPrecache == true) {
    $('#variant_select').ddslick('destroy');
    document.getElementsByClassName("fltrow")[0]["childNodes"][1].innerHTML = "";
    variantdiv_str = '<div id="variants_div">';
    variantdiv_str += '<select id="variant_select">';
    variantdiv_str += '<option value="0" data-imagesrc="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAT0lEQVQ4jWNgYGAIxQnC0iAggQEE0mAA lYcFgBWw4RZIQOEmYJNF0Q4zAQ4Qkqm4XQ8EASDFjMPeh4LD3YeMw96HgsMdjIA4HP75cNiXpQDz LMP3r8Y/VgAAAABJRU5ErkJggg==" style="max-width:none;" title="AT2G24270.1"></option>';
    variantdiv_str += '<option value="1" data-imagesrc="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAUUlEQVQ4jWNgYGAIxQnC0iAggQEE0mAA lYcFgBWw4RZIQOEmYJNF0Q4zAQ6QJRNQhFJRPBAAkmEc9j4UHO4+ZBz2PhQc7mAExOHwz4fDviwF AHwvt+HVrHUkAAAAAElFTkSuQmCC" style="max-width:none;" title="AT2G24270.2"></option>';
    variantdiv_str += '<option value="2" data-imagesrc="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAUUlEQVQ4jWNggIJQbCAsDQISwErSYACV hwWAFbDhFkhA4SZgk0XRDjMBDhCSqQFQIVY0twfAFTMOex8KDncfMg57HwoOdzAC4nD458NhX5YC AMtOmiH6inyxAAAAAElFTkSuQmCC" style="max-width:none;" title="AT2G24270.3"></option>';
    variantdiv_str += '<option value="3" data-imagesrc="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAVUlEQVQ4jWNggIJQMEhLY0AGbGkQkADm pcEAKg8LQNGMRSABhZuATRZFexqau5AkU0MDIEKsoaggAK6Ycdj7UHC4+5Bx2PtQcLiDERCHwz8f DvuyFABHFHz72l50RQAAAABJRU5ErkJggg==" style="max-width:none;" title="AT2G24270.4"></option>';
    variantdiv_str += '</select>';
    variantdiv_str += '</div>';
    document.getElementsByClassName("fltrow")[0]["childNodes"][1].innerHTML = variantdiv_str;
  }
  else if (isPrecache == false) {
    $('#variant_select').ddslick('destroy');
    document.getElementsByClassName("fltrow")[0]["childNodes"][1].innerHTML = "";
    variantdiv_str = '<div id="variants_div">';
    variantdiv_str += '</div>';
    document.getElementsByClassName("fltrow")[0]["childNodes"][1].innerHTML = variantdiv_str;
  }

  $('#variant_select').ddslick({
    width: "100%",
    onSelected: function(selectedData){
      setData = selectedData;
      callVariantChange(selectedData);
    }
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
      var innerDescription = document.getElementById(document.getElementById(details_id).name);
      innerDescription.innerHTML = innerDescription.getAttribute("name");    
    }
    else if (document.getElementById(details_id).innerHTML == lessDetails) {
      var ogID = details_id.substring(0, (details_id.length - 5));
      document.getElementById(ogID).removeAttribute("hidden");
      // Truncate the details
      var innerDescription = document.getElementById(document.getElementById(details_id).name);
      innerDescription.innerHTML = truncateDescription(innerDescription.getAttribute("name"));
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
      var newString = stringInput.substring(0, 30) + "...";
      return newString;
    }
    else {
      return stringInput;
    }
  }
}

var remainder_efp = 0;
var efp_length = 0;
var eFPSortedSRA = [];
var efp_RPKM_values = [];
/**
* Creates a table of the coloured SVGs and their corresponding RPKM values
* @param {String | Number} status Index call version
*/
function populate_efp_modal(status) {
  toggleResponsiveTable(2);
  $("#efpModalTable").empty();
  // Reset variables
  efp_table_column = '';
  eFPSortedSRA = [];

  var allSRASorted = document.getElementsByClassName("colTitle");
  for (s = 2; s < allSRASorted.length; s++) {
    var SRASortedID = allSRASorted[s].id.substr(0, allSRASorted[s].id.length - 6);
    if (document.getElementById(SRASortedID + "_row").style.display != "none") {
      eFPSortedSRA.push(SRASortedID);
    }    
  }
  
  remainder_efp = eFPSortedSRA.length % 11;
  efp_length = eFPSortedSRA.length;
  efp_RPKM_values = [];

  for (i = 0; i < eFPSortedSRA.length; i++) {
    if (isNaN(parseFloat(sraDict[eFPSortedSRA[i]]["RPKM"])) == false) {
      efp_RPKM_values.push(parseFloat(sraDict[eFPSortedSRA[i]]["RPKM"]));
    }
  }

  // Insert eFP Table header
  $("#efpModalTable").append('<p class="eFP_thead"> AGI-ID: <a href="https://www.arabidopsis.org/servlets/TairObject?type=locus&name=' + locus + '" target="_blank" rel="noopener">' + locus + '</a></p>');

  // Check radio
  if (current_radio == "abs") {
    $("#efpModalTable").append('<p class="eFP_thead"> eFP Colour Scale: <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQD//wD//AD/+QD/9wD/9AD/8gD/7wD/7QD/6gD/6AD/5QD/4gD/4AD/3QD/2wD/2AD/1gD/ 0wD/0QD/zgD/zAD/yQD/xgD/xAD/wQD/vwD/vAD/ugD/twD/tQD/sgD/rwD/rQD/qgD/qAD/pQD/ owD/oAD/ngD/mwD/mQD/lgD/kwD/kQD/jgD/jAD/iQD/hwD/hAD/ggD/fwD/fAD/egD/dwD/dQD/ cgD/cAD/bQD/awD/aAD/ZgD/YwD/YAD/XgD/WwD/WQD/VgD/VAD/UQD/TwD/TAD/SQD/RwD/RAD/ QgD/PwD/PQD/OgD/OAD/NQD/MwD/MAD/LQD/KwD/KAD/JgD/IwD/IQD/HgD/HAD/GQD/FgD/FAD/ EQD/DwD/DAD/CgD/BwD/BQD/AgCkIVxRAAAAs0lEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hERLGBmpbgljbBwjiiWMnFyMVLcECOhkCZBIZUzPYKSV JaDgYkxKZkxNY2SkmU8gljDCLaFdxDMmw4NrGOWTUUuItwQAG8496iMoCNwAAAAASUVORK5CYII=" alt="Absolute RPKM"> Min: ' + Math.min.apply(null, efp_RPKM_values).toFixed(1) + ' RPKM, Max: ' + Math.max.apply(null, efp_RPKM_values).toFixed(1) + ' RPKM</p>' + '<br><table><tbody class="eFP_tbody"></tbody>');
  } else if (current_radio == "rel") {
    $("#efpModalTable").append('<p class="eFP_thead"> eFP Colour Scale: <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQAAAP8FBfkKCvQPD+8UFOoZGeUeHuAjI9soKNYtLdEzM8w4OMY9PcFCQrxHR7dMTLJRUa1W VqhbW6NgYJ5mZplra5NwcI51dYl6eoR/f3+EhHqJiXWOjnCTk2uZmWaenmCjo1uoqFatrVGysky3 t0e8vELBwT3GxjjMzDPR0S3W1ijb2yPg4B7l5Rnq6hTv7w/09Ar5+QX//wD/+wD/9gD/8QD/7AD/ 5wD/4gD/3QD/2AD/0wD/zQD/yAD/wwD/vgD/uQD/tAD/rwD/qgD/pQD/oAD/mgD/lQD/kAD/iwD/ hgD/gQD/fAD/dwD/cgD/bQD/ZwD/YgD/XQD/WAD/UwD/TgD/SQD/RAD/PwD/OgD/NAD/LwD/KgD/ JQD/IAD/GwD/FgD/EQD/DAD/BwBUljDTAAAA1klEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hDRLGDi5GICWMBBvCSMjIUsYY+MYUS0BApJ8wmhlzUjI EiDAYgkD0CcMwgxUtQRIpDKmZzCiBBcDgwgDlSwBBRdjUjJjahojI2qcMAhT2RJGNEuAYUasJURH PGMyPLiGTz4ZtYQESwCEoDnh8dGTkQAAAABJRU5ErkJggg==" alt="Relative RPKM"> Min: ' + Math.min.apply(null, efp_RPKM_values).toFixed(1) + ', Max: ' + Math.max.apply(null, efp_RPKM_values).toFixed(1) + '</p>' + '<br><table><tbody></tbody>');
  }

  // Insert eFP Table
  $("#efpModalTable").append('<table id="eFPtable" class="table"></table>');

  // Creating eFP representative table
  for (i = 0; i < (~~ (eFPSortedSRA.length / 11) * 11); i += 11) {
    if (document.getElementById(eFPSortedSRA[i + 10]).outerHTML != 'null') {
      efp_table_column = '<tr>';
      for (r = 0; r < 11; r++) {
        efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + eFPSortedSRA[i + r] + '_rep" onclick="ScrollToRNARow(\'' + eFPSortedSRA[i + r] + '_row\')">' + document.getElementById(eFPSortedSRA[i + r] + "_svg").outerHTML + '<span class="efp_table_tooltip_text">' + eFPSortedSRA[i + r] + " - " +  sraDict[eFPSortedSRA[i + r]]["title"] + '</span></div></td>';
      }
      efp_table_column += '</tr>';
      $("#eFPtable").append(efp_table_column);
    }
  }

  for (r = 0; r < 12; r++) {
    if (remainder_efp === r) {
      efp_table_column = '<tr>';
      for (c = remainder_efp; c > 0; c--) {
        efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + eFPSortedSRA[efp_length - c] + '_rep" onclick="ScrollToRNARow(\'' + eFPSortedSRA[efp_length - c] + '\')">' + document.getElementById(eFPSortedSRA[efp_length - c] + "_svg").outerHTML + '<span class="efp_table_tooltip_text">' + eFPSortedSRA[efp_length - c] + " - " +  sraDict[eFPSortedSRA[efp_length - c]]["title"] + '</span></div></td>';
      }
      efp_table_column += '</tr>';
      $("#eFPtable").append(efp_table_column);
    }
  }

  toggleResponsiveTable();
}

/**
* Changes the legend for scales.
*/
function change_rpkm_colour_scale(colouring_mode) {
  if (svg_colouring_element == null) {
    svg_colouring_element = document.getElementById("flt3_theTable").parentElement;
  }
  svg_colouring_element.innerHTML = "";
  if (colouring_mode == "rel") {
    var img_created = document.createElement('img');
    img_created.src = 'data:image/png;base64,' + relative_rpkm_scale;
    img_created.style = 'margin-top: 10px;';
    svg_colouring_element.appendChild(img_created);
  }
  else {
    var img_created = document.createElement('img');
    img_created.src = 'data:image/png;base64,' + absolute_rpkm_scale;
    img_created.style = 'margin-top: 10px;';
    svg_colouring_element.appendChild(img_created);
  }
  // Add border to fltrow class tr's child td elements
  var columnList = ["colTitle", "colRNA", "colrpb", "coleFP", "colRPKM", "colDetails"]
  var tds = document.getElementsByClassName("fltrow")[0].getElementsByTagName("td");
  for (var i = 0; i < tds.length; i++) {
    tds[i].style = "border: 1px solid #D3D3D3";
    tds[i].classList.add(columnList[i]);
  }
}

/* Disables the absolute RPKM scale input button if the relative mode is selected. */
$("input[name=svg_colour_radio_group]:radio").change(function() {
  colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();
  absOrRel();
  if (colouring_mode == "abs") {
    $("#rpkm_scale_input").removeAttr('disabled');
  }
  else {
    $("#rpkm_scale_input").prop("disabled", true);
  }
});

function locus_validation() {
  var loc = document.getElementById("locus").value;
  if (loc.length == 9 && (loc[0] == 'A' || loc[0] == 'a') && (loc[1] == 'T' || loc[1] == 't') && ((loc[2] >= 1 && loc[2] <= 5) || loc[2] == 'C' || loc[2] == 'M' || loc[2] == 'c' || loc[2] == 'm') && (loc[3] == 'G' || loc[3] == 'g') && (loc[4] >= 0 && loc[4] <= 9) && (loc[5] >= 0 && loc[5] <= 9) && (loc[6] >= 0 && loc[6] <= 9) && (loc[7] >= 0 && loc[7] <= 9) && (loc[8] >= 0 && loc[8] <= 9)) {
    $("#locus_button").removeAttr('disabled');
  }
  else {
    $("#locus_button").prop("disabled", true);
  }
}

function yscale_validation() {
  var yscale = document.getElementById("yscale_input").value;
  if (parseInt(yscale) > 0 || yscale == "Auto" || yscale == "") {
    //$("#yscale_button").removeAttr('disabled');
    $("#locus_button").removeAttr('disabled');
  }
  else {
    //$("#yscale_button").prop("disabled", true);
    $("#locus_button").prop("disabled", true);
  }
}

function rpkm_validation() {
  var rpkmScale = parseInt(document.getElementById("rpkm_scale_input").value);
  if (rpkmScale > 0) {
    $("#abs_scale_button").removeAttr('disabled');
  }
  else {
    $("#abs_scale_button").prop("disabled", true);
  }
}

/* Used for resetting dataset_dictionary */
var base_dataset_dictionary = {
  "Araport 11 RNA-seq data": 'cgi-bin/data/bamdata_amazon_links.xml',
  "Developmental transcriptome - Klepikova et al": 'cgi-bin/data/bamdata_Developmental_transcriptome.xml'
};
var databasesAdded = false;
/**
* Resets the dataset_dictionary and removes users added tags from index.html (document)
*/
function reset_database_options() {
  $('.userAdded').remove();
  dataset_dictionary = base_dataset_dictionary; // Resets dictionary
  list_modified = false;
  databasesAdded = false;
}

var get_xml_list_output = [];
var user_exist = false;
var list_modified = false;
var check_for_change = 0;
var xml_title;
var match_title = {};
var title_list = [];
/**
* Gets list of users private XMLs
*/
function get_user_XML_display() {
  // First check to make sure there is is a user logged in or else this script will not run
  if ((users_email != "" || users_email != undefined || users_email != null) && (users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3)) {
    $.ajax({
      url: "https://bar.utoronto.ca/~asher/efp_seq_userdata/get_xml_list.php?user=" + users_email,
      dataType: 'json',
      failure: function(get_xml_list_return) {
        console.log("ERROR! Something went wrong");
      },
      success: function(get_xml_list_return) {
        // Reset all variables
        xml_title;
        match_title = {};
        title_list = [];
        // Unnamed dataset name number:
        var unnamed_title_num = 1;
        var private_version_num = 1;
        // Check if the output is working and store as variable
        get_xml_list_output = get_xml_list_return
        if (get_xml_list_output["status"] == "fail") {
          console.log("Error code: " + get_xml_list_output["error"]);
          user_exist = false;
        }
        else if (get_xml_list_output["status"] == "success") {
          user_exist = true;
          // Check for change in output from last time ran function
          if (check_for_change != get_xml_list_output["files"].length) {
            reset_database_options();
            list_modified = false;
          }
          check_for_change = get_xml_list_output["files"].length;
          // Check each file in output
          var old_data_input = "empty";
          var new_data_input = "empty";
          if (get_xml_list_output["files"].length > 0) {
            for (i = 0; i < get_xml_list_output["files"].length; i++) {
              var xml_file;
              xml_title;
              xml_title = get_xml_list_output["files"][i][1];
              // Make sure there is a title or if not, make one
              if (xml_title == "" || xml_title == "Uploaded dataset" || xml_title == undefined || xml_title == null) {
                xml_title = "Uploaded dataset - Unnamed dataset #" + unnamed_title_num;
                unnamed_title_num += 1;
              }
              else if (xml_title == "Araport 11 RNA-seq data") {
                xml_title = "Araport 11 RNA-seq data - Private version #" + private_version_num;
                private_version_num += 1;
              }
              else if (xml_title == "Developmental transcriptome - Klepikova et al") {
                xml_title = "Developmental transcriptome - Klepikova et al - Private version #" + private_version_num;
                private_version_num += 1;
              }
              title_list.push(xml_title);
              xml_fle_name = get_xml_list_output["files"][i][0]
              // This needed for later on
              match_title[xml_title] = xml_fle_name;
              // Obtain data location for each individual XML
              if (i == (get_xml_list_output["files"].length - 1)) {
                create_data_list(get_xml_list_output["files"].length)
              }
            }
          }
          setTimeout(function() {
            if (list_modified == false) {
              for (i = 0; i < get_xml_list_output["files"].length; i++) {
                // Add data to list of accessible datasets
                dataset_dictionary[title_list[i]] = datalist_Title[title_list[i]];
                // Create option to select data from user
                document.getElementById("xmlDatabase").innerHTML += '<option class="userAdded" tag="private" value="' + title_list[i] + '" id="' + title_list[i] + '">' + title_list[i] + '</option>';
              }
            };
            list_modified = true;
          }, 1000)
        }
        databasesAdded = true;
      }
    })
  }
  else if (users_email != "" && users_email != gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
    signOut();
    alert("Error occurred with your account, you have now been logged out. Please log back in");
  }
}

/**
* Creates a list of base64 strings that contains XML of user's private datasets
* @param {Number} size - How many private datasets the user has
* @return {List} datalist_Title - Dictionary of base64 strings
*/
var datalist = [];
var datalist_Title = {};
function create_data_list(size) {
  datalist = [];// Reset
  datalist_Title = {}; // Reset
  for (i = 0; i < size; i++) {
    $.ajax({
      url: "https://bar.utoronto.ca/~asher/efp_seq_userdata/get_xml.php?file=" + match_title[title_list[i]],
      dataType: 'json',
      success: function(get_xml_return) {
        xml_file = get_xml_return;
        datalist.push(xml_file["data"]);
      }
    })

    if (i === (size - 1)) {
      setTimeout(function() {
        dlCallLength = size;
        DatalistXHRCall(datalist);
      }, 200)
    }
  }  
}

var dlCallLength = 0;
var dlCallPosition = 0;
var testDoc;
/**
 * Retrieves information and titles of individual XMLs
 * @param {List} datalist The list of base64/url for the XML's being parsed through 
 */
function DatalistXHRCall(datalist) {
  if (dlCallPosition != dlCallLength) {
    const xhr = new XMLHttpRequest();
    let url = datalist[dlCallPosition];

    xhr.responseType = 'document';
    xhr.onreadystatechange = () => {
      if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
        let response = xhr.responseXML;
        let responseTitle = response.getElementsByTagName("files")[0].attributes.xmltitle.nodeValue;
        datalist_Title[responseTitle] = datalist[dlCallPosition];

        // Make function recursive
        dlCallPosition += 1;
        DatalistXHRCall(datalist);
      }
    }

    xhr.open('GET', url);
    xhr.send();
  }
}

/**
 * Checks if the user is logged in or not
 */
function check_if_Google_login() {
  if (users_email != "" && users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
    if (databasesAdded === false) {
      document.getElementById("private_dataset_header").style.display = 'block';
      get_user_XML_display();
    }
  }
  else if (users_email != "" && users_email != gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
    signOut();
    alert("Error occurred with your account, you have now been logged out. Please log back in");
  }
  else {
    remove_private_database();
  }
}

/**
* If user does not exist, adds user to our database and upload file; if does, upload file
*/
function add_user_xml_by_upload() {
  get_user_XML_display(); // Updates data and determines if user_exists or now
  // setTimeout is necessary due to xmlTitleName taking a while to be generated. Though only requires 3 seconds to obtain, setTimeout set to 4 just in case
  setTimeout(function() {
    if (user_exist == false) {
      // Creates a new user if the user does not already exist
      if (users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
        $.ajax({
          method: "POST",
          url: "https://bar.utoronto.ca/~asher/efp_seq_userdata/upload.php",
          data: {
            user: users_email,
            xml: upload_src,
            title: xmlTitleName
          }
        })
      }
      else if (users_email != "" && users_email != gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
        signOut();
        alert("Error occurred with your account, you have now been logged out. Please log back in");
      }      
    }
    else if (user_exist == true) {
      if (dataset_dictionary[xmlTitleName] == undefined) {
        // If the file does not already exist in the account, add it
        if (users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
          $.ajax({
            method: "POST",
            url: "https://bar.utoronto.ca/~asher/efp_seq_userdata/upload.php",
            data: {
              user: users_email,
              xml: upload_src,
              title: xmlTitleName
            }
          })
        }
        else if (users_email != "" && users_email != gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
          signOut();
          alert("Error occurred with your account, you have now been logged out. Please log back in");
        }     
      }
      else if (dataset_dictionary[xmlTitleName] != undefined) {        
        if (users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
          // reset variables for get_user_XML_display
          list_modified = false;
          check_for_change = 0;
          // If the file does already exist in the account, delete old and add new
          $.ajax({
            url: "https://bar.utoronto.ca/~asher/efp_seq_userdata/delete_xml.php?user=" + users_email + "&file=" + match_title[xmlTitleName]
          })
          $.ajax({
            method: "POST",
            url: "https://bar.utoronto.ca/~asher/efp_seq_userdata/upload.php",
            data: {
              user: users_email,
              xml: upload_src,
              title: xmlTitleName
            }
          })
        }
        else if (users_email != "" && users_email != gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
          signOut();
          alert("Error occurred with your account, you have now been logged out. Please log back in");
        }        
      }
    }
    get_user_XML_display(); // Update data again
  }, 10000);
}

var uploadingData = false;
/**
* UI function: If logged in, upload to account vs not
*/
function which_upload_option() {
  uploadingData = true;
  if (users_email != "" && users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
    document.getElementById("upload_modal").click();
  } 
  else if (users_email != "" && users_email != gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
    signOut();
    alert("Error occurred with your account, you have now been logged out. Please log back in");
  } 
  else if (users_email == "") {
    document.getElementById("upload_logX").click();
  }
}

/* User's private dataset_dictionary */
var public_dataset_dictionary = {
  "Araport 11 RNA-seq data": 'cgi-bin/data/bamdata_amazon_links.xml',
  "Developmental transcriptome - Klepikova et al": 'cgi-bin/data/bamdata_Developmental_transcriptome.xml'
};

var public_title_list = [];
var total_amount_of_datasets = 0;
/**
* Fills the manage XML modal with all available XMLs to delete from an account
*/
function delete_fill() {
  $("#delete_fill").empty(); // Empties the manage XML modal every time it is loaded
  $("#publicDatabaseDownload").empty();
  public_title_list = [];
  for (var public_title in public_dataset_dictionary) {
    if (public_dataset_dictionary.hasOwnProperty(public_title)) {
      public_title_list.push(public_title);
    }
  }
  var deleteBoxNum = 0;
  total_amount_of_datasets = public_title_list.length + title_list.length;
  for (i = 0; i < public_title_list.length; i++) {
    // Fills the manage XML modal with available XMLs on the account
    $("#publicDatabaseDownload").append('<input type="checkbox" tag="publicDataCheckbox" class="publicDataCheckbox" onchange="disableDeletePublic()" id="deleteBox_' + deleteBoxNum + '" value="' + public_title_list[i] + '"> ' + public_title_list[i] + '</input><br>');
    deleteBoxNum += 1;
  }
  for (i = 0; i < title_list.length; i++) {
    // Fills the manage XML modal with available XMLs on the account
    $("#delete_fill").append('<input type="checkbox" tag="privateDataCheckbox" class="privateDataCheckbox" onchange="disableDeletePublic()" id="deleteBox_' + deleteBoxNum + '" value="' + title_list[i] + '"> ' + title_list[i] + '</input><br>');
    deleteBoxNum += 1;
  }
}

var isDeletePublicDisabled = false;
/**
* Prevents users from deleting public databases visually... even without this they cannot actually do it
*/
function disableDeletePublic() {
  for (i = 0; i < public_title_list.length; i++) {
    if (document.getElementById("deleteBox_" + i).checked == true && document.getElementById("deleteBox_" + i).className == "publicDataCheckbox") {
      if (isDeletePublicDisabled == false) {
        document.getElementById("deleteXML_button").classList.add('disabled');
        isDeletePublicDisabled = true;
      }
      break
    }
    else {
      if (isDeletePublicDisabled == true) {
        document.getElementById("deleteXML_button").classList.remove('disabled');
        isDeletePublicDisabled = false;
      }
    }
  }
}

/**
 * Check if any XML's from "Manage Account" has been selected or not
 */
function CheckIfSelectedXML() {
  var returnTrue = false;
  for (i = 0; i < title_list.length; i++) {
    var deleteBox_id = "deleteBox_" + (i + 2); // Find id of what is being called
    if (document.getElementById(deleteBox_id).checked == true && users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
      returnTrue = true;
      return true;
      break;
    }
  }
  if (returnTrue === false) {
    return false;
  }
}

/**
* Delete selected XMLs from their private account
*/
function delete_selectedXML() {
  for (i = 0; i < title_list.length; i++) {
    var deleteBox_id = "deleteBox_" + (i + 2); // Find id of what is being called
    if ((document.getElementById(deleteBox_id) != null && document.getElementById(deleteBox_id).checked == true && users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3)) {
      $.ajax({
        url: "https://bar.utoronto.ca/~asher/efp_seq_userdata/delete_xml.php?user=" + users_email + "&file=" + match_title[document.getElementById(deleteBox_id).value]
      });
    }
  }
  databasesAdded = false;
}

/**
 * Confirm the action of delete all users and if so, begin deletion process
 */
function confirm_deleteUser() {
  if (users_email != "" && users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3 && $('#logoutModal').is(':visible')) {
    delete_allXMLs(gapi.auth2.getAuthInstance().currentUser.Ab.w3.Eea);
  }
}

/**
 * Delete all XMLs related to an account
 * @param {String} verify Verification code related to an account
 */
function delete_allXMLs(verify) {
  if (verify === gapi.auth2.getAuthInstance().currentUser.Ab.w3.Eea) {
    for (i = 0; i < title_list.length; i++) {
      var deleteBox_id = "deleteBox_" + (i + 2); // Find id of what is being called
      if (users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
        $.ajax({
          url: "https://bar.utoronto.ca/~asher/efp_seq_userdata/delete_xml.php?user=" + users_email + "&file=" + match_title[document.getElementById(deleteBox_id).value]
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
  if (users_email != "" && users_email === gapi.auth2.getAuthInstance().currentUser.Ab.w3.U3) {
    $.ajax({
      url: "https://bar.utoronto.ca/~asher/efp_seq_userdata/delete_user.php?user=" + users_email
    });
  }
  signOut();
}

var warningActive_index_XML = "nope";
var warningActive_index_account = "nope";
/**
 * Show warning before making permanent decision
 * @param {Number} whichWarning Which warning to be displayed? 01 for XML, 02 for accounts
 */
function showWarning_index(whichWarning) {
  if (whichWarning === 01) { // Delete single XML
    if (isDeletePublicDisabled == false) {
      if (warningActive_index_XML == "nope") {
        document.getElementById("warning_index_xml").className = "warning_index";
        warningActive_index_XML = "yes";
      } 
      else if (warningActive_index_XML == "yes") {
        hideWarning_index(whichWarning);
      }
    }
  }
  else if (whichWarning === 02) { // Delete account
    if (warningActive_index_account == "nope") {
      document.getElementById("warning_index_account").className = "warning_index";
      warningActive_index_account = "yes";
    } 
    else if (warningActive_index_account == "yes") {
      hideWarning_index(whichWarning);
    }
  }
}

/**
* Hide warning of permanent decision
 * @param {Number} whichWarning Which warning to be displayed? 01 for XML, 02 for accounts
*/
function hideWarning_index(whichWarning) {
  if (whichWarning === 01) { // Delete single XML
    document.getElementById("warning_index_xml").className = "warning_nope_index";
    warningActive_index_XML = "nope";
  }
  else if (whichWarning === 02) { // Delete account
    document.getElementById("warning_index_account").className = "warning_nope_index";
    warningActive_index_account = "nope";
  }
}

/**
* Download selected file (in document's/index.html "Manage data") as an XML
* @return {File} XML - Download selected file as an XML
*/
function manage_DownloadXML() {
  var numberOfOptions = (title_list.length + 2);
  for (i = 0; i < numberOfOptions; i++) {
    var downloadBox_id = "deleteBox_" + i; // Find id of what is being called
    if (document.getElementById(downloadBox_id).checked == true) {
      $('#downloadXML').attr('href', dataset_dictionary[document.getElementById(downloadBox_id).value]).attr('download', document.getElementById(downloadBox_id).value + '.xml');
      document.getElementById("downloadXML_button").click();
    }
  }
}

var table_base = "\t\t<tr>\n\t\t\t<th>Title*</th>\n\t\t\t<th>Description*</th>\n\t\t\t<th>Record Number *</th>\n\t\t\t<th>RNA-Seq Data/BAM file repository link*</th>\n\t\t\t<th>Repository type*</th>\n\t\t\t<th>BAM Filename*</th>\n\t\t\t<th>Publication Link</th>\n\t\t\t<th>SRA/NCBI Link</th>\n\t\t\t<th>Total Reads Mapped*</th>\n\t\t\t<th>Read Map Method</th>\n\t\t\t<th>Species*</th>\n\t\t\t<th>Tissue*</th>\n\t\t\t<th>Tissue subunit*</th>\n\t\t\t<th>Controls</th>\n\t\t\t<th>Replicate Controls</th>\n\t\t</tr>\n";
/**
* Initializes and fills a hidden table (#XMLtoCSVtable) to be filled with potentially downloadable CSV files
*/
function fill_tableCSV() {
  $("#XMLtoCSVtable").empty();
  for (i = 0; i < total_amount_of_datasets; i++) {
    var downloadBox_id = "deleteBox_" + i; // Find id of what is being called
    //console.log("Initializing fill_tableCSV() on " + downloadBox_id);
    $.ajax({
      url: dataset_dictionary[document.getElementById(downloadBox_id).value],
      dataType: 'xml',
      failure: function(xml_data) {
        console.log("Failed at opening XML for conversion into a CSV file. Please contact an admin");
      },
      success: function(xml_data) {
        var $xmltitle = $(xml_data).find("files");
        $xmltitle.each(function() {
          fileTitle = $(this).attr('xmltitle');
          if (fileTitle == "" || fileTitle == "Uploaded dataset") {
            fileTitle = "Uploaded dataset";
          }
          fileTitle = fileTitle.split(' ').join('_')
        });
        var $title = $(xml_data).find("file"); // XML title
        var table_add = "";
        table_add += "<table id='" + fileTitle + "'>\n\t<tbody>\n";
        table_add += "\t\t<caption>" + fileTitle + "</caption>\n";
        table_add += table_base; // CSV header
        $title.each(function() {
          table_add += "\t\t<tr>\n";
          // Title
          var title = $(this).attr('description'); 
          table_add += "\t\t\t<td>" + title + "</td>\n";
          // Description
          var desc = $(this).attr('info'); 
          table_add += "\t\t\t<td>" + desc + "</td>\n";
          // Record number
          var record_number = $(this).attr('record_number');
          table_add += "\t\t\t<td>" + record_number + "</td>\n";
          // BAM/repository link
          var bam_link = $(this).attr('name');
          table_add += "\t\t\t<td>" + bam_link + "</td>\n";
          // BAM/repo type
          var bam_type = $(this).attr('bam_type');
          table_add += "\t\t\t<td>" + bam_type + "</td>\n";
          // BAM/repo type
          var bam_filename = $(this).attr('filename');
          if (bam_filename === null || bam_filename === undefined || bam_filename === "undefined" || bam_filename === ".bam") {
            bam_filename = "accepted_hits.bam";
          }
          table_add += "\t\t\t<td>" + bam_filename + "</td>\n";
          // Publication link
          var publication_link = $(this).attr('publication_link');
          table_add += "\t\t\t<td>" + publication_link + "</td>\n";
          // Publication URL
          var publication_url = $(this).attr('url');
          table_add += "\t\t\t<td>" + publication_url + "</td>\n";
          // Total reads mapped
          var total_reads_mapped = $(this).attr('total_reads_mapped');
          if (total_reads_mapped == null || total_reads_mapped == "") {
            total_reads_mapped = "0";
          }
          table_add += "\t\t\t<td>" + total_reads_mapped + "</td>\n";
          // Read mapped method
          var read_map_method = $(this).attr('read_map_method');
          table_add += "\t\t\t<td>" + read_map_method + "</td>\n";
          // Species
          var species = $(this).attr('species');
          if (species == null || species == "") {
            species = "Arabidopsis thaliana";
          }
          table_add += "\t\t\t<td>" + species + "</td>\n";
          // Tissue
          var svgname = $(this).attr('svgname');
          table_add += "\t\t\t<td>" + svgname + "</td>\n";
          // Tissue subunit
          var svg_subunit = $(this).attr('svg_subunit');
          table_add += "\t\t\t<td>" + svg_subunit + "</td>\n";
          // Controls
          var controlsXMLString = "";
          if ($(this).find("controls")[0].innerHTML != undefined) {
            for (i = 1; i < $(this).find("controls")[0].childNodes.length; i = i+2) {
              if ($(this).find("controls")[0].childNodes[i].firstChild != undefined) {
                controlsXMLString += ($(this).find("controls")[0].childNodes[i].firstChild.textContent);
                if (i < ($(this).find("controls")[0].childNodes.length - 2)) {
                  controlsXMLString += ", ";
                }
              }        
            }
          }
          table_add += "\t\t\t<td>" + controlsXMLString + "</td>\n";
          // Replicate Controls
          var RcontrolsXMLString = "";
          if ($(this).find("groupwith")[0].innerHTML != undefined) {
            for (i = 1; i < $(this).find("groupwith")[0].childNodes.length; i = i+2) {
              if ($(this).find("groupwith")[0].childNodes[i].firstChild != undefined) {
                RcontrolsXMLString += ($(this).find("groupwith")[0].childNodes[i].firstChild.textContent);
                if (i < ($(this).find("groupwith")[0].childNodes.length - 2)) {
                  RcontrolsXMLString += ", ";
                }
              }
            }
          }
          table_add += "\t\t\t<td>" + RcontrolsXMLString + "</td>\n";
          // Closing
          table_add += "\t\t</tr>\n"
        })
        table_add += "\t</tbody>\n</table>";
        //console.log(table_add);
        document.getElementById("XMLtoCSVtable").innerHTML += table_add;
      }
    })
  }
}

/**
* Download selected file (in document's/index.html "Manage data") as an CSV
* @return {File} CSV - Download selected file as an CSV
*/
function download_XMLtableCSV() {
  for (i = 0; i < total_amount_of_datasets; i++) {
    var downloadBox_id = "deleteBox_" + i; // Find id of what is being called
    if (document.getElementById(downloadBox_id).checked == true) {
      var tableTitle = document.getElementById(downloadBox_id).value.split(' ').join('_');
      $("#" + tableTitle).tableToCSV();
    }
  }
}

var downloadIndexTable_base = "\t\t<tr>\n\t\t\t<th>Title</th>\n\t\t\t<th>Record Number</th>\n\t\t\t<th>Tissue</th>\n\t\t\t<th>Tissue subunit</th>\n\t\t\t<th>Locus</th>\n\t\t\t<th>bp Length</th>\n\t\t\t<th>bp Start site</th>\n\t\t\t<th>bp End site</th>\n\t\t\t<th>Total number of reads</th>\n\t\t\t<th>Reads mapped to locus</th>\n\t\t\t<th>rpb</th>\n\t\t\t<th>RPKM</th>\n\t\t\t<th>Controls</th>\n\t\t</tr>\n";
/**
* Converts and downloads index's (document) main table as an CSV
* @return {File} CSV
*/
function download_mainTableCSV() {
  populate_efp_modal(1); // Needed for the filtered_2d_x variables
  $("#hiddenDownloadModal_table").empty(); // reset
  var downloadIndexTable_str = "<table id='downloadIndexTable'>\n\t<tbody>\n";
  downloadIndexTable_str += "\t\t<caption>" + document.getElementById("xmlDatabase").value + "</caption>\n";
  downloadIndexTable_str += downloadIndexTable_base;
  // Looping through each row of the table
  for (i = 0; i < eFPSortedSRA.length; i++) {
    downloadIndexTable_str += "\t\t<tr>\n";
    downloadIndexTable_str += "\t\t\t<td>" + sraDict[eFPSortedSRA[i]]["title"] + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + eFPSortedSRA[i] + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + sraDict[eFPSortedSRA[i]]["svg"].substr(4, sraDict[eFPSortedSRA[i]]["svg"].length-8) + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + sraDict[eFPSortedSRA[i]]["svg_part"] + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + sraDict[eFPSortedSRA[i]]["locusValue"] + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[eFPSortedSRA[i]]["bp_length"]) + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[eFPSortedSRA[i]]["bp_start"]) + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[eFPSortedSRA[i]]["bp_end"]) + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + sraDict[eFPSortedSRA[i]]["numberofreads"] + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[eFPSortedSRA[i]]["MappedReads"]) + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + sraDict[eFPSortedSRA[i]]["rpb"] + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[eFPSortedSRA[i]]["RPKM"][variantPosition].toFixed(2)) + "</td>\n";
    downloadIndexTable_str += "\t\t\t<td>" + String(sraDict[eFPSortedSRA[i]]["controlsString"]) + "</td>\n";
    downloadIndexTable_str += "\t\t</tr>\n";
  }
  downloadIndexTable_str += "\t</tbody>\n</table>"; // Closing
  document.getElementById("hiddenDownloadModal_table").innerHTML += downloadIndexTable_str;
  $("#hiddenDownloadModal_table").tableToCSV();
}

var publicData = true;
/**
* Checks if the index.html's (document) "RNA-Seq Database" is currently selected on a public or private database
* @return {Boolean} forceFalse - Force a the publicData boolean to be false or have it be decided by design
*/
function changePublicData(forceFalse = false) {
  if (forceFalse || uploadingData) {
    publicData = false;
  }
  else if ((document.getElementById("xmlDatabase").selectedIndex == 1) || (document.getElementById("xmlDatabase").selectedIndex == 2)) {
    publicData = true;
  }
  else {
    publicData = false;
  }
}

var isPrecache = true;
/**
* Determines if dataset should load a preCached data or new set of information
*/
function checkPreload() {
  get_input_values();
  // Update progress bar and add loading screen
  loadingScreen(false);
  progress_percent = 0;
  document.getElementById('progress').title = '0%';
  $('div#progress').width(progress_percent + '%');
  // Check if public data or not
  if ((publicData == true) && (locus == "AT2G24270") && (dumpMethod == "simple") && (callDumpOutputs === false)) {
    populate_table(1);
    isPrecache = true;
  } else {
    update_all_images(0);
    isPrecache = false;
  };
};

var GFF_List = [];
var parse_output;
/**
* Gets the variant ID for the splice variants and adds as a title/tooltip to each splice variant image
* @param {String} locusID - The locus ID
* @return {List} GFF_list - A list of variant IDs which are used to adds as a title/tooltip to each splice variant image
*/
function getGFF(locusID) {
  GFF_List = [];
  $.ajax({
    url: 'https://bar.utoronto.ca/webservices/bar_araport/gene_structure_by_locus.php?locus=' + locusID,
    dataType: 'json',
    failure: function(gene_res) {
      console.log("Getting GFFs (getGFF) information failed to retrieve locus information from Araport11");
    },
    success: function(gene_res) {
      parse_output = gene_res;
      if (parse_output["wasSuccessful"] != false) {
        var parsed_features = parse_output['features'][0]['subfeatures'];
        for (i = 0; i < parsed_features.length; i++) {
          if (parsed_features[i]["uniqueID"] != null) {
            GFF_List.push(parsed_features[i]["uniqueID"]);
          }
          else {
            GFF_List.push("Error retrieving unique ID/GFF");
          }
        }
      }
      else if (parse_output["status"] == "fail") {
        console.log("Error: Cannot find GFF ID's with parse output. Please contact admin");
      }
      else if (parse_output["wasSuccessful"] == "false") {
        if (parse_output["error"] != null) {
          console.log("Error: Cannot find GFF ID's due to following error: " + parse_output["error"] + ". Please contact admin");
        }
        else {
          console.log("Error: Cannot find GFF ID's with parse output. Please contact admin");
        }
      }
    }
  });
}

/**
 * Adds to the GFFs to the ddSlick dropdown
 */
function addGFF() {
  eachVariant = document.getElementsByClassName("dd-option");
  if (eachVariant.length > 0) {
  for (i = 0; i < GFF_List.length; i++) {
      document.getElementsByClassName("dd-option")[i].setAttribute("title", GFF_List[i]); 
    }
  }
}

/**
* Modifies and adds a id attribute to the hidden g-signin2 on the index page
*/
function hiddenGoogleSignin() {
  var signInButtonList = document.getElementsByClassName("abcRioButtonLightBlue");
  for (i = 0; i < signInButtonList.length; i++) {
    signInButtonList[i].setAttribute("id", "loginClick" + i);
  }
}

function callVariantChange(inputData) {
  gene_structure_radio_on_change();
}

/**
* Makes all privates databases none-visible anymore
*/
function remove_private_database() {
  document.getElementById("private_dataset_header").style.display = 'none';
  var privateList = document.getElementsByClassName("userAdded");
  for (i = 0; i < privateList.length; i++) {
    $("#xmlDatabase option:last").remove();
  }
  check_for_change = 0;
}

/**
* After autocomplete, correct AGI (locusBrowser) input value
*/
function correctAGIIDInput() {
  if (document.getElementById("locus").value != "" || document.getElementById("locus").value != " " || document.getElementById("locus").value != undefined || document.getElementById("locus").value != null) {
    var locusID = document.getElementById("locus").value.split("/");
    document.getElementById("locus").value = locusID[0].toUpperCase().trim();
    locus_validation();
  }
}

/**
* Return back to top of page
*/
function returnBackToTop() {
  mainBody = document.getElementById("main_content");
  mainBody.scrollTop = 0;
}

var downloadDivNum = 1;
/**
 * Download the DIV as a image
 * @param {String} id - The string of the body's ID
 */
function downloadDiv(id) {
  html2canvas(document.getElementById(id)).then(canvas => {
    $("#appendCanvas").empty(); // reset
      canvas.id = "downloadDivNum_" + downloadDivNum;
      document.getElementById("appendCanvas").appendChild(canvas);
      document.getElementById("downloadDivNum_" + downloadDivNum).style.width = '100%';
      document.getElementById("downloadImage_button").click();
      downloadDivNum++;
  })
}

/**
* On click, hide the nav bar from main screen
*/
function displayNavBAR() {
  if ($("#navbar_menu").is(":visible") == true) {
    document.getElementById("navbar_menu").style.display = "none";
    document.getElementById("main_content").className = "col-sm-12";
    document.getElementById("openMenu").style.display = "block";
    document.getElementById("theTable").classList.add("RNATable");
    document.getElementById("mainRow").removeAttribute("style");
  }
  else if ($("#navbar_menu").is(":visible") == false) {
    document.getElementById("navbar_menu").style.display = "block";
    document.getElementById("main_content").className = "col-sm-9";
    document.getElementById("openMenu").style.display = "none";
    document.getElementById("theTable").classList.remove("RNATable");
    document.getElementById("mainRow").style.display = "inline-block";
  }
}

/**
 * Adjust the size of the navbar menu footer to fit the size of the navbar itself
 */
function adjustFooterSize() {
  var navbar = document.getElementById("navbar_menu");
  document.getElementById("nm_footer").style.width = (navbar.offsetWidth * 1.1) + "px";
  if (navbar.scrollHeight == navbar.clientHeight) {
    if (document.getElementById("nm_footer").classList.contains("navbar_menu_footer_overflow_abs") == false) {
      document.getElementById("nm_footer").classList.remove('navbar_menu_footer_overflow_sticky');
      document.getElementById("nm_footer").classList.add('navbar_menu_footer_overflow_abs');
    }
  }
  else if (navbar.scrollHeight > navbar.clientHeight) { 
    if (document.getElementById("nm_footer").classList.contains("navbar_menu_footer_overflow_sticky") == false) {
      document.getElementById("nm_footer").classList.remove('navbar_menu_footer_overflow_abs');
      document.getElementById("nm_footer").classList.add('navbar_menu_footer_overflow_sticky');
    }
  }
}

/**
 * Adjust the submission iFrame (generate data modal) based on window's height
 */
function adjustSubmissionIFrameSize() {
  var iFrameSize = window.innerHeight * 0.7;
  document.getElementById("submissioniframe").height = iFrameSize + "px";
}

var usedToggle = false;
/**
 * Toggles columns in the RNA-Seq table
 * @param {String} colClass The class that is being toggled
 * @param {Boolean} enable True = toggle on, False = toggle off
 */
function toggleTableCol(colClass, enable) {
  var column = document.getElementsByClassName(colClass);
  if (enable == true) {
    for (i = 0; i < column.length; i++) {
      column[i].removeAttribute("hidden");
    }
  }
  else if (enable == false) {    
    for (i = 0; i < column.length; i++) {
      column[i].setAttribute("hidden", true);
    }
  }
}

var responsiveRNAWidthAdjusted = false;
/**
 * Creates a responsive design for the RNA-Seq images
 */
function responsiveRNAWidthResize() {
  var responsive = document.getElementsByClassName("responsiveRNAWidth");
  if (window.innerWidth <= 575) {    
    for (i = 0; i < responsive.length; i++) {
      responsive[i].style.minWidth = (window.innerWidth * 0.93) + "px";
    }
    responsiveRNAWidthAdjusted = true;
  }
  else if (window.innerWidth > 575 && responsiveRNAWidthAdjusted == true) {
    for (i = 0; i < responsive.length; i++) {
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
 */
function toggleResponsiveTableOptions(colTitleBool, colRNABool, colrpbBool, coleFPBool, colRPKMBool, colDetailsBool) {
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
  RememberToggleOptions(colTitleBool, colRNABool, colrpbBool, coleFPBool, colRPKMBool, colDetailsBool);
}

/**
 * Creates a responsive mobile/small screen RNA-Table design *
 * @param {number} [forceToggle=0] Forces a toggled responsive design. 0 = none, 1 = mobile, 2 = desktop
 * @param {bool} [buttonClick=false] If clicked from mobile/responsive page, hide nav bar
 */
function toggleResponsiveTable(forceToggle = 0, buttonClick = false) {
  if (document.getElementById("tableToggle").style.display != 'none') {
    // Mobile design
    if ((forceToggle == 1) || (window.innerWidth <= 575 && usedToggle == false)) {
      toggleResponsiveTableOptions(false, true, false, false, false, false);
    }
    // Default
    else if ((forceToggle == 2) || (window.innerWidth >= 1100 && usedToggle == false)) {
      toggleResponsiveTableOptions(true, true, true, true, true, true);
    }
    // Toggle off same as below but also rpb values at windows resolution less than 830 pixels
    else if ((forceToggle == 3) || (window.innerWidth < 830 && usedToggle == false)) {
      toggleResponsiveTableOptions(true, true, false, false, false, false);
    }
    // Toggle off same as below but also RPKM count at windows resolution less than 900 pixels
    else if ((forceToggle == 4) || (window.innerWidth < 900 && usedToggle == false)) {
      toggleResponsiveTableOptions(true, true, true, false, false, false);
    }
    // Toggle off same as below but also eFP images at windows resolution less than 990 pixels
    else if ((forceToggle == 5) || (window.innerWidth < 990 && usedToggle == false)) {
      toggleResponsiveTableOptions(true, true, true, false, true, false);
    }
    // Toggle off details at windows resolution less than 1100 pixels
    else if ((forceToggle == 6) || (window.innerWidth < 1100 && usedToggle == false)) {
      toggleResponsiveTableOptions(true, true, true, true, true, false);
    }
  }
}

var ToggledTable = [true, true, true, true, true, true];
/**
 * Remember what toggle options were chosen in the RNA table
 * @param {boolean} [title=true] Title
 * @param {boolean} [rna=true] RNA-Seq Coverage
 * @param {boolean} [rpb=true] rpb
 * @param {boolean} [efp=true] eFP
 * @param {boolean} [rpkm=true] RPKM
 * @param {boolean} [details=true] Details
 */
function RememberToggleOptions(title = true, rna = true, rpb = true, efp = true, rpkm = true, details = true) {
  ToggledTable = [title, rna, rpb, efp, rpkm, details];
}

var colSortList = ["colTitle", "colrpb", "colRPKM", "colDetails"];
/**
 * Resize the directional arrows to more accurately fix the column size
 */
function ResizeArrowRow() {
  for (i = 0; i < colSortList.length; i++) {
    var colRow = colSortList[i] + "Row"
    document.getElementById(colRow).style.width = (document.getElementById(colRow).parentNode.offsetWidth - 2) + "px";
    var colArrow = colSortList[i] + "Arrow";
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
  var arrowDown = "./cgi-bin/SVGs/arrowSortDown.min.svg";
  var arrowUp = "./cgi-bin/SVGs/arrowSortUp.min.svg";
  setTimeout(function(){
    var arrowColID = tableArrowID + "Arrow";
    if (document.getElementById(tableArrowID).classList.contains("headerSortDown")) {
      document.getElementById(arrowColID).src = arrowDown;
    }
    else if (document.getElementById(tableArrowID).classList.contains("headerSortUp")) {
      document.getElementById(arrowColID).src = arrowUp;
    }
    for (i = 0; i < colSortList.length; i++) {
      var colArrow = colSortList[i] + "Arrow";
      CheckElementWidth(colArrow, 8);
    }
  }, 100)  
}

let cardIDList = ['aboutCardTitle', 'navbarCardTitle', 'additionalFeaturesCardTitle', 'generateDataCardTitle', 'xmlCardTitle', 'accountCardTitle', 'feedbackCardTitle'];
/**
 * Changes the help directional arrow on each card when clicked
 * @param {String} elementID The element ID for the help card's title
 */
function ChangeHelpArrowDirection(elementID) {
  for (i = 0; i < cardIDList.length; i++) {
    // If have arrow down, change to up (or down if up)
    if (elementID === cardIDList[i]) {
      let elementText = document.getElementById(elementID).innerHTML.trim();
      if (elementText.substr(-1) == "▼") {
        let replaceText = elementText.substr(0, elementText.length-1) + "▲";
        document.getElementById(elementID).innerHTML = replaceText;
      }
      else if (elementText.substr(-1) == "▲") {
        let replaceText = elementText.substr(0, elementText.length-1) + "▼";
        document.getElementById(elementID).innerHTML = replaceText;
      }
    }
    // Make all other cards have an arrow down
    else {
      let elementText = document.getElementById(cardIDList[i]).innerHTML.trim();
      let replaceText = elementText.substr(0, elementText.length-1) + "▼";
        document.getElementById(cardIDList[i]).innerHTML = replaceText;
    }
  }  
}

/**
 * Scroll to a desired RNA row 
 * @param {String} rowID The ID of the row which will be scrolled to 
 */
function ScrollToRNARow(rowID) {  
  // Close eFP Overview if open
  document.getElementById("closemodal_efPOverview").click();
  // Scroll to RNA row
  $('#main_content').animate({scrollTop: $("#" + rowID).offset().top}, 'slow');
  // Add background colour of selected row for clarity 
  document.getElementById(rowID).className += " scrollToRow";
  // Fade out colour
  setTimeout(function() {
    document.getElementById(rowID).className += " scrollToRowRemove";
  }, 1000);
  // Remove those classes
  setTimeout(function() {
    document.getElementById(rowID).classList.remove('scrollToRow');
    document.getElementById(rowID).classList.remove('scrollToRowRemove');
  }, 1600);
  
}

/**
 * Determine if a enter was pressed and if so, click a button
 * @param {Event} event The key press
 * @param {String} toClickButton Which button to click
 */
function IfPressEnter(event, toClickButton) {
  if (event.which == 13 || event.keyCode == 13) {
    $('#' + toClickButton).click();
  }
}

var BrowserDetected = false;
/**
 * Detect the browser the user is using and change the manage cookies string
 */
function DetectBrowser() {
  if (BrowserDetected === false) {
    // userAgent Browser detection object
    var userAgentParser = {
      'Microsoft+Edge': {
        'Contain': ['Edge']
      },
      'Opera': {
        'Contain': ['OPR', 'Opera']
      },
      'Firefox': {
        'Contain': ['Firefox'],
        'NContain': ['Seamonkey']
      },
      'Seamonkey': {
        'Contain': ['Seamonkey']
      },
      'Chrome': {
        'Contain': ['Chrome'],
        'NContain': ['Chromium']
      },
      'Chromium': {
        'Contain': ['Chromium']
      },
      'Internet+Explorer': {
        'Contain': ['MSIE']
      },
      'Safari': {
        'Contain': ['Safari'],
        'NContain': ['Chromium', 'Chrome']
      }
    };
    // Retrieve keys from userAgent in the instance this is modified
    var userAgentParserKeys = Object.keys(userAgentParser);
    var detectBrowser;
    var notDetectedBrowser = true;

    for (i = 0; i < userAgentParserKeys.length; i++) {
      // If contains the required keyword
      for (c = 0; c < userAgentParser[userAgentParserKeys[i]]["Contain"].length; c++) {
        if (notDetectedBrowser && navigator.userAgent.indexOf(userAgentParser[userAgentParserKeys[i]]["Contain"][c]) !== -1){
          // If detected key has a exclusion, go through those
          if (userAgentParser[userAgentParserKeys[i]]["NContain"]) {
            // If pass is the same as fail, then it contains the excluded keywords and fails the test
            var failLength = userAgentParser[userAgentParserKeys[i]]["NContain"].length;
            var passLength = 0;
            for (n = 0; n < userAgentParser[userAgentParserKeys[i]]["NContain"].length; n++) {
              // If contains exclusion word, increase pass count towards failure
              if (navigator.userAgent.indexOf(userAgentParser[userAgentParserKeys[i]]["NContain"][n]) !== -1){
                passLength++;
              }
            }
            if (passLength != failLength) {
              detectBrowser = userAgentParserKeys[i];
              notDetectedBrowser = false;
              break;
            }
          }
          else {
            detectBrowser = userAgentParserKeys[i];
            notDetectedBrowser = false;
            break;
          }
        }
      }
    }

    // Change the help string to manage cookies
    if (detectBrowser) {    
      $("#notChrome").empty();
      append_str = ' or through the following <a href="https://www.google.com/search?q=manage+cookies+in+' + detectBrowser + '" target="_blank" rel="noopener">Google search results</a>';
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
  var allTissuesDisplayed = Object.keys(tissueSRADic);
  for (i = 0; i < allTissuesDisplayed.length; i++) {
    var append_str = '<li class="form-check">';
    append_str += '<input class="form-check-input" type="checkbox" id="' + allTissuesDisplayed[i].replace(" ", "_") + '" onclick="ToggleFilteredeFP(this.id, this.checked);" style="margin: 6px 5px 0;" value="toggleeFP" checked>'
    append_str += '<p class="form-check-label" for="toggleTitle" style="padding-left: 20px; font-weight: 10;">' + allTissuesDisplayed[i] + '</p>';
    append_str += '</li>';
    $("#filtereFPList").append(append_str);
  }
}

/**
 * Toggle eFP (RPKM) rows to visible or not
 * @param {String} whichToToggle Which tissue to filter in or out
 * @param {Boolean} OnOrOff True = visible, False = filtered out
 */
function ToggleFilteredeFP(whichToToggle, OnOrOff) {
  var whichSVG = whichToToggle.replace("_", " ");
  var whichSRA = tissueSRADic[whichSVG];
  if (OnOrOff === true) {
    for (i = 0; i < whichSRA.length; i++) {
      document.getElementById(whichSRA[i] + "_row").removeAttribute("hidden");
    }    
  }  
  else if (OnOrOff === false) {
    for (i = 0; i < whichSRA.length; i++) {
      document.getElementById(whichSRA[i] + "_row").setAttribute("hidden", true);
    }    
  }
};

/**
 * Load newly generated data from the submission page
 */
function LoadSubmittedData() {
  emptyLanding();
  progress_percent = 0;
  loadingScreen(false);
  setTimeout(function() {
    count_bam_num();
  }, 200);
  update_all_images(0);
};

// Whenever browser resized, checks to see if footer class needs to be changed
$(window).resize(function() {
  adjustFooterSize();
  adjustSubmissionIFrameSize();
  responsiveRNAWidthResize();
  toggleResponsiveTable();
  setTimeout(function() {adjustFooterSize();}, 10);
})

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

  // Check if mobile
  if (legacy == true) {
    checkMobile();
    publicData = false;
  }

  // Bind event listeners...
  $('input[type=radio][name=radio_group]').change(function() {
    gene_structure_radio_on_change();
  });

  $('#locus').keyup(function() {
    locus_validation();
  });

  $('#yscale_input').keyup(function() {
    yscale_validation();
  });

  $('#rpkm_scale_input').keyup(function() {
    rpkm_validation();
  });

  setTimeout(function() {
    if (signInButton = document.getElementsByClassName("abcRioButtonLightBlue").length > 0) {
      hiddenGoogleSignin();
    }
    getGFF(locus);
  }, 700);

  $("#locus").autocomplete({
    source: function(request, response) {
  		var last = request.term.split(/,\s*/).pop();
  		$.ajax({
  			type: "GET",
  			url: "cgi-bin/idautocomplete.cgi?species=Arabidopsis_thaliana&term=" + last,
  			dataType: "json"
  			}).done(function(data) {
  			response(data);
  		});
  	},
    close: function (e, ui) {
      correctAGIIDInput();
    }
  });

  // Delay and resize the iFrame for submission page
  var subiFrame = document.getElementById("submissioniframe");
  if (subiFrame.getAttribute('data-src')) {
    subiFrame.setAttribute('src', subiFrame.getAttribute('data-src'));
  }
  adjustSubmissionIFrameSize();
}

setTimeout(function(){init()}, 100);
