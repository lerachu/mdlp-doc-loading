#!/bin/bash
/opt/cprocsp/bin/amd64/certmgr -install  -provname "Crypto-Pro GOST R 34.10-2012 KC1 CSP" -pfx -file '/app/info/olalalala.pfx' -pin 12345678 -silent
#!/bin/bash
read -r line < /app/info/license.txt
/opt/cprocsp/sbin/amd64/cpconfig -license -license -set "$line"
python load_xml_app.py
