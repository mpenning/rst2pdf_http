This is a helper to run [rst2pdf](https://github.com/rst2pdf/rst2pdf), including serving the final pdf file over python's http.server

# Problem Statement
If you are like me, you have a linux vm running under VMWare that you use to do things that you wouldn't do under windows; I edit most of my text files in linux, including many rst files that I convert to pdf (using [rst2pdf](https://github.com/rst2pdf/rst2pdf)).

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

In this topology, I edit files on 10.0.0.6 but consume them in Windows; automagically serving the PDF via http in the linux vm is helpful so I can see the rendered pdf immediately after editing.


# Typical Use-case

Assume I am building a pdf for a doocument saved as `CoverLetter_20230927.rst` with an 8-point font, and want to serve it on port 8080....

```
$ make all
...

$ python rst2pdf_http.py -f ../CoverLetter_20230927.rst -s 8 -i -w 8080

rst2pdf --stylesheet-path=/home/my_user/.rst2pdf/ --stylesheets=rst2pdf_stylesheet.yml CoverLetter_20230927.rst -o CoverLetter_20230927.pdf
/home/my_user/rst2pdf_http.py:284: UserWarning: Source and destination are the same file; no file copy was required.
  warnings.warn("Source and destination are the same file; no file copy was required.")

Local URL http://10.0.0.6:8080/
Local URL http://[fe80::20c:29ff:fed9:91f9]:8080/

Serving HTTP on :: port 8080 (http://[::]:8080/) ...
```

## Automate Documentation Components

This project can automate parts of your document.  My use-case is generating a Restructured-text file with the contents of today's date as words in a file named ``~/.rst2pdf/custom_rst_imports/today_as_words.rst``.  Instead of remembering to manually edit a document with today's date, I can just import a file with:

```
.. include:: /home/my_user/.rst2pdf/custom_rst_imports/localtime_today_as_words.rst
```

# FAQ

- Can I copy and run this script outside this git repo?  Maybe, but some things will break; you really shouldn't do that.
- Do I need to run 'make all' every time?  You only need to run 'make all' once per rst2pdf_http.py version.
- When I use `..include:: foo` in my RestructuredText document, why do I see this error: `(SEVERE/4) Problems with "include" directive path:`?  Your RestructuredText import path in your document is wrong.
- Is this script supported on a Read-Only filesystem?  No.
- Can you use this with non-RestructuredText files?  Yes, but PDF conversion is only implemented for RestructuredText.  If a non-RestructuredText file is used with `-f`, then the file is served with the HTTP server as it was originally found.

# Full Syntax

```
$ python rst2pdf_http.py --help

usage: rst2pdf_http.py [-h] [-f START_FILEPATH] [-w WEBSERVER_PORT] [-i] [-n {Mono,Sans,Serif}] [-s {10,12,14}] [-a {Bold,Italic,Oblique}] [-d STYLESHEET_DIRECTORY]
                       [-e STYLESHEET_FILENAME] [-t TERMINAL_ENCODING] [-v]

Build a PDF from RestructuredText and serve via Go HTTP

optional arguments:
  -h, --help            show this help message and exit

required:
  -f START_FILEPATH, --start_filepath START_FILEPATH
                        start filepath.

optional:
  -w WEBSERVER_PORT, --webserver_port WEBSERVER_PORT
                        Start a webserver on this port.
  -n {Mono,Sans,Serif}, --font_name {Mono,Sans,Serif}
                        rst2pdf font name; the default is 'Serif'.
  -s {10,12,14}, --font_size {10,12,14}
                        rst2pdf font size; default is '12'.
  -a {Bold,Italic,Oblique}, --font_attrs {Bold,Italic,Oblique}
                        rst2pdf font attrs; default is no font attributes.
  -d STYLESHEET_DIRECTORY, --stylesheet_directory STYLESHEET_DIRECTORY
                        rst2pdf stylesheet_directory; the default is '/home/mpenning/.rst2pdf/'.
  -e STYLESHEET_FILENAME, --stylesheet_filename STYLESHEET_FILENAME
                        rst2pdf stylesheet_filename; the default is 'rst2pdf_stylesheet.yml'.
  -t TERMINAL_ENCODING, --terminal_encoding TERMINAL_ENCODING
                        .
  --no_write_rst_imports
                        Don't write the canned rst imports.
  -v, --version         Output the script version number to stdout.

```
