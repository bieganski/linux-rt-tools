#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/inotify.h>

#define EVENT_SIZE (sizeof(struct inotify_event))
#define BUF_LEN (1024 * (EVENT_SIZE + 16))

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    int inotify_fd, watch_fd;
    char buffer[BUF_LEN];

    // Initialize inotify
    inotify_fd = inotify_init();
    if (inotify_fd == -1) {
        perror("inotify_init");
        exit(EXIT_FAILURE);
    }

    // Add watch for the specified file
    watch_fd = inotify_add_watch(inotify_fd, argv[1], IN_OPEN | IN_CLOSE);
    if (watch_fd == -1) {
        perror("inotify_add_watch");
        exit(EXIT_FAILURE);
    }

    printf("Monitoring file: %s\n", argv[1]);

    while (1) {
        ssize_t len = read(inotify_fd, buffer, BUF_LEN);
        if (len == -1) {
            perror("read");
            exit(EXIT_FAILURE);
        }

        // Process events
        for (char *ptr = buffer; ptr < buffer + len;) {
            struct inotify_event *event = (struct inotify_event *)ptr;

            if (event->mask & IN_OPEN) {
                printf("File opened: %s\n", argv[1]);
            }

            if (event->mask & IN_CLOSE) {
                printf("File closed: %s\n", argv[1]);
            }

            ptr += EVENT_SIZE + event->len;
        }
    }

    // Clean up
    close(inotify_fd);

    return 0;
}

