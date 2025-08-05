import requests
import feedparser
import os
import time
from datetime import datetime, timedelta

# 환경변수에서 설정값 가져오기
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

def send_message(text):
    """텔레그램으로 메시지 전송"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': CHANNEL_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print(f"✅ 전송 성공: {text[:50]}...")
            return True
        else:
            print(f"❌ 전송 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

def is_recent_article(entry, hours=2.5):
    """최근 N시간 내 글인지 확인 (2시간 주기보다 조금 여유있게)"""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pub_time = time.mktime(entry.published_parsed)
            pub_datetime = datetime.fromtimestamp(pub_time)
            cutoff_time = datetime.now() - timedelta(hours=hours)
            is_recent = pub_datetime > cutoff_time
            
            # 디버깅 정보 출력
            pub_time_str = pub_datetime.strftime('%m-%d %H:%M')
            status = '🆕새글' if is_recent else '⏰이전글'
            print(f"  📅 [{pub_time_str}] {entry.title[:40]}... - {status}")
            
            return is_recent
        else:
            print(f"  ⚠️ 시간 정보 없음: {entry.title[:40]}...")
            return False
    except Exception as e:
        print(f"  ❌ 시간 파싱 오류: {e}")
        return False

def send_bulk_summary(count):
    """대량 전송 시작 알림 (5개 이상일 때)"""
    if count >= 5:
        summary_msg = f"📢 <b>GeekNews 대량 전송 알림</b>\n\n🆕 새로운 글 <b>{count}개</b>를 전송합니다!\n🔔 알림이 많을 수 있으니 양해 부탁드려요."
        send_message(summary_msg)
        time.sleep(3)  # 3초 대기

def check_all_new_posts():
    """새로운 글을 모두 확인하고 전송 (조용한 버전)"""
    print("🔍 GeekNews RSS 피드 분석 중...")
    
    try:
        # RSS 피드 파싱
        feed = feedparser.parse('https://news.hada.io/rss/news')
        
        if not feed.entries:
            print("❌ RSS 피드를 가져올 수 없습니다.")
            send_message("❌ <b>GeekNews 봇 오류</b>\n\nRSS 피드를 가져올 수 없습니다.")
            return
        
        print(f"📰 전체 글 수: {len(feed.entries)}개")
        print(f"🕐 기준 시간: 최근 2.5시간 ({(datetime.now() - timedelta(hours=2.5)).strftime('%m-%d %H:%M')} 이후)")
        
        # 최근 2.5시간 내 모든 글 필터링 (개수 제한 없음)
        print("\n📋 글 목록 분석:")
        new_entries = []
        for entry in feed.entries:
            if is_recent_article(entry, hours=2.5):
                new_entries.append(entry)
        
        print(f"\n🎯 분석 결과: 새로운 글 {len(new_entries)}개 발견")
        
        # 새 글이 없으면 조용히 종료 (알림 없음)
        if not new_entries:
            print("📭 새로운 글이 없습니다. 조용히 종료합니다.")
            return
        
        print(f"🚀 {len(new_entries)}개 새 글 전송을 시작합니다!")
        
        # 5개 이상이면 대량 전송 알림
        send_bulk_summary(len(new_entries))
        
        # 새 글 모두 전송 (개수 제한 없음)
        success_count = 0
        fail_count = 0
        
        for i, entry in enumerate(new_entries):
            title = entry.title
            link = entry.link
            
            # 발행 시간 표시 (있다면)
            time_info = ""
            if hasattr(entry, 'published'):
                time_info = f"\n📅 {entry.published}"
            
            # 글 번호 표시 (3개 이상일 때만)
            number_info = f" <code>({i+1}/{len(new_entries)})</code>" if len(new_entries) >= 3 else ""
            
            # 메시지 구성
            message = f"🆕 <b>{title}</b>{number_info}\n\n🔗 {link}{time_info}\n\n#GeekNews #새글"
            
            # 메시지 전송
            if send_message(message):
                success_count += 1
                print(f"✅ 전송 완료 [{i+1}/{len(new_entries)}]: {title[:30]}...")
            else:
                fail_count += 1
                print(f"❌ 전송 실패 [{i+1}/{len(new_entries)}]: {title[:30]}...")
            
            # 텔레그램 API 제한 고려 (1초 대기)
            time.sleep(1)
            
            # 20개마다 장시간 휴식 (API 제한 방지)
            if (i + 1) % 20 == 0 and i + 1 < len(new_entries):
                print(f"⏸️ 20개 전송 완료. 5초 휴식 중... (남은 글: {len(new_entries) - i - 1}개)")
                time.sleep(5)
        
        # 전송 완료 요약 (새 글이 있었을 때만)
        if success_count > 0:
            summary_parts = [
                "✅ <b>GeekNews 전송 완료!</b>",
                f"📊 성공: <b>{success_count}개</b>"
            ]
            
            if fail_count > 0:
                summary_parts.append(f"⚠️ 실패: <b>{fail_count}개</b>")
            
            total_time = len(new_entries) + (len(new_entries) // 20) * 5  # 대략적인 소요 시간
            summary_parts.append(f"⏱️ 소요 시간: 약 {total_time}초")
            
            summary = "\n".join(summary_parts)
            send_message(summary)
            
        print(f"\n🏁 전송 작업 완료: 성공 {success_count}개, 실패 {fail_count}개")
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ RSS 처리 중 오류 발생: {error_msg}")
        
        # 오류는 중요하므로 알림 전송
        send_message(f"❌ <b>GeekNews 봇 오류</b>\n\n시스템 오류가 발생했습니다:\n<code>{error_msg}</code>")

def main():
    """메인 실행 함수 (조용한 버전)"""
    print("=" * 60)
    print("🤖 GeekNews 스마트 봇 시작!")
    print(f"📡 채널 ID: {CHANNEL_ID}")
    print(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 시간대: UTC (한국 시간 +9시간)")
    print("=" * 60)
    
    # 환경변수 확인
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN이 설정되지 않았습니다!")
        return
    
    if not CHANNEL_ID:
        print("❌ CHANNEL_ID가 설정되지 않았습니다!")
        return
    
    print("✅ 봇 설정 확인 완료")
    print("🔄 RSS 피드 확인을 시작합니다...\n")
    
    # RSS 확인 및 전송 실행
    check_all_new_posts()
    
    print(f"\n🏁 봇 실행 완료 - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()
