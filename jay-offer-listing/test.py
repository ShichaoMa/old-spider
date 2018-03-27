import asyncio
import aiohttp

headers = {
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    }

def main():
    loop = asyncio.get_event_loop()
    server_coro = asyncio.start_server(get_offer_price, "127.0.0.1", 1234, loop=loop)
    server = loop.run_until_complete(server_coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

=
async def get_offer_price(reader, writer):
    data = await reader.read(1024)
    auth = aiohttp.BasicAuth(*"longen:jinanlongen2016".split(":"))
    async with aiohttp.ClientSession() as session:
        async with session.request("GET", data.decode(), headers=headers,
                                     proxy="http://mx13.headedeagle.com:12017", proxy_auth=auth) as resp:

            print(1111111, resp)
            buffer = await resp.read()
            print(222222222, buffer)
    writer.write(buffer or b"503")


if __name__ == "__main__":
    main()