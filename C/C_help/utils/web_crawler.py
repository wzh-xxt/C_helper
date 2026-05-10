import os
import requests
from bs4 import BeautifulSoup
import time

def fetch_clang_analyzer(save_path):
    # 兜底静态内容
    fallback = [
        "core.DivideZero: 检查除零错误",
        "core.NullDereference: 检查空指针解引用",
        "core.UndefinedBinaryOperatorResult: 检查未定义二元运算",
        "unix.Malloc: 检查内存分配相关错误",
        "security.insecureAPI: 检查不安全API使用"
    ]
    try:
        # 直接用GitHub的rst文档
        url = "https://raw.githubusercontent.com/llvm/llvm-project/main/clang/docs/analyzer/checkers.rst"
        resp = requests.get(url, timeout=10)
        print(resp.status_code)
        if resp.status_code == 200:
            lines = []
            for line in resp.text.splitlines():
                if line.strip().startswith(("The rule","The goal","Warn","This checker","The checker","Check","core.", "unix.", "cplusplus.", "security.", "deadcode.", "optin.", "osx.", "apiModeling.")):
                    lines.append(line)
                    print(line)
            if lines:
                with open(save_path, "w", encoding="utf-8") as f:
                    for rule in lines:
                        f.write(rule + "\n")
                print(f"已自动抓取Clang Static Analyzer规则，共{len(lines)}条")
                return
    except Exception as e:
        print(f"Clang规则抓取失败，使用本地静态内容: {e}")
    # 兜底
    with open(save_path, "w", encoding="utf-8") as f:
        for rule in fallback:
            f.write(rule + "\n")
    print("已写入Clang Static Analyzer静态规则")

def fetch_cppcheck(save_path):
    try:
        url = "https://cppcheck.sourceforge.io/manual.html#available-checks"
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        rules = []
        for li in soup.select("ul li"):
            text = li.get_text(strip=True)
            if text and "-" in text:
                rules.append(text)
        if rules:
            with open(save_path, "w", encoding="utf-8") as f:
                for rule in rules:
                    f.write(rule + "\n")
            print(f"已自动抓取Cppcheck规则，共{len(rules)}条")
            return
    except Exception as e:
        print(f"Cppcheck规则抓取失败，使用本地静态内容: {e}")
    # 兜底
    fallback = [
        "uninitvar: 检查未初始化变量",
        "memleak: 检查内存泄漏",
        "bufferAccessOutOfBounds: 检查缓冲区越界",
        "nullPointer: 检查空指针解引用",
        "useClosedFile: 检查对已关闭文件的使用"
    ]
    with open(save_path, "w", encoding="utf-8") as f:
        for rule in fallback:
            f.write(rule + "\n")
    print("已写入Cppcheck静态规则")

def fetch_stackoverflow(save_path, tag="c", pagesize=100):
    try:
        url = f"https://api.stackexchange.com/2.3/questions?order=desc&sort=votes&tagged={tag}&site=stackoverflow&filter=withbody&pagesize={pagesize}"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        with open(save_path, "w", encoding="utf-8") as f:
            for item in data.get("items", []):
                f.write(f"Title: {item['title']}\n")
                f.write(f"Link: {item['link']}\n")
                f.write(f"Body: {BeautifulSoup(item['body'], 'html.parser').get_text()}\n\n")
        print(f"已抓取Stack Overflow高票问答{len(data.get('items', []))}条")
    except Exception as e:
        print(f"Stack Overflow抓取失败: {e}")

def fetch_cppreference(save_path, url_list):
    try:
        with open(save_path, "w", encoding="utf-8") as f:
            for url in url_list:
                resp = requests.get(url, timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.find("h1").get_text(strip=True)
                desc = soup.find("div", {"id": "mw-content-text"}).get_text(strip=True)[:500]
                f.write(f"{title}\n{desc}\n\n")
                time.sleep(1)
        print(f"已抓取cppreference函数说明{len(url_list)}条")
    except Exception as e:
        print(f"cppreference抓取失败: {e}")

def auto_update_all():
    os.makedirs("data/external_defects", exist_ok=True)
    os.makedirs("data/rag_resources", exist_ok=True)
    # fetch_clang_analyzer("data/external_defects/clang_analyzer.txt")
    # fetch_cppcheck("data/external_defects/cppcheck.txt")
    # fetch_stackoverflow("data/rag_resources/stackoverflow.txt", tag="c", pagesize=50)
    # fetch_cppreference("data/rag_resources/cppreference.txt", [
    #     # 字符串操作
    #     "https://en.cppreference.com/w/c/string/byte/strcpy",
    #     "https://en.cppreference.com/w/c/string/byte/strncpy",
    #     "https://en.cppreference.com/w/c/string/byte/strcat",
    #     "https://en.cppreference.com/w/c/string/byte/strncat",
    #     "https://en.cppreference.com/w/c/string/byte/strcmp",
    #     "https://en.cppreference.com/w/c/string/byte/strncmp",
    #     "https://en.cppreference.com/w/c/string/byte/strlen",
    #     "https://en.cppreference.com/w/c/string/byte/memcpy",
    #     "https://en.cppreference.com/w/c/string/byte/memmove",
    #     "https://en.cppreference.com/w/c/string/byte/memset",
    #     "https://en.cppreference.com/w/c/string/byte/memcmp",
    #     # 内存管理
    #     "https://en.cppreference.com/w/c/memory/malloc",
    #     "https://en.cppreference.com/w/c/memory/calloc",
    #     "https://en.cppreference.com/w/c/memory/realloc",
    #     "https://en.cppreference.com/w/c/memory/free",
    #     # 文件 I/O
    #     "https://en.cppreference.com/w/c/io/fopen",
    #     "https://en.cppreference.com/w/c/io/fclose",
    #     "https://en.cppreference.com/w/c/io/fread",
    #     "https://en.cppreference.com/w/c/io/fwrite",
    #     "https://en.cppreference.com/w/c/io/fseek",
    #     "https://en.cppreference.com/w/c/io/ftell",
    #     "https://en.cppreference.com/w/c/io/fgetc",
    #     "https://en.cppreference.com/w/c/io/fputc",
    #     "https://en.cppreference.com/w/c/io/fgets",
    #     "https://en.cppreference.com/w/c/io/fputs",
    #     # 数学函数
    #     "https://en.cppreference.com/w/c/numeric/math/abs",
    #     "https://en.cppreference.com/w/c/numeric/math/labs",
    #     "https://en.cppreference.com/w/c/numeric/math/fabs",
    #     "https://en.cppreference.com/w/c/numeric/math/sqrt",
    #     "https://en.cppreference.com/w/c/numeric/math/pow",
    #     "https://en.cppreference.com/w/c/numeric/math/ceil",
    #     "https://en.cppreference.com/w/c/numeric/math/floor",
    #     "https://en.cppreference.com/w/c/numeric/math/fmod",
    #     # 类型转换
    #     "https://en.cppreference.com/w/c/string/byte/atoi",
    #     "https://en.cppreference.com/w/c/string/byte/atol",
    #     "https://en.cppreference.com/w/c/string/byte/atof",
    #     # 其他常用
    #     "https://en.cppreference.com/w/c/string/byte/memchr",
    #     "https://en.cppreference.com/w/c/string/byte/strchr",
    #     "https://en.cppreference.com/w/c/string/byte/strrchr",
    #     "https://en.cppreference.com/w/c/string/byte/strstr",
    # ])

if __name__ == "__main__":
    auto_update_all()