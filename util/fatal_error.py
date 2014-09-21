from sys import exit


def fatal_error(msg='Unknown'):
    print('\033[91m A fatal error has occurred: {0}\033[0m'.format(msg))
    print('\033[93m The program will now exit.\033[0m')
    exit(1)