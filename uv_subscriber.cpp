#include <vector>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <uv.h>

struct subscriber_s
{
	uv_tcp_t tcp_stream;
	uv_connect_t connect_req;

    bool await_header;
	unsigned await_size;
    std::vector<char> buffer;
};

void alloc_buffer(uv_handle_t *handle, size_t suggested_size, uv_buf_t *buf)
{
    // purposely use a value smaller than our largest payload,
    // in order to exercise our data accum logic
    suggested_size = 5000;

    buf->base = (char*)malloc(suggested_size);
    buf->len = suggested_size;
}

void on_read(uv_stream_t *client, ssize_t nread, const uv_buf_t *buf)
{
	struct subscriber_s *sub = (struct subscriber_s *)client->data;

    bool do_close = false;

    if (nread < 0) {
		fprintf(stderr, "read error : %s\n", uv_strerror(nread));
        do_close = true;
    }
    else if (nread == UV_EOF) {
        do_close = true;
    }
    else if (nread == 0) {
        // EAGAIN
    }
    else {
        sub->buffer.insert(sub->buffer.end(), buf->base, buf->base + nread);

        while (sub->buffer.size() >= sub->await_size)
        {
            if (sub->await_header) {
                int payload_size;
                memcpy(&payload_size, &sub->buffer[0], sizeof(payload_size));
                payload_size = ntohl(payload_size);

                sub->await_header = false;
                sub->await_size += payload_size;
            }
            else {
                int index;
                memcpy(&index, &sub->buffer[4], sizeof(index));
                printf("%d %d\n", index, sub->await_size - 4);

                sub->buffer.erase(sub->buffer.begin(), sub->buffer.begin() + sub->await_size);

                sub->await_header = true;
                sub->await_size = 4;
            }
        }
    }

    free(buf->base);

    if (do_close) {
        uv_close((uv_handle_t*) client, NULL);
    }
}

void on_connect(uv_connect_t *req, int status)
{
	if (status < 0) {
		fprintf(stderr, "connect error : %s\n", uv_strerror(status));
	}
    else {
        struct subscriber_s *sub = (struct subscriber_s *)req->data;
        sub->buffer.clear();
        sub->await_header = true;
        sub->await_size = 4;

        uv_read_start((uv_stream_t*)&sub->tcp_stream, alloc_buffer, on_read);
    }
}

void
do_connect(uv_loop_t *uvloop, struct subscriber_s *sub, const char *ipaddr, int port)
{
	struct sockaddr_in sin;
	uv_ip4_addr(ipaddr, port, &sin);

	uv_tcp_init(uvloop, &sub->tcp_stream);
	sub->tcp_stream.data = sub;
	sub->connect_req.data = sub;

	uv_tcp_connect(&sub->connect_req, &sub->tcp_stream, (struct sockaddr*)&sin, on_connect);
}

int main()
{
    uv_loop_t uvloop;
    uv_loop_init(&uvloop);

	struct subscriber_s sub;

	do_connect(&uvloop, &sub, "127.0.0.1", 10000);

	uv_run(&uvloop, UV_RUN_DEFAULT);
    uv_loop_close(&uvloop);
}
