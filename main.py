import requests
from bs4 import BeautifulSoup
import json
import os

TELEGRAM_TOKEN = os.environ.get("8275350052:AAEsNV22eML9TaalMrF1wXwIi77HkmM69s0")
TELEGRAM_CHAT_ID = os.environ.get("8759609671")

DATA_FILE = "last_posts.json"

SITES_TO_MONITOR = {
    "서울시_고시공고": {
        "url": "https://www.smc.seoul.kr/board/BoardList.do?boardTypeId=128&menuId=006003",
        "post_list_selector": "table tbody tr",  
        "post_id_selector": "td.num",            
        "post_title_selector": "td.title a"      
    }
}

def load_previous_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_current_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_telegram_message(text):
    """텔레그램 봇 API를 이용해 메시지를 전송합니다."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML" # 링크를 깔끔하게 보내기 위함
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"텔레그램 발송 실패: {e}")

def check_new_posts():
    headers = {'User-Agent': 'Mozilla/5.0'}
    history_data = load_previous_data()

    for site_key, config in SITES_TO_MONITOR.items():
        try:
            response = requests.get(config['url'], headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            post_elements = soup.select(config['post_list_selector'])
            if not post_elements:
                continue

            latest_post = post_elements[0]
            id_elem = latest_post.select_one(config['post_id_selector'])
            title_elem = latest_post.select_one(config['post_title_selector'])
            
            if id_elem and title_elem:
                current_post_id = id_elem.text.strip()
                current_post_title = title_elem.text.strip()
                
                last_seen_id = history_data.get(site_key, "")
                
                if current_post_id != last_seen_id:
                    # 새 글을 발견하면 텔레그램 메시지 조립
                    message = f"🚨 <b>[{site_key}] 새 글 알림</b>\n\n"
                    message += f"<b>제목:</b> {current_post_title}\n"
                    message += f"<a href='{config['url']}'>👉 게시판 바로가기</a>"
                    
                    send_telegram_message(message)
                    history_data[site_key] = current_post_id
                    print(f"새 글 발송 완료: {current_post_title}")
                    
        except Exception as e:
            print(f"[{site_key}] 크롤링 중 에러 발생: {e}")

    save_current_data(history_data)

if __name__ == "__main__":
    check_new_posts()
