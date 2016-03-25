#include <string>
#include <vector>

#include <assert.h>
#include <string.h>
#include <stdio.h>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <unistd.h>

#include <zmq.h>

int socket_connect(const char *ipaddr, int port);
void zstream_recvfrom(void *zsock, std::string& peerid, std::string& payload);
void zstream_sendto(void *zsock, const std::string& peerid, const std::string& payload);

int main()
{
    void *zctx = zmq_ctx_new();
    assert(zctx);

    void *zsock_server = zmq_socket(zctx, ZMQ_STREAM);
    assert(zsock_server);
    int rc = zmq_bind(zsock_server, "tcp://127.0.0.1:12345");
    assert(rc!=-1);

    printf("client connecting\n");

    int client_sock = socket_connect("127.0.0.1", 12345);
    assert(client_sock!=-1);

    std::string peerid;
    std::string payload;

    zstream_recvfrom(zsock_server, peerid, payload);
    assert(peerid.size()!=0);
    assert(payload.size()==0);

    printf("client connected\n");

    printf("server disconnecting client\n");

    zstream_sendto(zsock_server, peerid, "");

    // client will not get disconnected
    // unless one of the below is enabled
 
    #if 0
        // client will get disconnected
        // but the send will have an error
        zstream_sendto(zsock_server, peerid, "");
    #elif 0
        // client will get disconnected
        // a nonzero timeout is required
        zmq_pollitem_t zsockitem = {zsock_server, 0, ZMQ_POLLIN};
        rc = zmq_poll(&zsockitem, 1, 1);
        assert(rc==0);
    #endif

    while (1)
    {
        zmq_pollitem_t sockitem = {NULL, client_sock, ZMQ_POLLIN};
        rc = zmq_poll(&sockitem, 1, 250);
        assert(rc!=-1);
        if (rc==0) {
            printf("FAIL: client timeout\n");
            break;
        }

        char buffer[16];
        int nbytes = recv(client_sock, buffer, sizeof(buffer), 0);
        assert(nbytes >= 0);

        if (nbytes > 0) {
            printf("client received %d bytes\n", nbytes);
        } else {
            printf("SUCCESS: client got disconnected\n");
            break;
        }
    }

    close(client_sock);
    zmq_close(zsock_server);

    zmq_ctx_destroy(zctx);
    return 0; 
}

int socket_connect(const char *ipaddr, int port)
{
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    assert(fd!=-1);

    struct sockaddr_in saddr;
    memset(&saddr, 0, sizeof(saddr));
    saddr.sin_family = AF_INET;
    inet_pton(AF_INET, ipaddr, &saddr.sin_addr.s_addr);
    saddr.sin_port = htons(port);

    int rc = connect(fd, (struct sockaddr *)&saddr, sizeof(saddr));
    assert(rc!=-1);

    return fd;
}

void zstream_recvfrom(void *zsock, std::string& peerid, std::string& payload)
{
    zmq_msg_t frame;
    zmq_msg_init(&frame);

    int rc = zmq_msg_recv(&frame, zsock, 0);
    assert(rc!=-1);

    peerid.resize(0);
    peerid.insert(0, (char*)zmq_msg_data(&frame), zmq_msg_size(&frame));

    zmq_msg_close(&frame);
    zmq_msg_init(&frame);

    rc = zmq_msg_recv(&frame, zsock, 0);
    assert(rc!=-1);

    payload.resize(0);
    payload.insert(0, (char*)zmq_msg_data(&frame), zmq_msg_size(&frame));

    zmq_msg_close(&frame);
}

void zstream_sendto(void *zsock, const std::string& peerid, const std::string& payload)
{
    int rc = zmq_send(zsock, peerid.data(), peerid.size(), ZMQ_SNDMORE);
    if (rc==-1) {
        fprintf(stderr, "*** %s ***\n", zmq_strerror(zmq_errno()));
    }
    else {
        rc = zmq_send(zsock, payload.data(), payload.size(), ZMQ_SNDMORE);
        assert(rc!=-1);
    }
}

