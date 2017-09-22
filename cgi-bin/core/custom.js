// Get initial values
var colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();

var locus; // Which locus does the user want?
if (document.getElementById("locus") != null) {
  locus = document.getElementById("locus").value;
};

var yscale_input; // What Y-Scale does the user want?
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
var exp_info = []; // Keep track of the FPKM related information // TODO : rename all exp_info to fpkm_info
var rnaseq_success = 0; // Make a list of records and tissues we need to query....
var date_obj = new Date();
var rnaseq_success_start_time = date_obj.getTime(); // Keep track of start time
//console.log(rnaseq_success_start_time);
var rnaseq_success_current_time;
var rnaseq_success_end_time;
var max_absolute_fpkm = -1;
var max_log_fpkm = -1;
var svg_colouring_element = null; // the element for inserting the SVG colouring scale legend
var gene_structure_colouring_element = null; // the element for inserting the gene structure scale legend

//Used to create location for uploaded XML, clientside
var default_url = 'data/bamdata_amazon_links.xml';
var base_src = 'cgi-bin/data/bamdata_amazon_links.xml';
var upload_src = '';
var dataset_dictionary = {
  "Araport 11 RNA-seq data":'cgi-bin/data/bamdata_amazon_links.xml',
  "Developmental transcriptome - Plant J - Sample": 'cgi-bin/data/bamdata_Developmental-transcriptome-PlantJ.xml',
  "Developmental transcriptome - Klepikova et al": 'cgi-bin/data/bamdata_Developmental_transcriptome.xml'
};

//Following lines are used to count and determine how many BAM entries are in the XML file
var count_bam_entries_in_xml = 0;

var xhr = new XMLHttpRequest();
xhr.open( 'GET', base_src, true );
xhr.onreadystatechange = function ( e ) {
    if ( xhr.readyState == 4 && xhr.status == 200 )
        count_bam_entries_in_xml = xhr.responseXML.getElementsByTagName( "bam_file" ).length ;
        //document.getElementById("testing_code").innerHTML = count_bam_entries_in_xml;
};
xhr.send( null );

var send_null_count = 0;
function count_bam_num () {
  send_null_count = 0;
  var xhr = new XMLHttpRequest();
  var old_count = count_bam_entries_in_xml
  //send_null_count = 0;
  xhr.open( 'GET', base_src, true );
  xhr.onreadystatechange = function ( e ) {
      if ( xhr.readyState == 4 && xhr.status == 200 )
          count_bam_entries_in_xml = xhr.responseXML.getElementsByTagName( "bam_file" ).length ;
          //document.getElementById("testing_code").innerHTML = count_bam_entries_in_xml;
  };
  if (progress_percent < 10) {
    var max_null_calls = (count_bam_entries_in_xml * 1.5);
    if (send_null_count < max_null_calls) {
      xhr.send(null);
      send_null_count += 1;
    }
  }
  document.getElementById("testing_count").innerHTML = count_bam_entries_in_xml;
};

function testmobile() {
  if (navigator.userAgent.match(/iPhone/i) || navigator.userAgent.match(/iPad/i) || navigator.userAgent.match(/iPod/i) || navigator.userAgent.match(/Android/i) || navigator.userAgent.match(/webOS/i) || navigator.userAgent.match(/BlackBerry/i) || navigator.userAgent.match(/Windows Phone/i)) {
    return true;
  }
  else {
    return false;
  }
};
//document.getElementById("testing_mobile").innerHTML = testmobile();

if (testmobile() == true) {
  document.getElementById("correctspacing").style.display="none";
  //document.getElementById("feedback_button").style.display="none";
  //document.getElementById("help_icon").style.display="none";
  document.getElementById("butbarborder").style.display="none";
  //document.getElementById("middle_buttons").style.display="none";
  document.getElementById("uploaddata").style.display="none";
  document.getElementById("google_iden_login_button").style.display="none";
  document.getElementById("generatedata").style.display="none";
  document.getElementById("publicdatabase").className = document.getElementById("publicdatabase").className.replace("col-xs-4","")
  document.getElementById("eFP_button").style.display="none";
  document.getElementById("locusbrowser").className="col-xs-6";
  document.getElementById("locus").style.width="100%";
  //$(".locus_button_visual").hide();
  //document.getElementById("tt4").className="col-xs-6";
  document.getElementById("yscale_input").style.width="100%";
  //document.getElementById("locusbuttonmobile").style.display="inline";
  document.getElementById("mobilebrspacing").style.display="inline";
  document.getElementById("default_radio").className="col-xs-6";
  //document.getElementById("absolutedefault").className="col-xs-6";
  document.getElementById("rpkm_scale_input").style.width="100%";
  //document.getElementById("variants_div").style.width="475px";
  document.getElementById("mobilenavbar").style.display="block";
};

// Code edited by StackOverFlow user Matthew "Treeless" Rowlandson http://stackoverflow.com/questions/42166138/css-transition-triggered-by-javascript?noredirect=1#comment71503764_42166138
function generate_loading_screen() {
  window.setInterval(function(){
    if (progress_percent < 96) {
      document.getElementById("loading_screen").className = "loading";
      document.getElementById("body_of").className = "body_of_loading";
      $(':button').prop('disabled', true);
      $('#help_button').prop('disabled', true);
    }
    else if (progress_percent > 96) {
      document.getElementById("loading_screen").className = "loading done_loading";
      document.getElementById("body_of").className = "body_of_loading body_of_loading_done";
      $(':button').prop('disabled', false);
      $('#help_button').prop('disabled', false);
      stop_generating_loading();
    }
  }, 50);
  stop_generating_loading();
  // populate_efp_modal(1); // Not needed to be called during loading
};

function stop_generating_loading() {
  clearInterval(generate_loading_screen);
};

// Base 64 images
var img_loading_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyCAYAAADP/dvoAAAABmJLR0QAwADAAMAanQdUAAAACXBIWXMAAA7CAAAOwgEVKEqAAAAAB3RJTUUH4AoRDzYeAMpyUgAABGJJREFUeNrt3TFoE3scwPGvjxtOzKAQMEOECBkyROhQsWOEChURBFtssdJFB9Gl4OJkwaEtRRAUdLAUqYJgwamIEFAwUoS43RCw0AwpOjhkuCHDQd5Qes9q+7A+7cP2+1na5K53cH/Kl19yIfu63W4XSZL2qL+8BJIkQyhJ0h4VfPvExMSEV0WStGt92zknQkmSE+GPFFOSpN00CToRSpJkCCVJhlCSJEMoSZIhlCTJEEqSZAglSTKEkiQZQkmSDKEkSYZQkiRDKEmSIZQkyRBKe8HDhw/5/Pnzbzn2/v3709/Hx8d/23kkGULpp01PT9NoNH7LsTudDgBJktBut0mSxAsu/Q8CL4G0fUmSEEURcRxTLpc5ePBguu3Lly9EUUQ2m6VcLm/4u0ajQRzH9PT0/PNPGARcu3aNXC6X7lMqlVheXv5u3/Xt69NjJpOht7fXBZEMobRz2u02Z8+eJY5jCoUCtVqN58+fU6lUePLkCXfu3KGnp4d6vU5vby9zc3PA2peCzs7OUiqVvjvm8ePHWVlZoVAocPr0aQYHB6nX6zSbTSqVSnqMkZGRdHp88+YNw8PDzM/PuyiSIZR2zv3798lms7x9+xZYex/x5s2bLC0tce7cOYaHhwmCgHa7zaFDh5ibm6PZbDI9Pc3Hjx/J5/MsLCxQrVa3PMfhw4d5/fo1rVaLI0eOMDk5CUC1WuXTp08EQcCxY8e4cOGCCyIZQmlnffjwgfPnz6ePBwYGuHr1KrD2UmW1WqVWq7G6upru02w2yeVy5PN5AAYHB//1HOvb1/fvdDpkMhniOGZ5eZlCoUCSJOnLqZIMobRjkiRJb3RZF4YhAFNTUywuLnLr1i2KxSKPHj36df+sQUChUODSpUt0Oh0uXrzo+4PSL+Bdo9I2nThxgsePH6d3eS4sLDAwMADA+/fvOXPmDP39/RtiWSqVaLVaRFEEwN27d7d93iiKCIKA27dv8+DBAy5fvpxuazQa1Ov1dHp89uxZuq1ardJqtVw4yYlQ2r4wDDl58mT6eGZmhuvXr/Pu3TuOHj1KJpMhDENevHgBwNjYGFeuXOHVq1eEYUg2mwUgl8sxMzPDqVOnyOfz9PX1pS97/sgkCFAul2m32zx9+pQkSajVaoyOjjI5Ocns7CxRFPHy5UuiKGJkZIT+/n6y2Szj4+OMjY1x48YNF1TaxL5ut9v9+omJiYkNPyVtLo5jkiTZ8NEJWPv4BJBG8GudTockSchkMts+39TUFKurq9y7dw+Aer3O0NAQKysrLob0A7bqmxOh9JO2itlmAfx6wvxZfX19DA0NEYYhBw4cYHFxkdHRURdC+o8MofSHqFQqLC0tUavVAJifn9/0M4mSDKG0axWLRYrFohdC+oW8a1SSZAglSTKEkiQZQkmSDKEkSYZQkiRDKEmSIZQkyRBKkmQIJUkyhJIkGUJJkgyhJEmGUJKkP9mWX8PkN9RLkpwIJUna5fZ1u92ul0GS5EQoSdIe9DfEVWhcl8IjHgAAAABJRU5ErkJggg==";

