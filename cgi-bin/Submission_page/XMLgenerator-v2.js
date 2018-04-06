//=============================================================================
//
// Purpose: Code required for generating new XMLs based on the data submission form
//
//=============================================================================
var count_clicks = 1;

$(function() {
  $('#GenerateButton').click(function() {
    var file_name = document.getElementById("reqxml").value.replace(/ /g, "_")
    document.getElementById("not_filled").innerHTML = "";
    var formatXML = '';
    var filledbase = updatebase(filledbase);
    correct_links(".sub_link");
    correct_ReadMapCount(".readNumberClass");
    remove_outline(".reqfield");
    remove_outline(".bam_link");
    remove_outline_tissue(".reqtissue");
    no_null_contact();
    if (document.getElementById("reqxml").value.length > 0 && document.getElementById("reqauthor").value.length > 0 && check_req(".reqfield") && check_req_tissue(".reqtissuebutton") && check_links(".channelbamtype", ".bam_link")) {
      $(".Entries").each(function(i, v) {
        formatXML += update(formatXML, v)
        $('#ResultXml').val(filledbase + formatXML + existingXML + end);
        $('#DownloadLink').attr('href', 'data:text/xml;base64,' + btoa(filledbase + formatXML + existingXML + end)).attr('download', file_name + '.xml');
        $('#generated').show();
      });
    }
    else {
      if (check_req(".reqfield") == false) {
        outline_req(".reqfield");
      }
      if (check_req_tissue(".reqtissuebutton") == false) {
        outline_req_tissue(".reqtissuebutton");
      }
      document.getElementById("not_filled").innerHTML += "Please fill in all red highlighted fields. ";
      if (check_links(".channelbamtype", ".bam_link") == false) {
        outline_links(".channelbamtype", ".bam_link");
        document.getElementById("not_filled").innerHTML += "<br> Please only use proper and valid links only. BAM Repository Links can only contain Google Drive URLs and/or Amazon AWS URLs. ";
      }
    }
  });
});

var end = ['\t</files>'].join('\r\n');

var base = ['<?xml version="1.0" encoding="UTF-8"?>', '\t<files xmltitle=\"<?channelxmltitle?>\" author=\"<?channelauthor?>\" contact=\"<?channelcontact?>\">', '\n'].join('\r\n');

var template = [
  '\t\t<file info=\"<?channeldescription?>\" record_number=\"<?channelrecordnumber?>\"  foreground=\"<?channelforeground?>\" hex_colour=\"<?channelhexcolor?>\" bam_type=\"<?channelbamtype?>\" name=\"<?channelbamlink?>\" total_reads_mapped=\"<?channeltotalreadsmapped?>\" read_map_method=\"<?channelreadmapmethod?>\" publication_link=\"<?channelpublicationlink?>\" svg_subunit=\"<?channeltissue?>\" svgname="<?channelsvgname?>\" description=\"<?channeltitle?>\" url=\"<?channelpublicationurl?>\" species=\"<?channelspecies?>\" title=\"<?channeligbtitle?>\">',
  '\t\t\t<controls>',
  '\t\t\t\t<bam_exp><?channelcontrols?></bam_exp>',
  '\t\t\t</controls>',
  '\t\t\t<groupwith>',
  '\t\t\t\t<bam_exp><?channelgroupwidtho?></bam_exp>',
  '\t\t\t</groupwith>',
  '\t\t</file>',
  '\n'
].join('\r\n');

var topXML = ['\t\t<file info=\"<?channeldescription?>\" record_number=\"<?channelrecordnumber?>\" foreground=\"<?channelforeground?>\" hex_colour=\"<?channelhexcolor?>\" bam_type=\"<?channelbamtype?>\" name=\"<?channelbamlink?>\" total_reads_mapped=\"<?channeltotalreadsmapped?>\" read_map_method=\"<?channelreadmapmethod?>\" publication_link=\"<?channelpublicationlink?>\" svg_subunit=\"<?channeltissue?>\" svgname="<?channelsvgname?>\" description=\"<?channeltitle?>\" url=\"<?channelpublicationurl?>\" species=\"<?channelspecies?>\" title=\"<?channeligbtitle?>\">', '\t\t\t<controls>\n'].join('\r\n');

var controlsXML = [].join('\r\n');

var replicatesXML = ['\t\t\t</controls>', '\t\t\t<groupwith>\n'].join('\r\n');

var endingXML = ['\t\t\t</groupwith>', '\t\t</file>', '\n'].join('\r\n');

var existingXML = [].join('\r\n');

var all_controls = "";
var all_replicates = "";

