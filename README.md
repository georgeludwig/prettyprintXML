# prettyprintXML
You might get a very large (multi-gigabyte) XML file without a single CR/LF in it.
And when you try to view it, your editor crashes with an OOM error, in spite of the fact that you have plenty of system memory available.
This is because your editor is trying to read the file a line at a time, and has a baked-in line cache, of, say a single MB.
This is normally reasonable, until it tries to load a 6GB file, in which case it crashes with an OOM error even if you have 256GB of available RAM. 
You might then try insert appropriate CR/LFs by using your system-default XML tools to pretty-print to a new file...but your system default tools will also fail with an OOM error, for the same reason your editor failed. 

If this has happened to you, you'll want to use this program to do your pretty-printing.