//var img_loading_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyCAYAAADP/dvoAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAA7CAAAOwgEVKEqAAAAAB3RJTUUH4AoRDzghKC9y4QAABG1JREFUeNrt3TFoE2sAwPG/jxtOzKAQMEOECBkyROhQsWOEChURBFtssdJFC6JLwcVJwaEtRRAUlGIpUgXBglMRIaBgpAhxuyFgoRlSdHDIcEOGg7xBek+fVqxP+7D9/6Ymd72D7yP8+S53ZFe32+0iSdIO9ZdDIEkyhJIk7VDBv9+YnZ11VCRJ29b4+LgrQkmSNlwRblRMSZL+ZBtd8XRFKEna0QyhJMkQSpJkCCVJMoSSJBlCSZIMoSRJhlCSJEMoSZIhlCTJEEqSZAglSTKEkiQZQmnbu3fvHh8+fPgtx969e3f698TExG87jyRDKP206elpGo3Gbzl2p9MBIEkS2u02SZI44NL/IHAIpM1LkoQoiojjmHK5zN69e9NtHz9+JIoistks5XL5i/9rNBrEcUxPT88/H8Ig4NKlS+RyuXSfUqnEysrKV/uub19fPWYyGXp7e50QyRBKW6fdbnPy5EniOKZQKFCr1Xjy5AmVSoWHDx9y8+ZNenp6qNfr9Pb2Mj8/D8D169eZm5ujVCp9dczDhw+zurpKoVDg+PHjDA4OUq/XaTabVCqV9BgjIyPp6vHly5cMDw+zsLDgpEiGUNo6d+7cIZvN8urVK+DT94hXr15leXmZU6dOMTw8TBAEtNtt9u3bx/z8PM1mk+npad69e0c+n2dxcZFqtbrhOfbv38+LFy9otVocOHCAyclJAKrVKu/fvycIAg4dOsSZM2ecEMkQSlvr7du3nD59On09MDDAxYsXgU+XKqvVKrVajbW1tXSfZrNJLpcjn88DMDg4+N1zrG9f37/T6ZDJZIjjmJWVFQqFAkmSpJdTJRlCacskSZLe6LIuDEMApqamWFpa4tq1axSLRe7fv//rPqxBQKFQ4Ny5c3Q6Hc6ePev3g9Iv4F2j0iYdOXKEBw8epHd5Li4uMjAwAMCbN284ceIE/f39X8SyVCrRarWIogiAW7dubfq8URQRBAE3btzg7t27nD9/Pt3WaDSo1+vp6vHx48fptmq1SqvVcuIkV4TS5oVhyNGjR9PXMzMzXL58mdevX3Pw4EEymQxhGPL06VMAxsbGuHDhAs+fPycMQ7LZLAC5XI6ZmRmOHTtGPp+nr68vvez5IytBgHK5TLvd5tGjRyRJQq1WY3R0lMnJSebm5oiiiGfPnhFFESMjI/T395PNZpmYmGBsbIwrV644odI37Op2u93P35idnQVgfHzc0ZG+I45jkiT54tEJ+PT4BJBG8HOdTockSchkMps+39TUFGtra9y+fRuAer3O0NAQq6urTob0AzbqmytC6SdtFLNvBfDzFebP6uvrY2hoiDAM2bNnD0tLS4yOjjoR0n9kCKU/RKVSYXl5mVqtBsDCwsI3n0mUZAilbatYLFIsFh0I6RfyrlFJkiGUJMkQSpJkCCVJMoSSJBlCSZIMoSRJhlCSJEMoSZIhlCTJEEqSZAglSTKEkiQZQkmS/mQb/gzT+i/5SpLkilCSpG1qV7fb7ToMkiRXhJIk7UB/A1moaKrp8fOjAAAAAElFTkSuQmCC";
//var img_loading_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyCAYAAADP/dvoAAAABGdBTUEAALGPC/xhBQAAAAlwSFlzAAAOwgAADsIBFShKgAAAABh0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC45bDN+TgAAA7NJREFUeF7t26FTFk8cB2ADgT+AQDAYCQQDgWAgGAwEI4FgIBIMBoMzBAKBQCQYCASDgUAgEAhEAoFAIBgMBIPBYCDcj8/+3sV3Xk/kdTTAPs/Md969vb27dPOZ3dv3UQcADROEADRNEALQtJ+D8NF1l1JKKfVQa0RPz8gFSiml1EOqET09/QMB4F4ThAA0TRAC0DRBCEDTBCEATROEADRNEALQNEEIQNMEIQBNE4QANE0QAtA0QQhA0wQhAE0ThAA0TRDC+La3t7vLy8vB0d81OTk5aHXd69ev/9lzgAFBCON78uRJd3R0NDj6ux4N3rOrq6vu1atX3efPn8sx8I8IQhjfr4Iw4XV6etodHx93X79+HfT+78uXL+Was7OzQc8P5+fn3cnJSbm+BmHUvsiYuLi4KM8YlfO5fyrXAXckCGF8fUGY4Hv27Fn39OnT7uXLl93U1NTNmN3d3dKfGd7s7Gz5rdbW1rrHjx93z58/LzUchGl/+vSptPPMN2/edAsLC6U9fI+lpaXuxYsX5fqJiYlueXl5cAb4rV/kW09P/0BoUV8Qrq+vlwCs8h1xfn6+tL99+3Yzs0tg1rBLyOWbYF3+/Pjx4825GA3Czc3N0s74nMv3w1RCt94/Qbu/v1/awB3knRt676qenv6B0KK+IEwIZuZXJcCGQ+3w8LDM/lZWVm76c4/ca9htQVjbUc9lyTVhmqXR79+/dzMzM5ZGYRx554beu6qnp38gtKgvCBcXF7v3798Pjn7M9mJjY6MsmyYMhwPybwRhZpgJv7m5uTIbzMwUGEPeuaH3rurp6R8ILeoLwgRQwq4uUWYZsy6V5jdhGJm51bDLsma+6dUNNFtbWzfn4i5BmI05CcCDg4PSHv67Rd2EE5ktfvjwobQjoWxHKlzLOzf03lU9Pf0DoUWZgSWIaiX0MjPLhpVsfMn5bI6pwbW3t1e+42WjS8akXSX8pqeny4xudXW1XF/dFoQJ0BznubkmG2SyaSbtt2/fljHZXJPnRQIx98tSaiQ86zdHaNr1e1FqhCCEP5SNMQmnUQmgGkKjMlvLdX8iM80EaJXAG11uBW4hCOF+yxJtZpiZ/WUzTmaW7969G5wFfksQwv2XP9nv7OyUqn+8B+5IEALQNEEIQNMEIQBNE4QANE0QAtA0QQhA0wQhAE0ThAA0TRAC0DRBCEDTBCEATROEADRNEALQNEEIQNMEIQBNGzsIlVJKqYdYI3p6Ri5QSimlHlKN+LkHABoiCAFoWNf9Bx2Q2ZDpi98WAAAAAElFTkSuQmCC";
var img_gene_struct_1 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAAS0lEQVQ4jWMIxQfSoCCBAQRgvDRUHhYAVsCGWyABhZuATRZFO8wEOEBIpuL1 ABAwhAYOex8KDncfBg57HwoOdzAC4nD458NhX5YCAOtozsHok4ONAAAAAElFTkSuQmCC ";
var absolute_rpkm_scale = "iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQD//wD//AD/+QD/9wD/9AD/8gD/7wD/7QD/6gD/6AD/5QD/4gD/4AD/3QD/2wD/2AD/1gD/ 0wD/0QD/zgD/zAD/yQD/xgD/xAD/wQD/vwD/vAD/ugD/twD/tQD/sgD/rwD/rQD/qgD/qAD/pQD/ owD/oAD/ngD/mwD/mQD/lgD/kwD/kQD/jgD/jAD/iQD/hwD/hAD/ggD/fwD/fAD/egD/dwD/dQD/ cgD/cAD/bQD/awD/aAD/ZgD/YwD/YAD/XgD/WwD/WQD/VgD/VAD/UQD/TwD/TAD/SQD/RwD/RAD/ QgD/PwD/PQD/OgD/OAD/NQD/MwD/MAD/LQD/KwD/KAD/JgD/IwD/IQD/HgD/HAD/GQD/FgD/FAD/ EQD/DwD/DAD/CgD/BwD/BQD/AgCkIVxRAAAAs0lEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hERLGBmpbgljbBwjiiWMnFyMVLcECOhkCZBIZUzPYKSV JaDgYkxKZkxNY2SkmU8gljDCLaFdxDMmw4NrGOWTUUuItwQAG8496iMoCNwAAAAASUVORK5CYII= ";
var relative_rpkm_scale = "iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQAAAP8FBfkKCvQPD+8UFOoZGeUeHuAjI9soKNYtLdEzM8w4OMY9PcFCQrxHR7dMTLJRUa1W VqhbW6NgYJ5mZplra5NwcI51dYl6eoR/f3+EhHqJiXWOjnCTk2uZmWaenmCjo1uoqFatrVGysky3 t0e8vELBwT3GxjjMzDPR0S3W1ijb2yPg4B7l5Rnq6hTv7w/09Ar5+QX//wD/+wD/9gD/8QD/7AD/ 5wD/4gD/3QD/2AD/0wD/zQD/yAD/wwD/vgD/uQD/tAD/rwD/qgD/pQD/oAD/mgD/lQD/kAD/iwD/ hgD/gQD/fAD/dwD/cgD/bQD/ZwD/YgD/XQD/WAD/UwD/TgD/SQD/RAD/PwD/OgD/NAD/LwD/KgD/ JQD/IAD/GwD/FgD/EQD/DAD/BwBUljDTAAAA1klEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hDRLGDi5GICWMBBvCSMjIUsYY+MYUS0BApJ8wmhlzUjI EiDAYgkD0CcMwgxUtQRIpDKmZzCiBBcDgwgDlSwBBRdjUjJjahojI2qcMAhT2RJGNEuAYUasJURH PGMyPLiGTz4ZtYQESwCEoDnh8dGTkQAAAABJRU5ErkJggg==";
var exon_intron_scale = "iVBORw0KGgoAAAANSUhEUgAAALQAAAAPBAMAAAC/7vi3AAAAGFBMVEX///9QUFAAAADcFDz/jAAA AP+m3KYAfQCnICW7AAAArklEQVQ4jd3UMQ+CQAwF4OaG66ourpcO/DCGm7v17/vKBUU8SozBGBvy xo9HD6DzB3OicK4WTa7RfIGWgiiH0In6tBK/iMpKhsvyWAfB7NGlJEHQFA+6U5ZVjf2OTtfBI6YF OgIpadkaklGjZtrepIsXL63+U2s8vzHpila+0zsLEQe9ty+kQ7OuFgJ+pseY3nr5cIxtIQt6OkY/ 3lxReHMhF4nm1z+Zv6KP+/PdANuwQcLhhEyQAAAAAElFTkSuQmCC";

/* Produces an intermediate HEX colour. */
function generate_colour(start_color, end_color, percent) {
    // strip the leading # if it's there
    start_color = start_color.replace(/^\s*#|\s*$/g, '');
    end_color = end_color.replace(/^\s*#|\s*$/g, '');
    // convert 3 char codes --> 6, e.g. `E0F` --> `EE00FF`
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

/* Round the float X to DIGIT number of decimal places. */
function round(x, digits) {
    return parseFloat(x.toFixed(digits))
}

var colouring_part;
var colouring_count = 1;
/* Find and colour a particular SVG in the DOM. */
function colour_part_by_id(id, part, fpkm, mode) {
    var exp_to_colouring_part = [
        ["ERR274310", "shoot"],
        ["SRR547531", "shoot"],
        ["SRR548277", "shoot"],
        ["SRR847503", "shoot"],
        ["SRR847504", "shoot"],
        ["SRR847505", "shoot"],
        ["SRR847506", "shoot"],
        ["SRR1207194", "carpels"],
        ["SRR1207195", "carpels"],
        ["SRR1019436", "etiolatedseedling"],
        ["SRR1019437", "etiolatedseedling"],
        ["SRR1049784", "shoot"],
        ["SRR477075", "etiolatedseedling"],
        ["SRR477076", "etiolatedseedling"],
        ["SRR493237", "etiolatedseedling"],
        ["SRR493238", "etiolatedseedling"],
        ["SRR314815", "stage12bud"],
        ["SRR800753", "stage12bud"],
        ["SRR800754", "stage12bud"],
        ["SRR1105822", "leaf"],
        ["SRR1105823", "leaf"],
        ["SRR1159821", "leaf"],
        ["SRR1159827", "leaf"],
        ["SRR1159837", "leaf"],
        ["SRR314813", "leaf"],
        ["SRR446027", "leaf"],
        ["SRR446028", "leaf"],
        ["SRR446033", "leaf"],
        ["SRR446034", "leaf"],
        ["SRR446039", "leaf"],
        ["SRR446040", "leaf"],
        ["SRR446484", "leaf"],
        ["SRR446485", "shootapexinflorescence"],
        ["SRR446486", "leaf"],
        ["SRR446487", "shootapexinflorescence"],
        ["SRR493036", "leaf"],
        ["SRR493097", "leaf"],
        ["SRR493098", "leaf"],
        ["SRR493101", "leaf"],
        ["SRR764885", "leaf"],
        ["SRR924656", "leaf"],
        ["SRR934391", "leaf"],
        ["SRR942022", "leaf"],
        ["SRR070570", "etiolatedseedling"],
        ["SRR070571", "etiolatedseedling"],
        ["SRR1001909", "all"],
        ["SRR1001910", "all"],
        ["SRR1019221", "all"],
        ["SRR345561", "all"],
        ["SRR345562", "all"],
        ["SRR346552", "all"],
        ["SRR346553", "all"],
        ["SRR394082", "all"],
        ["SRR504179", "all"],
        ["SRR504180", "all"],
        ["SRR504181", "all"],
        ["SRR515073", "all"],
        ["SRR515074", "all"],
        ["SRR527164", "all"],
        ["SRR527165", "all"],
        ["SRR584115", "all"],
        ["SRR584121", "all"],
        ["SRR584129", "all"],
        ["SRR584134", "all"],
        ["SRR653555", "all"],
        ["SRR653556", "all"],
        ["SRR653557", "all"],
        ["SRR653561", "all"],
        ["SRR653562", "all"],
        ["SRR653563", "all"],
        ["SRR653564", "all"],
        ["SRR653565", "all"],
        ["SRR653566", "all"],
        ["SRR653567", "all"],
        ["SRR653568", "all"],
        ["SRR653569", "all"],
        ["SRR653570", "all"],
        ["SRR653571", "all"],
        ["SRR653572", "all"],
        ["SRR653573", "all"],
        ["SRR653574", "all"],
        ["SRR653575", "all"],
        ["SRR653576", "all"],
        ["SRR653577", "all"],
        ["SRR653578", "all"],
        ["SRR797194", "all"],
        ["SRR797230", "all"],
        ["SRR833246", "all"],
        ["SRR847501", "all"],
        ["SRR847502", "all"],
        ["SRR1260032", "all"],
        ["SRR1260033", "all"],
        ["SRR1261509", "all"],
        ["SRR401413", "receptacle"],
        ["SRR401414", "receptacle"],
        ["SRR401415", "receptacle"],
        ["SRR401416", "receptacle"],
        ["SRR401417", "receptacle"],
        ["SRR401418", "receptacle"],
        ["SRR401419", "receptacle"],
        ["SRR401420", "receptacle"],
        ["SRR401421", "receptacle"],
        ["ERR274309", "root"],
        ["SRR1046909", "root"],
        ["SRR1046910", "root"],
        ["SRR1524935", "root"],
        ["SRR1524938", "root"],
        ["SRR1524940", "root"],
        ["SRR314814", "root"],
        ["SRR949956", "all"],
        ["SRR949965", "all"],
        ["SRR949988", "all"],
        ["SRR949989", "all"]
    ];

    colouring_part = "all";

    /*
    for (var i = 0; i < exp_to_colouring_part.length; i++) {
        if (id.replace("_svg", "") == exp_to_colouring_part[i][0]) {
            colouring_part = exp_to_colouring_part[i][1];
        }
    }
    */

    for (var i = 0; i < svg_part_list.length; i++) {
        if (id.replace("_svg", "") == svg_part_list[i][0]) {
            colouring_part = svg_part_list[i][1];
        }
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
            var g = 255 - parseInt(fpkm / max_abs_scale * 255);
            var b = 0;
            //console.log('abs fpkm = ' + fpkm + ' -> rgb(' + r + ', ' + g + ', ' + b + ')');
            if (colouring_part == "all") {
                for (i = 0; i < paths.length; i++) {
                    paths[i].style.fill = 'rgb(' + r + ', ' + g + ', ' + b + ')';
                }
            } else {
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
                        } else {
                            paths[i].style.fill = 'rgb(' + r + ', ' + g + ', ' + b + ')';
                        }
                    }
                }
            }
        } else if (mode == "rel") { // For relative FPKM colouring
            var hex = "";
            // Make the log FPKM a number between 0 and 1 to denote the 0 to +-3 scale.
            var log_scale_max = 3;
            var log_scaling = 0;
            if (fpkm != "Missing controls data" && Math.abs(fpkm) > log_scale_max)
                log_scaling = log_scale_max;
            else if (fpkm != "Missing controls data")
                log_scaling = Math.abs(fpkm);
            log_scaling /= log_scale_max;

            if (fpkm == "Missing controls data") {
                hex = "#D9D9D9"
            } else if (fpkm > 0) { // yellow-red
                hex = generate_colour("FFFF00", "FF0000", log_scaling);
            } else if (fpkm == 0) { // yellow
                hex = "FFFF00";
            } else if (fpkm < 0) { // yellow-blue
                hex = generate_colour("FFFF00", "0000FF", log_scaling);
            }
            //console.log('fpkm = ' + fpkm + ' -> hex = ' + hex);
            if (colouring_part == "all") {
                for (i = 0; i < paths.length; i++) {
                    paths[i].style.fill = hex;
                }
            } else {
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
                        } else {
                            paths[i].style.fill = hex;
                        }
                    }
                }
            }
        }
        if (fpkm == "Missing controls data") {
            document.getElementById(id.replace('_svg', '_rpkm')).innerHTML = fpkm;
        } else {
            document.getElementById(id.replace('_svg', '_rpkm')).innerHTML = round(fpkm, 5);
            //console.log("id = " + id + "sort! " + fpkm + " rounded = " + round(fpkm, 5));
        }
    } else {
        console.log("Paths is null for id = " + id);
    }
}

