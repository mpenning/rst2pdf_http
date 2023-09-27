
"""

"""
from functools import wraps
# subprocess.run() is generally-recommended instead of subprocess.call()
from subprocess import run, call
import argparse
import tempfile
import warnings
import shutil
import shlex
import yaml
import sys
import os
import re


VALID_FONT_ATTRS = set({"Bold", "Italic", "Oblique"})
VALID_FONT_NAMES = set({"Mono", "Sans", "Serif",}) # Sans is similar to Arial
VALID_FONT_SIZES = set({10, 12, 14,})
DEFAULT_STYLESHEET_DIRECTORY = os.path.expanduser("~/.rst2pdf/")
DEFAULT_STYLESHEET_FILENAME = "rst2pdf_stylesheet.yml"
DEFAULT_STYLESHEET_FONTATTR = []
DEFAULT_STYLESHEET_FONTNAME = "Serif"
DEFAULT_STYLESHEET_FONTSIZE = 12
DEFAULT_TERMINAL_ENCODING = "UTF-8"

LOGURU_IMPORTED = None
try:
    from loguru import logger
    LOGURU_IMPORTED = True
    logger.info("loguru imported")
except (NameError, ModuleNotFoundError):
    LOGURU_IMPORTED = False
    print("loguru NOT imported")

    class logger(object):
        """
        Dummy loguru.logger.catch() implementation.
        """
        def catch(reraise=False):
            """
            Catch of the logger.catch() class-method stub.

            Usage:

                @logger.catch(reraise=True)
                def main():
                    pass
            """
            def outside_wrapper(wrapped_func):
                @wraps(wrapped_func)
                def inner_call(*args, **kwargs):
                    # add some meaningful manipulations later
                    response = wrapped_func(*args, **kwargs)
                    return response

                @wraps(wrapped_func)
                def inner_call_new(*args, **kwargs):
                    # add some meaningful manipulations later
                    response = wrapped_func(*args, **kwargs)
                    return response

                if wrapped_func is object.__new__:
                    return inner_call_new
                else:
                    return inner_call
            return outside_wrapper

class Stylesheet(object):

    # This is on the Stylesheet() class
    @logger.catch(reraise=True)
    def __init__(self, font_name, font_size=12, font_attrs=None):
        """
        rst2pdf Stylesheet.
        """
        if font_attrs is None:
            font_attrs = []
        elif isinstance(font_attrs, list):
            for attr in font_attrs:
                # rst2pdf doesnt use 'Normal'... it is internal to this script
                if attr == "Normal":
                    continue
                if attr not in VALID_FONT_ATTRS:
                    raise ValueError(f"`{attr}` is an invalid font attribute.  Choose from: {VALID_FONT_ATTRS}.")
        else:
            raise ValueError(f"Stylesheet(font_attrs='''{font_attrs}''' {type(font_attrs)}) must be a `list` or None.")

        self.font_name = font_name
        self.font_size = font_size
        self.font_attrs = font_attrs

    # This is on the Stylesheet() class
    def __repr__(self):
        return f"""<Stylesheet font_name: {self.font_name}, font_size: {self.font_size}, font_attrs: {self.font_attrs}>"""

    # This is on the Stylesheet() class
    @logger.catch(reraise=True)
    def save_stylesheet_yaml(self, directory=DEFAULT_STYLESHEET_DIRECTORY, filename=DEFAULT_STYLESHEET_FILENAME):
        """dump `data` as an rst2pdf YAML stylesheet"""
        try:
            os.makedirs(f"{directory}")
        except Exception:
            pass
        filepath = os.path.normpath(f"{directory}/{filename}")
        data = self.get_rst2pdf_data_dict(font_name=self.font_name)
        with open(filepath, 'w') as fh:
            yaml.dump(data, fh, default_flow_style=False)

    # This is on the Stylesheet() class
    @logger.catch(reraise=True)
    def get_rst2pdf_data_dict(self, font_name=None):
        return {
            "styles": {
                #"fontName": self.get_rst2pdf_fontName(font_name=font_name),
                "base": {
                        "alignment": "LEFT",
                        "allowOrphans": False,
                        "backColor": None,
                        "borderColor": None,
                        "borderPadding": 0,
                        "borderRadius": None,
                        "borderWidth": 0,
                        "commands": [],
                        "firstLineIndent": 0,
                        "fontName": self.get_rst2pdf_fontName(font_name=font_name),
                        "fontSize": self.font_size,
                        "hyphenation": False,
                        "leading": self.font_size,
                        "leftIndent": 0,
                        "parent": None,
                        "rightIndent": 0,
                        "spaceAfter": 0,
                        "spaceBefore": 0,
                        "strike": False,
                        "textColor": "black",
                        "underline": False,
                        "wordwrap": None,
                },
            },
        }

    # This is on the Stylesheet() class
    @logger.catch(reraise=True)
    def get_rst2pdf_fontName(self, font_name=""):
        """Get the rst2pdf fontName, which usually looks like: 'fontMonoBoldItalic'."""
        if isinstance(font_name, str):
            for ii in sorted(self.font_attrs):
                font_name += ii
            if font_name[0:3]=="font":
                return font_name
            else:
                font_name = "font" + font_name
                return font_name
        else:
            raise ValueError()


