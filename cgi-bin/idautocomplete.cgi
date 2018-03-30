#!/usr/bin/python

import cgi
import MySQLdb
import json

# Retrieve parameters
arguments = cgi.FieldStorage()
species = arguments['species'].value
term = arguments['term'].value

# Print header
print 'Content-Type: application/json\n'

try:
    if species == 'Arabidopsis_thaliana':
        con = MySQLdb.connect('localhost', 'hans', 'un1pr0t', 'eplant2')
        cur = con.cursor()
        
        # First add aliases
        query = 'SELECT agi,alias FROM agi_alias WHERE agi LIKE "%' + term + '%" OR alias LIKE "%' + term + '%" LIMIT 15;'
        cur.execute(query)
        output = []
        for row in cur:
            output.append(row[0] + "/" + row[1])

        # Now add names
        query = 'SELECT agi,name FROM agi_names WHERE agi LIKE "%' + term + '%" OR name LIKE "%' + term + '%" LIMIT 15;'
        cur.execute(query)
        for row in cur:
            output.append(row[0] + "/" + row[1])

        if len(output) < 15:
            query = 'SELECT geneId FROM tair10_gff3 WHERE type="gene" AND geneId LIKE "%' + term + '%" LIMIT ' + str(15 - len(output)) + ';'
            cur.execute(query)
            for row in cur:
                duplicate = False
                for identifier in output:
                    if identifier.upper().startswith(row[0].upper()):
                        duplicate = True
                        break
                if not duplicate:
                    output.append(row[0])
        print json.dumps(output)
except:
    print "{}"