/* Find and update each SVG in the DOM. */
var current_radio = "abs";
function colour_svgs_now(mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val()) {
    //console.log("colour_svgs_now function is called with mode = " + mode);
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

        //console.log("id = " + exp_info[i][0] + " fpkm = " + exp_info[i][3] + " controls = " + ctrl_count + " controls fpkm = " + ctrl_avg_fpkm + " log2() = " + Math.log2(exp_info[i][3] / ctrl_avg_fpkm));

        // Save the average fpkm of controls and the log fpkm...
        if (ctrl_count > 0) {
            if (exp_info[i][3] == 0 && ctrl_avg_fpkm == 0) {
                // Define log2(0/0) = 0 as opposed to undefined
                exp_info[i].splice(4, 1, 0);
            } else {
                exp_info[i].splice(4, 1, Math.log2(exp_info[i][3] / ctrl_avg_fpkm));
            }
        } else {
            exp_info[i].splice(4, 1, "Missing controls data");
        }
        exp_info[i].splice(6, 1, ctrl_avg_fpkm);

        // See if the absolute or the relative FPKM is max
        if (exp_info[i][3] >= max_absolute_fpkm)
            max_absolute_fpkm = exp_info[i][3];
        if (exp_info[i][4] != "Missing controls data" && Math.abs(exp_info[i][4]) >= max_log_fpkm && Math.abs(exp_info[i][4]) < 1000)
            max_log_fpkm = Math.abs(exp_info[i][4]);

        // Colour SVGs based on the mode requested. Pass in the correct FPKM value...
        if (mode == "rel") {
            if (!exp_info[i][4] && exp_info[i][4] != 0)
                exp_info[i][4] = -999999;
            colour_part_by_id(exp_info[i][0], exp_info[i][1], exp_info[i][4], mode); // index 5 = relative fpkm
        } else {
            if (!exp_info[i][3] && exp_info[i][3] != 0)
                exp_info[i][3] = -999999;
            colour_part_by_id(exp_info[i][0], exp_info[i][1], exp_info[i][3], mode); // index 3 = absolute fpkm
        }
    }
    //console.log('Max ABS FPKM = ' + max_absolute_fpkm);
    //console.log('Max Log FPKM = ' + max_log_fpkm);
    //console.log("Colouring function finished. Errors should be above this log entry.");

    $("#thetable").trigger("update");

    colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();
    change_rpkm_colour_scale(colouring_mode);
}

/* Re-read the value from the input box*/
function get_input_values() {
    colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();
    locus = document.getElementById("locus").value;
    yscale_input = document.getElementById("yscale_input").value;
    if (yscale_input == "Auto" || parseInt(yscale_input) < 1) {
        yscale_input = parseInt(-1);
        //console.log("yscale_input value set to -1.");
    } else {
        //console.log("yscale_input value set to " + yscale_input + ".");
    }
    max_abs_scale = document.getElementById("rpkm_scale_input").value;
}

/* When user clicks GO button, this function is called to update gene structure AND RNA-Seq images*/
function update_all_images(status) {
    $.xhrPool.abortAll();
    variants_radio_options(status);
    send_null_count = 0;
    //count_bam_num();
    //setTimeout(function(){ populate_table(0); }, 3500); //Currently existing a bug that prevents this from being called
    // later on in the code. This forces the populate_table(status) call after 3.5 seconds. Temporary placement
}

/* Updates the radio button <DIV> with new variants images. */
function variants_radio_options(status) {
    get_input_values();
    $.ajax({
        url: 'http://bar.utoronto.ca/~dev/eFP-Seq_Browser/cgi-bin/get_gene_structures.cgi?locus=' + locus,
        dataType: 'json',
        success: function(gene_res) {
            // Update locus_start and locus_end
            locus_start = gene_res['locus_start'];
            locus_end = gene_res['locus_end'];
            splice_variants = JSON.stringify(gene_res['splice_variants']);
            populate_table(status);
            populate_efp_modal(status);

            // Remove existing variant images.
            var variants_div = document.getElementById("variants_div");
            while (variants_div.firstChild) {
                variants_div.removeChild(variants_div.firstChild);
            }
            for (var i = 0; i < parseInt(gene_res['variant_count']); i++) {
                // retrieve the base64 and create the element to insert
                var append_str = "<div class=\"radio\"><label><input type=\"radio\" value=\"" + i + "\"";
                if (i == 0) { // The first gene structure should be selected by default
                    append_str += "checked=\"checked\"";
                }
                append_str += " name=\"radio_group\"><img id=\"variant_" + i + "\" src=\"data:image/png;base64," + gene_res['splice_variants'][i]['gene_structure'] + "\" ></label></div>";
                // Append the element to the div
                $("#variants_div").append(append_str);
            }
            img_gene_struct_1 = "data:image/png;base64," + gene_res['splice_variants'][0]['gene_structure'];
            var all_gene_structure_imgs = document.getElementsByClassName('gene_structure_img');
            for (var i = 0; i < all_gene_structure_imgs.length; i++) {
                all_gene_structure_imgs[i].src = "data:image/png;base64," + gene_res['splice_variants'][0]['gene_structure'];
            }
            $('input[type=radio][name=radio_group]').change(function() { // Bind an event listener..
                gene_structure_radio_on_change();
            });

            $("#thetable").trigger("update");
        },
        error: function() {
          $("tbody").empty();
          var variants_div = document.getElementById("variants_div");
          while (variants_div.firstChild) {
              variants_div.removeChild(variants_div.firstChild);
          }
          var append_str = "<p class=\"warning_core\" style=\"text-align:center;\"> ERROR IN get_gene_structures ! PLEASE REFRESH PAGE AND UPLOAD DATA AGAIN OR CONTACT AN ADMIN </p>"
          $("#variants_div").append(append_str);
          $('#locus_button').prop('disabled', true);
          $('#abs_scale_button').prop('disabled', true);
        }
    });
}

/* When radio button changes, update the gene structure throughout the document and update the PCC values */
function gene_structure_radio_on_change() {
    // Find out which variant is currently selected
    var variant_selected = $('input[type="radio"][name="radio_group"]:checked').val();
    // Get the variant's img src
    var base64 = document.getElementById('variant_' + variant_selected).src;
    // Find all img tags that should be updated (all the <img> with class gene_structure)
    var all_gene_structure_imgs = document.getElementsByClassName('gene_structure_img');
    // Change their src to the newly selected variant's src
    for (var i = 0; i < all_gene_structure_imgs.length; i++) {
        all_gene_structure_imgs[i].src = base64;
    }
    // update all pcc pcc_value
    // Go through the exp_info array and make changes
    for (var i = 0; i < exp_info.length; i++) {
        //console.log("exp_info[i] = " + exp_info[i]);
        document.getElementById(rnaseq_calls[i][1] + '_pcc').innerHTML = exp_info[i][5][variant_selected];
    }

    $("#thetable").trigger("update");
}

/* Converts numbers stored as str to int. */
function parseIntArray(arr) {
    for (var i = 0, len = arr.length; i < len; i++) {
        arr[i] = parseInt(arr[i], 10);
    }
    return arr;
}

