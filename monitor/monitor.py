# -*- coding:utf-8 -*-
import os
import glob
import subprocess
from argparse import ArgumentParser, _HelpAction, _SubParsersAction


class ArgparseHelper(_HelpAction):
    """
        显示格式友好的帮助信息
    """

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        subparsers_actions = [action for action in parser._actions if isinstance(action, _SubParsersAction)]

        for subparsers_action in subparsers_actions:
            for choice, subparser in subparsers_action.choices.items():
                print("Command '{}'".format(choice))
                print(subparser.format_usage())

        parser.exit()


def main():
    monitors = [i.replace("_monitor.py", "") for i in glob.glob("*_monitor.py")]
    parser = ArgumentParser(description="All monitor process. ", add_help=False)
    parser.add_argument('-h', '--help', action=ArgparseHelper, help='Show this help message and exit. ')
    base_parser = ArgumentParser(description="Common args. ", add_help=False)
    base_parser.add_argument("process", choices=monitors + ["all"], help="All process. ")
    sub_parsers = parser.add_subparsers(help="Command. ", dest="command")
    # start
    sub_parsers.add_parser("start", help="Start monitor. ", parents=[base_parser])
    # stop
    sub_parsers.add_parser("stop", help="Stop monitor. ", parents=[base_parser])
    # restart
    sub_parsers.add_parser("restart", help="Restart monitor. ", parents=[base_parser])
    # status
    sub_parsers.add_parser("status", help="Monitor status. ", parents=[base_parser])
    args = parser.parse_args()
    if args.process != "all":
        process = subprocess.Popen(["python", "%s_monitor.py"%args.process, args.command, "--daemon"])
        process.wait()
        #os.system("python %s_monitor.py %s --daemon"%(args.process, args.command))
    else:
        for monitor in monitors:
            process = subprocess.Popen(["python", "%s_monitor.py" % monitor, args.command, "--daemon"])
            process.wait()
            #os.system("python %s_monitor.py %s --daemon" % (monitor, args.command))


if __name__ == "__main__":
    main()