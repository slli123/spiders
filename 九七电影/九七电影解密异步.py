import subprocess
import requests
import re
from urllib import parse
from fake_useragent import UserAgent
import asyncio
import aiohttp
import aiofiles
from Crypto.Cipher import AES


ua = UserAgent()
user_agent = ua.edge

# 先访问html，找到网页中的藏在iframe中的m3u8
# 对m3u8发起请求，获取得到第二个m3u8,这个是真正的m3u8链接、
# 对获取到真的m3u8链接发送请求获取得到的加密的ts链接
# 解析出每一个ts文件的路径，启动协程
# 对ts文件进行解密操作，先拿到：key
# 对ts文件进行合并，返回MP4文件

url = 'https://ukzy.ukubf3.com/share/lLvozncp364PSH7M'  # 视频页链接
headers = {
    'user-agent': user_agent
}

def get_html(url):
    print('获取页面')
    resp = requests.get(url=url,headers=headers)
    # print(resp.text)
    return resp.text

def get_m3u8_url():
    # 获取视频页的m3u8 链接
    print('获取视频页中的m3u8网址')
    page_source = get_html(url)
    ojb = re.compile(r'"url":"(?P<m3u8>.*?)"}',re.S)
    result = ojb.search(page_source)
    m3u8_url = result.group('m3u8')
    m3u8_url = parse.urljoin(url,m3u8_url)
    print(m3u8_url)
    return m3u8_url

def down_m3u8_url(m3u8_url):
    print('获取m3u8文件')
    # 获取m3u8文件
    page_source = get_html(m3u8_url)
    print(page_source)
    with open('./m3u8需解密.txt','w',encoding='utf-8') as f:
        f.write(page_source)

semaphore = asyncio.Semaphore(50)
async def download_one(session,url_ts):  # 使用异步方法去下载，毕竟量太大了
    for i in range(4):  # 重试4次
        try:
            file_name = url_ts.split('/')[-1]
            async with semaphore: #
                async with session.get(url_ts,timeout=30) as resp: # 30s都没有就算了
                    content = await resp.content.read()
                    async with aiofiles.open(f"./电影_源_加密/{file_name}",mode="wb") as f:
                        await f.write(content)
            print(url_ts,'下载成功')
            break
        except:
            print('下载失败',url_ts)
            await asyncio.sleep((i+1)*2) # 失败了就休息一下再爬

async def download_ts_all(session):
    tasks = []
    with open('./m3u8需解密.txt','r',encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                continue
            line = parse.urljoin(url,line)
            task = asyncio.create_task(download_one(session,line))
            tasks.append(task)
    await asyncio.wait(tasks) # 把任务挂起，去等待执行

def get_key():  # 获取key
    obj = re.compile(r'URI="(.*?)"',re.S)

    with open('m3u8需解密.txt','r',encoding='utf-8') as f:
        result = obj.findall(f.read())[0]
        f.close()
    url_key=parse.urljoin(url,result)
    print(url_key)
    key_str = get_html(url_key)
    print(key_str.encode('utf-8'))
    return key_str.encode('utf-8')

async def des_all_ts_file(key):  # 获取文件名
    tasks = []
    with open('m3u8需解密.txt','r',encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                continue
            line = line.strip()
            file_name = line.split('/')[-1]
            # 依旧异步操作
            task = asyncio.create_task(dec_one(file_name,key))
            tasks.append(task)
    await asyncio.wait(tasks)

# 解密 对称加密
async def dec_one(filename,key):  # 解密
    print(f"{filename}：开始解密")
    # 加密解密对象开始创建，偏移量0，模式MODE_CBC
    aes = AES.new(key=key,IV=b'0000000000000000',mode=AES.MODE_CBC)
    async with aiofiles.open(f'./电影_源_加密/{filename}',mode='rb') as f1, \
            aiofiles.open(f'./电影_源_解密后/{filename}', mode='wb') as f2:
        # 解密后直接保存到另一个文件夹
        content = await  f1.read()
        bc = aes.decrypt(content) # 解密
        await f2.write(bc)
        print(f"{filename}：解密完成")

def merge_ts(output_file): # 合并所有的ts文件，但是需要安装顺序去合并

    with open('./m3u8需解密.txt', 'r', encoding='utf-8') as f1,\
    open('./ts文件按顺序排列.txt','w',encoding='utf-8') as f2:
        for line in f1:
            if line.startswith('#'):
                continue
            line = parse.urljoin(url, line)
            file_name = line.split('/')[-1]
            f2.write(f"file './电影_源_解密后/{file_name}'\n")  # 按顺序把这些名字个给存起来
    # 执行 FFmpeg 合并命令
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',          # 允许非安全路径
        '-i', './ts文件按顺序排列.txt',  # 输入文件列表
        '-c', 'copy',          # 直接复制流（不重新编码）
        output_file            # 输出文件
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"合并完成: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"合并失败: {e}")



async def main():
    # m3u8_txt = get_html(url)
    m3u8_url = get_m3u8_url()
    down_m3u8_url(m3u8_url)
    async with aiohttp.ClientSession() as session:
        await download_ts_all(session)

    # 进行解密
    # key = get_key()
    # await(des_all_ts_file(key))

if __name__ == '__main__':
    # asyncio.run(main())
    # key = get_key()
    # asyncio.run(des_all_ts_file(key))
    # 合并视频输出
    merge_ts('奇迹少女伦敦篇.mp4')