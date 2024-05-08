#include <stdio.h>
#include<dirent.h>
#include<sys/stat.h>


void explore(char *root){
    DIR *dir = opendir(root);
    struct dirent *entry;
    struct stat entry_stat;
    char tmp_path[999];

    if(dir == NULL)
        return;
    //readdir sposta automaticamente a prox entry
    while(entry = readdir(dir)){
        strcpy(tmp_path, root);
        strcat(tmp_path, "/");
        strcat(tmp_path, entry->d_name);
        stat(entry->d_name,&entry_stat);
// se cartella la esploro, escludo percorsi "speciali": '.', ' ..' per evitare loop
        if(S_ISDIR(entry_stat.st_mode) && strcmp(entry->d_name, ".") && strcmp(entry->d_name, "..") ){
            explore(tmp_path);
        }
        else{ printf("%s\n", entry->d_name); }
    }
    return;
}


int main(int argc , char *argv[]){
    explore(argv[1]);
    return 0;
}