/* Makes AJAX request for each RNA-Seq image based on the rnaseq_calls array that was produced by the populate_table() function */
var rnaseq_image_url = "http://bar.utoronto.ca/~asullivan/eFP-Seq_Browser/cgi-bin/webservice.cgi?tissue=";
var match_drive = "";
//var testing_rnaseq_image = 0;
var progress_percent = 0;
var recordReg = /&record(.+&l)/g;
var regRecord;
var sra_list_check = [];
var rnaseq_change = 1;
var check_sra;
var sra_array;
var delay = 1000;
var bp_length_dic = {};
var bp_start_dic = {};
var bp_end_dic = {};
var mapped_reads_dic = {};
var locus_dic = {};
function rnaseq_images(status) {
    bp_length_dic = {};
    mapped_reads_dic = {};
    locus_dic = {};
    rnaseq_success = 1;
    //date_obj2 = new Date();
    //rnaseq_success_start_time = date_obj2.getTime(); // Keep track of start time
    get_input_values();
    //count_bam_num();
    if (rnaseq_calls.length == count_bam_entries_in_xml) {
        sra_list_check = [];
        rnaseq_change = 1;
        for (var i = 0; i < count_bam_entries_in_xml; i++) {
              // delay = i;
              if (bam_type_list[i] == "Google Drive") {
                var myRegexp = /^https:\/\/drive.google.com\/drive\/folders\/(.+)/g;
                var linkString = drive_link_list[i];
                match_drive = myRegexp.exec(linkString);
                // rnaseq_image_url = "http://bar.utoronto.ca/~asullivan/eFP-Seq_Browser/cgi-bin/webservice_gdrive.cgi?numberofreads=" + numberofreads_list[i] + "&gdrive=" + match_drive[1] + "&tissue=" + tissue_list[i] + "&record=" + sra_list[i];
                rnaseq_image_url = "http://bar.utoronto.ca/~asullivan/eFP-Seq_Browser/cgi-bin/webservice_gdrive.cgi?numberofreads=" + numberofreads_list[i] + "&gdrive=" + match_drive[1] + "&tissue=";
                //testing_rnaseq_image += 1;
                if (splice_variants == '') {
                  splice_variants = "[{\"exon_coordinates\":[{\"exon_start\":10326918,\"exon_end\":10327438},{\"exon_start\":10327325,\"exon_end\":10327438},{\"exon_start\":10327519,\"exon_end\":10327635},{\"exon_start\":10327519,\"exon_end\":10327635},{\"exon_start\":10327716,\"exon_end\":10328094},{\"exon_start\":10327716,\"exon_end\":10328094},{\"exon_start\":10328181,\"exon_end\":10328336},{\"exon_start\":10328181,\"exon_end\":10328336},{\"exon_start\":10328414,\"exon_end\":10328550},{\"exon_start\":10328414,\"exon_end\":10328550},{\"exon_start\":10328624,\"exon_end\":10328743},{\"exon_start\":10328624,\"exon_end\":10328743},{\"exon_start\":10328836,\"exon_end\":10328964},{\"exon_start\":10328836,\"exon_end\":10328964},{\"exon_start\":10329058,\"exon_end\":10329251},{\"exon_start\":10329058,\"exon_end\":10329251},{\"exon_start\":10329457,\"exon_end\":10330048},{\"exon_start\":10329457,\"exon_end\":10329601}],\"start\":10326918,\"end\":10330048,\"gene_structure\":\"iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAARklEQVQ4jWNIIwYkMIAAnIvKwwLACthwCySgcBOwyaJoh5kABwjJ1FACgCEt cdj7UHC4+zBx2PtQcLiDERCHwz8fDvuyFACN3Nv0vy8+hAAAAABJRU5ErkJggg== \"},{\"exon_coordinates\":[{\"exon_start\":10326925,\"exon_end\":10327438},{\"exon_start\":10327325,\"exon_end\":10327438},{\"exon_start\":10327519,\"exon_end\":10327635},{\"exon_start\":10327519,\"exon_end\":10327635},{\"exon_start\":10327716,\"exon_end\":10328094},{\"exon_start\":10327716,\"exon_end\":10328094},{\"exon_start\":10328181,\"exon_end\":10328336},{\"exon_start\":10328181,\"exon_end\":10328336},{\"exon_start\":10328414,\"exon_end\":10328550},{\"exon_start\":10328414,\"exon_end\":10328550},{\"exon_start\":10328624,\"exon_end\":10328743},{\"exon_start\":10328624,\"exon_end\":10328743},{\"exon_start\":10328836,\"exon_end\":10328964},{\"exon_start\":10328836,\"exon_end\":10328964},{\"exon_start\":10329058,\"exon_end\":10329251},{\"exon_start\":10329058,\"exon_end\":10329251},{\"exon_start\":10329457,\"exon_end\":10329618},{\"exon_start\":10329457,\"exon_end\":10329618},{\"exon_start\":10329722,\"exon_end\":10330008},{\"exon_start\":10329722,\"exon_end\":10329824}],\"start\":10326918,\"end\":10330048,\"gene_structure\":\"iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAAS0lEQVQ4jWNgSyMCJDCAAJyLysMCwArYcAskoHATsMmiaIeZAAfIkgkoQqmh yCAAJJE47H0oONx9yDjsfSg43MEIiMPhnw+HfVkKAGJJyHVybZqTAAAAAElFTkSuQmCC \"},{\"exon_coordinates\":[{\"exon_start\":10327035,\"exon_end\":10327438},{\"exon_start\":10327325,\"exon_end\":10327438},{\"exon_start\":10327519,\"exon_end\":10327635},{\"exon_start\":10327519,\"exon_end\":10327635},{\"exon_start\":10327716,\"exon_end\":10328094},{\"exon_start\":10327716,\"exon_end\":10328094},{\"exon_start\":10328181,\"exon_end\":10328336},{\"exon_start\":10328181,\"exon_end\":10328336},{\"exon_start\":10328414,\"exon_end\":10328550},{\"exon_start\":10328414,\"exon_end\":10328550},{\"exon_start\":10328624,\"exon_end\":10328743},{\"exon_start\":10328624,\"exon_end\":10328743},{\"exon_start\":10328836,\"exon_end\":10328964},{\"exon_start\":10328836,\"exon_end\":10328964},{\"exon_start\":10329058,\"exon_end\":10329251},{\"exon_start\":10329058,\"exon_end\":10329251},{\"exon_start\":10329457,\"exon_end\":10329607},{\"exon_start\":10329457,\"exon_end\":10329601},{\"exon_start\":10329722,\"exon_end\":10329941}],\"start\":10326918,\"end\":10330048,\"gene_structure\":\"iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAASklEQVQ4jWNggII0fCABVQlBDWAFbLgFElC4CdhkUbTDTIADhGRqAFSINRQV BMAVMw57HwoOdx8yDnsfCg53MALicPjnw2FflgIAMFykVMBo2gsAAAAASUVORK5CYII= \"},{\"exon_coordinates\":[{\"exon_start\":10327035,\"exon_end\":10327134},{\"exon_start\":10327109,\"exon_end\":10327134},{\"exon_start\":10327330,\"exon_end\":10327438},{\"exon_start\":10327330,\"exon_end\":10327438},{\"exon_start\":10327519,\"exon_end\":10327635},{\"exon_start\":10327519,\"exon_end\":10327635},{\"exon_start\":10327716,\"exon_end\":10328094},{\"exon_start\":10327716,\"exon_end\":10328094},{\"exon_start\":10328181,\"exon_end\":10328336},{\"exon_start\":10328181,\"exon_end\":10328336},{\"exon_start\":10328414,\"exon_end\":10328550},{\"exon_start\":10328414,\"exon_end\":10328550},{\"exon_start\":10328624,\"exon_end\":10328743},{\"exon_start\":10328624,\"exon_end\":10328743},{\"exon_start\":10328836,\"exon_end\":10328964},{\"exon_start\":10328836,\"exon_end\":10328964},{\"exon_start\":10329058,\"exon_end\":10329251},{\"exon_start\":10329058,\"exon_end\":10329251},{\"exon_start\":10329457,\"exon_end\":10329618},{\"exon_start\":10329457,\"exon_end\":10329601},{\"exon_start\":10329722,\"exon_end\":10329941}],\"start\":10326918,\"end\":10330048,\"gene_structure\":\"iVBORw0KGgoAAAANSUhEUgAAAcIAAAAIBAMAAACYMuIQAAAAFVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQDytQt7AAAAUElEQVQ4jWNggII0KGBABmxQwQQUJWmoPCwARTMWgQQUbgI2WRTt6O5CkkwN DYAIsYaiggC4YsZh70PB4e5DxmHvQ8HhDkZAHA7/fDjsy1IAaSZ/xYh30LgAAAAASUVORK5CYII=\"}]";
                }
              }

              else {
                // New rnaseq_image_url with BAM file name
                //var amazon_filename = repo_list[i].split("/");
                //rnaseq_image_url = "http://bar.utoronto.ca/~asullivan/eFP-Seq_Browser/cgi-bin/webservice.cgi?numberofreads=" + numberofreads_list[i] + "&amazonfile=" + amazon_filename[amazon_filename.length - 1] + "&tissue=";
                rnaseq_image_url = "http://bar.utoronto.ca/~asullivan/eFP-Seq_Browser/cgi-bin/webservice.cgi?numberofreads=" + numberofreads_list[i] + "&tissue=";
                // New rnaseq_image_url with numberofreads
                //rnaseq_image_url = "http://bar.utoronto.ca/~asullivan/eFP-Seq_Browser/cgi-bin/webservice.cgi?numberofreads=" + numberofreads_list[i] + "&tissue=" + tissue_list[i] + "&record=" + sra_list[i];

                // Original rnaseq_image_url
                // rnaseq_image_url = "http://bar.utoronto.ca/~asullivan/eFP-Seq_Browser/cgi-bin/webservice.cgi?tissue=";
              }

              $.ajax({
                  url: rnaseq_image_url + rnaseq_calls[i][0] + '&record=' + rnaseq_calls[i][1] + '&locus=' + locus + '&variant=1&start=' + locus_start + '&end=' + locus_end + '&yscale=' + yscale_input + '&status=' + status + '&struct=' + splice_variants,
                  dataType: 'json',
                  failure: function(failure_response) {
                      $('#failure').show();
                      //console.log(response_rnaseq['record']);
                  },
                  success: function(response_rnaseq) {
                      //console.log(response_rnaseq['record']);
                      sra_list_check.push(response_rnaseq['record']);
                      bp_length_dic[response_rnaseq['record']] = (parseFloat(response_rnaseq['end']) - parseFloat(response_rnaseq['start']));
                      bp_start_dic[response_rnaseq['record']] = (parseFloat(response_rnaseq['start']));
                      bp_end_dic[response_rnaseq['record']] = (parseFloat(response_rnaseq['end']));
                      mapped_reads_dic[response_rnaseq['record']] = response_rnaseq['reads_mapped_to_locus'];
                      locus_dic[response_rnaseq['record']] = response_rnaseq['locus'];
                      if (locus != response_rnaseq['locus']) {
                          console.log("ERROR: " + locus + "'s RNA-Seq API request returned with data for some other locus.");
                      }
                      // Update the progress bar
                      if (response_rnaseq['status'] == 200) {
                          rnaseq_success++;
                          date_obj3 = new Date();
                          rnaseq_success_current_time = date_obj3.getTime(); // Keep track of start time
                          // progress_percent = rnaseq_success / count_bam_entries_in_xml * 100;
                          progress_percent = rnaseq_change / count_bam_entries_in_xml * 100;
                          $('div#progress').width(progress_percent + '%');
                          document.getElementById('progress_tooltip').innerHTML = rnaseq_success + " / count_bam_entries_in_xml requests completed<br/>Load time <= " + String(round(parseInt(rnaseq_success_current_time - rnaseq_success_start_time) / (1000 * 60))) + " mins.";
                          //console.log("Requests = " + String(rnaseq_success) + ", time delta = " + String(parseInt(rnaseq_success_current_time - rnaseq_success_start_time)));
                      } else {
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
                      } else {
                          //r.push(parseIntArray(String(response_rnaseq['r']).replace(/\[/g, "").replace(/\]/g, "").replace(/"/g, "").split(',')));
                          r = response_rnaseq['r'];
                          //console.log(r);
                      }
                      //console.log("ss_y = ", ss_y, ", sum_y = ", sum_y, ", sum_xy = ", sum_xy, ", sum_x = ", sum_x, ", sum_xx = ", sum_xx, ", ss_x = ", ss_x, ", ssx = ", ssx, ", ssy = ", ssy, ", n = ", n, ", sp = ", sp, ", ssx = ", ssx, ", ssy = ", ssy, ", r = ", r);

                      // FOR CACHE PURPOSES, swap the 2nd and 3rd statements
                      //console.log("if (record == \"" + response_rnaseq['record'] + "\"):");
                      //console.log("\tdumpJSON(" + response_rnaseq['status'] + ", \"" + response_rnaseq['locus'] + "\", " + response_rnaseq['variant'] + ", " + response_rnaseq['chromosome'] + ", " + response_rnaseq['start'] + ", " + response_rnaseq['end'] + ", \"" + response_rnaseq['record'] + "\", \"" + response_rnaseq['tissue'] + "\", \"" + response_rnaseq['rnaseqbase64'] + "\", " + response_rnaseq['reads_mapped_to_locus'] + ", " + response_rnaseq['absolute-fpkm'] + ", " + response_rnaseq['ss_y'] + ", " + response_rnaseq['sum_y'] + ", \"" + response_rnaseq['sum_xy'] + "\", \"" + response_rnaseq['sum_x'] + "\", \"" + response_rnaseq['sum_xx'] + "\", \"" + response_rnaseq['ss_x'] + "\")");
                      //console.log("\tdumpJSON(" + response_rnaseq['status'] + ", \"" + response_rnaseq['locus'] + "\", " + response_rnaseq['variant'] + ", " + response_rnaseq['chromosome'] + ", " + response_rnaseq['start'] + ", " + response_rnaseq['end'] + ", \"" + response_rnaseq['record'] + "\", \"" + response_rnaseq['tissue'] + "\", \"" + response_rnaseq['rnaseqbase64'] + "\", " + response_rnaseq['reads_mapped_to_locus'] + ", " + response_rnaseq['absolute-fpkm'] + ", \"" + response_rnaseq['r'] + "\")");

                      // find the correct row and update coverage image, and stats info
                      /*
                      if (response_rnaseq['record'] == null || response_rnaseq['record'] == undefined) {
                        document.getElementById(currentSRA + '_rnaseq_img').src = 'cgi-bin/img/error.png';
                        console.log("Error in generating image for: " + currentSRA);
                      }
                      */
                      document.getElementById(response_rnaseq['record'] + '_rnaseq_img').src = 'data:image/png;base64,' + response_rnaseq['rnaseqbase64'];
                      rnaseq_change += 1;
                      document.getElementById(response_rnaseq['record'] + '_pcc').innerHTML = r[0];
                      document.getElementById(response_rnaseq['record'] + '_rpkm').innerHTML = response_rnaseq['absolute-fpkm'];

                      // Save the abs-fpkm, and the stats numbers
                      for (var ii = 0; ii < count_bam_entries_in_xml; ii++) {
                          if (exp_info[ii][0] == response_rnaseq['record'] + '_svg') { // Find the correct element
                              exp_info[ii].splice(3, 1, response_rnaseq['absolute-fpkm']);
                              exp_info[ii].splice(5, 1, r);
                              //console.log("Found " + response_rnaseq['record'] + " == " + exp_info[ii][0] + ".");
                          }
                      }

                      // TODO: Need a map of record to svg subunits

                      // Colour SVG by Absolute RPKM
                      /*
                      if (response_rnaseq['record'] == null || response_rnaseq['record'] == undefined) {
                        // document.getElementById(sraNum + '_rnaseq_img').src = 'cgi-bin/img/error.png';
                        console.log("Error in generating image for: " + currentSRA);
                      }
                      */
                      colour_part_by_id(response_rnaseq['record'] + '_svg', 'Shapes', response_rnaseq['absolute-fpkm'], 'abs');

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

                      $("#thetable").trigger("update");
                  }
              });

              // setTimeout(function() { call_ajax(i) }, (i * 10))
              // call_ajax(i);
        }
    } // this one
}
/*
window.setInterval(function(){
  document.getElementById("testing_progress").innerHTML = progress_percent
}, 50);
*/


