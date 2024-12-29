import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import logging

# 로깅 설정
def setup_logger(debug_mode=False):
    level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

# 텍스트 파일 읽기
def read_chat(file_path):
    with open(file_path, encoding='utf-8') as file:
        return file.readlines()

# 저장 날짜 추출
def extract_saved_date(lines):
    saved_date_match = re.search(r'저장한 날짜 : (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', lines[1])
    if saved_date_match:
        return datetime.strptime(saved_date_match.group(1), '%Y-%m-%d %H:%M:%S')
    raise ValueError("파일에서 저장 날짜를 찾을 수 없습니다.")

# 대화 내용 파싱
def parse_chat(lines):
    pattern = r'\[(.*?)\] \[(.*?)\] (.*)'
    messages = []
    current_date = None

    for line in lines:
        # 디버깅용 출력
        logging.debug(f"처리 중인 라인: {line.strip()}")

        # 날짜 변경 감지
        date_match = re.match(r'-+ (\d{4}년 \d{1,2}월 \d{1,2}일).* -+', line)
        if date_match:
            try:
                current_date = datetime.strptime(date_match.group(1), '%Y년 %m월 %d일').date()
                logging.debug(f"감지된 날짜: {current_date}")
            except ValueError as e:
                logging.error(f"날짜 파싱 실패: {e}")
            continue

        # 메시지 파싱
        match = re.match(pattern, line)
        if match and current_date:
            user = match.group(1)
            timestamp = match.group(2)
            message = match.group(3)

            # 시간 변환: "오전" → "AM", "오후" → "PM"
            timestamp = timestamp.replace("오전", "AM").replace("오후", "PM")

            # 날짜와 시간 추출
            try:
                time_obj = datetime.strptime(timestamp, '%p %I:%M').time()
            except ValueError as e:
                logging.error(f"시간 파싱 실패: {e}, 라인: {line.strip()}")
                continue

            # 날짜와 시간을 합쳐 datetime 생성
            date_time_obj = datetime.combine(current_date, time_obj)
            messages.append((user, date_time_obj, message))

    return messages

# 지정된 기간 동안의 대화 추출
def filter_chats_in_period(messages, reference_date, period_days):
    start_date = reference_date - timedelta(days=period_days)
    return [msg for msg in messages if msg[1] >= start_date]

# 참여율 계산
def calculate_participation(messages):
    user_counts = Counter([msg[0] for msg in messages])
    total_messages = sum(user_counts.values())
    participation_rate = {user: (count / total_messages) * 100 for user, count in user_counts.items()}
    return participation_rate

# 사용자별 가장 최근 대화 일자 찾기
def find_latest_message_per_user(messages):
    latest_messages = defaultdict(lambda: datetime.min)
    for user, timestamp, _ in messages:
        if timestamp > latest_messages[user]:
            latest_messages[user] = timestamp

    return latest_messages

# 메인 함수
def main(debug_mode=False):
    import argparse

    setup_logger(debug_mode)

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, required=True, help="분석할 카카오톡 대화 파일 경로")
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화")
    args = parser.parse_args()

    file_path = args.file
    lines = read_chat(file_path)

    # 저장 날짜 추출
    saved_date = extract_saved_date(lines)
    logging.debug(f"저장 날짜: {saved_date}")

    messages = parse_chat(lines)

    # 사용자 입력을 통해 분석 기간 설정
    try:
        period_days = int(input("분석할 기간(일)을 입력하세요 (예: 30): "))
    except ValueError:
        print("잘못된 입력입니다. 기본값 30일로 설정합니다.")
        period_days = 30

    # 지정된 기간 동안 데이터 분석
    period_messages = filter_chats_in_period(messages, saved_date, period_days)
    participation = calculate_participation(period_messages)
    latest_messages = find_latest_message_per_user(period_messages)

    # 참여율 출력
    print(f"지난 {period_days}일간 대화 참여율:")
    for user, rate in sorted(participation.items(), key=lambda x: x[1], reverse=True):
        print(f"{user}: {rate:.2f}%")

    # 사용자별 가장 최근 대화 일자 출력
    print(f"\n사용자별 가장 최근 대화 일자 (지난 {period_days}일):")
    for user, timestamp in sorted(latest_messages.items(), key=lambda x: x[1], reverse=True):
        print(f"{user}: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    import sys
    main(debug_mode="--debug" in sys.argv)
