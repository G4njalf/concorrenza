#include<stdio.h>
#include<unistd.h>

int main()
{
    char buffer[1024];
    int n  = read(0, buffer, 1024);

    for (int i = 0; i < n; i++) {
        if (buffer[i] == '\0')
        {
            printf("merda\n");
        }
        
        write(1, &buffer[i], 1);
    }

    return 0;
}