/* Checking subunit matches tissue */
function checkSubunit(svg, subunit) {
  if (svg == "ath-10dayOldSeedling.svg") {
    if (subunit != "all" && subunit != "root" && subunit != "shoot") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-15dayOldSeedling.svg") {
    if (subunit != "all" && subunit != "root" && subunit != "shoot") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-etiolatedSeedling.svg") {
    if (subunit != "etiolatedseedling") {
      return "etiolatedseedling";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-Flower.svg") {
    if (subunit != "flower" && subunit != "receptacle") {
      return "flower";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-FlowerParts.svg") {
    if (subunit != "all" && subunit != "petals" && subunit != "stamen" && subunit != "sepals" && subunit != "carpels") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-GerminatingSeed.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-Internode.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-leaf.svg") {
    if (subunit != "leaf") {
      return "leaf";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-LeafParts.svg") {
    if (subunit != "all" && subunit != "lamina" && subunit != "petiole" && subunit != "veins") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-Pollen.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-RootTip.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-rosettePlusRoot.svg") {
    if (subunit != "all" && subunit != "shoot" && subunit != "root") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-SeedStage1-4.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-SeedStage5-7.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-SeedStage8+.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-SenescentLeaf.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-ShootApexInflorescense.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-ShootApexVegetative-Transition.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-SiliqueStage1-5.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-SiliqueStage6-10.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-Stage1-4Leaf.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-Stage1Flowers.svg") {
    if (subunit != "all" && subunit != "shoot" && subunit != "buds") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-Stage12Bud.svg") {
    if (subunit != "stage12bud") {
      return "stage12bud";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-Stamen.svg") {
    if (subunit != "all" && subunit != "anthers" && subunit != "filament") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-StigmaAndOvaries.svg") {
    if (subunit != "all" && subunit != "Stigma_tissue" && subunit != "Ovary_tissue") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-WholeSilique.svg") {
    if (subunit != "all" && subunit != "silique" && subunit != "seed") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-youngSeedling.svg") {
    if (subunit != "all" && subunit != "root" && subunit != "hypocotyl" && subunit != "cotyledon") {
      return "all";
    }
    else {
      return subunit
    }
  }
  else if (svg == "ath-Other.svg") {
    if (subunit != "all") {
      return "all";
    }
    else {
      return subunit
    }
  }

}

/* Gets the BAM locator XML to create + populate the table. Leeps track of all RNA-Seq calls it will have to make. */
var bam_type_list = [];
var sra_list = [];
var drive_link_list = [];
var numberofreads_list = [];
var svg_part_list = [];
var efp_rep_2d = [];
var efp_column_count = 0;
var efp_table_column;
var efp_rep_2d_title = [];
var repo_list = [];
var efp_rpkm_names = [];
var efp_pcc_names = [];
var xmlTitleName = "";
var tissue_list = [];
var svg_pat = [];

function populate_table(status) {
    // Reset values
    $("#thetable").empty();
    rnaseq_calls = [];
    exp_info = [];
    rnaseq_success = 0;
    date_obj5 = new Date();
    rnaseq_success_start_time = date_obj5.getTime(); // Keep track of start time
    max_absolute_fpkm = -1;
    max_log_fpkm = -1;
    svg_colouring_element = null;
    gene_structure_colouring_element = null;
    bam_type_list = [];
    drive_link_list = [];
    numberofreads_list = [];
    svg_part_list = [];
    efp_rep_2d = [];
    efp_rep_2d_title = [];
    efp_rpkm_names = [];
    efp_pcc_names = [];
    sra_list = [];
    repo_list = [];
    tissue_list = [];

    // Insert table headers
    $("#thetable").append('<thead><tr>' +
        '<th class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 250px;">Title<div class="arrowdown arrowup"></div></th>' +
        '<th class="" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 460px;">RNA-Seq Coverage</th>' +
        '<th class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;">PCC</th>' +
        '<th id="eFP_th" class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 100px;">eFP (RPKM)</th>' +
        '<th class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;">RPKM</th>' +
        '<th class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 275px;">Details</th>' +
        '</tr></thead>' +
        '<tbody id="data_table_body"></tbody>');

    $.ajax({
        url: base_src,
        dataType: 'xml',
        success: function(xml_res) {
            var $xmltitle = $(xml_res).find("rnaseq_experiments");
            $xmltitle.each(function() {
              xmlTitleName = $(this).attr('xmltitle');
              if (xmlTitleName != "" || xmlTitleName != "Uploaded dataset") {
                document.getElementById("uplodaed_dataset").innerHTML = xmlTitleName;
              }
              else if (xmlTitleName == "" || xmlTitleName == "Uploaded dataset") {
                document.getElementById("uplodaed_dataset").innerHTML = "Uploaded dataset";
              }
            });
            var $title = $(xml_res).find("bam_file");
            $title.each(function() { // Iterate over each subtag inside the <file> tag.
                // Extract information
                var title = $(this).attr('title');
                var description = $(this).attr('desc');
                var svg = $(this).attr('svgname');
                var svg_part = $(this).attr('svg_subunit');
                svg_part = checkSubunit(svg, svg_part);
                tissue_list.push(svg_part);
                var experimentno = $(this).attr('record_number');
                sra_list.push(experimentno);
                svg_part_list.push([experimentno, svg_part]);
                efp_rep_2d.push(experimentno + "_svg");
                efp_rep_2d_title.push(title);
                efp_rpkm_names.push(experimentno + "_rpkm");
                efp_pcc_names.push(experimentno + "_pcc");
                var url = $(this).attr('publication_url');
                var publicationid = $(this).attr('publication_link');
                var numberofreads = $(this).attr('total_reads_mapped');
                if (numberofreads == null || numberofreads == "") {
                  numberofreads_list.push("1")
                }
                else {
                  numberofreads_list.push(numberofreads)
                }
                var species = $(this).attr('species');
                var controls = $(this).find("controls")[0].innerHTML.replace(/<bam_exp>/g, "").replace(/<\/bam_exp>/g, ",").replace(/\n/g, " ").replace(/ /g, "").split(",");
                var links = "";
                for (var i = controls.length; i--;) {
                    if (controls[i] != "MEDIAN") {
                        links += '<a href="http://www.ncbi.nlm.nih.gov/Traces/sra/?run=' + controls[i] + '" target="blank">' + controls[i] + '</a> ';
                    } else {
                        links += controls[i];
                    }
                }
                var name = $(this).attr('bam_link').split("/");
                repo_list.push($(this).attr('bam_link'));
                if ($(this).attr('bam_type') == "Amazon AWS") {
                  var tissue = $(this).attr('bam_link').split("/")[8];
                  /*
                  if ($(this).attr('bam_link').split("/")[8] != "aerial") {
                    tissue = undefined;
                  }
                  */
                };
                var bam_type = $(this).attr('bam_type');
                bam_type_list.push(bam_type);
                var drive_link = $(this).attr('bam_link');
                drive_link_list.push(drive_link);

                //console.log(experimentno + ", " + svg_part);

                // Keep track of what experiments we want to query:
                // Need: tissue, experimentno in rnaseq_calls ... (also need start, end, and locus)
                rnaseq_calls.push([tissue, experimentno]);

                // Construct a table row <tr> element
                var append_str = '<tr>';
                // table_dl_str is used for downloading the table as CSV
                var table_dl_str = "<table id='table_dl'>\n\t<tbody>\n";
                table_dl_str += "\t\t<caption>" + document.getElementById("xmldatabase").value + "</caption>\n";
                // Append title <td>
                append_str += '<td style="width: 250px; font-size: 12px;" id="' + experimentno + '_title">' + title + '</td>\n';
                // Append RNA-Seq and Gene Structure images (2 imgs) in one <td>
                append_str += '<td style="width: 460px;">' + '<img id="' + experimentno + '_rnaseq_img" width="450px" height="50px" class="rnaseq_img" src="' + img_loading_base64 + '" /><br/>' + '<img id="' + experimentno + '_gene_structure_img" width="450px" height="8px" class="gene_structure_img" src="' + img_gene_struct_1 + '" />' + '</td>\n';
                // Append the PCC <td>
                append_str += '<td id="' + experimentno + '_pcc' + '" class="pcc_value" style="font-size: 10px; width: 50px; ">' + -9999 + '</td>';
                // Append the approparite SVG with place holder sorting number in front of it .. all in one <td>
                append_str += '<td tag="svg_name" style="width:  75px;">' + '<div id="' + experimentno + '_svg" name="' + svg.substring(0, svg.length - 4).slice(4) + '_tissue" tag=' + svg_part + '_subtissue" width="75" height="75" style="width: 75px; height: 75px; max-width: 75px; max-height: 75px;">' + document.getElementById(svg.substring(4).replace(".svg", "_svg")).innerHTML + '</div>' + '<div class="mdl-tooltip" for="' + experimentno + '_svg' + '">' + svg.substring(4).replace(".svg", "") + '</div></td>\n';
                // Append abs/rel RPKM
                append_str += '<td id="' + experimentno + '_rpkm' + '" style="font-size: 10px; width: 50px; ">-9999</td>';
                // Append the details <td>
                append_str += '<td style="width: 200px; font-size: 12px;">' + description + '<br/>' + '<a href="' + url + '" target="blank">' + 'NCBI SRA' + '</a>; <a href="' + publicationid + '" target="blank">PubLink</a>' + '<br/><a href="javascript:(function(){$(\'#' + url.substring(44) + '\').toggle();})()"></a><div id="' + url.substring(44) + '" >Total reads = ' + numberofreads + '.<br/>Controls: ' + links + '.<br/>Species: ' + species + '</div></td>\n';
                append_str += '</tr>';

                // Append the <tr> to the table
                $("#thetable").append(append_str);

                exp_info.push([experimentno + '_svg', svg_part, controls, 0, 0, 0, 0]);

                /* Checking to see if this causes the error in loading uploaded files
                if (rnaseq_calls.length == count_bam_entries_in_xml) {
                    rnaseq_images(status);
                }
                */
                //count_bam_num();
                rnaseq_images(status);
            });
            // add parser through the tablesorter addParser method
            $.tablesorter.addParser({
                // set a unique id
                id: 'pcc_sorter',
                is: function(s) {
                    // return false so this parser is not auto detected
                    return false;
                },
                format: function(s) {
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
                type: 'numeric'
            });
            $('#thetable').tablesorter({
                headers: {
                    0: {},
                    1: {
                        sorter: false // disable sorting on this column
                    },
                    2: {
                        sorter: 'pcc_sorter'
                    },
                    3: {
                        //sorter: false // disable sorting on this column
                    },
                    4: {
                        sorter: 'rpkm_sorter'
                    },
                    5: {
                        //sorter: false // disable sorting on this column
                    }
                }
            });
            $("#thetable").trigger("update");
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
        //col_3: 'none', // no filter option
        popup_filters: false,
        filters_row_index: 1,
        alternate_rows: false,
        msg_filter: 'Filtering...'
    };
    //var tf = new TableFilter('thetable', {base_path: 'core/tablefilter/'});
    var tf = new TableFilter('thetable', filtersConfig);
    //var tf = new TableFilter('demo', filtersConfig);
    tf.init();
    colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();
    change_rpkm_colour_scale(colouring_mode);

    if (gene_structure_colouring_element == null) {
        gene_structure_colouring_element = document.getElementById("flt1_thetable").parentElement;
    }
    gene_structure_colouring_element.innerHTML = "";
    var img_created = document.createElement('img');
    img_created.src = 'data:image/png;base64,' + exon_intron_scale;
    img_created.style = 'margin-top: 10px; float: right; margin-right: 10px;';
    gene_structure_colouring_element.appendChild(img_created);
}

var remainder_efp = 0;
var efp_length = 0;
var efp_RPKM_values = [];
var filtered_2d_title = [];
var filtered_2d = [];
var filtered_2d_id = [];
var filtered_2d_tissue = [];
var filtered_2d_subtissue = [];
var filtered_2d_totalReads = [];
var filtered_2d_PCC = [];
var filtered_2d_rpkmNames = [];
var filtered_2d_mappedReads = [];
var filtered_2d_bpLength = [];
var filtered_2d_bpStart = [];
var filtered_2d_bpEnd = [];
var filtered_2d_locus = [];
var tr_of_table;
var to_be_removed_efp =[];
var keep_loop_var = [];
function populate_efp_modal(status) {
  $("#eFPtable").empty();
  efp_table_column = '';
  efp_column_count = 0;
  keep_loop_var = [];

  // Creating new options for Filtering
  var all_of_table = document.getElementById("data_table_body").innerHTML;
  tr_of_table = all_of_table.split("</tr>");
  if (tr_of_table[tr_of_table.length-1] == "") {tr_of_table.splice(tr_of_table.length-1)}; // Remove empty at end

  // Remove display:none; from count
  to_be_removed_efp = [];
  for (i = 0; i < tr_of_table.length; i++) {
    var single_trs = tr_of_table[i].split('"'); // Split items so increased of having a long string, have large array
    var dislpay_loop_number = single_trs.length; // The max number of the display:none; loop so it does not go on for too long
    if (single_trs.length >= 3) { // An if statement to make sure single_trs is longer than 4 to prevent any errors
      display_loop_number = 3; // To check for display:none; in early parts only
    }
    for (u = 0; u < dislpay_loop_number; u++) {
      var single_var = single_trs[u]; // Testing purposes for debugging
      if (single_trs[u] == "display: none;") {
        to_be_removed_efp.push(i); // The index of what item needs to be removed
        break;
      }
    }
  }
  if (to_be_removed_efp.length > 0) {
    for (i = (to_be_removed_efp.length -1); i >= 0; i--) {
      tr_of_table.splice(to_be_removed_efp[i], 1); // Removing the hidden based off of index
    }
  }

  // Create arrays of SVG names and titles
  filtered_2d = [];
  filtered_2d_title = [];
  filtered_2d_id = [];
  filtered_2d_tissue = [];
  filtered_2d_subtissue = [];
  filtered_2d_totalReads = [];
  filtered_2d_PCC = [];
  filtered_2d_rpkmNames = [];
  filtered_2d_mappedReads = [];
  filtered_2d_bpLength = [];
  filtered_2d_locus = [];
  filtered_2d_bpStart = [];
  filtered_2d_bpEnd = [];
  for (i = 0; i < tr_of_table.length; i++) {
    var single_trs = tr_of_table[i].split('"'); // Split items so increased of having a long string, have large array
    // Title
    for (u = 0; u < single_trs.length; u++) {
      var single_var = single_trs[u]; // Testing purposes for debugging
      if ((single_trs[u].length > 6) && (single_trs[u].substr(single_trs[u].length - 6) == "_title")) {
        var trs_title_left = single_trs[u+1].split(">");
        var trs_title_right = trs_title_left[1].split("<");
        if (trs_title_right[0] == "") {
          filtered_2d_title.push(trs_title_right[1]);
        }
        else {
          filtered_2d_title.push(trs_title_right[0]);
        }
        break;
      }
    }
    // SRR/SRA number or ID number
    for (u = 0; u < single_trs.length; u++) {
      var single_var = single_trs[u]; // Testing purposes for debugging
      if ((single_trs[u].length > 4) && (single_trs[u].substr(single_trs[u].length - 4) == "_svg")) {
        filtered_2d.push(single_trs[u]);
        filtered_2d_id.push(single_trs[u].substring(0, single_trs[u].length - 4));
        filtered_2d_bpLength.push(bp_length_dic[single_trs[u].substring(0, single_trs[u].length - 4)]);
        filtered_2d_mappedReads.push(mapped_reads_dic[single_trs[u].substring(0, single_trs[u].length - 4)]);
        filtered_2d_locus.push(locus_dic[single_trs[u].substring(0, single_trs[u].length - 4)]);
        filtered_2d_bpStart.push(bp_start_dic[single_trs[u].substring(0, single_trs[u].length - 4)]);
        filtered_2d_bpEnd.push(bp_end_dic[single_trs[u].substring(0, single_trs[u].length - 4)]);
        break;
      }
    }
    // Tissue
    for (u = 0; u < single_trs.length; u++) {
      var single_var = single_trs[u]; // Testing purposes for debugging
      if ((single_trs[u].length > 7) && (single_trs[u].substr(single_trs[u].length - 7) == "_tissue")) {
        filtered_2d_tissue.push(single_trs[u].substring(0, single_trs[u].length - 7));
        break;
      }
    }
    // Subtissue
    for (u = 0; u < single_trs.length; u++) {
      var single_var = single_trs[u]; // Testing purposes for debugging
      if ((single_trs[u].length > 16) && (single_trs[u].substr(single_trs[u].length - 16) == "_subtissue&quot;")) {
        filtered_2d_subtissue.push(single_trs[u].substring(0, single_trs[u].length - 16));
        break;
      }
    }
    // Total reads mapped number
    for (u = 0; u < single_trs.length; u++) {
      var single_var = single_trs[u]; // Testing purposes for debugging
      if ((single_trs[u].length > 23) && (single_trs[u].substr(single_trs[u].length - 23) == ".<br>Controls: <a href=") && (single_trs[u].substr(0, 15) == ">Total reads = ")) {
        filtered_2d_totalReads.push(single_trs[u].substr(0, single_trs[u].length - 23).substr(15));
        break;
      }
    }
    // PCC
    for (u = 0; u < single_trs.length; u++) {
      var single_var = single_trs[u]; // Testing purposes for debugging
      if ((single_trs[u].length > 13) && (single_trs[u].substr(single_trs[u].length - 13) == "</td><td tag=")) {
        filtered_2d_PCC.push(single_trs[u].substr(0, single_trs[u].length - 13).substr(1));
        break;
      }
    }
    // Filtered RPKM names
    for (u = 0; u < single_trs.length; u++) {
      var single_var = single_trs[u]; // Testing purposes for debugging
      if ((single_trs[u].length > 5) && (single_trs[u].substr(single_trs[u].length - 5) == "_rpkm")) {
        filtered_2d_rpkmNames.push(single_trs[u]);
        break;
      }
    }
  }

  // remainder_efp = efp_rep_2d.length % 11; // Old without filter option
  // efp_length = efp_rep_2d.length; // Old without filter option
  remainder_efp = tr_of_table.length % 11;
  efp_length = tr_of_table.length;
  efp_RPKM_values = [];

  for (i = 0; i < filtered_2d_rpkmNames.length; i++) {
    if (isNaN(parseFloat(document.getElementById(filtered_2d_rpkmNames[i]).textContent)) == false) {
      efp_RPKM_values.push(parseFloat(document.getElementById(filtered_2d_rpkmNames[i]).textContent));
    }
  }

  // Insert eFP Table header
  $("#eFPtable").append('<p class="eFP_thead"> AGI-ID: <a href="https://www.arabidopsis.org/servlets/TairObject?type=locus&name=' + locus + '" target="_blank">' + locus +  '</a></p>');

  // Check radio
  if (current_radio == "abs") {
    $("#eFPtable").append('<p class="eFP_thead"> eFP Colour Scale: <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQD//wD//AD/+QD/9wD/9AD/8gD/7wD/7QD/6gD/6AD/5QD/4gD/4AD/3QD/2wD/2AD/1gD/ 0wD/0QD/zgD/zAD/yQD/xgD/xAD/wQD/vwD/vAD/ugD/twD/tQD/sgD/rwD/rQD/qgD/qAD/pQD/ owD/oAD/ngD/mwD/mQD/lgD/kwD/kQD/jgD/jAD/iQD/hwD/hAD/ggD/fwD/fAD/egD/dwD/dQD/ cgD/cAD/bQD/awD/aAD/ZgD/YwD/YAD/XgD/WwD/WQD/VgD/VAD/UQD/TwD/TAD/SQD/RwD/RAD/ QgD/PwD/PQD/OgD/OAD/NQD/MwD/MAD/LQD/KwD/KAD/JgD/IwD/IQD/HgD/HAD/GQD/FgD/FAD/ EQD/DwD/DAD/CgD/BwD/BQD/AgCkIVxRAAAAs0lEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hERLGBmpbgljbBwjiiWMnFyMVLcECOhkCZBIZUzPYKSV JaDgYkxKZkxNY2SkmU8gljDCLaFdxDMmw4NrGOWTUUuItwQAG8496iMoCNwAAAAASUVORK5CYII="> Min: ' + Math.min.apply(null, efp_RPKM_values) + ' RPKM, Max: ' + Math.max.apply(null, efp_RPKM_values) + ' RPKM</p>' + '<br><table><tbody class="eFP_tbody"></tbody>');
  }

  else if (current_radio == "rel") {
    $("#eFPtable").append('<p class="eFP_thead"> eFP Colour Scale: <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAAAPCAMAAAAlD5r/AAABQVBMVEX///8AAADcFDz/jAAAAP+m 3KYAfQAAAP8FBfkKCvQPD+8UFOoZGeUeHuAjI9soKNYtLdEzM8w4OMY9PcFCQrxHR7dMTLJRUa1W VqhbW6NgYJ5mZplra5NwcI51dYl6eoR/f3+EhHqJiXWOjnCTk2uZmWaenmCjo1uoqFatrVGysky3 t0e8vELBwT3GxjjMzDPR0S3W1ijb2yPg4B7l5Rnq6hTv7w/09Ar5+QX//wD/+wD/9gD/8QD/7AD/ 5wD/4gD/3QD/2AD/0wD/zQD/yAD/wwD/vgD/uQD/tAD/rwD/qgD/pQD/oAD/mgD/lQD/kAD/iwD/ hgD/gQD/fAD/dwD/cgD/bQD/ZwD/YgD/XQD/WAD/UwD/TgD/SQD/RAD/PwD/OgD/NAD/LwD/KgD/ JQD/IAD/GwD/FgD/EQD/DAD/BwBUljDTAAAA1klEQVQ4jWNg5+Dk4ubh5eMXEBQSFhEVE5eQlJKW kZWTV1BUUlZRVVPX0NTS1tHV0zcwNDI2MTUzt7C0sraxtbN3cHRydnF1c/fw9PL28fXzDwgMCg4J DQuPiIyKjomNi09ITEpOSU1Lz8jMYhi1hDRLGDi5GICWMBBvCSMjIUsYY+MYUS0BApJ8wmhlzUjI EiDAYgkD0CcMwgxUtQRIpDKmZzCiBBcDgwgDlSwBBRdjUjJjahojI2qcMAhT2RJGNEuAYUasJURH PGMyPLiGTz4ZtYQESwCEoDnh8dGTkQAAAABJRU5ErkJggg=="> Min: ' + Math.min.apply(null, efp_RPKM_values) + ', Max: '+ Math.max.apply(null, efp_RPKM_values) + '</p>' + '<br><table><tbody></tbody>');
  }

  // Creating eFP representative table
  for (i = 0; i < (~~(filtered_2d.length/11) * 11); i+=11) {
    if (document.getElementById(filtered_2d[i+10]).outerHTML != 'null') {
      efp_table_column = '<tr>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i] + '_rep">' + document.getElementById(filtered_2d[i]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+1] + '_rep">' + document.getElementById(filtered_2d[i+1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+1] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+2] + '_rep">' + document.getElementById(filtered_2d[i+2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+2] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+3] + '_rep">' + document.getElementById(filtered_2d[i+3]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+3] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+4] + '_rep">' + document.getElementById(filtered_2d[i+4]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+4] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+5] + '_rep">' + document.getElementById(filtered_2d[i+5]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+5] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+6] + '_rep">' + document.getElementById(filtered_2d[i+6]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+6] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+7] + '_rep">' + document.getElementById(filtered_2d[i+7]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+7] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+8] + '_rep">' + document.getElementById(filtered_2d[i+8]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+8] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+9] + '_rep">' + document.getElementById(filtered_2d[i+9]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+9] + '</span></div></td>';
      efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[i+10] + '_rep">' + document.getElementById(filtered_2d[i+10]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[i+10] + '</span></div></td>';
      efp_table_column += '</tr>';
      $("#eFPtable").append(efp_table_column);
    }
  }

  if (remainder_efp == 1) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }
  else if (remainder_efp == 2) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-2] + '_rep">' + document.getElementById(filtered_2d[efp_length-2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-2] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }
  else if (remainder_efp == 3) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-3] + '_rep">' + document.getElementById(filtered_2d[efp_length-3]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-3] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-2] + '_rep">' + document.getElementById(filtered_2d[efp_length-2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-2] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }
  else if (remainder_efp == 4) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-4] + '_rep">' + document.getElementById(filtered_2d[efp_length-4]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-4] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-3] + '_rep">' + document.getElementById(filtered_2d[efp_length-3]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-3] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-2] + '_rep">' + document.getElementById(filtered_2d[efp_length-2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-2] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }
  else if (remainder_efp == 5) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-5] + '_rep">' + document.getElementById(filtered_2d[efp_length-5]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-5] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-4] + '_rep">' + document.getElementById(filtered_2d[efp_length-4]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-4] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-3] + '_rep">' + document.getElementById(filtered_2d[efp_length-3]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-3] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-2] + '_rep">' + document.getElementById(filtered_2d[efp_length-2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-2] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }
  else if (remainder_efp == 6) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-6] + '_rep">' + document.getElementById(filtered_2d[efp_length-6]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-6] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-5] + '_rep">' + document.getElementById(filtered_2d[efp_length-5]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-5] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-4] + '_rep">' + document.getElementById(filtered_2d[efp_length-4]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-4] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-3] + '_rep">' + document.getElementById(filtered_2d[efp_length-3]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-3] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-2] + '_rep">' + document.getElementById(filtered_2d[efp_length-2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-2] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }
  else if (remainder_efp == 7) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-7] + '_rep">' + document.getElementById(filtered_2d[efp_length-7]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-7] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-6] + '_rep">' + document.getElementById(filtered_2d[efp_length-6]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-6] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-5] + '_rep">' + document.getElementById(filtered_2d[efp_length-5]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-5] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-4] + '_rep">' + document.getElementById(filtered_2d[efp_length-4]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-4] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-3] + '_rep">' + document.getElementById(filtered_2d[efp_length-3]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-3] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-2] + '_rep">' + document.getElementById(filtered_2d[efp_length-2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-2] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }
  else if (remainder_efp == 8) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-8] + '_rep">' + document.getElementById(filtered_2d[efp_length-8]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-8] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-7] + '_rep">' + document.getElementById(filtered_2d[efp_length-7]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-7] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-6] + '_rep">' + document.getElementById(filtered_2d[efp_length-6]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-6] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-5] + '_rep">' + document.getElementById(filtered_2d[efp_length-5]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-5] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-4] + '_rep">' + document.getElementById(filtered_2d[efp_length-4]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-4] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-3] + '_rep">' + document.getElementById(filtered_2d[efp_length-3]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-3] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-2] + '_rep">' + document.getElementById(filtered_2d[efp_length-2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-2] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }
  else if (remainder_efp == 9) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-9] + '_rep">' + document.getElementById(filtered_2d[efp_length-9]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-9] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-8] + '_rep">' + document.getElementById(filtered_2d[efp_length-8]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-8] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-7] + '_rep">' + document.getElementById(filtered_2d[efp_length-7]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-7] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-6] + '_rep">' + document.getElementById(filtered_2d[efp_length-6]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-6] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-5] + '_rep">' + document.getElementById(filtered_2d[efp_length-5]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-5] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-4] + '_rep">' + document.getElementById(filtered_2d[efp_length-4]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-4] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-3] + '_rep">' + document.getElementById(filtered_2d[efp_length-3]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-3] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-2] + '_rep">' + document.getElementById(filtered_2d[efp_length-2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-2] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }
  else if (remainder_efp == 10) {
    efp_table_column = '<tr>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-10] + '_rep">' + document.getElementById(filtered_2d[efp_length-10]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-10] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-9] + '_rep">' + document.getElementById(filtered_2d[efp_length-9]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-9] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-8] + '_rep">' + document.getElementById(filtered_2d[efp_length-8]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-8] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-7] + '_rep">' + document.getElementById(filtered_2d[efp_length-7]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-7] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-6] + '_rep">' + document.getElementById(filtered_2d[efp_length-6]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-6] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-5] + '_rep">' + document.getElementById(filtered_2d[efp_length-5]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-5] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-4] + '_rep">' + document.getElementById(filtered_2d[efp_length-4]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-4] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-3] + '_rep">' + document.getElementById(filtered_2d[efp_length-3]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-3] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-2] + '_rep">' + document.getElementById(filtered_2d[efp_length-2]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-2] + '</span></div></td>';
    efp_table_column += '<td>' + '<div class="efp_table_tooltip" id="' + filtered_2d[efp_length-1] + '_rep">' + document.getElementById(filtered_2d[efp_length-1]).outerHTML + '<span class="efp_table_tooltip_text">' + filtered_2d_title[efp_length-1] + '</span></div></td>';
    efp_table_column += '</tr>';
    $("#eFPtable").append(efp_table_column);
  }

}

