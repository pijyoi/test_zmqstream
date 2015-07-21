#include <assert.h>
#include <string.h>
#include <stdio.h>

#include <netinet/in.h>
#include <netinet/tcp.h>
#include <unistd.h>

#include <zmq.h>

int main()
{
    const char *endpoint = "tcp://127.0.0.1:12345";

    void *zctx = zmq_ctx_new();
    assert(zctx);
    void *zsock_s = zmq_socket(zctx, ZMQ_DEALER);
    assert(zsock_s);
    int rc = zmq_bind(zsock_s, endpoint);
    assert(rc!=-1);
    void *zsock_c = zmq_socket(zctx, ZMQ_DEALER);
    assert(zsock_c);
    rc = zmq_connect(zsock_c, endpoint);
    assert(rc!=-1);

    const int num_small = 200;
    const int num_large = 1;

    for (int idx=0; idx < num_small; idx++)
    {
        zmq_msg_t msg;
        zmq_msg_init_size(&msg, 1);
        memset(zmq_msg_data(&msg), 0, zmq_msg_size(&msg));
        rc = zmq_msg_send(&msg, zsock_c, 0);
        assert(rc!=-1);
        zmq_msg_close(&msg);
    }

    for (int idx=0; idx < num_large; idx++)
    {
        zmq_msg_t msg;
        zmq_msg_init_size(&msg, 1000);
        memset(zmq_msg_data(&msg), 0, zmq_msg_size(&msg));
        rc = zmq_msg_send(&msg, zsock_c, 0);
        assert(rc!=-1);
        zmq_msg_close(&msg);
    }

    for (int idx=0; idx < num_small; idx++)
    {
        zmq_msg_t msg;
        zmq_msg_init(&msg);
        rc = zmq_msg_recv(&msg, zsock_s, 0);
        assert(rc!=-1);
        assert(!zmq_msg_more(&msg));
        zmq_msg_close(&msg);
    }

    for (int idx=0; idx < num_large; idx++)
    {
        zmq_msg_t msg;
        zmq_msg_init(&msg);

        int rcvbytes = zmq_msg_recv(&msg, zsock_s, 0);
        assert(rcvbytes!=-1);
        printf("got %d bytes\n", rcvbytes);

        zmq_msg_close(&msg);
    }

    zmq_close(zsock_c);
    zmq_close(zsock_s);
    zmq_ctx_destroy(zctx);

}

