#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main () {
    char command[500];

    // TODO: Change the string between the quotes to be the path to your audio-visual-player code folder
    const char* path = "/path/to/visualizer/folder";

    sprintf(command, "python3 %s/main.py %s", path, path);
    system(command);
    sleep(10);

    return(0);
}