/* Changes the legend for scales. */
function change_rpkm_colour_scale(colouring_mode) {
    if (svg_colouring_element == null) {
        svg_colouring_element = document.getElementById("flt3_thetable").parentElement;
    }
    svg_colouring_element.innerHTML = "";
    if (colouring_mode == "rel") {
        var img_created = document.createElement('img');
        img_created.src = 'data:image/png;base64,' + relative_rpkm_scale;
        img_created.style = 'margin-top: 10px;';
        svg_colouring_element.appendChild(img_created);
    } else {
        var img_created = document.createElement('img');
        img_created.src = 'data:image/png;base64,' + absolute_rpkm_scale;
        img_created.style = 'margin-top: 10px;';
        svg_colouring_element.appendChild(img_created);
    }
    // Add border to fltrow class tr's child td elements
    var tds = document.getElementsByClassName("fltrow")[0].getElementsByTagName("td");
    for (var i = 0; i < tds.length; i++) {
        tds[i].style = "border: 1px solid #D3D3D3";
    }
}

/* Disables the absolute RPKM scale input button if the relative mode is selected. */
$("input[name=svg_colour_radio_group]:radio").change(function() {
    colouring_mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val();
    if (colouring_mode == "abs") {
        $("#rpkm_scale_input").removeAttr('disabled');
    } else {
        $("#rpkm_scale_input").prop("disabled", true);
    }
});

