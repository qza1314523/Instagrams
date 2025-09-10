import re
import requests
import pyotp
from fake_useragent import UserAgent

def login(username: str, password: str, two_fa: str = None, proxy: str = None):
    """
    使用用户名和密码登录 Instagram，支持代理和两步验证。

    Args:
        username (str): Instagram 账户的用户名。
        password (str): Instagram 账户的密码。
        two_fa (str, optional): Google Authenticator 或类似的 TOTP 密钥。默认为 None。
        proxy (str, optional): HTTP 代理地址，例如 '127.0.0.1:100'。默认为 None。

    Returns:
        dict: 包含登录状态和最终 Cookies 的字典。例如：
              {'status': '登录成功', 'cookies': {...}}
              {'status': '密码错误', 'cookies': None}
              {'status': '2FA', 'cookies': None}
              {'status': '请求失败', 'cookies': None}
    """
    
    # --- 内部辅助函数 ---
    
    def _get_proxies(proxy_str: str) -> dict:
        if proxy_str:
            return {
                "http": f"http://{proxy_str}",
                "https": f"http://{proxy_str}",
            }
        return {}

    def _get_csrf_token(user_agent: str, proxies: dict) -> dict:
        try:
            r = requests.get(
                "https://www.instagram.com/",
                headers={"User-Agent": user_agent},
                proxies=proxies,
                timeout=10
            )
            text = r.text
            cookies = r.cookies

            def _search(pattern, default=None):
                match = re.search(pattern, text)
                return match.group(1) if match else default

            return {
                "mid": cookies.get("mid") or _search(r'"machine_id":"(.*?)"'),
                "csrftoken": cookies.get("csrftoken") or _search(r'"csrf_token":"(.*?)"'),
                "datr": cookies.get("datr") or _search(r'qeid\\":\\"(.*?)\\",.*?fb_loggedout'),
                "ig_did": cookies.get("ig_did") or _search(r'"device_id":"([0-9A-F-]{36})"'),
                "ps_l": "1",
                "ps_n": "1",
                "ig_nrcb": "1",
                "wd": "1720x1203",
                "ig_lang": "zh-cn"
            }
        except Exception as e:
            print(f"获取初始 Cookies 失败: {e}")
            return {}

    def _create_session(cookies: dict, user_agent: str, referer: str, proxies: dict) -> requests.Session:
        session = requests.Session()
        session.cookies.update(cookies)
        session.proxies = proxies
        session.headers.update({
            "User-Agent": user_agent,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": referer,
            "X-CSRFToken": cookies.get("csrftoken", ""),
            "X-IG-App-ID": "936619743392459"
        })
        return session

    def _send_post(session: requests.Session, url: str, data: dict) -> dict:
        try:
            return session.post(url, data=data, timeout=10).json()
        except Exception as e:
            print(f"POST 请求失败: {e}")
            return {"status": "fail", "error_message": str(e)}

    def _get_cookie_value(session: requests.Session, cookie_name: str) -> str:
        """安全获取cookie值，处理多个同名cookie的情况"""
        try:
            # 尝试直接获取
            return session.cookies.get(cookie_name)
        except requests.cookies.CookieConflictError:
            # 如果有多个同名cookie，获取第一个
            for cookie in session.cookies:
                if cookie.name == cookie_name:
                    return cookie.value
            return ""

    # --- 主登录流程 ---

    ua = UserAgent()
    user_agent = next((ua.chrome for _ in range(100) if "Windows" in ua.chrome), "")
    if not user_agent:
        user_agent = ua.chrome

    proxies = _get_proxies(proxy)
    initial_cookies = _get_csrf_token(user_agent, proxies)
    if not initial_cookies or "csrftoken" not in initial_cookies:
        return {"status": "请求失败", "cookies": None}

    print("初始 Cookies:", initial_cookies)

    session = _create_session(initial_cookies, user_agent, "https://www.instagram.com/accounts/login/", proxies)

    login_url = "https://www.instagram.com/accounts/login/ajax/"
    login_data = {
        "username": username,
        "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:0:{password}",
        "csrfmiddlewaretoken": initial_cookies["csrftoken"],
    }

    response = _send_post(session, login_url, login_data)

    # --- 处理 2FA ---
    if response.get("two_factor_required"):
        if two_fa:
            try:
                totp = pyotp.TOTP(two_fa)
                verification_code = totp.now()
            except Exception as e:
                print(f"生成 2FA 验证码失败: {e}")
                return {"status": "2FA密钥无效", "cookies": None}

            two_factor_identifier = response.get("two_factor_info", {}).get("two_factor_identifier")
            two_factor_data = {
                'isPrivacyPortalReq': "false",
                'queryParams': "{\"next\":\"/\"}",
                'trust_signal': "true",
                'username': username,
                'verificationCode': verification_code,
                'identifier': two_factor_identifier,
            }
            
            # 为2FA请求更新特定的headers
            csrf_token = _get_cookie_value(session, "csrftoken")
            session.headers.update({
                "X-CSRFToken": csrf_token,
                "Referer": "https://www.instagram.com/accounts/login/two_factor?next=%2F"
            })
            
            two_factor_url = "https://www.instagram.com/api/v1/web/accounts/login/ajax/two_factor/"
            response = _send_post(session, two_factor_url, two_factor_data)

            if response.get("authenticated") and response.get("status") == "ok":
                final_cookies = {**initial_cookies, **session.cookies.get_dict()}
                return {"status": "登录成功", "cookies": final_cookies}
            else:
                print(f"2FA 验证失败: {response}")
                return {"status": "2FA验证失败", "cookies": None}
        else:
            return {"status": "2FA", "cookies": None}

    # --- 普通登录判断 ---
    elif response.get("authenticated") and response.get("status") == "ok":
        final_cookies = {**initial_cookies, **session.cookies.get_dict()}
        print("登录成功！")
        return {"status": "登录成功", "cookies": final_cookies}

    else:
        print(f"登录失败: {response.get('message', '密码错误')}")
        return {"status": "密码错误", "cookies": None}


# --- 示例调用 ---
if __name__ == "__main__":
    two_fa_key = "PCTSULA7JDVNETAUCQ2KBIGUM463575B"  # 替换为你的实际 2FA 密钥
    proxy_address = "163.61.207.113:101"  # 替换为你的代理地址

    print("--- 尝试使用错误密码登录 ---")
    result_fail = login("shengda100090", "Qq112233", two_fa=two_fa_key, proxy=proxy_address)
    print("返回结果:", result_fail)

    # 登录成功示例 (需要真实用户名和密码)
    # result_success = login("your_username", "your_password", two_fa=two_fa_key, proxy=proxy_address)
    # print("返回结果:", result_success)