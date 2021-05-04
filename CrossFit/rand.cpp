#include <stdio.h>
#include <stdlib.h>
#include <time.h>
using namespace std;

int main(int argc, char **argv){   
    int t = atoi(argv[1]);
    srand(time(0)+t);
    printf("%d\n",rand());
    return 0;
}