/**
* Update potentially generated XML will form filled strings
* @param {String} formatXML - The file/XML body portion of the XML that will be filled
* @param {Any} v - Document's (Submission_page.html) filled form area
* @return {String} fillXML - The filled XML
*/
function update(formatXML, v) {
  controlsXML = [].join('\r\n');
  all_controls = $(v).find('.channelcontrols').val().split(',');
  for (i = 0; i < all_controls.length; i++) {
    all_controls[i] = all_controls[i].trim()
    controlsXML += "\t\t\t\t<bam_exp>" + all_controls[i] + "</bam_exp>\n";
  };

  replicatesXML = ['\t\t\t</controls>', '\t\t\t<groupwith>\n'].join('\r\n');
  all_replicates = $(v).find('.channelgroupwidtho').val().split(',');
  for (i = 0; i < all_replicates.length; i++) {
    all_replicates[i] = all_replicates[i].trim()
    replicatesXML += "\t\t\t\t<bam_exp>" + all_replicates[i] + "</bam_exp>\n";
  };

  var variables = {
    'channeldescription': $(v).find('.channeldescription').val(),
    'channelrecordnumber': $(v).find('.channelrecordnumber').val(),
    'channelhexcolor': $(v).find('.channelhexcolor').val(),
    'channelbamtype': $(v).find('.channelbamtype').val(),
    'channelbamlink': $(v).find('.channelbamlink').val(),
    'channeltotalreadsmapped': $(v).find('.channeltotalreadsmapped').val(),
    'channelreadmapmethod': $(v).find('.channelreadmapmethod').val(),
    'channelpublicationlink': $(v).find('.channelpublicationlink').val(),
    'channeltissue': $(v).find('.channeltissue').val(),
    'channelsvgname': $(v).find('.channelsvgname').val(),
    'channeltitle': $(v).find('.channeltitle').val(),
    'channelpublicationurl': $(v).find('.channelpublicationurl').val(),
    'channelspecies': $(v).find('.channelspecies').val(),
    'channelcontrols': $(v).find('.channelcontrols').val(),
    'channelgroupwidtho': $(v).find('.channelgroupwidtho').val(),
    'channelforeground': $(v).find('.channelforeground').val(),
    'channeligbtitle': document.getElementById("reqxml").value + "/" + $(v).find('.channelrecordnumber').val()
  };

  var fillXML = topXML.replace(/<\?(\w+)\?>/g, function(match, name) {
    return variables[name];
  });

  fillXML += controlsXML;
  fillXML += replicatesXML;
  fillXML += endingXML;

  return fillXML;

}

/**
* An updated top portion of the XML
* @param {Any} filledbase - The variable that will be replaced with the filled top XML
* @return {String} fillbase - The filled top portion of the XML
*/
function updatebase(filledbase) {
  var variables = {
    'channelxmltitle': document.getElementById("reqxml").value,
    'channelauthor': document.getElementById("reqauthor").value,
    'channelcontact': document.getElementById("contectinfo").value
  };

  var fillbase = base.replace(/<\?(\w+)\?>/g, function(match, name) {
    return variables[name];
  });

  return fillbase;

}

// Whenever #CloneForm button is clicked, a cloned (and emptied) section will be created
$(function() {
  $("#CloneForm").click(CloneSection);
});

var tissue_sub_name = "";
var new_tissue = "";
var new_tissue_subunit = "";
var new_svg = "";
var new_hexID = "";
/**
* Creates an empty clone of the submission form
*/
function CloneSection() {
  var cacheQuery = document.getElementsByClassName("tissueInput")[document.getElementsByClassName("tissueInput").length - 1].value;
  document.getElementsByClassName("tissueInput")[document.getElementsByClassName("tissueInput").length - 1].value = "";
  updateTable(document.getElementsByClassName("tissueInput")[document.getElementsByClassName("tissueInput").length - 1].id);
  $(".SubmissionArea").append($(".Entries:first").clone(true));
  document.getElementsByClassName("tissueInput")[document.getElementsByClassName("tissueInput").length - 2].value = cacheQuery;
  count_clicks += 1;
  new_tissue = "tissue" + count_clicks;
  new_tissue_subunit = "tissue" + count_clicks + "_subunit";
  new_svg = "svg" + count_clicks;
  new_hexID = "hexID_num" + count_clicks;
  new_foregroundID = "foregroundID_num" + count_clicks;
  new_foregroundID = "igbtitle_num" + count_clicks;
  tissueInput = "tissueInput" + count_clicks;
  $("legend:last").text("Entry " + count_clicks);
  $(".change_div_id").last().attr("name", new_tissue);
  $(".change_button_id").last().attr("id", new_tissue);
  $(".change_id_tissue_subunit").last().attr("name", new_tissue_subunit);
  $(".change_id_tissue_subunit").last().attr("id", new_tissue_subunit);
  $(".change_id_tissue").last().attr("id", new_tissue);
  $(".change_svg").last().attr("id", new_svg);
  $(".change_hexcolor").last().attr("id", new_hexID);
  $(".tissueInput").last().attr("id", tissueInput);
  $(".tissue_table").last().attr("id", "tissueTable_" + tissueInput);
  // resetting form values and emptying new form
  resetLastEntryValues();
};

