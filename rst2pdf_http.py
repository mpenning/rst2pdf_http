
"""

"""
# subprocess.run() is generally-recommended instead of subprocess.call()
from subprocess import run, call
from functools import wraps
import ipaddress
import argparse
import tempfile
import warnings
import pathlib
import shutil
import shlex
import yaml
import sys
import os
import re

from rich.console import Console
from loguru import logger

VALID_FONT_ATTRS = set({"Bold", "Italic", "Oblique"})
VALID_FONT_NAMES = set({"Mono", "Sans", "Serif",}) # Sans is similar to Arial
VALID_FONT_SIZES = set({10, 12, 14,})
DEFAULT_STYLESHEET_DIRECTORY = os.path.expanduser("~/.rst2pdf/")
DEFAULT_STYLESHEET_FILENAME = "rst2pdf_stylesheet.yml"
DEFAULT_STYLESHEET_FONTATTR = []
DEFAULT_STYLESHEET_FONTNAME = "Serif"
DEFAULT_STYLESHEET_FONTSIZE = 12
DEFAULT_TERMINAL_ENCODING = Console().encoding
DEFAULT_START_FILENAME_SUFFIX = "rst"

class dummy_property(object):
    """
    dummy_property.catch() implementation.
    """
    def catch(**dummy_catch_kwargs):
        """
        Catch of the logger.catch() class-method stub.

        Usage:

            @logger.catch(reraise=True)
            def main():
                pass
        """
        # Keep this `dummy_catch_kwargs` reference to ensure
        # what python vulture can pass at 100% unused-code
        # confidence...
        reraise = get(dummy_catch_kwargs, 'reraise', False)

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

def is_valid_ipv4addr(addr, raise_error=True):
    if isinstance(addr, str):
        try:
            ipaddress.IPv4Address(addr)
            return True
        except Exception:
            if raise_error:
                raise ValueError(f"{addr} is not a valid IPv4 Address.")
            else:
                return False
    else:
        if raise_error:
            raise ValueError(f"{addr} must be a string IPv4 address")
        else:
            return False

