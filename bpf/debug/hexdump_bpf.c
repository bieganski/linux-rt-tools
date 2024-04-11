#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <linux/bpf.h>
#include <linux/filter.h>
#include <sys/syscall.h>

// if 'raw', pipe to 'xxd' (and possibly xxd -r)
void print_hexdump(const void *data, size_t size, int raw) {
    const unsigned char *ptr = data;
    if (!raw) {
        for (size_t i = 0; i < size; i++) {
            printf("%02x ", ptr[i]);
            if ((i + 1) % 16 == 0) {
                printf("\n");
            }
        }
        printf("\n");
    } else {
        write(1, ptr, size);
    }
    
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <bpf_prog_id>\n", argv[0]);
        return EXIT_FAILURE;
    }

    int bpf_prog_id = atoi(argv[1]);

    static union bpf_attr attr;
    static struct bpf_prog_info info = {};
    int ret;

	attr.prog_id = bpf_prog_id;
    
    int fd = syscall(__NR_bpf, BPF_PROG_GET_FD_BY_ID, &attr, sizeof(union bpf_attr));
    if (fd < 0) {
        perror("BPF_PROG_GET_FD_BY_ID");
        return EXIT_FAILURE;
    }
    
    memset(&attr, 0x0, sizeof(union bpf_attr));
	attr.info.bpf_fd = fd;
	attr.info.info_len = sizeof(struct bpf_prog_info);
	attr.info.info = (uint64_t) &info; // see libbpf/src/bpf.c

    // first syscall fetches 'info.xlated_prog_len'
    ret = syscall(__NR_bpf, BPF_OBJ_GET_INFO_BY_FD, &attr, sizeof(union bpf_attr));

    int copy_xlated_prog_len = info.xlated_prog_len;
    fprintf(stderr, "first get_info: xlated len %d\n", copy_xlated_prog_len);
    
    memset(&info, 0x0, sizeof(struct bpf_prog_info));
    uint64_t* PTR = malloc(copy_xlated_prog_len); // // (struct bpf_insn*)
    memset(PTR, 0xff, copy_xlated_prog_len);
    info.xlated_prog_insns = (uint64_t) PTR;
    info.xlated_prog_len = copy_xlated_prog_len;
    
    // second syscall fetches variable-size chunk of 'xlated_prog_len'-bytes.
    ret = syscall(__NR_bpf, BPF_OBJ_GET_INFO_BY_FD, &attr, sizeof(union bpf_attr));

    print_hexdump(PTR, copy_xlated_prog_len, 1);

    close(fd);

    return 0;
}
