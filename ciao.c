/*
Scrivere la funzione:
char **vreaddir(const char *path)
che restituisca l'elenco dei nomi dei file in una directory come vettore di stringhe terminato con un
puntatore NULL. (lo stesso formato di argv o envp).
Il vettore e le stringhe dei nomi sono allocate dinamicamente.
completare l'esercizio con un programma principale che testi il corretto funzionamento della funzione
vreaddir.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>


char **vreaddir(const char *path){
    DIR *dir;
    struct dirent *entry;
    char **files = NULL;
    int i = 0;
    if((dir = opendir(path)) == NULL){
        perror("opendir");
        return NULL;
    }
    while((entry = readdir(dir)) != NULL){
        files = realloc(files, (i+1)*sizeof(char*));
        files[i] = strdup(entry->d_name);
        i++;
    }
    files = realloc(files, (i+1)*sizeof(char*));
    files[i] = NULL;
    closedir(dir);
    return files;
}

int main(int argc, char *argv[]){
    char **files = vreaddir(".");
    for(int i = 0; files[i] != NULL; i++){
        printf("%s\n", files[i]);
        free(files[i]);
    }
    free(files);
    return 0;
}