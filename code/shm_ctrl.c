#include<fcntl.h>
#include<sys/shm.h>
#include<sys/stat.h>
#include<sys/mman.h>

#include<stdio.h>
#include<stdlib.h>
#include<string.h>

#include"shm_ctrl.h"
#include"const.h"

static void* ptr=0;

void* shm_setting(){
    int fd;
    if(ptr){
        fprintf(stderr, "E:ptr was already setted...\n");
        return ptr;
    }
    fd=shm_open("SHM_NAME",O_RDWR|O_CREAT|O_TRUNC,0666);
    if(fd<0){
        fprintf(stderr,"E:shm_setting failed\n");
        return NULL;
    }

    ptr=mmap(0,SOUND_BUF_SZ,PROT_READ|PROT_WRITE,0666,fd,0);
    return ptr;
}

int shm_write(void* buf, size_t size){
    struct s_shm_buf shm_buf;
    if(size>sizeof(struct s_shm_buf)){
        fprintf(stderr,"E:buf size too big\n");
        return -1;
    }
    memcpy(shm_buf.buf, buf, size);
    shm_buf.sampling_rate=100;
    memcpy(ptr, &shm_buf, sizeof(shm_buf));
    return 0;
}