/**
* Resets the values of the last form entry
*/
function resetLastEntryValues() {
  $("input[id=reqtitle]").last().val("");
  $("textarea[id=reqdesc]").last().val("");
  $("input[id=rec]").last().val("");
  $("input[id=bam_input]").last().val("");
  $("input[id=publink]").last().val("");
  $("input[id=sralink]").last().val("");
  $("input[id=reqread]").last().val("");
  $("input[id=readmapmethod]").last().val("");
  $("button[id=" + new_tissue + "]").html("Tissue select");
  $("input[id=" + new_tissue_subunit + "]").last().val("");
  $("input[id=" + new_hexID + "]").last().val("");
  $("input[id=controls]").last().val("");
  $("input[id=replicate_controls1]").last().val("");
  $("input[id=" + new_svg + "]").last().html("");
}

/**
* Deletes the last entry in the form
*/
function DeleteSection() {
  if ($("div[id=entries]").length > 1) {
    $("div[id=entries]").last().remove();
    count_clicks -= 1;
  }
}

/**
* Resets the entire form
*/
function resetForm() {
  count_clicks = 0;
  CloneSection();
  while ($("div[id=entries]").length != 1) {
    $("div[id=entries]").first().remove();
  }
  resetLastEntryValues();
  hideWarning();

  // Empty all in "Add from existing" whenever called to refresh data
  $("#araport11XML").empty();
  $("#klepikovaXML").empty();
  display_add_button(false);
}

/**
* Parses through links and corrects weblink formatting to match what we require
* @param {String} class_name - The HTML <class=""> that is being parsed through
*/
function correct_links(class_name) {
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  var gDriveChecking = "?usp=sharing";
  for (i = 0; i < x.length; i++) {
    if (x[i].value.length > 0) {
      x[i].value = x[i].value.trim();
      if ((x[i].value.substring(0, 7) == "http://" || x[i].value.substring(0, 8) == "https://") == false) {
        x[i].value = "https://" + x[i].value;
      }
      if (x[i].id == "bam_input") {
        if ((x[i].value.substr(x[i].value.length - gDriveChecking.length)) == gDriveChecking) {
          x[i].value = x[i].value.split(gDriveChecking)[0];
        }
      }
    }
  }
}

var read_num = "";
/**
* Parses through links and corrects number formatting to match what we require
* @param {String} class_name - The HTML <class=""> that is being parsed through
*/
function correct_ReadMapCount(class_name) {
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  var u;
  for (i = 0; i < x.length; i++) {
    if (x[i].value.length > 0) {
      x[i].value = x[i].value.trim();
      x[i].value = only_ReadNum(x[i].value);
    }
  }
}

/**
* Makes sure a number is an integer
* @param {Number} input_string - Float
* @return {Number} input_string - Integer
*/
function only_ReadNum(input_string) {
  var u;
  read_num = "";
  for (u = 0; u < input_string.length; u++) {
    if (isNaN(input_string[u]) == false) {
      read_num += input_string[u];
    }
  }
  input_string = read_num;
  input_string = Math.round(input_string);
  return input_string;
}

/**
* Make sure links are only either Amazon AWS or Google Drive
* @param {String} bam_name - BAM file type HTML <class=""> location
* @param {String} repo_name - The repo's link HTML <class=""> location
* @return {bool} bool - Valid link or not
*/
function check_links(bam_name, repo_name) {
  var repo_match = document.getElementById("Entries_all").querySelectorAll(repo_name).length;
  var x = document.getElementById("Entries_all").querySelectorAll(repo_name);
  var bam_x = document.getElementById("Entries_all").querySelectorAll(bam_name);
  var i;
  for (i = 0; i < x.length; i++) {
    if (x[i].id = "bam_input") {
      if (x[i].value.length > 0) {
        if (bam_x[i].value == "Google Drive") {
          if ((x[i].value.includes("drive.google.com/drive/folders/")) == true) {
            return true;
          }
          else if ((x[i].value.includes("drive.google.com/drive/folders/")) == false) {
            return false;
          }
          else {
            return false;
          }
        }
        else if (bam_x[i].value == "Amazon AWS") {
          if ((x[i].value.includes("amazonaws.com/") && (check_amazon_for_bam(x[i].value) == true)) == true) {
            return true;
          }
          else if ((x[i].value.includes("amazonaws.com/") && (check_amazon_for_bam(x[i].value) == true)) == false) {
            return false;
          }
          else {
            return false;
          }
        }
        else {
          return false;
        }
      }
      else {
        return false;
      }
    }
  }
}

