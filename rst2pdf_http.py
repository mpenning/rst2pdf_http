
"""

"""
# subprocess.run() is generally-recommended instead of subprocess.call()
from subprocess import run, call
from functools import wraps
import ipaddress
import datetime
import argparse
import tempfile
import warnings
import pathlib
import shutil
import shlex
import json
import sys
import os
import re

from rich.console import Console
from loguru import logger
import yaml

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

class DummyLoggerProperty(object):
    """
    DummyLoggerProperty.catch() implementation.

    This was originally included in case Loguru to fake ``logger.catch()``; however, this approach was abandoned.  This class remains as a reminder of the aborted effort.

    If this class was used, it would have been renamed as ``logger`` and defined in a try / except block while importing ``loguru``.
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

@logger.catch(reraise=True)
def check_file_exists(filepath=None):
    """
    Check whether ``filepath`` exists; if so, return True.

    Arguments
    ---------

    :param filepath: Filepath to be checked
    :type src: str

    Raises
    ------

    ``OSError()`` if ``filepath`` does not exist.

    Returns
    -------

    A boolean indicating that the file exists.


    :Example:

    >>> check_file_exists("/etc/passwd")
    True

    """
    if not isinstance(filepath, str):
        raise ValueError(f"{filepath} must be a string.")

    abspath = os.path.abspath(os.path.expanduser(os.path.normpath(f"{filepath}")))
    logger.info(f"    filepath: {filepath}")
    logger.debug(f"        checking: {abspath}")

    if os.path.exists(abspath):
        return True
    else:
        raise OSError(f"{abspath} must exist.")


class Stylesheet(object):

    # This is on the Stylesheet() class
    @logger.catch(reraise=True)
    def __init__(self, font_name, font_size=12, font_attrs=None):
        """
        Write a custom rst2pdf Stylesheet with ``font_name``, ``font_size` and ``font_attrs``.
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
    @logger.catch(reraise=True)
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

        check_file_exists(start_filepath)

        start_pathobj = pathlib.PurePosixPath(start_filepath)
        start_directory = pathlib.posixpath.dirname(start_filepath)

        start_filename = start_pathobj.parts[-1]
        start_filename_suffix = start_pathobj.suffix.split(".")[-1]
        start_filename_prefix = start_pathobj.stem
        current_directory = os.getcwd()

        if "." in start_filename_suffix:
            raise ValueError(f"This is an invalid suffix: '{start_filename_suffix}'")

        self.start_filepath = start_filepath
        self.start_filename = start_filename
        self.start_filename_suffix = start_filename_suffix

        if start_filename_suffix == "rst":
            self.finish_filename = f"{start_filename_prefix}.pdf"
            self.finish_filepath = os.path.normpath(f"{start_directory}/{start_filename_prefix}.pdf")
            self.finish_filename_suffix = "pdf"
        else:
            self.finish_filename = start_filename
            self.finish_filepath = start_filepath
            self.finish_filename_suffix = start_filename_suffix

        self.rst2pdf_home = DEFAULT_STYLESHEET_DIRECTORY

        # Technically we will call
        if len(sys.argv) > 0:
            self.cli_args = parse_cli_args(sys.argv[1:])
        else:
            self.cli_args = None

        self.custom_imports_directory = os.path.normpath(f"{self.rst2pdf_home}/custom_imports")
        # Write text files to rst_imports/ to be imported
        self.write_custom_imports_directory()
        self.write_custom_rst_imports()

    @logger.catch(reraise=True)
    def create_stylesheet(self, directory=None, filename=None, font_name=None, font_size=None, font_attrs=None):
        ssobj = Stylesheet(font_name=font_name, font_size=font_size, font_attrs=font_attrs,)
        ssobj.save_stylesheet_yaml(directory=directory, filename=filename)

    @logger.catch(reraise=True)
    def convert_rst_to_pdf(self, stylesheet_directory=None, stylesheet_filename=None):
        if self.start_filename_suffix == "rst":
            check_file_exists(filepath=f"{self.start_filepath}")
            check_file_exists(filepath=f"{stylesheet_directory}/{stylesheet_filename}")

            rst2pdf_cmd = f"rst2pdf --stylesheet-path={stylesheet_directory} --stylesheets={stylesheet_filename} {self.start_filepath} -o {self.finish_filepath}"
            logger.info(f"{rst2pdf_cmd}")

            output_namedtuple = run(
                shlex.split(rst2pdf_cmd),
                shell=False,
                capture_output=True,
            )
            check_file_exists(self.finish_filepath)

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
    def copy_file(self, src, dst):
        """copy_file(src, dst)

        Copy a file.

        Arguments
        ---------

        :param src: Filepath of the source
        :type src: str
        :param dst: Filepath of the destination
        :type dst: str

        Returns
        -------

        A boolean indicating success or failure.

        - True: Copy success.
        - False: Copy failure.

        :Example:

        >>> app = ThisApplication()
        >>> app.copy_file("/tmp/this.txt", "/tmp/that.txt")

        """
        logger.debug(f"copy {src} {dst}")
        try:
            shutil.copy(src, dst)
            return True
        except shutil.SameFileError:
            warnings.warn("Source and destination are the same file; no file copy was required.")
            return False
        except Exception as eee:
            logger.error(f"{eee}")
            return False

    def write_custom_imports_directory(self):
        try:
            os.makedirs(f"{self.rst2pdf_home}/custom_imports")
        except FileExistsError:
            # Directory already exists...
            pass
        except Exception as eee:
            logger.critical(f"{eee}")
            raise OSError(f"{eee}")
        return True

    def write_custom_rst_imports(self):
        """write_custom_rst_imports()

        Write custom imports if the script is called with ``-i``.
        """

        if self.cli_args.write_rst_imports is True:
            self.write_localtime_today_as_words()

    def write_localtime_today_as_words(self):
        today = datetime.date.today()
        day = today.day
        month = today.month
        year = today.year
        output_filepath = os.path.normpath(f"{self.custom_imports_directory}/localtime_today_as_words.rst")
        today_as_words = datetime.date(year, month, day).strftime(f"%A %B {day}, {year}")
        logger.info(f"writing '{today_as_words}' to {output_filepath}")
        with open(output_filepath, 'w+') as fh:
            fh.write(today_as_words)

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
                self.copy_file(src=f"{self.finish_filepath}", dst=temporary_finish_path)
            except shutil.SameFileError:
                warnings.warn("Source and temporary destination are the same file; no file copy was required.")


            ###############################################################
            # Change to the temporary directory and start the Golang
            #     webserver to serve files from `temp_dir` locally...
            ###############################################################
            try:

                print("")
                for v46addr in local_ipv46_addrs:
                    # Skip binding to loopback addresses... this is pointless.  If it's sufficient to bind
                    # to the loopback, then you dont need this script.
                    if re.search(r"^(::1|127\.\d+\.\d+\.\d+)$", v46addr):
                        continue
                    elif ":" in v46addr:
                        logger.success(f"Local URL --> http://[{v46addr}]:{args.webserver_port}/")
                    else:
                        logger.success(f"Local URL --> http://{v46addr}:{args.webserver_port}/")

                return_code = call(
                    shlex.split(f"{os.getcwd()}/filesystem_webserver --webserverPort {webserver_port} --webserverDirectory {temp_dir}"),
                    shell=False,
                )
            except KeyboardInterrupt:
                logger.info("    Webserver interrupted by KeyboardInterrupt.")
            except Exception as eee:
                logger.error(f"   {eee}: Did you type `make build` before running the script?")

@logger.catch(reraise=True)
def get_version_number(version_filename="resources/version.json"):
    version_digits_file = None
    version_digits = None
    try:
        with open(version_filename, "r") as fh:
            version_digits_file = fh.read().strip()
    except Exception as eee:
        logger.critical(f"{eee}")
        raise OSError(f"{eee}")

    version_digits = [str(ii) for ii in json.loads(version_digits_file)]

    if isinstance(version_digits, list):
        version = ".".join(version_digits)
        return version
    else:
        error = f"version_digits: {version_digits} must be a list."
        logger.critical(error)
        raise ValueError(error)

@logger.catch(reraise=True)
def parse_cli_args(sys_argv1):
    """
    Reference: https://docs.python.org/3/library/argparse.html
    """
    if isinstance(sys_argv1, (list, tuple)):
        pass
    else:
        raise ValueError("`sys_argv1` must be a list or tuple with CLI options from `sys.argv[1:]`")

    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__),
        description="Build a PDF from RestructuredText and serve via Go HTTP",
        add_help=True,
    )
    parser_required = parser.add_argument_group("required")
    parser_required.add_argument("-f", "--start_filepath",
        type=str,
        default=None,
        choices=None,
        action="store",
        help="start filepath.",
    )
    parser_optional = parser.add_argument_group("optional")
    parser_optional.add_argument("-w", "--webserver_port",
        type=int,
        default=0,
        choices=None,
        action="store",
        help="Start a webserver on this port."
    )
    parser_optional.add_argument("-i", "--write_rst_imports",
        default=False,
        action="store_true",
        help=f"Write the canned rst imports."
    )
    parser_optional.add_argument("-n", "--font_name",
        type=str,
        default=DEFAULT_STYLESHEET_FONTNAME,
        choices=sorted(VALID_FONT_NAMES),
        action="store",
        help=f"rst2pdf font name; the default is '{DEFAULT_STYLESHEET_FONTNAME}'.",
    )
    parser_optional.add_argument("-s", "--font_size",
        type=int,
        default=DEFAULT_STYLESHEET_FONTSIZE,
        choices=sorted(VALID_FONT_SIZES),
        action="store",
        help="rst2pdf font size; default is '12'.",
    )
    parser_optional.add_argument("-a", "--font_attrs",
        type=str,
        default=DEFAULT_STYLESHEET_FONTATTR,
        choices=sorted(VALID_FONT_ATTRS),
        action="append",
        help="rst2pdf font attrs; default is no font attributes.",
    )
    parser_optional.add_argument("-d", "--stylesheet_directory",
        type=str,
        default=DEFAULT_STYLESHEET_DIRECTORY,
        choices=None,
        action="store",
        help=f"rst2pdf stylesheet_directory; the default is '{DEFAULT_STYLESHEET_DIRECTORY}'.",
    )
    parser_optional.add_argument("-e", "--stylesheet_filename",
        type=str,
        default=DEFAULT_STYLESHEET_FILENAME,
        choices=None,
        action="store",
        help=f"rst2pdf stylesheet_filename; the default is '{DEFAULT_STYLESHEET_FILENAME}'.",
    )
    parser_optional.add_argument("-t", "--terminal_encoding",
        type=str,
        default="UTF-8",
        choices=None,
        action="store",
        help="."
    )
    parser_optional.add_argument("-v", "--version",
        default=False,
        action="store_true",
        help=f"Output the script version number to stdout."
    )

    args = parser.parse_args(sys_argv1)

    # Special-case: handle the --version argument...
    if args.version is True:
        today = datetime.date.today()
        this_year = today.year
        start_year = 2023
        if this_year != start_year:
            all_years = f"{start_year}-{year}"

        try:
            version = get_version_number()
            print(f"{__file__} version: {version}; Copyright {all_years} David Michael Pennington.")
            sys.exit(0)
        except Exception as eee:
            raise OSError(f"{eee}")

    return args

@logger.catch(reraise=True)
def is_valid_ipv4addr(addr, raise_error=True):
    """
    Check whether ``addr`` is a valid IPv4 address; if so, return True.

    Arguments
    ---------

    :param addr: IPv4 address to be checked
    :type addr: str

    Raises
    ------

    If ``raise_error`` is True, raise ``ValueError()`` if ``addr`` is not valid.

    Returns
    -------

    A boolean indicating that the address is valid.


    :Example:

    >>> is_valid_ipv4_addr("127.0.0.1", raise_error=False)
    True
    >>> is_valid_ipv4_addr("scrambled eggs", raise_error=False)
    False

    """
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

@logger.catch(reraise=True)
def is_valid_ipv6addr(addr, raise_error=True):
    """
    Check whether ``addr`` is a valid IPv6 address; if so, return True.

    Arguments
    ---------

    :param addr: IPv6 address to be checked
    :type addr: str

    Raises
    ------

    If ``raise_error`` is True, raise ``ValueError()`` if ``addr`` is not valid.

    Returns
    -------

    A boolean indicating that the address is valid.


    :Example:

    >>> is_valid_ipv6_addr("::1", raise_error=False)
    True
    >>> is_valid_ipv6_addr("scrambled eggs", raise_error=False)
    False

    """
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

