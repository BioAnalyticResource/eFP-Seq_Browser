$(function () {
  $('#SubmitButton').click(update);
});

var template = [
  '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
  '<!DOCTYPE rnaseq_experiments SYSTEM "bamdata_amazon_links.dtd">',
  '\t<rnaseq_experiments>',
  '\t\t<bam_file desc=\"<?channeldescription?>\" record_number=\"<?channelrecordnumber?>\" hex_color=\"<?channelhexcolor?>\" bam_link=\"<?channelbamlink?>\" total_reads_mapped=\"<?channeltotalreadsmapped?>\" publication_link=\"<?channelpublicationlink?>\" svg_subunit=\"<?channeltissue?>\" svgname="<?channelsvgname?>\" title=\"<?channeltitle?>\" publication_url=\"<?channelpublicationlink?>\">',
  '\t\t\t<controls>',
  '\t\t\t\t<bam_exp><?channelcontrols?></bam_exp>',
  '\t\t\t</controls>',
  '\t\t\t<groupwidth>',
  '\t\t\t\t<bam_exp><?channelgroupwidth?></bam_exp>',
  '\t\t\t</groupwidth>',
  '\t\t</bam_file>',
  '\t</rnaseq_experiments>'
].join('\r\n');

var base = [
  '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
  '<!DOCTYPE rnaseq_experiments SYSTEM "bamdata_amazon_links.dtd"',
  '\t<rnaseq_experiments>',
].join('\r\n');

var end = [
  '\t</rnaseq_experiments>'
].join('\r\n');

var adding = [
  '\t\t<bam_file desc=\"<?channeldescription?>\" record_number=\"<?channelrecordnumber?>\" hex_color=\"<?channelhexcolor?>\" bam_link=\"<?channelbamlink?>\" total_reads_mapped=\"<?channeltotalreadsmapped?>\" publication_link=\"<?channelpublicationlink?>\" svg_subunit=\"<?channeltissue?>\" svgname="<?channelsvgname?>\" title=\"<?channeltitle?>\" publication_url=\"<?channelpublicationlink?>\">',
  '\t\t\t<controls>',
  '\t\t\t\t<bam_exp><?channelcontrols?></bam_exp>',
  '\t\t\t</controls>',
  '\t\t\t<groupwidth>',
  '\t\t\t\t<bam_exp><?channelgroupwidth?></bam_exp>',
  '\t\t\t</groupwidth>',
  '\t\t</bam_file>',
].join('\r\n');

function update() {
  var variables = {
    'channeldescription': $('#channeldescription').val(),
    'channelrecordnumber': $('#channelrecordnumber').val(),
    'channelhexcolor': $('#channelhexcolor').val(),
    'channelbamlink': $('#channelbamlink').val(),
    'channeltotalreadsmapped': $('#channeltotalreadsmapped').val(),
    'channelpublicationlink': $('#channelpublicationlink').val(),
    'channeltissue': $('#channeltissue').val(),
    'channelsvgname': $('#channelsvgname').val(),
    'channeltitle': $('#channeltitle').val(),
    'channelpublicationlink': $('#channelpublicationlink').val(),
    'channelcontrols': $('#channelcontrols').val(),
    'channelgroupwidth': $('#channelgroupwidth').val()
  };

  var newXml = adding.replace(/<\?(\w+)\?>/g,
    function(match, name) {
      return variables[name];
    });

  var finalXML = base + '\n' + newXml + '\n' + end; 

  $('#ResultXml').val(finalXML);
  $('#DownloadLink')
    .attr('href', 'data:text/xml;base64,' + btoa(finalXML))
    .attr('download', 'bamdata.xml');
  $('#generated').show();
}

onClick = 0

$(function (){
  $("#CloneForm").click(function (){
    $("body").append($("#Entries:first").clone(true));
  });
});
