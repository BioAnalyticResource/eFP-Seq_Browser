// Code was edited and modified by StackOverFlow user: madalin ivascu, who made the XML generator work for multiple entries. With greatest thanks <3
var count_clicks = 1;

$(function () {
    $('#GenerateButton').click(function(){
         var file_name = document.getElementById("reqxml").value.replace(/ /g, "_")
         var formatXML = '';
         var filledbase = updatebase(filledbase);
         remove_outline(".reqfield");
         no_null_contact();
         if (document.getElementById("reqxml").value.length > 0 && document.getElementById("reqauthor").value.length > 0 && check_req(".reqfield"))  {
           $(".Entries").each(function(i,v) {formatXML +=update(formatXML, v)
             $('#ResultXml').val(filledbase + formatXML + end);
           $('#DownloadLink')
             .attr('href', 'data:text/xml;base64,' + btoa(filledbase + formatXML + end))
             .attr('download', file_name + '.xml');
           $('#generated').show();
                   });
         }
         else {
           outline_req(".reqfield");
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

var adding = [
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

function update(formatXML,v) {
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

function CloneSection() {
  $(".SubmissionArea").append($(".Entries:first").clone(true));
  count_clicks += 1;
  var new_tissue = "tissue" + count_clicks;
  var new_svg = "svg" + count_clicks;
  $("legend:last").text("Entry " + count_clicks);
  $(".change_div_id").last().attr("name", new_tissue);
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

function no_null_contact() {
  if (document.getElementById("contectinfo") == null) {
    document.getElementById("contectinfo").innerHTML = " ";
  }
};


var which_svg = "";
var clickid_test = "";
function clickclick(clickid) {
    document.getElementById(tissue_click).value = clickid;
    clickid_test = clickid;
    var count_which_click = tissue_click.match(/\d/g).join("");
    which_svg = "svg" + count_which_click;
    document.getElementById(which_svg).value = determine_svgname(clickid);
};

function determine_svgname(from_svg) {
  if (from_svg == "shoots") {
    return "ath-rosettePlusRoot.svg";
  }
}
