import os
import logging
import sys

# --- 상수 정의 ---
SEPARATOR = ": "
OUTPUT_DIR_NAME = "outputs"
LOGS_DIR_NAME = "logs"
LOG_FORMAT = '[%(asctime)s][%(levelname)s] %(message)s'
LOGGER_NAME = 'ChatLogFilter'

# --- 기본 설정 ---
# 입력 로그 파일 경로 (스크립트 실행 시 변경 가능하도록 남겨둘 수 있음)
DEFAULT_INPUT_LOG_FILE = r'e:\ChzzkChat-main\chat_samples\chat copy 2.log'

# 무시할 패턴 리스트
DEFAULT_IGNORE_PATTERNS = [
    "{",
    "}",
    "[SYSTEM]",
    "***님이 입장했습니다.",
    # 필요에 따라 추가
]

def prepare_environment(input_log_file, output_dir, logs_dir):
    """
    입력 파일 존재 여부 확인, 출력 및 로그 디렉토리 생성, 파일 경로 설정.
    Returns:
        dict: input_path, output_chat_path, run_log_path를 포함하는 딕셔너리
    Raises:
        FileNotFoundError: 입력 파일이 존재하지 않을 경우
    """
    if not os.path.isfile(input_log_file):
        raise FileNotFoundError(f"[ERROR] 입력 파일 '{input_log_file}'을(를) 찾을 수 없습니다.")

    # 디렉토리 생성 (이미 존재하면 무시)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    # 파일 경로 생성
    input_base = os.path.basename(input_log_file)
    input_name, input_ext = os.path.splitext(input_base)
    output_chat_path = os.path.join(output_dir, f"{input_name}_messages_only{input_ext}")
    run_log_path = os.path.join(logs_dir, f"{input_name}_filter_run.log")

    return {
        "input": input_log_file,
        "output_chat": output_chat_path,
        "run_log": run_log_path
    }

def setup_logger(log_file_path, logger_name=LOGGER_NAME, log_format=LOG_FORMAT):
    """로거 설정 및 반환"""
    logger = logging.getLogger(logger_name)
    # 핸들러 중복 추가 방지
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(log_format)

    # 파일 핸들러
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def filter_chat_log(input_path, output_path, ignore_patterns, separator, logger):
    """로그 파일을 필터링하고 결과를 새 파일에 저장"""
    logger.info(f"로그 파일 처리 시작: {input_path}")
    total_lines = 0
    ignored_lines = 0
    processed_lines = 0

    try:
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:

            for line in infile:
                total_lines += 1

                # 1. 무시 패턴 확인
                if any(pattern in line for pattern in ignore_patterns):
                    ignored_lines += 1
                    continue

                # 2. 구분자 위치 찾기
                separator_pos = line.find(separator)

                # 3. 메시지 추출 및 저장
                if separator_pos != -1:
                    message_start_pos = separator_pos + len(separator)
                    message = line[message_start_pos:]
                    if message.strip():
                        outfile.write(message)
                        processed_lines += 1
                # else:
                    # logger.warning(f"구분자 '{separator}' 없음 - 라인 {total_lines}: {line.strip()}")

        logger.info("처리 완료.")
        logger.info(f"  총 읽은 줄 수: {total_lines}")
        logger.info(f"  무시된 줄 수 (지정된 패턴 포함): {ignored_lines}")
        logger.info(f"  추출된 채팅 메시지 수: {processed_lines}")
        logger.info(f"  결과 저장 파일: {output_path}")
        return True # 성공 시 True 반환

    except IOError as e:
        logger.error(f"파일 읽기/쓰기 오류 발생 ('{input_path}' 또는 '{output_path}'): {e}")
        return False # 실패 시 False 반환

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    logger = None # 로거 초기화 (오류 발생 시 참조 위함)
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, OUTPUT_DIR_NAME)
        logs_dir = os.path.join(script_dir, LOGS_DIR_NAME)

        # 입력 파일 경로 설정 (필요 시 argparse 등으로 변경 가능)
        input_log_file = DEFAULT_INPUT_LOG_FILE
        # 만약 입력 파일 경로가 상대 경로라면 스크립트 기준 또는 작업 디렉토리 기준으로 해석될 수 있음
        # 절대 경로 사용 권장 또는 os.path.join(script_dir, ...) 사용 고려

        paths = prepare_environment(input_log_file, output_dir, logs_dir)

        # 2. 로거 설정
        logger = setup_logger(paths["run_log"])

        # 3. 실행 정보 로깅
        logger.info("스크립트 실행 시작")
        logger.info(f"입력 로그 파일: {paths['input']}")
        logger.info(f"추출된 메시지 저장 파일: {paths['output_chat']}")
        logger.info(f"실행 로그 파일: {paths['run_log']}")
        logger.info(f"무시할 패턴: {DEFAULT_IGNORE_PATTERNS}") # 설정값 사용

        # 4. 핵심 로직 실행
        success = filter_chat_log(
            input_path=paths['input'],
            output_path=paths['output_chat'],
            ignore_patterns=DEFAULT_IGNORE_PATTERNS, # 설정값 사용
            separator=SEPARATOR, # 상수 사용
            logger=logger
        )
        if not success:
             sys.exit(1) # 필터링 중 오류 발생 시 종료 코드 1

    except FileNotFoundError as e:
        # 환경 준비 단계에서 오류 발생 시 (로거 설정 전일 수 있음)
        print(e, file=sys.stderr) # 표준 에러로 출력
        if logger: logger.error(f"초기화 오류: {e}") # 로거가 있다면 로그도 남김
        sys.exit(1) # 종료 코드 1
    except Exception as e:
        # 예상치 못한 오류 처리
        error_message = f"예상치 못한 오류 발생: {e}"
        print(error_message, file=sys.stderr)
        if logger: logger.exception(error_message) # 스택 트레이스 포함 로깅
        sys.exit(1) # 종료 코드 1
    finally:
        if logger:
            logger.info("스크립트 실행 종료")
        # logging.shutdown() # 필요 시 로깅 시스템 종료
