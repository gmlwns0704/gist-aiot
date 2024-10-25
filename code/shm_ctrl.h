#include<fcntl.h>
#include<sys/shm.h>
#include<sys/stat.h>
#include<sys/mman.h>
#include"const.h"
#define SHM_NAME "sound_raw"
#define SOUND_BUF_SZ 16000

struct s_shm_buf{
    long long sampling_rate;
    char buf[SOUND_BUF_SZ];
};

void* shm_setting();
int shm_write(void* buf, size_t size);