/**
* Check if tagged entries meet the desired requirements or not
* @param {String} class_name - Entries' HTML <class="">
* @return {bool} bool - Meet requirements or not
*/
function check_req(class_name) {
  var filled = 0;
  var match = document.getElementById("Entries_all").querySelectorAll(class_name).length;
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  for (i = 0; i < x.length; i++) {
    if (x[i].value.length > 0) {
      x[i].value = x[i].value.trim();
      filled += 1;
    }
  }
  if (filled == match) {
    return true
  }
  else {
    return false
  }
};

/**
* Check if tagged tissue entries meet the desired requirements or not
* @param {String} class_name - Entries' HTML <class="">
* @return {bool} bool - Meet requirements or not
*/
function check_req_tissue(class_name) {
  var match = document.getElementById("Entries_all").querySelectorAll(class_name).length;
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  var sub_filled = 0
  for (i = 1; i <= count_clicks; i++) {
    var tissue_sub_parse = "tissue" + i + "_subunit";
    if (document.getElementById(tissue_sub_parse).value.length > 0) {
      sub_filled += 1
    }
  }
  if (sub_filled == count_clicks) {
    return true
  }
  else {
    return false
  }
};

/**
* Outline all unfilled required fields
* @param {String} class_name - Entries' HTML <class="">
*/
function outline_req(class_name) {
  var filled = 0;
  var match = document.getElementById("Entries_all").querySelectorAll(class_name).length;
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  for (i = 0; i < x.length; i++) {
    if (x[i].value.length <= 0) {
      x[i].style.borderColor = "#ff2626";
      x[i].style.boxShadow = "0 0 10px #ff2626";
    }
  }
};

/**
* Outline all unfilled required tissue fields
* @param {String} class_name - Entries' HTML <class="">
*/
function outline_req_tissue(class_name) {
  var match = document.getElementById("Entries_all").querySelectorAll(class_name).length;
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  for (i = 0; i < x.length; i++) {
    var tissue_sub_parse = "tissue" + (i + 1) + "_subunit";
    if (document.getElementById(tissue_sub_parse).value.length <= 0) {
      x[i].style.borderColor = "#ff2626";
      x[i].style.boxShadow = "0 0 10px #ff2626";
    }
  }
};

/**
* Outline all unfilled required link fields
* @param {String} class_name - Entries' HTML <class="">
*/
function outline_links(bam_name, repo_name) {
  var repo_match = document.getElementById("Entries_all").querySelectorAll(repo_name).length;
  var x = document.getElementById("Entries_all").querySelectorAll(repo_name);
  var bam_x = document.getElementById("Entries_all").querySelectorAll(bam_name);
  var i;
  for (i = 0; i < repo_match; i++) {
    if (x[i].id = "bam_input") {
      if (x[i].value.length > 0) {
        if (bam_x[i].value == "Google Drive") {
          if ((x[i].value.includes("drive.google.com/drive/folders/")) == true) {
            x[i].style.borderColor = null;
            x[i].style.boxShadow = null;
          }
          else if ((x[i].value.includes("drive.google.com/drive/folders/")) == false) {
            x[i].style.borderColor = "#ff2626";
            x[i].style.boxShadow = "0 0 10px #ff2626";
          }
          else {
            x[i].style.borderColor = "#ff2626";
            x[i].style.boxShadow = "0 0 10px #ff2626";
          }
        }
        else if (bam_x[i].value == "Amazon AWS") {
          if ((x[i].value.includes("amazonaws.com/") && (check_amazon_for_bam(x[i].value) == true)) == true) {
            x[i].style.borderColor = null;
            x[i].style.boxShadow = null;
          }
          else if ((x[i].value.includes("amazonaws.com/") && (check_amazon_for_bam(x[i].value) == true)) == false) {
            x[i].style.borderColor = "#ff2626";
            x[i].style.boxShadow = "0 0 10px #ff2626";
          }
          else {
            x[i].style.borderColor = "#ff2626";
            x[i].style.boxShadow = "0 0 10px #ff2626";
          }
        }
        else {
          x[i].style.borderColor = "#ff2626";
          x[i].style.boxShadow = "0 0 10px #ff2626";
        }
      }
      else {
        x[i].style.borderColor = "#ff2626";
        x[i].style.boxShadow = "0 0 10px #ff2626";
      }
    }
  }
}

