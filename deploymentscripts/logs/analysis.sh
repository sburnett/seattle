cp 20* log
ls 20* > results.txt
cat log | grep "PO\!" | awk {'print $2'} > `ls 20*`listFailed
mv 20* archive
echo "Good:" >> results.txt; cat log | grep "GOOD" | wc | awk '{print $2}' >> results.txt
echo "Scp failed:" >> results.txt; cat log | grep "scp " | wc | awk '{print $2}' >> results.txt
echo "Didn't pass all of the tests:" >> results.txt; cat log | grep "PO!" | wc | awk '{print $2}' >> results.txt
cat log | grep "PO\!" | awk {'print $2'}