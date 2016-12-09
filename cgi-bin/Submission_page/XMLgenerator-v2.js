// Code was edited and modified by StackOverFlow user: madalin ivascu, who made the XML generator work for multiple entries. With greatest thanks <3

$(function () {

  $('#SubmitButton').click(function(){
       var formatXML = '';
       $(".Entries").each(function(i,v) {formatXML +=update(formatXML,v)
         $('#ResultXml').val(base + formatXML + end)
  $('#DownloadLink')
    .attr('href', 'data:text/xml;base64,' + btoa(base + formatXML + end))
    .attr('download', 'bamdata_amazon_links.xml');
  $('#generated').show();
    $('.return').hide();
          });
  });
});

var base = [
  '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
  '<!DOCTYPE rnaseq_experiments SYSTEM "bamdata.dtd">',
  '\t<rnaseq_experiments>',
  '\n'
].join('\r\n');

var end = [
  '\t</rnaseq_experiments>'
].join('\r\n');

var added = [
  '\t\t<bam_file desc=\"<?channeldescription?>\" record_number=\"<?channelrecordnumber?>\" hex_colour=\"<?channelhexcolor?>\" bam_link=\"<?channelbamlink?>\" total_reads_mapped=\"<?channeltotalreadsmapped?>\" publication_link=\"<?channelpublicationlink?>\" svg_subunit=\"<?channeltissue?>\" svgname="<?channelsvgname?>\" title=\"<?channeltitle?>\" publication_url=\"<?channelpublicationlink?>\">',
  '\t\t\t<controls>',
  '\t\t\t\t<bam_exp><?channelcontrols?></bam_exp>',
  '\t\t\t</controls>',
  '\t\t\t<groupwith>',
  '\t\t\t\t<bam_exp><?channelgroupwidtho?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth2?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth3?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth4?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth5?></bam_exp>',
  '\t\t\t</groupwith>',
  '\t\t</bam_file>',
  '\n'
].join('\r\n');

var adding = [
  '\t\t<bam_file desc=\"<?channeldescription?>\" record_number=\"<?channelrecordnumber?>\" hex_colour=\"<?channelhexcolor?>\" bam_link=\"<?channelbamlink?>\" total_reads_mapped=\"<?channeltotalreadsmapped?>\" publication_link=\"<?channelpublicationlink?>\" svg_subunit=\"<?channeltissue?>\" svgname="<?channelsvgname?>\" title=\"<?channeltitle?>\" publication_url=\"<?channelpublicationlink?>\">',
  '\t\t\t<controls>',
  '\t\t\t\t<bam_exp><?channelcontrols?></bam_exp>',
  '\t\t\t</controls>',
  '\t\t\t<groupwith>',
  '\t\t\t\t<bam_exp><?channelgroupwidtho?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth2?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth3?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth4?></bam_exp>',
  '\t\t\t\t<bam_exp><?channelgroupwidth5?></bam_exp>',
  '\t\t\t</groupwith>',
  '\t\t</bam_file>',
  '\n'
].join('\r\n');

function update(formatXML,v) {
  var variables = {
    'channeldescription': $(v).find('.channeldescription').val(),
    'channelrecordnumber': $(v).find('.channelrecordnumber').val(),
    'channelhexcolor': $(v).find('.channelhexcolor').val(),
    'channelbamlink': $(v).find('.channelbamlink').val(),
    'channeltotalreadsmapped': $(v).find('.channeltotalreadsmapped').val(),
    'channelpublicationlink': $(v).find('.channelpublicationlink').val(),
    'channeltissue': $(v).find('.channeltissue').val(),
    'channelsvgname': $(v).find('.channelsvgname').val(),
    'channeltitle': $(v).find('.channeltitle').val(),
    'channelpublicationlink': $(v).find('.channelpublicationlink').val(),
    'channelcontrols': $(v).find('.channelcontrols').val(),
    'channelgroupwidtho': $(v).find('.channelgroupwidtho').val(),
    'channelgroupwidth2': $(v).find('.channelgroupwidth2').val(),
    'channelgroupwidth3': $(v).find('.channelgroupwidth3').val(),
    'channelgroupwidth4': $(v).find('.channelgroupwidth4').val(),
    'channelgroupwidth5': $(v).find('.channelgroupwidth5').val()
  };

  var fillXML = added.replace(/<\?(\w+)\?>/g,
    function(match, name) {
      return variables[name];
    });

  return fillXML;


}

$(function () {
  $("#CloneForm").click(CloneSection);
});

function CloneSection() {
  $(".SubmissionArea").append($(".Entries:first").clone(true));
}
