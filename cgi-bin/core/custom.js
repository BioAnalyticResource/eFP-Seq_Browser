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
//Code taken from: http://stackoverflow.com/questions/37699927/file-not-uploading-in-file-reader
var default_url = 'cgi-bin/data/bamdata_amazon_links.xml';
var base_src = 'cgi-bin/data/bamdata_amazon_links.xml';
var upload_src = '';


//Following lines are used to count and determine how many BAM entries are in the XML file
var count_bam_entries_in_xml = 0;

var xhr = new XMLHttpRequest();
xhr.open( 'GET', base_src, true );
xhr.onreadystatechange = function ( e ) {
    if ( xhr.readyState == 4 && xhr.status == 200 )
        count_bam_entries_in_xml = xhr.responseXML.getElementsByTagName( "bam_file" ).length ;
        document.getElementById("testing_code").innerHTML = count_bam_entries_in_xml;
};
xhr.send( null );

document.getElementById("testing_count").innerHTML = count_bam_entries_in_xml;

function count_bam_num () {
  var xhr = new XMLHttpRequest();
  xhr.open( 'GET', base_src, true );
  xhr.onreadystatechange = function ( e ) {
      if ( xhr.readyState == 4 && xhr.status == 200 )
          count_bam_entries_in_xml = xhr.responseXML.getElementsByTagName( "bam_file" ).length ;
          document.getElementById("testing_code").innerHTML = count_bam_entries_in_xml;
  };
  xhr.send( null );

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
document.getElementById("testing_mobile").innerHTML = testmobile();

if (testmobile() == true) {
  document.getElementById("correctspacing").style.display="none";
  document.getElementById("feedback_button").style.display="none";
  document.getElementById("help_button").style.display="none";
  document.getElementById("butbarborder").style.display="none";
  //document.getElementById("middle_buttons").style.display="none";
  document.getElementById("uploaddata").style.display="none";
  document.getElementById("generatedata").style.display="none";
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
    if (progress_percent < 90) {
      document.getElementById("loading_screen").className = "loading";
      document.getElementById("body_of").className = "body_of_loading";
    }
    else if (progress_percent > 90) {
      document.getElementById("loading_screen").className = "loading done_loading";
      document.getElementById("body_of").className = "body_of_loading body_of_loading_done";
      stop_generating_loading();
    }
  }, 50);
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

    var colouring_part = "all";

    for (var i = 0; i < exp_to_colouring_part.length; i++) {
        if (id.replace("_svg", "") == exp_to_colouring_part[i][0]) {
            colouring_part = exp_to_colouring_part[i][1];
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
function colour_svgs_now(mode = $('input[type="radio"][name="svg_colour_radio_group"]:checked').val()) {
    //console.log("colour_svgs_now function is called with mode = " + mode);
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
}

/* Updates the radio button <DIV> with new variants images. */
function variants_radio_options(status) {
    get_input_values();
    $.ajax({
        url: 'http://bar.utoronto.ca/~ppurohit/RNA-Browser/cgi-bin/get_gene_structures.cgi?locus=' + locus,
        dataType: 'json',
        success: function(gene_res) {
            // Update locus_start and locus_end
            locus_start = gene_res['locus_start'];
            locus_end = gene_res['locus_end'];
            splice_variants = JSON.stringify(gene_res['splice_variants']);
            populate_table(status);

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
var rnaseq_image_url = "http://ec2-52-70-232-122.compute-1.amazonaws.com/RNA-Browser/cgi-bin/webservice.cgi?tissue=";
var match_drive = "";
//var testing_rnaseq_image = 0;
var progress_percent = 0
function rnaseq_images(status) {
    rnaseq_success = 0;
    //date_obj2 = new Date();
    //rnaseq_success_start_time = date_obj2.getTime(); // Keep track of start time
    get_input_values();
    if (rnaseq_calls.length == count_bam_entries_in_xml) {
        for (var i = 0; i < count_bam_entries_in_xml; i++) {
            if (bam_type_list[i] == "Google Drive") {
              var myRegexp = /^https:\/\/drive.google.com\/drive\/folders\/(.+)/g;
              var linkString = drive_link_list[i];
              match_drive = myRegexp.exec(linkString);
              rnaseq_image_url = "http://142.150.214.168/~asher/webservices/RNA-Browser/cgi-bin/webservice_gdrive.cgi?gdrive=" + match_drive[1] + "&tissue=";
              //testing_rnaseq_image += 1;
            }

            else {
              rnaseq_image_url = "http://ec2-52-70-232-122.compute-1.amazonaws.com/RNA-Browser/cgi-bin/webservice.cgi?tissue=";
            }

            $.ajax({
                url: rnaseq_image_url + rnaseq_calls[i][0] + '&record=' + rnaseq_calls[i][1] + '&locus=' + locus + '&variant=1&start=' + locus_start + '&end=' + locus_end + '&yscale=' + yscale_input + '&status=' + status + '&struct=' + splice_variants,
                dataType: 'json',
                failure: function(failure_response) {
                    $('#failure').show();
                },
                success: function(response_rnaseq) {
                    if (locus != response_rnaseq['locus']) {
                        console.log("ERROR: " + locus + "'s RNA-Seq API request returned with data for some other locus.");
                    }
                    // Update the progress bar
                    if (response_rnaseq['status'] == 200) {
                        rnaseq_success++;
                        date_obj3 = new Date();
                        rnaseq_success_current_time = date_obj3.getTime(); // Keep track of start time
                        progress_percent = rnaseq_success / count_bam_entries_in_xml * 100;
                        $('div#progress').width(progress_percent + '%');
                        document.getElementById('progress_tooltip').innerHTML = rnaseq_success + " / count_bam_entries_in_xml requests completed<br/>Load time <= " + String(round(parseInt(rnaseq_success_current_time - rnaseq_success_start_time) / (1000 * 60))) + " mins.";
                        //console.log("Requests = " + String(rnaseq_success) + ", time delta = " + String(parseInt(rnaseq_success_current_time - rnaseq_success_start_time)));
                    } else {
                        $('#failure').show();
                        console.log("ERROR CODE = " + response_rnaseq['status'] + " returned for " + locus + " RNA-Seq data.");
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
                    document.getElementById(response_rnaseq['record'] + '_rnaseq_img').src = 'data:image/png;base64,' + response_rnaseq['rnaseqbase64'];
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
        }
    }
}

window.setInterval(function(){
  document.getElementById("testing_progress").innerHTML = progress_percent
}, 50);

/* Gets the BAM locator XML to create + populate the table. Leeps track of all RNA-Seq calls it will have to make. */
var bam_type_list = []
var drive_link_list = []

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
    bam_type_list = []
    drive_link_list = []

    // Insert table headers
    $("#thetable").append('<thead><tr>' +
        '<th class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 250px;">Title<div class="arrowdown arrowup"></div></th>' +
        '<th class="" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 460px;">RNA-Seq Coverage</th>' +
        '<th class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;">PCC</th>' +
        '<th id="eFP_th" class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 100px;">eFP (RPKM)</th>' +
        '<th class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 75px;">RPKM</th>' +
        '<th class="sortable arrows" style="border: 1px solid #D3D3D3; background-color: #F0F0F0; width: 275px;">Details</th>' +
        '</tr></thead>' +
        '<tbody></tbody>');

    $.ajax({
        url: base_src,
        dataType: 'xml',
        success: function(xml_res) {
            var $title = $(xml_res).find("bam_file");
            $title.each(function() { // Iterate over each subtag inside the <file> tag.
                // Extract information
                var title = $(this).attr('title');
                var description = $(this).attr('desc');
                var svg = $(this).attr('svgname');
                var svg_part = $(this).attr('svg_subunit');
                var experimentno = $(this).attr('record_number');
                var url = $(this).attr('publication_url');
                var publicationid = $(this).attr('publication_link');
                var numberofreads = $(this).attr('total_reads_mapped');
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
                if ($(this).attr('bam_type') == "Amazon AWS") {
                  var tissue = $(this).attr('bam_link').split("/")[8];
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
                // Append title <td>
                append_str += '<td style="width: 250px; font-size: 12px;">' + title + '</td>\n';
                // Append RNA-Seq and Gene Structure images (2 imgs) in one <td>
                append_str += '<td style="width: 460px;">' + '<img id="' + experimentno + '_rnaseq_img" width="450px" height="50px" class="rnaseq_img" src="' + img_loading_base64 + '" /><br/>' + '<img id="' + experimentno + '_gene_structure_img" width="450px" height="8px" class="gene_structure_img" src="' + img_gene_struct_1 + '" />' + '</td>\n';
                // Append the PCC <td>
                append_str += '<td id="' + experimentno + '_pcc' + '" class="pcc_value" style="font-size: 10px; width: 50px; ">' + -9999 + '</td>';
                // Append the approparite SVG with place holder sorting number in front of it .. all in one <td>
                append_str += '<td style="width:  75px;">' + '<div id="' + experimentno + '_svg' + '" width="75" height="75" style="width: 75px; height: 75px; max-width: 75px; max-height: 75px;">' + document.getElementById(svg.substring(4).replace(".svg", "_svg")).innerHTML + '</div>' + '<div class="mdl-tooltip" for="' + experimentno + '_svg' + '">' + svg.substring(4).replace(".svg", "") + '</div></td>\n';
                // Append abs/rel RPKM
                append_str += '<td id="' + experimentno + '_rpkm' + '" style="font-size: 10px; width: 50px; ">-9999</td>';
                // Append the details <td>
                append_str += '<td style="width: 200px; font-size: 12px;">' + description + '<br/>' + '<a href="' + url + '" target="blank">' + 'NCBI SRA' + '</a>; <a href="' + publicationid + '" target="blank">PubLink</a>' + '<br/><a href="javascript:(function(){$(\'#' + url.substring(44) + '\').toggle();})()"></a><div id="' + url.substring(44) + '" >Total reads = ' + numberofreads + '.<br/>Controls: ' + links + '.<br/>Species: ' + species + '</div></td>\n';
                append_str += '</tr>';

                // Append the <tr> to the table
                $("#thetable").append(append_str);

                exp_info.push([experimentno + '_svg', svg_part, controls, 0, 0, 0, 0]);

                if (rnaseq_calls.length == count_bam_entries_in_xml) {
                    rnaseq_images(status);
                }
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
        columns_exact_match: [false, false, true, false, true, false],
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

    if (gene_structure_colouring_element == null) {
        gene_structure_colouring_element = document.getElementById("flt1_thetable").parentElement;
    }
    gene_structure_colouring_element.innerHTML = "";
    var img_created = document.createElement('img');
    img_created.src = 'data:image/png;base64,' + exon_intron_scale;
    img_created.style = 'margin-top: 10px; float: right; margin-right: 10px;';
    gene_structure_colouring_element.appendChild(img_created);
});