@logger.catch(reraise=True)
def parse_cli_args():
    """
    Reference: https://docs.python.org/3/library/argparse.html
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--stylesheet_directory",
        type=str,
        default=DEFAULT_STYLESHEET_DIRECTORY,
        choices=None,
        action="store",
        help=f"rst2pdf stylesheet_directory; the default is '{DEFAULT_STYLESHEET_DIRECTORY}'.",
    )
    parser.add_argument("-e", "--stylesheet_filename",
        type=str,
        default=DEFAULT_STYLESHEET_FILENAME,
        choices=None,
        action="store",
        help=f"rst2pdf stylesheet_filename; the default is '{DEFAULT_STYLESHEET_FILENAME}'.",
    )
    parser.add_argument("-n", "--font_name",
        type=str,
        default=DEFAULT_STYLESHEET_FONTNAME,
        choices=sorted(VALID_FONT_NAMES),
        action="store",
        help=f"rst2pdf font name; the default is '{DEFAULT_STYLESHEET_FONTNAME}'.",
    )
    parser.add_argument("-s", "--font_size",
        type=int,
        default=DEFAULT_STYLESHEET_FONTSIZE,
        choices=sorted(VALID_FONT_SIZES),
        action="store",
        help="rst2pdf font size; default is '12'.",
    )
    parser.add_argument("-a", "--font_attrs",
        type=str,
        default=DEFAULT_STYLESHEET_FONTATTR,
        choices=sorted(VALID_FONT_ATTRS),
        action="append",
        help="rst2pdf font attrs; default is no font attributes.",
    )
    parser.add_argument("-r", "--rst_prefix",
        type=str,
        default=None,
        choices=None,
        action="store",
        help="restructured-text filename prefix; example: if rst file is 'my_document.rst', the prefix is 'my_document'",
    )
    parser.add_argument("-w", "--webserver_port",
        type=int,
        default=0,
        choices=None,
        action="store",
        help="Start a webserver on this port."
    )
    parser.add_argument("-t", "--terminal_encoding",
        type=str,
        default="UTF-8",
        choices=None,
        action="store",
        help="."
    )
    args = parser.parse_args()
    return args

@logger.catch(reraise=True)
def posix_list_local_ipaddrs(terminal_encoding=None):
    ipv46_addrs = []
    cmd = "ifconfig -a"
    output_namedtuple = run(
        shlex.split(cmd),
        shell=False,
        capture_output=True,
    )
    for line in output_namedtuple.stdout.splitlines():
        mm = re.search(r"\s*(inet|inet6)\s+(\S+)", line.decode(terminal_encoding))
        if mm is not None:
            ipv46_addrs.append(mm.group(2))

    if len(ipv46_addrs) > 0:
        return ipv46_addrs
    else:
        raise ValueError("No ipv4_addrs or ipv6_addrs found.")

@logger.catch(reraise=True)
def list_local_ipaddrs(**kwargs):
    # platforms from
    #     https://stackoverflow.com/a/13874620
    pltfm = sys.platform
    if pltfm == 'linux' or pltfm == 'linux2':
        return posix_list_local_ipaddrs(**kwargs)
    elif pltfm == 'cygwin':
        return posix_list_local_ipaddrs(**kwargs)
    elif pltfm == 'darwin':
        return posix_list_local_ipaddrs(**kwargs)
    elif re.search(r"^freebsd", pltfm):
        return posix_list_local_ipaddrs(**kwargs)
    else:
        raise ValueError(f"Unsupported sys.platform: {pltfm}.")


if __name__=="__main__":
    args = parse_cli_args()
    obj = Stylesheet(font_name=args.font_name, font_size=args.font_size, font_attrs=args.font_attrs,)
    obj.save_stylesheet_yaml()
    rst2pdf_cmd = f"rst2pdf --stylesheet-path={args.stylesheet_directory} --stylesheets={args.stylesheet_filename} {args.rst_prefix}.rst -o {args.rst_prefix}.pdf"
    print(rst2pdf_cmd)
    output_namedtuple = run(
        shlex.split(rst2pdf_cmd),
        shell=False,
        capture_output=True,
    )


    #original_path = os.path.normpath(f"{args.rst_prefix}/{original_filename}")
    #original_path = os.path.normpath(f"{args.rst_prefix}")
    original_filename = os.path.normpath(f"{args.rst_prefix}".split('/')[-1]+".pdf")

    # Copy from original directory to current-working-directory...
    current_path = os.path.normpath(f"{os.getcwd()}/{original_filename}")
    try:
        shutil.copy(original_filename, current_path)
    except shutil.SameFileError:
        warnings.warn("Source and destination are the same file; no file copy was required.")

    # Copy from original directory to temporary-directory...
    with tempfile.TemporaryDirectory() as temp_dir:
        temporary_path = os.path.normpath(f"{temp_dir}/{original_filename}")
        try:
            shutil.copy(original_filename, temporary_path)
        except shutil.SameFileError:
            warnings.warn("Source and temporary destination are the same file; no file copy was required.")

        # List local http URLs and start a temporary webserver...
        if args.webserver_port > 0:
            print("")
            ipv46_addrs = list_local_ipaddrs(terminal_encoding=args.terminal_encoding)
            for v46addr in ipv46_addrs:
                if re.search(r"^(::1|127\.\d+\.\d+\.\d+)$", v46addr):
                    # I cant make the python webserver bind to linux loopback...
                    continue
                elif ":" in v46addr:
                    print(f"Local URL http://[{v46addr}]:{args.webserver_port}/")
                else:
                    print(f"Local URL http://{v46addr}:{args.webserver_port}/")

            print("")
            # Change to the temporary directory and start a webserver to serve locally...
            try:
                os.chdir(temp_dir)
                #return_code = call(f"python -m http.server --bind 0.0.0.0 {args.webserver_port}", shell=True)
                return_code = call(f"python -m http.server --bind :: {args.webserver_port}", shell=True)
            except KeyboardInterrupt:
                print("    Webserver interrupted by KeyboardInterrupt.")