/**
* Check Amazon repository links if they end with .bam or not
* @param {String} class_name - Entries' HTML <class="">
* @return {bool} bool - Meet requirements or not
*/
function check_amazon_for_bam(input) {
  var checking = ".bam"
  if (input.slice(-4) == checking) {
    return true
  } else {
    return false
  }
}

/**
* Removes the outline of class_name tagged entries
* @param {String} class_name - Entries' HTML <class="">
*/
function remove_outline(class_name) {
  document.getElementById("not_filled").innerHTML = "";
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  for (i = 0; i < x.length; i++) {
    if (x[i].value.length > 0) {
      x[i].style.borderColor = null;
      x[i].style.boxShadow = null;
    }
  }
};

var tissue_doc;
var tissue_sub_parse_remove;
/**
* Removes the outline of class_name tagged entries' tissues
* @param {String} class_name - Entries' HTML <class="">
*/
function remove_outline_tissue(class_name) {
  document.getElementById("not_filled").innerHTML = "";
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  for (i = 0; i < x.length; i++) {
    tissue_doc = "tissue" + (
    i + 1);
    tissue_sub_parse_remove = "tissue" + (
    i + 1) + "_subunit";
    if (document.getElementById(tissue_sub_parse_remove).value.length > 0) {
      document.getElementById(tissue_doc).style.borderColor = null;
      document.getElementById(tissue_doc).style.boxShadow = null;
    }
  }
};

/**
* If the user enters no contact information, changes a null entry into a single space character entry
*/
function no_null_contact() {
  if (document.getElementById("contectinfo") == null) {
    document.getElementById("contectinfo").innerHTML = " ";
  }
};

var which_svg = "";
var tissue_subunit = "";
var clicked_id = "";

/**
* Determine which SVG was clicked
* @param {String} clickid - The SVG's id in the HTML's document
*/
function clickclick(clickid) {
  document.getElementById(tissue_click).innerHTML = clickid.replace(/_/g, " ");
  tissue_subunit = tissue_click + "_subunit";
  clicked_id = clickid;
  tissue_sub_name = document.getElementById(clickid).className.split(" ")[1];
  document.getElementById(tissue_subunit).value = tissue_sub_name;
  var count_which_click = tissue_click.match(/\d/g).join("");
  which_svg = "svg" + count_which_click;
  which_hex = "hexID_num" + count_which_click;
  which_forground = "foregroundID_num" + count_which_click;
  which_forground = "igbtitle_num" + count_which_click;
  document.getElementById(which_svg).value = determine_svgname(clickid);
  document.getElementById(which_hex).value = determine_hexcode(determine_svgname(clickid), clickid);
  document.getElementById(which_forground).value = determine_foreground(determine_hexcode(determine_svgname(clickid), clickid));
};