def is_valid_ipv6addr(addr, raise_error=True):
    if isinstance(addr, str):
        try:
            ipaddress.IPv6Address(addr)
            return True
        except Exception:
            if raise_error:
                raise ValueError(f"{addr} is not a valid IPv6 Address.")
            else:
                return False
    else:
        if raise_error:
            raise ValueError(f"{addr} must be a string IPv6 address")
        else:
            return False

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
        """Use PyYaml to save `get_rst2pdf_data_dict()` as an rst2pdf stylesheet"""
        try:
            os.makedirs(f"{directory}")
        except Exception:
            pass
        filepath = os.path.normpath(f"{directory}/{filename}")
        with open(filepath, 'w') as fh:
            yaml.dump(
                data=self.get_rst2pdf_data_dict(font_name=self.font_name),
                stream=fh,
                default_flow_style=False
            )

    # This is on the Stylesheet() class
    @logger.catch(reraise=True)
    def get_rst2pdf_data_dict(self, font_name=None):
        """
        Create the most essential rst2pdf stylesheet from scratch.
        """
        return {
            "styles": {
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
        if font_name in VALID_FONT_NAMES:
            pass
        else:
            raise ValueError(f"{font_name} is an invalid font name.")

        for ii in sorted(self.font_attrs):
            font_name += ii
        if font_name[0:3]=="font":
            return font_name
        else:
            font_name = "font" + font_name
            return font_name

class ThisApplication(object):

    @logger.catch(reraise=True)
    def __init__(self, start_filepath=None):
        """
        `start_filename` is the string filename.
        """

        self.check_file_exists(start_filepath)

        start_pathobj = pathlib.PurePosixPath(start_filepath)
        start_directory = pathlib.posixpath.dirname(start_filepath)

        start_filename = start_pathobj.parts[-1]
        start_filename_suffix = DEFAULT_START_FILENAME_SUFFIX
        start_filename_suffix = start_pathobj.suffix.split(".")[-1]
        start_filename_prefix = start_pathobj.stem
        current_directory = os.getcwd()

        if "." in start_filename_suffix:
            raise ValueError(f"This is an invalid suffix: '{start_filename_suffix}'")

        self.start_pathobj = start_pathobj
        self.start_directory = start_directory
        self.start_filepath = start_filepath
        self.start_filename = start_filename
        self.start_filename_suffix = start_filename_suffix
        self.start_filename_prefix = start_filename_prefix
        self.current_directory = current_directory
        self.current_filepath = os.path.normpath(f"{self.current_directory}/{start_filename}")

        if start_filename_suffix == "rst":
            self.finish_directory = start_directory
            self.finish_filepath = f"{start_filename_prefix}.pdf"
            self.finish_filename_prefix = start_filename_prefix
            self.finish_filename_suffix = "pdf"
            self.finish_filename = f"{start_filename_prefix}.{self.finish_filename_suffix}"
        else:
            self.finish_directory = start_directory
            self.finish_filepath = start_filepath
            self.finish_filename_prefix = start_filename
            self.finish_filename_suffix = start_filename_suffix
            self.finish_filename = start_filename


    @logger.catch(reraise=True)
    def create_stylesheet(self, directory=None, filename=None, font_name=None, font_size=None, font_attrs=None):
        ssobj = Stylesheet(font_name=font_name, font_size=font_size, font_attrs=font_attrs,)
        ssobj.save_stylesheet_yaml(directory=directory, filename=filename)

    @logger.catch(reraise=True)
    def convert_rst_to_pdf(self, stylesheet_directory=None, stylesheet_filename=None):
        if self.start_filename_suffix == "rst":
            self.check_file_exists(filepath=f"{self.start_filepath}")
            self.check_file_exists(filepath=f"{stylesheet_directory}/{stylesheet_filename}")

            rst2pdf_cmd = f"rst2pdf --stylesheet-path={stylesheet_directory} --stylesheets={stylesheet_filename} {self.start_filepath} -o {self.finish_filepath}"
            logger.info(f"{rst2pdf_cmd}")

            output_namedtuple = run(
                shlex.split(rst2pdf_cmd),
                shell=False,
                capture_output=True,
            )
            if output_namedtuple.returncode > 0:
                logger.error(output_namedtuple)
                raise OSError(output_namedtuple.stderr.strip())
            else:
                logger.debug(output_namedtuple)
                return True
        else:
            logger.warning(f"The start filename suffix is not 'rst'.  No conversion is implemented for '{self.start_filename_suffix}'.")
            return False

    @logger.catch(reraise=True)
    def check_file_exists(self, filepath=None):
        """
        Check whether `filepath` exists; if so, return True.
        """
        if not isinstance(filepath, str):
            raise ValueError(f"{filepath} must be a string.")

        abspath = os.path.abspath(os.path.expanduser(os.path.normpath(f"{filepath}")))
        logger.info(f"    filepath: {filepath}")
        logger.info(f"        checking: {abspath}")

        if os.path.exists(abspath):
            pass
        else:
            raise OSError(f"{abspath} must exist.")
        return True

    @logger.catch(reraise=True)
    def copy_file(self, src, dst):
        logger.debug(f"copy {src} {dst}")
        try:
            shutil.copy(src, dst)
            return True
        except shutil.SameFileError:
            warnings.warn("Source and destination are the same file; no file copy was required.")
            return False

    @logger.catch(reraise=True)
    def check_ipv46_addrs(self, ipv46_addrs):
        """
        Walk all the strings in ipv46_addrs and return True if they are all valid.

        Raise an error if one is not valid.
        """
        if not isinstance(ipv46_addrs, list):
            error = "`ipv46_addrs` must be a non-empty list."
            raise ValueError(error)

        if len(ipv46_addrs) == 0:
            error = "`ipv46_addrs` must be a non-empty list."
            raise ValueError(error)

        for addr in ipv46_addrs:
            # Raise an error if the address is invalid
            if not (is_valid_ipv4addr(addr, raise_error=False) or is_valid_ipv6addr(addr, raise_error=False)):
                raise ValueError(f"addr: {addr} is an invalid address.")

        return True

    @logger.catch(reraise=True)
    def start_webserver(self, local_ipv46_addrs=None, webserver_port=0):
        """
        Create a temporary directory, copy files into it, and start webserver on all sockets.
        """
        if webserver_port == 0:
            error = "Webserver port must not be 0"
            raise ValueError(error)

        start_filename = self.start_filename

        # Check the local ipv4 / ipv6 addresses for problems...
        self.check_ipv46_addrs(local_ipv46_addrs)

        with tempfile.TemporaryDirectory() as temp_dir:
            temporary_finish_path = os.path.normpath(f"{temp_dir}/{self.finish_filename}")
            try:
                self.copy_file(src=f"{self.start_filepath}", dst=temp_dir)
                self.copy_file(src=f"{self.finish_filename}", dst=temporary_finish_path)
            except shutil.SameFileError:
                warnings.warn("Source and temporary destination are the same file; no file copy was required.")

            print("")
            for v46addr in local_ipv46_addrs:
                # Skip binding to loopback addresses... this is pointless.  If it's sufficient to bind
                # to the loopback, then you dont need this script.
                if re.search(r"^(::1|127\.\d+\.\d+\.\d+)$", v46addr):
                    continue
                elif ":" in v46addr:
                    print(f"Local URL http://[{v46addr}]:{args.webserver_port}/")
                else:
                    print(f"Local URL http://{v46addr}:{args.webserver_port}/")

            ###############################################################
            # Change to the temporary directory and start the Golang
            #     webserver to serve files from `temp_dir` locally...
            ###############################################################
            try:
                return_code = call(
                    f"{os.getcwd()}/filesystem_webserver --webserverPort {webserver_port} --webserverDirectory {temp_dir}",
                    shell=True
                )
            except KeyboardInterrupt:
                print("    Webserver interrupted by KeyboardInterrupt.")

@logger.catch(reraise=True)
def parse_cli_args(sys_argv1):
    """
    Reference: https://docs.python.org/3/library/argparse.html
    """
    if isinstance(sys_argv1, list):
        pass
    else:
        raise ValueError("`sys_argv1` must be a list with CLI options from `sys.argv[1:]`")

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--start_filepath",
        type=str,
        default=None,
        choices=None,
        action="store",
        help="start filepath.",
    )
    parser.add_argument("-w", "--webserver_port",
        type=int,
        default=0,
        choices=None,
        action="store",
        help="Start a webserver on this port."
    )
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
    parser.add_argument("-t", "--terminal_encoding",
        type=str,
        default="UTF-8",
        choices=None,
        action="store",
        help="."
    )
    args = parser.parse_args(sys_argv1)
    return args

@logger.catch(reraise=True)
def nix_list_local_ipaddrs(terminal_encoding=None):
    """
    List the local ip addresses on a *nix machine with `ifconfig -a`.
    """
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
        return nix_list_local_ipaddrs(**kwargs)
    elif pltfm == 'cygwin':
        return nix_list_local_ipaddrs(**kwargs)
    elif pltfm == 'darwin':
        return nix_list_local_ipaddrs(**kwargs)
    elif re.search(r"^freebsd", pltfm):
        return nix_list_local_ipaddrs(**kwargs)
    else:
        raise ValueError(f"Unsupported sys.platform: {pltfm}.")


if __name__=="__main__":

    args = parse_cli_args(sys.argv[1:])
    app = ThisApplication(start_filepath=args.start_filepath)
    app.create_stylesheet(
        directory=args.stylesheet_directory,
        filename=args.stylesheet_filename,
        font_name=args.font_name,
        font_size=args.font_size,
        font_attrs=args.font_attrs,
    )
    app.convert_rst_to_pdf(stylesheet_directory=args.stylesheet_directory, stylesheet_filename=args.stylesheet_filename)
    ipv46_addrs = list_local_ipaddrs(terminal_encoding=args.terminal_encoding)
    if args.webserver_port > 0:
        app.start_webserver(local_ipv46_addrs=ipv46_addrs, webserver_port=args.webserver_port)

