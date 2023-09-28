Helper to run rst2pdf, including serving the final pdf file over python's http.server

# Problem Statement
If you are like me, you have a linux vm running under vmware that you use to do things that you wouldn't do under windows; I edit most of my text files in linux, including many rst files that I convert to pdf (using rst2pdf).

This means I have a topology like this:

```
       ( public internet )
                |
        (Firewall + NAT)
                |
+---------------+--------------+
|                              |        <--- default gw      +--------------------+
|  Windows with VMWare Player  +-------{ private vnic }------+ ens33   linux vm   |
|                              |          10.0.0.0/24        |        10.0.0.6/24 |
+------------------------------+                             +--------------------+
```

In this topology, I edit files on 10.0.0.6 but consume them in Windows; automagically serving the PDF via http is helpful so I can see the rendered pdf immediately after editing.

# Typical Use-case

Assume I am building a pdf for a doocument saved as `CoverLetter_20230927.rst` and want to serve it on port 8080....

```
$ make build
...

$ python ./rst2pdf_builder.py -r CoverLetter_20230927 -w 8080

rst2pdf --stylesheet-path=/home/mpenning/.rst2pdf/ --stylesheets=rst2pdf_stylesheet.yml CoverLetter_20230927.rst -o CoverLetter_20230927.pdf
/home/mpenning/rst2pdf_http.py:284: UserWarning: Source and destination are the same file; no file copy was required.
  warnings.warn("Source and destination are the same file; no file copy was required.")

Local URL http://10.0.0.6:8080/
Local URL http://[fe80::20c:29ff:fed9:91f9]:8080/

Serving HTTP on :: port 8080 (http://[::]:8080/) ...
```

# Full Syntax

```
$ python rst2pdf_http.py -h
usage: rst2pdf_http.py [-h] [-d STYLESHEET_DIRECTORY] [-e STYLESHEET_FILENAME] [-n {Mono,Sans,Serif}] [-s {10,12,14}] [-a {Bold,Italic,Oblique}] [-r RST_PREFIX]
                       [-w WEBSERVER_PORT] [-t TERMINAL_ENCODING]

options:
  -h, --help            show this help message and exit
  -d STYLESHEET_DIRECTORY, --stylesheet_directory STYLESHEET_DIRECTORY
                        rst2pdf stylesheet_directory; the default is '/home/mpenning/.rst2pdf/'.
  -e STYLESHEET_FILENAME, --stylesheet_filename STYLESHEET_FILENAME
                        rst2pdf stylesheet_filename; the default is 'rst2pdf_stylesheet.yml'.
  -n {Mono,Sans,Serif}, --font_name {Mono,Sans,Serif}
                        rst2pdf font name; the default is 'Serif'.
  -s {10,12,14}, --font_size {10,12,14}
                        rst2pdf font size; default is '12'.
  -a {Bold,Italic,Oblique}, --font_attrs {Bold,Italic,Oblique}
                        rst2pdf font attrs; default is no font attributes.
  -r RST_PREFIX, --rst_prefix RST_PREFIX
                        restructured-text filename prefix; example: if rst file is 'my_document.rst', the prefix is 'my_document'
  -w WEBSERVER_PORT, --webserver_port WEBSERVER_PORT
                        Start a webserver on this port.
  -t TERMINAL_ENCODING, --terminal_encoding TERMINAL_ENCODING 
```
