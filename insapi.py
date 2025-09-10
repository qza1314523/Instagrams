import requests
import random
import json
import time
from typing import Optional, List, Dict, Any, Union, Tuple

class InstagramAPI:
    def __init__(self):
        self.proxies = []
        self.failed_proxies = set()  # 记录失败的代理
        self.update_proxies()
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 1  # 重试延迟(秒)
    
    def update_proxies(self):
        """获取代理列表"""
        try:
            response = requests.get("https://www.trtrc.com/ipv4.php", timeout=10)
            if response.status_code == 200:
                self.proxies = response.json()
                print(f"成功获取 {len(self.proxies)} 个代理")
        except Exception as e:
            print(f"获取代理失败: {e}")
            # 失败时不清空代理列表，保留之前的代理
    
    def get_random_proxy(self, avoid_failed=True) -> Tuple[Dict[str, str], str]:
        """随机获取一个代理，可选择避免使用失败的代理"""
        if not self.proxies:
            self.update_proxies()
        
        if self.proxies:
            # 过滤掉失败的代理（如果启用）
            available_proxies = [
                proxy for proxy in self.proxies 
                if not avoid_failed or proxy['ip'] not in self.failed_proxies
            ]
            
            if not available_proxies:
                # 如果没有可用代理，重置失败代理列表
                print("所有代理都失败了，重置失败代理列表")
                self.failed_proxies = set()
                available_proxies = self.proxies
            
            proxy = random.choice(available_proxies)
            proxy_dict = {
                "http": f"http://{proxy['ip']}:101",
                "https": f"http://{proxy['ip']}:101"
            }
            return proxy_dict, proxy['name']  # 返回代理字典和代理名称
        return {}, "无可用代理"
    
    def _extract_csrf_token(self, cookie: str) -> str:
        """从cookie中提取csrftoken"""
        if not cookie:
            return "1"  # 默认值
        
        for part in cookie.split(";"):
            if "csrftoken" in part:
                return part.split("=")[1].strip()
        return "1"  # 默认值
    
    def _get_instagram_headers(self, cookie: str, referer: str = "https://www.instagram.com/") -> Dict[str, str]:
        """获取Instagram请求的固定请求头"""
        csrf_token = self._extract_csrf_token(cookie)
        
        return {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            'accept-language': "ja-JP,ja;q=0.9",
            'content-type': "application/x-www-form-urlencoded",
            'origin': "https://www.instagram.com",
            'priority': "u=1, i",
            'referer': referer,
            'sec-ch-prefers-color-scheme': "light",
            'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'sec-ch-ua-full-version-list': '"Not(A:Brand";v="99.0.0.0", "Google Chrome";v="133.0.6943.10", "Chromium";v="133.0.6943.10"',
            'sec-ch-ua-mobile': "?0",
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': "empty",
            'sec-fetch-mode': "cors",
            'sec-fetch-site': "same-origin",
            'x-csrftoken': csrf_token,
            'x-requested-with': "XMLHttpRequest",
            'cookie': cookie
        }
    
    def _make_request(self, method: str, url: str, headers: Dict[str, str], 
                     data: Optional[Union[Dict[str, Any], str]] = None, 
                     use_proxy: bool = False, 
                     proxy: Optional[Dict[str, str]] = None,
                     timeout: int = 10) -> Optional[requests.Response]:
        """通用的请求方法，支持代理失败重试"""
        retries = 0
        used_proxies = set()  # 记录本次请求已使用的代理
        
        while retries <= self.max_retries:
            try:
                # 确定使用的代理
                if use_proxy:
                    # 避免使用已经失败的代理和本次请求已使用的代理
                    final_proxy, proxy_name = self.get_random_proxy(avoid_failed=True)
                    
                    # 如果所有代理都已尝试过，返回错误
                    if not final_proxy:
                        print("所有代理都已失败，无法继续请求")
                        return None
                    
                    # 记录使用的代理
                    proxy_ip = final_proxy['http'].split('//')[1].split(':')[0]
                    used_proxies.add(proxy_ip)
                    print(f"使用代理: {proxy_name} ({proxy_ip})")
                else:
                    final_proxy = proxy
                    if proxy:
                        proxy_ip = proxy.get('http', '未知代理').split('//')[1].split(':')[0]
                        print(f"使用用户提供的代理: {proxy_ip}")
                    else:
                        print("不使用代理")
                
                # 处理数据
                if isinstance(data, dict):
                    processed_data = {}
                    for k, v in data.items():
                        if isinstance(v, (dict, list)):
                            processed_data[k] = json.dumps(v)
                        else:
                            processed_data[k] = v
                else:
                    processed_data = data
                
                # 发送请求
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, proxies=final_proxy, timeout=timeout)
                else:
                    response = requests.post(url, headers=headers, data=processed_data, proxies=final_proxy, timeout=timeout)
                
                # 如果请求成功，返回响应
                if response.status_code == 200:
                    return response
                else:
                    print(f"请求失败，状态码: {response.status_code}")
                    
            except Exception as e:
                print(f"请求失败 (尝试 {retries + 1}/{self.max_retries + 1}): {e}")
                
                # 记录失败的代理
                if use_proxy and 'proxy_ip' in locals():
                    self.failed_proxies.add(proxy_ip)
                    print(f"标记代理 {proxy_ip} 为失败")
            
            # 如果使用代理且请求失败，更新代理并重试
            if use_proxy:
                retries += 1
                if retries <= self.max_retries:
                    print(f"{self.retry_delay}秒后重试...")
                    time.sleep(self.retry_delay)
                else:
                    print("所有重试次数已用尽")
            else:
                break  # 不使用代理时，不重试
        
        return None
    
    def check_account_exists(self, username: str) -> Any:
        """判断账号是否存在，存在返回ID，不存在返回False"""
        url = "https://www.instagram.com/ajax/navigation/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'sec-fetch-site': 'same-origin',
            'x-asbd-id': '359341',
            'x-fb-lsd': '1'
        }
        
        data = {
            'route_url': f'/{username}/',
            '__a': '1',
            '__comet_req': '7',
            'lsd': '1'
        }
        
        response = self._make_request("POST", url, headers, data, use_proxy=True)
        
        if response and response.status_code == 200:
            # 使用字符串查找ID
            response_text = response.text
            id_start = response_text.find('"id":"')
            if id_start != -1:
                id_start += 6  # 跳过 '"id":"'
                id_end = response_text.find('"', id_start)
                if id_end != -1:
                    return response_text[id_start:id_end]
            return False
        return False
    
    def get_profile_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """ID获取主页信息"""
        url = "https://www.instagram.com/graphql/query"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-csrftoken': '1'
        }
        
        variables = {
            "enable_integrity_filters": True,
            "id": user_id,
            "render_surface": "PROFILE",
            "__relay_internal__pv__PolarisProjectCannesEnabledrelayprovider": False,
            "__relay_internal__pv__PolarisProjectCannesLoggedInEnabledrelayprovider": False,
            "__relay_internal__pv__PolarisProjectCannesLoggedOutEnabledrelayprovider": False,
            "__relay_internal__pv__PolarisCannesGuardianExperienceEnabledrelayprovider": False,
            "__relay_internal__pv__PolarisCASB976ProfileEnabledrelayprovider": False
        }
        
        data = {
            'fb_dtsg': '1',
            'variables': variables,
            'doc_id': '24621196980843703'
        }
        
        response = self._make_request("POST", url, headers, data, use_proxy=True)
        
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_user_posts(self, username: str) -> Optional[Dict[str, Any]]:
        """账号获取投稿信息"""
        url = "https://www.instagram.com/graphql/query"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-csrftoken': '1'
        }
        
        variables = {
            "data": {
                "count": 12,
                "include_reel_media_seen_timestamp": True,
                "include_relationship_info": True,
                "latest_besties_reel_media": True,
                "latest_reel_media": True
            },
            "username": username,
            "__relay_internal__pv__PolarisIsLoggedInrelayprovider": True
        }
        
        data = {
            'variables': variables,
            'doc_id': '32435654999367421'
        }
        
        response = self._make_request("POST", url, headers, data, use_proxy=True)
        
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_hashtag_popularity(self, hashtag: str, cookie: str, 
                              proxy: Optional[Dict] = None, 
                              referer: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取标签热度"""
        url = f"https://www.instagram.com/api/v1/web/search/topsearch/?context=hashtag&query={hashtag}"
        headers = self._get_instagram_headers(cookie, referer or "https://www.instagram.com/")
        
        response = self._make_request("GET", url, headers, use_proxy=False, proxy=proxy)
        
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def search_hashtag_posts(self, hashtag: str, cookie: str, 
                            proxy: Optional[Dict] = None,
                            referer: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """搜索标签投稿"""
        url = f"https://www.instagram.com/api/v1/fbsearch/web/top_serp/?query=%23{hashtag}"
        headers = self._get_instagram_headers(cookie, referer or "https://www.instagram.com/")
        headers['x-ig-app-id'] = '936619743392459'
        
        response = self._make_request("GET", url, headers, use_proxy=False, proxy=proxy)
        
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def follow_user(self, target_user_id: str, cookie: str, 
                   proxy: Optional[Dict] = None,
                   referer: Optional[str] = None) -> bool:
        """点击关注"""
        url = "https://www.instagram.com/graphql/query"
        headers = self._get_instagram_headers(cookie, referer or "https://www.instagram.com/")
        headers['x-ig-app-id'] = '936619743392459'
        
        variables = {
            "target_user_id": target_user_id,
            "container_module": "profile",
            "nav_chain": "PolarisProfilePostsTabRoot:profilePage:1:via_cold_start"
        }
        
        data = {
            'fb_dtsg': 'NAfvpmARbjk7-eqFTcM6G_rLG2MgeSptE-UO9dGG7qQCu_nzQ7413fw:17864970403026470:1755646376',
            'variables': variables,
            'server_timestamps': 'true',
            'doc_id': '9740159112729312'
        }
        
        response = self._make_request("POST", url, headers, data, use_proxy=False, proxy=proxy)
        
        return response is not None and response.status_code == 200
    
    def like_post(self, post_id: str, cookie: str, 
                 proxy: Optional[Dict] = None,
                 referer: Optional[str] = None) -> bool:
        """点击点赞"""
        url = f"https://www.instagram.com/api/v1/web/likes/{post_id}/like/"
        headers = self._get_instagram_headers(cookie, referer or "https://www.instagram.com/")
        headers['x-ig-app-id'] = '936619743392459'
        
        response = self._make_request("POST", url, headers, use_proxy=False, proxy=proxy)
        
        return response is not None and response.status_code == 200

# 辅助函数：截断长文本
def truncate_text(text, max_length=100):
    """截断文本到指定长度，添加省略号"""
    if text is None:
        return "None"
    text_str = str(text)
    if len(text_str) > max_length:
        return text_str[:max_length] + "..."
    return text_str

# 测试代码
if __name__ == "__main__":
    api = InstagramAPI()
    
    # 测试获取代理
    print("代理列表:", api.proxies)
    
    # 测试检查账号是否存在
    exists = api.check_account_exists("cheers_enrich")
    print(f"账号是否存在: {exists}")
    
    # 测试获取主页信息 (需要有效的用户ID)
    if exists:
        profile = api.get_profile_info(exists)
        print("主页信息:", truncate_text(str(profile)))
    
    # 测试获取用户投稿 (需要有效的用户名)
    posts = api.get_user_posts("cheers_enrich")
    print("用户投稿:", truncate_text(str(posts)))
    
    # 测试获取标签热度 (需要有效的cookie)
    # popularity = api.get_hashtag_popularity("花火大会", "你的cookie")
    # print("标签热度:", truncate_text(str(popularity)))
    
    # 测试搜索标签投稿 (需要有效的cookie)
    # hashtag_posts = api.search_hashtag_posts("ootdmagazine", "你的cookie")
    # print("标签投稿:", truncate_text(str(hashtag_posts)))
    
    # 测试关注用户 (需要有效的cookie和目标用户ID)
    # follow_result = api.follow_user("目标用户ID", "你的cookie")
    # print(f"关注结果: {follow_result}")
    
    # 测试点赞帖子 (需要有效的cookie和帖子ID)
    # like_result = api.like_post("帖子ID", "你的cookie")
    # print(f"点赞结果: {like_result}")