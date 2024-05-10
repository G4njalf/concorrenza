#include <stdlib.h>
#include<stdio.h>
#include<string.h>

int main(int argc, char const *argv[])
{
    for (int i = 1; i < argc; i++)
    {   
        fwrite(argv[i], 1, strlen(argv[i])+1, stdout); // Write the buffer to stdout
    }
    
    return 0;
}