/**
* Determine what the svgname is from the svg_subunit
* @param {String} from_svg - svg_subunit
* @return {String} - svg_subunit
*/
function determine_svgname(from_svg) {
  if (from_svg == "10_Day_old_Seedling" || from_svg == "10_Day_old_Seedling_roots" || from_svg == "10_Day_old_Seedling_shoots" || from_svg == "ath-10dayOldSeedling.svg") {
    return "ath-10dayOldSeedling.svg";
  } else if (from_svg == "15_Day_old_Seedling" || from_svg == "15_Day_old_Seedling_roots" || from_svg == "15_Day_old_Seedling_shoots" || from_svg == "ath-15dayOldSeedling.svg") {
    return "ath-15dayOldSeedling.svg";
  } else if (from_svg == "Etiolated_seedling" || from_svg == "ath-etiolatedSeedling.svg") {
    return "ath-etiolatedSeedling.svg";
  } else if (from_svg == "Flower" || from_svg == "Flower_receptacle" || from_svg == "ath-Flower.svg") {
    return "ath-Flower.svg";
  } else if (from_svg == "Carpel_petals_stamen_and_sepals" || from_svg == "Flowers_petals" || from_svg == "Flowres_stamen" || from_svg == "Flowers_sepals" || from_svg == "Flowers_carpel" || from_svg == "ath-FlowerParts.svg") {
    return "ath-FlowerParts.svg";
  } else if (from_svg == "Germinating_seed" || from_svg == "ath-GerminatingSeed.svg") {
    return "ath-GerminatingSeed.svg";
  } else if (from_svg == "Internode" || from_svg == "ath-Internode.svg") {
    return "ath-Internode.svg";
  } else if (from_svg == "leaf" || from_svg == "ath-leaf.svg") {
    return "ath-leaf.svg";
  } else if (from_svg == "Full_leaf" || from_svg == "Leaf_lamina" || from_svg == "Leaf_veins" || from_svg == "Leaf_petiole" || from_svg == "ath-LeafParts.svg") {
    return "ath-LeafParts.svg";
  } else if (from_svg == "Pollen" || from_svg == "ath-Pollen.svg") {
    return "ath-Pollen.svg";
  } else if (from_svg == "Roots_tip" || from_svg == "ath-RootTip.svg") {
    return "ath-RootTip.svg";
  } else if (from_svg == "Rosette_shoot" || from_svg == "Rosette_Plus_Root" || from_svg == "Rosette_root" || from_svg == "ath-rosettePlusRoot.svg") {
    return "ath-rosettePlusRoot.svg";
  } else if (from_svg == "Seed_stage_1-4" || from_svg == "ath-SeedStage1-4.svg") {
    return "ath-SeedStage1-4.svg";
  } else if (from_svg == "Seed_stage_5-7" || from_svg == "ath-SeedStage5-7.svg") {
    return "ath-SeedStage5-7.svg";
  } else if (from_svg == "Seed_Stage_8+" || from_svg == "ath-SeedStage8+.svg") {
    return "ath-SeedStage8+.svg";
  } else if (from_svg == "Senescent_Leaf" || from_svg == "ath-SenescentLeaf.svg") {
    return "ath-SenescentLeaf.svg";
  } else if (from_svg == "Shoot_Apex_Inflorescense" || from_svg == "ath-ShootApexInflorescense.svg") {
    return "ath-ShootApexInflorescense.svg";
  } else if (from_svg == "Shoot_Apex_Vegetative-Transition" || from_svg == "ath-ShootApexVegetative-Transition.svg") {
    return "ath-ShootApexVegetative-Transition.svg";
  } else if (from_svg == "Silique_Stage_1-5" || from_svg == "ath-SiliqueStage1-5.svg") {
    return "ath-SiliqueStage1-5.svg";
  } else if (from_svg == "Silique_Stage_6-10" || from_svg == "ath-SiliqueStage6-10.svg") {
    return "ath-SiliqueStage6-10.svg";
  } else if (from_svg == "Stage_1-4_Leaf" || from_svg == "ath-Stage1-4Leaf.svg") {
    return "ath-Stage1-4Leaf.svg";
  } else if (from_svg == "Stage_1_Flowers" || from_svg == "Stage_1_Flowers_shoot" || from_svg == "Stage_1_Flowers_buds" || from_svg == "ath-Stage1Flowers.svg") {
    return "ath-Stage1Flowers.svg";
  } else if (from_svg == "Stage_12_Bud" || from_svg == "ath-Stage12Bud.svg") {
    return "ath-Stage12Bud.svg";
  } else if (from_svg == "Stamen" || from_svg == "Stamen_anthers" || from_svg == "Stamen_filament" || from_svg == "ath-Stamen.svg") {
    return "ath-Stamen.svg";
  } else if (from_svg == "Stigma_and_Ovaries" || from_svg == "Stigma" || from_svg == "Ovaries" || from_svg == "ath-StigmaAndOvaries.svg") {
    return "ath-StigmaAndOvaries.svg";
  } else if (from_svg == "Whole_Silique" || from_svg == "Whole_Silique_silique" || from_svg == "Whole_Silique_seed" || from_svg == "ath-WholeSilique.svg") {
    return "ath-WholeSilique.svg";
  } else if (from_svg == "young_Seedling" || from_svg == "young_Seedling_root" || from_svg == "young_Seedling_hypocotyl" || from_svg == "young_Seedling_cotyledon" || from_svg == "ath-youngSeedling.svg") {
    return "ath-youngSeedling.svg";
  } else if (from_svg == "Other" || from_svg == "ath-Other.svg") {
    return "ath-Other.svg";
  }
};

