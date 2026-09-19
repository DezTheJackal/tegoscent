from .cli import main
import os
import sys

if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Piping our output into `head`, `less -F`, etc. closes stdin/stdout
        # early - that's the reader's choice, not our error. Exit quietly
        # instead of dumping a traceback, per the standard Python idiom.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(0)
