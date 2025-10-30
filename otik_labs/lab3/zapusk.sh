bash -lc "set -e; 
cd /home/smartkettle/Documents/otik/otik_labs/lab3; 
printf 'tut kakoito tekst nu realno' > q.txt;
./n1.py encode q.txt r.otik;
./n1.py decode r.otik q_out.txt;
diff -s q.txt q_out.txt || true"