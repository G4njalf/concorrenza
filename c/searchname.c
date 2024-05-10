#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>

// Funzione ricorsiva per lo scandire della directory
void list_directory(const char *dirname) {
    DIR *dir;
    struct dirent *entry;

    // Apre la directory
    if (!(dir = opendir(dirname))) {
        perror("opendir");
        exit(EXIT_FAILURE);
    }

    // Legge ogni elemento della directory
    while ((entry = readdir(dir)) != NULL) {
        // Ignora le directory speciali "." e ".."
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
            continue;

        // Costruisce il percorso completo dell'elemento
        char path[1024];
        snprintf(path, sizeof(path), "%s/%s", dirname, entry->d_name);

        // Stampa il percorso dell'elemento
        printf("%s\n", path);

        // Verifica se l'elemento è una directory
        struct stat info;
        if (stat(path, &info) == -1) {
            perror("stat");
            continue;
        }

        if (S_ISDIR(info.st_mode)) {
            // Se l'elemento è una directory, ricorsivamente esplora la directory
            list_directory(path);
        }
    }
    closedir(dir);
}

int main() {
    // Esegue la lista ricorsiva della directory corrente
    list_directory(".");

    return 0;
}