function locus_validation() {
    var loc = document.getElementById("locus").value;
    if (loc.length == 9 &&
        (loc[0] == 'A' || loc[0] == 'a') &&
        (loc[1] == 'T' || loc[1] == 't') &&
        ((loc[2] >= 1 && loc[2] <= 5) || loc[2] == 'C' || loc[2] == 'M' || loc[2] == 'c' || loc[2] == 'm') &&
        (loc[3] == 'G' || loc[3] == 'g') &&
        (loc[4] >= 0 && loc[4] <= 9) &&
        (loc[5] >= 0 && loc[5] <= 9) &&
        (loc[6] >= 0 && loc[6] <= 9) &&
        (loc[7] >= 0 && loc[7] <= 9) &&
        (loc[8] >= 0 && loc[8] <= 9)) {
        $("#locus_button").removeAttr('disabled');
    } else {
        $("#locus_button").prop("disabled", true);
    }
}

function yscale_validation() {
    var yscale = document.getElementById("yscale_input").value;
    if (parseInt(yscale) > 0 || yscale == "Auto" || yscale == "") {
        //$("#yscale_button").removeAttr('disabled');
        $("#locus_button").removeAttr('disabled');
    } else {
        //$("#yscale_button").prop("disabled", true);
        $("#locus_button").prop("disabled", true);
    }
}

function rpkm_validation() {
    var rpkmscale = parseInt(document.getElementById("rpkm_scale_input").value);
    if (rpkmscale > 0) {
        $("#abs_scale_button").removeAttr('disabled');
    } else {
        $("#abs_scale_button").prop("disabled", true);
    }
}

var base_dataset_dictionary = {
  "Araport 11 RNA-seq data":'cgi-bin/data/bamdata_amazon_links.xml',
  "Developmental transcriptome - Plant J - Sample": 'cgi-bin/data/bamdata_Developmental-transcriptome-PlantJ.xml',
  "Developmental transcriptome - Klepikova et al": 'cgi-bin/data/bamdata_Developmental_transcriptome.xml'
};

function reset_database_options() {
  $('.userAdded').remove();
  dataset_dictionary = base_dataset_dictionary;
  list_modified = false;
}

var get_xml_list_output = [];
var user_exist = false;
var list_modified = false;
var check_for_change = 0;
var xml_title;
var match_title = {};
var title_list = [];
var data_list = [];
function get_user_XML_display() {
  // First check to make sure there is is a user logged in or else this script will not run
  if (users_email != "" || users_email != undefined || users_email != null) {
    $.ajax({
      url: "http://bar.utoronto.ca/~asher/efp_seq_userdata/get_xml_list.php?user=" + users_email,
      dataType: 'json',
      failure: function(get_xml_list_return) {
  		    //get_xml_list_output = get_xml_list_return
          console.log("ERROR! Something went wrong");
    	},
      success: function(get_xml_list_return) {
          // reset all variables
          xml_title;
          match_title = {};
          title_list = [];
          data_list = [];
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
            if (get_xml_list_output["files"].length > 0) {
              for (i = 0; i < get_xml_list_output["files"].length; i++) {
                var xml_file;
                xml_title;
                xml_title = get_xml_list_output["files"][i][1];
                // Make sure there is a title or if not, make one
                if (xml_title == "" || xml_title == "Uploaded dataset" || xml_title == undefined || xml_title == null) {
                  xml_title = "Uploaded dataset - Unnamed dataset";
                }
                title_list.push(xml_title);
                xml_fle_name = get_xml_list_output["files"][i][0]
                // This needed for later on
                match_title[xml_title] = xml_fle_name;
                // Obtain data locatio for each individual XML
                $.ajax({
                  url: "http://bar.utoronto.ca/~asher/efp_seq_userdata/get_xml.php?file=" + xml_fle_name,
                  dataType: 'json',
                  success: function(get_xml_return) {
                    xml_file = get_xml_return;
                    data_list.push(xml_file["data"]);
                  }
                })
              }
            }
            setTimeout(function() {
              if (list_modified == false) {
                for (i = 0; i < get_xml_list_output["files"].length; i++) {
                  // Add data to list of accessible datasets
                  dataset_dictionary[title_list[i]] = data_list[i];
                  // Create option to select data from user
                  document.getElementById("xmldatabase").innerHTML += '<option class="userAdded" value="' + title_list[i] + '" id="' + title_list[i] + '">' + title_list[i] + '</option>';
                }
              };
              list_modified = true;
            }, 1000)
          }
    	}
    })
  }
}

