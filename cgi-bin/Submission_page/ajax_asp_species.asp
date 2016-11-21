<%
response.expires=-1
dim a(30)
'Not my code. code taken from: http://www.w3schools.com/ajax/ajax_asp.asp
a(1)="Arabidopsis thaliana"
a(2)="Selaginella moellendorffi"
a(3)="Brachypodium distachyon"
a(4)="Setaria viridis"
a(5)="Lotus japonicus"
a(6)="Maize"
a(7)="Nicotiana benthamiana"
a(8)="Oryza sativa"
a(9)="Caenorhabditis elegans"
a(10)="Saccharomyces cerevisiae"
a(11)="Tobacco mosaic virus"
a(12)="Escherichia coli"
a(13)="Bacillus subtilis"
a(14)="Pseudomonas fluorescens"
a(15)="Human"
a(16)="Mus muculus"

'get the q parameter from URL
q=ucase(request.querystring("q"))

'lookup all hints from array if length of q>0
if len(q)>0 then
  hint=""
  for i=1 to 30
    if q=ucase(mid(a(i),1,len(q))) then
      if hint="" then
        hint=a(i)
      else
        hint=hint & " , " & a(i)
      end if
    end if
  next
end if

'Output "no suggestion" if no hint were found
'or output the correct values
if hint="" then
  response.write("no suggestion")
else
  response.write(hint)
end if
%>