/**
* Determine hexcode based on svgname and its subunit
* @param {String} which_svg - svgname
* @param {String} which_svg - svg_subunit
* @return {String} - hexcode
*/
function determine_hexcode(which_svg, svg_subunit) {
  if (which_svg == "ath-10dayOldSeedling.svg" && svg_subunit == "10_Day_old_Seedling_shoots") {
    return "0x989800";
  } else if (which_svg == "ath-10dayOldSeedling.svg" && svg_subunit == "10_Day_old_Seedling") {
    return "0x98FF00";
  } else if (which_svg == "ath-10dayOldSeedling.svg" && svg_subunit == "10_Day_old_Seedling_roots") {
    return "0xCCCC97";
  } else if (which_svg == "ath-15dayOldSeedling.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-etiolatedSeedling.svg") {
    return "0xCCCC97";
  } else if (which_svg == "ath-Flower.svg") {
    return "0xCCFF00";
  } else if (which_svg == "ath-FlowerParts.svg") {
    return "0xFFFF00";
  } else if (which_svg == "ath-GerminatingSeed.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-Internode.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-leaf.svg") {
    return "0x64CC65";
  } else if (which_svg == "ath-LeafParts.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-Pollen.svg") {
    return "0xFF0000";
  } else if (which_svg == "ath-RootTip.svg") {
    return "0xBD7740";
  } else if (which_svg == "ath-rosettePlusRoot.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-SeedStage1-4.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-SeedStage5-7.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-SeedStage8+.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-SenescentLeaf.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-ShootApexInflorescense.svg") {
    return "0x999999";
  } else if (which_svg == "ath-ShootApexVegetative-Transition.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-SiliqueStage1-5.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-SiliqueStage6-10.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-Stage1-4Leaf.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-Stage1Flowers.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-Stage12Bud.svg") {
    return "0xFFFF65";
  } else if (which_svg == "ath-Stamen.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-StigmaAndOvaries.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-WholeSilique.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-youngSeedling.svg") { // TODO: Add hex_color
    return "0x64cc65";
  } else if (which_svg == "ath-Other.svg") { // TODO: Add hex_color
    return "0x64cc65";
  }
};

/**
* Determines foreground colour for the IGB viewer based on the hexcode
* @param {String} hexcode_colour - hexcode
* @return {String} - foreground hexcode
*/
function determine_foreground(hexcode_colour) {
  if (hexcode_colour.length > 2 && hexcode_colour.length < 9) {
    return hexcode_colour.substring(2).toUpperCase();
  }
  else {
    console.log("Error retrieving foreground hexcode on the following hexcode: " + hexcode_colour);
  }
}

var json_convert_output;
/**
* Covert the entire form into a JSON format
*/
function convert_to_json() {
  json_convert_output = JSON.parse(document.getElementById("dataOutput").value)
  var json_length = json_convert_output.length
  resetForm();
  for (i = 0; i < json_length; i++) {
    if (i != 0) {
      CloneSection()
    }
    $("select[id=bamtype]").last().val(json_convert_output[i]["repository type*"]);
    $("input[id=reqtitle]").last().val(json_convert_output[i]["title*"]);
    $("textarea[id=reqdesc]").last().val(json_convert_output[i]["description*"]);
    $("input[id=rec]").last().val(json_convert_output[i]["record number *"]);
    $("input[id=bam_input]").last().val(json_convert_output[i]["rna-seq data/bam file repository link*"]);
    $("input[id=publink]").last().val(json_convert_output[i]["publication link"]);
    $("input[id=sralink]").last().val(json_convert_output[i]["sra/ncbi link"]);
    $("input[id=reqread]").last().val(json_convert_output[i]["total reads mapped*"]);
    $("input[id=readmapmethod]").last().val(json_convert_output[i]["read map method"]);
    $("select[id=reqspecies]").last().val(json_convert_output[i]["species*"]);
    var json_svg = "svg" + (i + 1);
    $("input[id=" + json_svg + "]").last().val(determine_svgname(json_convert_output[i]["tissue*"]));
    var json_subunit = "tissue" + (i + 1) + "_subunit";
    $("input[id=" + json_subunit + "]").last().val(json_convert_output[i]["tissue subunit*"]);
    $("input[id=controls]").last().val(json_convert_output[i]["controls"]);
    $("input[id=replicate_controls1]").last().val(json_convert_output[i]["replicate controls"]);
    var json_tissue = "tissue" + (i + 1)
    $("button[id=" + json_tissue + "]").last().html(determine_svgname(json_convert_output[i]["tissue*"]));
  }
}

var warningActive = "nope";
/**
* Show a warning sign before an action
*/
function showWarning() {
  if (warningActive == "nope") {
    document.getElementById("warning").className = "warning";
    warningActive = "yes";
  } else if (warningActive == "yes") {
    hideWarning();
  }
}

/**
* Hide warning sign from showWarning()
*/
function hideWarning() {
  document.getElementById("warning").className = "warning_nope";
  warningActive = "nope";
}

function retriveSRR_existing(xml, id_name) {
  var x,
    xmlDoc;
  xmlDoc = xml.responseXML;
  x = xmlDoc.getElementsByTagName('file');
  var i;
  for (i = 0; i < x.length; i++) {
    $("#" + id_name).append('<input type="checkbox" class="xmlSRR_select" id="addBox' + i + '" value="' + x[i].getAttribute('record_number') + '"> ' + x[i].getAttribute('record_number') + '</input><br>');
  }
}

var xml_url;

function retriveSRR_call(filename) { // Unfinished
  var accountSRR = new XMLHttpRequest();
  accountSRR.open('GET', parent.dataset_dictionary[filename], true);
  accountSRR.responseType = 'document';
  accountSRR.send();
  var new_filename = filename + "_xml";
  setTimeout(function() {
    retriveSRR_existing(accountSRR, new_filename)
  }, 1000);
}

