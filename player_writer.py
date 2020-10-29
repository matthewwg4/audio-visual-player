import os

def main():

    cwd = os.getcwd()

    code1 = """// auto generated player.c file
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main () {
    char command[500];

    // TODO: Change the string between the quotes to be the path to your audio-visual-player code folder
"""

    code2 = '    const char* path = "{}";'.format(cwd)

    code3 = """

    sprintf(command, "python3 %s/main.py %s", path, path);
    system(command);
    sleep(10);

    return(0);
}
"""

    code = code1+code2+code3
    with open("player.c", "w") as file:
        file.write(code)

if __name__ == '__main__':
    main()