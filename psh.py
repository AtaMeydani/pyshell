#!/usr/bin/env python3

"""psh: a simple shell written in Python"""

import os, sys

def fork(command, wait):
    pid = os.fork()
    if pid > 0:
        print(f"Parent Process ID: {os.getpid()}")
        if wait:
            os.wait()  # Wait for child 
    elif pid == 0:
        # we are in child process
        print(f"Child Process ID: {os.getpid()}")
        execute_command(command)
    else:
        print("Error forking")


def execute_command(command):
    """execute commands and handle piping"""
    try:
        if ">" in command:
            commands = command.split(">")
            cmd = commands[0]
            file = commands[1].strip()

            with open(os.path.abspath(file), mode="w") as output:
                os.dup2(output.fileno(), 1)
                os.execvp(cmd.split()[0], cmd.split())
        if "<" in command:
            commands = command.split("<")
            cmd = commands[0]
            file = commands[1].strip()

            with open(os.path.abspath(file), mode="r") as input:
                os.dup2(input.fileno(), 0)
                os.execvp(cmd.split()[0], cmd.split())
        if "|" in command:
            commands = command.split("|")
            # save for restoring later on
            s_in, s_out = (0, 0)
            s_in = os.dup(0)
            s_out = os.dup(1)

            # first sub-command recieves input from stdin
            fdin = os.dup(s_in)

            # iterate over all the commands that are piped
            for counter, cmd in enumerate(commands, start=1):
                # fdin will be stdin if it's the first iteration
                os.dup2(fdin, 0)
                os.close(fdin)

                # restore stdout if this is the last command
                if counter == len(commands):
                    fdout = os.dup(s_out)
                else:
                    fdin, fdout = os.pipe()

                # redirect stdout to pipe
                os.dup2(fdout, 1)
                os.close(fdout)

                try:
                    pid = os.fork()
                    if pid == 0:
                        os.execvp(cmd.split()[0], cmd.split())
                    elif pid > 0:
                        os.wait()
                except Exception:
                    print("psh: command not found: {}".format(cmd.strip()))

            # restore stdout and stdin
            os.dup2(s_in, 0)
            os.dup2(s_out, 1)
            os.close(s_in)
            os.close(s_out)
        else:
            commands = command.split()
            os.execvp(commands[0], commands)
    except Exception as e:
        print(f"psh: command not found: {command}\n{e}")
    finally:
        sys.exit()


def psh_cd(path):
    """convert to absolute path and change directory"""
    try:
        os.chdir(os.path.abspath(path))
    except Exception:
        print("cd: no such file or directory: {}".format(path))


def psh_help():
    print("""psh: shell implementation in Python.
          Supports all basic shell commands.""")


def check_command(command):
    if command == "help":
        psh_help()
    elif command.startswith("cd "):
        psh_cd(command[3:])
    elif command.endswith("&"):
        fork(command=command[:-1], wait=False)
    else:
        fork(command=command, wait=True)


def main():
    last_command = None
    while True:
        inp = input(f"(pid:{os.getpid()})psh$ ").strip()

        if inp == "exit":
            break
        elif inp == "!!":
            if last_command:
                check_command(last_command)
            else:
                print("There is no last command")
        else:
            last_command = inp
            check_command(inp)
        

if '__main__' == __name__:
    main()