function update_accountAdd_options() { // Unfinished
  if (parent.users_email != "" && parent.title_list.length > 0) {
    document.getElementById("account_dataDisplay").removeAttribute("style");
    for (i = 0; i < parent.title_list.length; i++) {
      var account_SRR_var = "'" + parent.title_list[i] + "'";
      $("#existingDropdown_menu").append('<li style="padding-left: 3px;" onclick="openDataset(event, ' + account_SRR_var + '); display_add_button(true); display_or = true;">' + parent.title_list[i] + '</li>');
      $("#privateDatasets").append('<div id="' + parent.title_list[i] + '" class="tabcontent"><h3>' + parent.title_list[i] + '</h3><div id="' + parent.title_list[i] + '_xml"></div></div>');
    }
  } else {
    document.getElementById("account_dataDisplay").style.display = "none";
  }
}

function update_existingAdd_options() {
  display_add_button(display_or);
  parent.get_user_XML_display();

  // Add private databases:
  update_accountAdd_options();

  // Add Araport 11 database:
  var araport11XML = new XMLHttpRequest();
  araport11XML.open('GET', 'http://bar.utoronto.ca/~asullivan/RNA-Browser/cgi-bin/data/bamdata_amazon_links.xml', true);
  araport11XML.responseType = 'document';
  araport11XML.send();
  setTimeout(function() {
    retriveSRR_existing(araport11XML, "araport11XML")
  }, 1000);

  // Add Klepikova database:
  var klepikovaXML = new XMLHttpRequest();
  klepikovaXML.open('GET', 'http://bar.utoronto.ca/~asullivan/RNA-Browser/cgi-bin/data/bamdata_Developmental_transcriptome.xml', true);
  klepikovaXML.responseType = 'document';
  klepikovaXML.send();
  setTimeout(function() {
    retriveSRR_existing(klepikovaXML, "klepikovaXML")
  }, 1000);
}

var display_or = false;

function display_add_button(display_out) {
  if (display_out == true) {
    document.getElementById("addToData").removeAttribute("style");
  } else if (display_out == false) {
    document.getElementById("addToData").style.display = "none";
  }
}

var testing;

function retriveCONTENT_existing(xml, SRR_num) {
  console.log("Being called?");
  var x,
    xmlDoc;
  xmlDoc = xml.responseXML;
  x = xmlDoc.getElementsByTagName('file');
  var i;
  for (i = 0; i < x.length; i++) {
    if (x[i].getAttribute('record_number') == SRR_num) {
      console.log(x[i]);
      testing = x[i];
      existingXML += "\t\t";
      existingXML += x[i].outerHTML;
      existingXML += "\n";
    }
  }
}

function addPublic_toExisting() {
  console.log("Make sure its running");
  existingXML = [].join('\r\n');

  // See what Araport 11 data the user wants to add to their dataset:
  var araport11_count = (document.getElementById("araport11XML").childElementCount) / 2;
  for (i = 0; i < araport11_count; i++) {
    var addBox_id = "addBox" + i;
    if (document.getElementById(addBox_id).checked == true) {
      var araport11XML = new XMLHttpRequest();
      araport11XML.open('GET', 'http://bar.utoronto.ca/~asullivan/RNA-Browser/cgi-bin/data/bamdata_amazon_links.xml', true);
      araport11XML.responseType = 'document';
      araport11XML.send();
      setTimeout(function() {
        retriveCONTENT_existing(araport11XML, document.getElementById(addBox_id).value)
      }, 1000);
    }
  }

  // See what Araport 11 data the user wants to add to their dataset:
  var klepikovaXML_count = (document.getElementById("klepikovaXML").childElementCount) / 2;
  for (i = 0; i < klepikovaXML_count; i++) {
    var addBox_id = "addBox" + i;
    if (document.getElementById(addBox_id).checked == true) {
      var klepikovaXML = new XMLHttpRequest();
      klepikovaXML.open('GET', 'http://bar.utoronto.ca/~asullivan/RNA-Browser/cgi-bin/data/bamdata_Developmental_transcriptome.xml', true);
      klepikovaXML.responseType = 'document';
      klepikovaXML.send();
      setTimeout(function() {
        retriveCONTENT_existing(klepikovaXML, document.getElementById(addBox_id).value)
      }, 1000);
    }
  }
}

// Taken from w3schools Tab tutorial scripts
function openDataset(evt, datasetName) {
  var i,
    tabcontent,
    tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(datasetName).style.display = "block";
  evt.currentTarget.className += " active";
}
