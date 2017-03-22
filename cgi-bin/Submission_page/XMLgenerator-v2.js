// Code was edited and modified by StackOverFlow user: madalin ivascu, who made the XML generator work for multiple entries. With greatest thanks <3
var count_clicks = 1;

$(function () {
    $('#GenerateButton').click(function(){
         var file_name = document.getElementById("reqxml").value.replace(/ /g, "_")
         var formatXML = '';
         var filledbase = updatebase(filledbase);
         remove_outline(".reqfield");
         remove_outline_tissue(".reqtissue");
         no_null_contact();
         if (document.getElementById("reqxml").value.length > 0 && document.getElementById("reqauthor").value.length > 0 && check_req(".reqfield") && check_req_tissue(".reqtissuebutton"))  {
           $(".Entries").each(function(i,v) {formatXML +=update(formatXML, v)
             $('#ResultXml').val(filledbase + formatXML + end);
           $('#DownloadLink')
             .attr('href', 'data:text/xml;base64,' + btoa(filledbase + formatXML + end))
             .attr('download', file_name + '.xml');
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
           document.getElementById("not_filled").innerHTML = "Please fill in all red highlighted fields";
         }
    });
});

var end = [
  '\t</rnaseq_experiments>'
].join('\r\n');

var base = [
  '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
  '<!DOCTYPE rnaseq_experiments SYSTEM "bamdata.dtd">',
  '\t<rnaseq_experiments xmltitle=\"<?channelxmltitle?>\" author=\"<?channelauthor?>\" contact=\"<?channelcontact?>\">',
  '\n'
].join('\r\n');

var added = [
  '\t\t<bam_file desc=\"<?channeldescription?>\" record_number=\"<?channelrecordnumber?>\" hex_colour=\"<?channelhexcolor?>\" bam_type=\"<?channelbamtype?>\" bam_link=\"<?channelbamlink?>\" total_reads_mapped=\"<?channeltotalreadsmapped?>\" publication_link=\"<?channelpublicationlink?>\" svg_subunit=\"<?channeltissue?>\" svgname="<?channelsvgname?>\" title=\"<?channeltitle?>\" publication_url=\"<?channelpublicationlink?>\" species=\"<?channelspecies?>\">',
  '\t\t\t<controls>',
  '\t\t\t\t<bam_exp><?channelcontrols?></bam_exp>',
  '\t\t\t</controls>',
  '\t\t\t<groupwith>',
  '\t\t\t\t<bam_exp><?channelgroupwidtho?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth2?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth3?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth4?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth5?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth6?></bam_exp>',
  '\t\t\t</groupwith>',
  '\t\t</bam_file>',
  '\n'
].join('\r\n');

var all_controls = "";
function update(formatXML,v) {
  all_controls = $(v).find('.channelcontrols').val().split(',');
  var variables = {
    'channeldescription': $(v).find('.channeldescription').val(),
    'channelrecordnumber': $(v).find('.channelrecordnumber').val(),
    'channelhexcolor': $(v).find('.channelhexcolor').val(),
    'channelbamtype': $(v).find('.channelbamtype').val(),
    'channelbamlink': $(v).find('.channelbamlink').val(),
    'channeltotalreadsmapped': $(v).find('.channeltotalreadsmapped').val(),
    'channelpublicationlink': $(v).find('.channelpublicationlink').val(),
    'channeltissue': $(v).find('.channeltissue').val(),
    'channelsvgname': $(v).find('.channelsvgname').val(),
    'channeltitle': $(v).find('.channeltitle').val(),
    'channelpublicationlink': $(v).find('.channelpublicationlink').val(),
    'channelspecies': $(v).find('.channelspecies').val(),
    'channelcontrols': $(v).find('.channelcontrols').val(),
    'channelgroupwidtho': $(v).find('.channelgroupwidtho').val(),
    'channelgroupwidth2': $(v).find('.channelgroupwidth2').val(),
    'channelgroupwidth3': $(v).find('.channelgroupwidth3').val(),
    'channelgroupwidth4': $(v).find('.channelgroupwidth4').val(),
    'channelgroupwidth5': $(v).find('.channelgroupwidth5').val(),
    'channelgroupwidth6': $(v).find('.channelgroupwidth6').val()
  };

  var fillXML = added.replace(/<\?(\w+)\?>/g,
    function(match, name) {
      return variables[name];
    });

  return fillXML;

}

function updatebase(filledbase) {
  var variables = {
    'channelxmltitle': document.getElementById("reqxml").value,
    'channelauthor': document.getElementById("reqauthor").value,
    'channelcontact': document.getElementById("contectinfo").value
  };

  var fillbase = base.replace(/<\?(\w+)\?>/g,
    function(match, name) {
      return variables[name];
    });

  return fillbase;

}

$(function () {
  $("#CloneForm").click(CloneSection);
});

var tissue_sub_name = ""
function CloneSection() {
  $(".SubmissionArea").append($(".Entries:first").clone(true));
  count_clicks += 1;
  var new_tissue = "tissue" + count_clicks;
  var new_tissue_subunit = "tissue" + count_clicks + "_subunit";
  var new_svg = "svg" + count_clicks;
  $("legend:last").text("Entry " + count_clicks);
  $(".change_div_id").last().attr("name", new_tissue);
  $(".change_button_id").last().attr("id", new_tissue);
  $(".change_id_tissue_subunit").last().attr("name", new_tissue_subunit);
  $(".change_id_tissue_subunit").last().attr("id", new_tissue_subunit);
  $(".change_id_tissue").last().attr("id", new_tissue);
  $(".change_svg").last().attr("id", new_svg);
};

function check_req(class_name) {
  var filled = 0;
  var match = document.getElementById("Entries_all").querySelectorAll(class_name).length;
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  for (i = 0; i < x.length; i++) {
    if (x[i].value.length > 0) {
      filled += 1
    }
  }
  if (filled == match) {
    return true
  }
  else {
    return false
  }
};

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
function remove_outline_tissue(class_name) {
  document.getElementById("not_filled").innerHTML = "";
  var x = document.getElementById("Entries_all").querySelectorAll(class_name);
  var i;
  for (i = 0; i < x.length; i++) {
    tissue_doc = "tissue" + (i + 1);
    tissue_sub_parse_remove = "tissue" + (i + 1) + "_subunit";
    if (document.getElementById(tissue_sub_parse_remove).value.length > 0) {
      document.getElementById(tissue_doc).style.borderColor = null;
      document.getElementById(tissue_doc).style.boxShadow = null;
    }
  }
};

function no_null_contact() {
  if (document.getElementById("contectinfo") == null) {
    document.getElementById("contectinfo").innerHTML = " ";
  }
};


var which_svg = "";
var tissue_subunit = "";
var clicked_id = "";
function clickclick(clickid) {
  document.getElementById(tissue_click).innerHTML = clickid.replace(/_/g, " ");
  tissue_subunit = tissue_click + "_subunit";
  clicked_id = clickid;
  tissue_sub_name = document.getElementById(clickid).className.split(" ")[1];
  document.getElementById(tissue_subunit).value = tissue_sub_name;
  var count_which_click = tissue_click.match(/\d/g).join("");
  which_svg = "svg" + count_which_click;
  document.getElementById(which_svg).value = determine_svgname(clickid);
};

function determine_svgname(from_svg) {
  if (from_svg == "10_Day_old_Seedling" || from_svg == "10_Day_old_Seedling_roots" || from_svg == "10_Day_old_Seedling_shoots") {
    return "ath-10dayOldSeedling.svg";
  }
  else if (from_svg == "15_Day_old_Seedling" || from_svg == "15_Day_old_Seedling_roots" || from_svg == "15_Day_old_Seedling_shoots") {
    return "ath-15dayOldSeedling.svg";
  }
  else if (from_svg == "Etiolated_seedling") {
    return "ath-etiolatedSeedling.svg";
  }
  else if (from_svg == "Flower" || from_svg == "Flower_receptacle") {
    return "ath-Flower.svg";
  }
  else if (from_svg == "Carpel_petals_stamen_and_sepals" || from_svg == "Flowers_petals" || from_svg == "Flowres_stamen" || from_svg == "Flowers_sepals" || from_svg == "Flowers_carpel") {
    return "ath-FlowerParts.svg";
  }
  else if (from_svg == "Germinating_seed") {
    return "ath-GerminatingSeed.svg";
  }
  else if (from_svg == "Internode") {
    return "ath-Internode.svg";
  }
  else if (from_svg == "leaf") {
    return "ath-leaf.svg";
  }
  else if (from_svg == "Full_leaf" || from_svg == "Leaf_lamina" || from_svg == "Leaf_veins") {
    return "ath-LeafParts.svg";
  }
  else if (from_svg == "Pollen") {
    return "ath-Pollen.svg";
  }
  else if (from_svg == "Roots_tip") {
    return "ath-RootTip.svg";
  }
  else if (from_svg == "Rosette_shoot" || from_svg == "Rosette_Plus_Root" || from_svg == "Rosette_root") {
    return "ath-rosettePlusRoot.svg";
  }
  else if (from_svg == "Seed_stage_1-4") {
    return "ath-SeedStage1-4.svg";
  }
  else if (from_svg == "Seed_stage_5-7") {
    return "ath-SeedStage5-7.svg";
  }
  else if (from_svg == "Seed_Stage_8+") {
    return "ath-SeedStage8+.svg";
  }
  else if (from_svg == "Senescent_Leaf") {
    return "ath-SenescentLeaf.svg";
  }
  else if (from_svg == "Shoot_Apex_Inflorescense") {
    return "ath-ShootApexInflorescense.svg";
  }
  else if (from_svg == "Shoot_Apex_Vegetative-Transition") {
    return "ath-ShootApexVegetative-Transition.svg";
  }
  else if (from_svg == "Silique_Stage_1-5") {
    return "ath-SiliqueStage1-5.svg";
  }
  else if (from_svg == "Silique_Stage_6-10") {
    return "ath-SiliqueStage6-10.svg";
  }
  else if (from_svg == "Stage_1-4_Leaf") {
    return "ath-Stage1-4Leaf.svg";
  }
  else if (from_svg == "Stage_1_Flowers" || from_svg == "Stage_1_Flowers_shoot" || from_svg == "Stage_1_Flowers_buds") {
    return "ath-Stage1Flowers.svg";
  }
  else if (from_svg == "Stage_12_Bud") {
    return "ath-Stage12Bud.svg";
  }
  else if (from_svg == "Stamen" || from_svg == "Stamen_anthers" || from_svg == "Stamen_filament") {
    return "ath-Stamen.svg";
  }
  else if (from_svg == "Stigma_and_Ovaries" || from_svg == "Stigma" || from_svg == "Ovaries") {
    return "ath-StigmaAndOvaries.svg";
  }
  else if (from_svg == "Whole_Silique") {
    return "ath-WholeSilique.svg";
  }
  else if (from_svg == "young_Seedling" || from_svg == "young_Seedling_root" || from_svg == "young_Seedling_hypocotyl" || from_svg == "young_Seedling_cotyledon") {
    return "ath-youngSeedling.svg";
  }
  else if (from_svg == "Other") {
    return "ath-google_material_help-ic_help_black_24px.svg";
  }
};