function add_user_xml_by_upload() {
  get_user_XML_display(); // Updates data and determines if user_exists or now
  // setTimeout is necessary due to xmlTitleName taking a while to be generated. Though only requires 3 seconds to obtain, setTimeout set to 4 just in case
  setTimeout(function() {
    if (user_exist == false) {
      // Creates a new user if the user does not already exist
      $.ajax({
        method: "POST",
        url: "http://bar.utoronto.ca/~asher/efp_seq_userdata/upload.php",
        data: {user : users_email, xml : upload_src, title: xmlTitleName}
      })
    }
    else if (user_exist == true) {
      if (dataset_dictionary[xmlTitleName] == undefined) {
        // If the file does not already exist in the account, add it
        $.ajax({
          method: "POST",
          url: "http://bar.utoronto.ca/~asher/efp_seq_userdata/upload.php",
          data: {user : users_email, xml : upload_src, title: xmlTitleName}
        })
      }
      else if (dataset_dictionary[xmlTitleName] != undefined) {
        // reset variables for get_user_XML_display
        list_modified = false;
        check_for_change = 0;
        // If the file does already exist in the account, delete old and add new
        $.ajax({
          url: "http://bar.utoronto.ca/~asher/efp_seq_userdata/delete_xml.php?user=" + users_email + "&file=" + match_title[xmlTitleName]
        })
        $.ajax({
          method: "POST",
          url: "http://bar.utoronto.ca/~asher/efp_seq_userdata/upload.php",
          data: {user : users_email, xml : upload_src, title: xmlTitleName}
        })
      }
    }
    get_user_XML_display(); // Update data again
  }, 10000);
}

// Though change_dropSelect_width() is not needed anymore, keeping code just incase ever used again
var show_dropSelect_upload = false;
var show_dropSelect_account = false;
function change_dropSelect_width(id_bot, id_top, dropSelect_variable, size) {
	if (dropSelect_variable == false) {
		document.getElementById(id_bot).style.visibility = "visible";
		document.getElementById(id_bot).style.width = (document.getElementById(id_top).clientWidth * size) + "px";
		return dropSelect_variable = true;
	}
	else if (dropSelect_variable == true) {
		document.getElementById(id_bot).style.visibility = "hidden";
		return dropSelect_variable = false;
	}
}

function which_upload_option() {
  if (users_email != "") {
    document.getElementById("upload_modal").click();
  }
  else if (users_email == "") {
    document.getElementById("upload_logX").click();
  }
}

function if_user_in_dropSelect() {
  if (users_email != "") {
    change_dropSelect_width('upload_button_text', 'custom_view', show_dropSelect_account, 1.5);
    show_dropSelect_upload = change_dropSelect_width('upload_button_text', 'custom_view', show_dropSelect_account, 1.5);
  }
}

function delete_fill() {
  // Fills the manage XML modal with all available XMLs to delete from an account
  $("#delete_fill").empty(); // Empties the manage XML modal every time it is loaded
  for (i = 0; i < title_list.length; i++) {
    // Fills the manage XML modal with available XMLs on the account
    $("#delete_fill").append('<input type="checkbox" id="deleteBox_' + i + '" value="' + title_list[i] + '"> ' + title_list[i] + '</input><br>');
  }
}

function delete_selectedXML() {
  for (i = 0; i < title_list.length; i++) {
    var deleteBox_id = "deleteBox_" + i; // Find id of what is being called
    if (document.getElementById(deleteBox_id).checked == true) {
      $.ajax({
        url: "http://bar.utoronto.ca/~asher/efp_seq_userdata/delete_xml.php?user=" + users_email + "&file=" + match_title[document.getElementById(deleteBox_id).value]
      });
    }
  }
}

var warningActive_index = "nope";
function showWarning_index() {
  if (warningActive_index == "nope") {
    document.getElementById("warning_index").className = "warning_index";
    warningActive_index = "yes";
  }
  else if (warningActive_index == "yes") {
    hideWarning_index();
  }
}

function hideWarning_index() {
  document.getElementById("warning_index").className = "warning_nope_index";
  warningActive_index = "nope";
}

function manage_DownloadXML() {
  for (i = 0; i < title_list.length; i++) {
    var downloadBox_id = "deleteBox_" + i; // Find id of what is being called
    if (document.getElementById(downloadBox_id).checked == true) {
      $('#downloadXML')
        .attr('href', dataset_dictionary[document.getElementById(downloadBox_id).value])
        .attr('download', document.getElementById(downloadBox_id).value + '.xml');
      document.getElementById("downloadXML_button").click();
    }
  }
}

var table_base = "\t\t<tr>\n\t\t\t<th>Title*</th>\n\t\t\t<th>Description*</th>\n\t\t\t<th>Record Number *</th>\n\t\t\t<th>RNA-Seq Data/BAM file repository link*</th>\n\t\t\t<th>Repository type*</th>\n\t\t\t<th>Publication Link</th>\n\t\t\t<th>SRA/NCBI Link</th>\n\t\t\t<th>Total Reads Mapped*</th>\n\t\t\t<th>Read Map Method</th>\n\t\t\t<th>Species*</th>\n\t\t\t<th>Tissue*</th>\n\t\t\t<th>Tissue subunit*</th>\n\t\t</tr>\n";

function fill_tableCSV() {
  $("#XMLtoCSVtable").empty();
  for (i = 0; i < title_list.length; i++) {
    var downloadBox_id = "deleteBox_" + i; // Find id of what is being called
    $.ajax({
        url: dataset_dictionary[document.getElementById(downloadBox_id).value],
        dataType: 'xml',
        failure: function(xml_data) {
          console.log("Failed at opening XML for conversion into a CSV file. Please contact an admin");
        },
        success: function(xml_data) {
          var $xmltitle = $(xml_data).find("rnaseq_experiments");
          $xmltitle.each(function() {
            fileTitle = $(this).attr('xmltitle');
            if (fileTitle == "" || fileTitle == "Uploaded dataset") {
              fileTitle = "Uploaded dataset";
            }
            fileTitle = fileTitle.split(' ').join('_')
          });
          var $title = $(xml_data).find("bam_file");
          var table_add = "";
          table_add += "<table id='" + fileTitle + "'>\n\t<tbody>\n";
          //console.log(table_add);
          table_add += "\t\t<caption>" + fileTitle + "</caption>\n";
          //console.log(table_add);
          table_add += table_base;
          //console.log(table_add);
          $title.each(function() {
              table_add += "\t\t<tr>\n"
              var title = $(this).attr('title');
              table_add += "\t\t\t<td>" + title + "</td>\n";
              var desc = $(this).attr('desc');
              table_add += "\t\t\t<td>" + desc + "</td>\n";
              var record_number = $(this).attr('record_number');
              table_add += "\t\t\t<td>" + record_number + "</td>\n";
              var bam_link = $(this).attr('bam_link');
              table_add += "\t\t\t<td>" + bam_link + "</td>\n";
              var bam_type = $(this).attr('bam_type');
              table_add += "\t\t\t<td>" + bam_type + "</td>\n";
              var publication_link = $(this).attr('publication_link');
              table_add += "\t\t\t<td>" + publication_link + "</td>\n";
              var publication_url = $(this).attr('publication_url');
              table_add += "\t\t\t<td>" + publication_url + "</td>\n";
              var total_reads_mapped = $(this).attr('total_reads_mapped');
              if (total_reads_mapped == null || total_reads_mapped == "") {
                total_reads_mapped = "1";
              }
              table_add += "\t\t\t<td>" + total_reads_mapped + "</td>\n";
              var read_map_method = $(this).attr('read_map_method');
              table_add += "\t\t\t<td>" + read_map_method + "</td>\n";
              var species = $(this).attr('species');
              table_add += "\t\t\t<td>" + species + "</td>\n";
              var svgname = $(this).attr('svgname');
              table_add += "\t\t\t<td>" + svgname + "</td>\n";
              var svg_subunit = $(this).attr('svg_subunit');
              table_add += "\t\t\t<td>" + svg_subunit + "</td>\n";
              table_add += "\t\t</tr>\n"
          })
          table_add += "\t</tbody>\n</table>";
          //console.log(table_add);
          document.getElementById("XMLtoCSVtable").innerHTML += table_add;
        }
      })
  }
}

function download_XMLtableCSV() {
  for (i = 0; i < title_list.length; i++) {
    var downloadBox_id = "deleteBox_" + i; // Find id of what is being called
    if (document.getElementById(downloadBox_id).checked == true) {
      var tableTitle = document.getElementById(downloadBox_id).value.split(' ').join('_');
      $("#" + tableTitle).tableToCSV();
    }
  }
}

var downloadIndexTable_base = "\t\t<tr>\n\t\t\t<th>Title</th>\n\t\t\t<th>ID number</th>\n\t\t\t<th>Tissue</th>\n\t\t\t<th>Tissue subunit</th>\n\t\t\t<th>Locus</th>\n\t\t\t<th>bp Length</th>\n\t\t\t<th>bp Start site</th>\n\t\t\t<th>bp End site</th>\n\t\t\t<th>Total number of reads</th>\n\t\t\t<th>Reads mapped to locus</th>\n\t\t\t<th>PCC</th>\n\t\t\t<th>RPKM</th>\n\t\t</tr>\n";
function download_mainTableCSV() {
  populate_efp_modal(1);
  $("#hiddenDownloadModal_table").empty();
  var downlodaIndexTable_str = "<table id='downloadIndexTable'>\n\t<tbody>\n";
  downlodaIndexTable_str += "\t\t<caption>" + document.getElementById("xmldatabase").value + "</caption>\n";
  downlodaIndexTable_str += downloadIndexTable_base;
  for (i = 0; i < filtered_2d_title.length; i++) {
    downlodaIndexTable_str += "\t\t<tr>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + filtered_2d_title[i] + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + filtered_2d_id[i] + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + filtered_2d_tissue[i] + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + filtered_2d_subtissue[i] + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + filtered_2d_locus[i] + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + String(filtered_2d_bpLength[i]) + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + String(filtered_2d_bpStart[i]) + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + String(filtered_2d_bpEnd[i]) + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + filtered_2d_totalReads[i] + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + String(filtered_2d_mappedReads[i]) + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + filtered_2d_PCC[i] + "</td>\n";
    downlodaIndexTable_str += "\t\t\t<td>" + String(efp_RPKM_values[i]) + "</td>\n";
    downlodaIndexTable_str += "\t\t</tr>\n";
  }
  downlodaIndexTable_str += "\t</tbody>\n</table>";
  document.getElementById("hiddenDownloadModal_table").innerHTML += downlodaIndexTable_str;
  $("#hiddenDownloadModal_table").tableToCSV();
}

$(document).ready(function() {
    // On load, validate input
    locus_validation();
    yscale_validation();
    rpkm_validation();

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
    populate_table(1); // status 1 forces rna-seq api to return cached data for fast initial load
    // populate_efp_modal(1); // Shouldn't be called here, only when the button is pressed

    if (gene_structure_colouring_element == null) {
        gene_structure_colouring_element = document.getElementById("flt1_thetable").parentElement;
    }
    gene_structure_colouring_element.innerHTML = "";
    var img_created = document.createElement('img');
    img_created.src = 'data:image/png;base64,' + exon_intron_scale;
    img_created.style = 'margin-top: 10px; float: right; margin-right: 10px;';
    gene_structure_colouring_element.appendChild(img_created);
});
