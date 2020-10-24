#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main () {
   char command[150];

   strcpy(command, "python3 ~/Documents/python/music-visualizer/main.py ~/Documents/python/music-visualizer" );
   system(command);
   sleep(10);

   return(0);
}
