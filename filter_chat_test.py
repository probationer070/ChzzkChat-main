import os
import logging
import sys
import glob

# --- 설정 클래스 정의 ---
class Config:
    """스크립트 설정을 관리하는 클래스"""
    def __init__(self):
        # 파일 및 디렉토리 이름
        self.INPUT_DIR_NAME = "chat_samples"
        self.OUTPUT_DIR_NAME = "outputs"
        self.LOGS_DIR_NAME = "logs"
        self.COMBINED_OUTPUT_FILE_NAME = "filtered_messages.log"
        self.RUN_LOG_FILE_NAME = "batch_filter_run.log"

        # 파일 처리 관련 설정
        self.INPUT_FILE_PATTERN = "chat*.log"
        self.SEPARATOR = ": "
        self.DEFAULT_IGNORE_PATTERNS = [
            "{",
            "}",
            "[SYSTEM]",
            "***님이 입장했습니다.",
            "ㅋㅋㅋ", "??", "...", "ㄷㄷ"
            # 필요에 따라 추가
        ]

        # 로깅 관련 설정
        self.LOGGER_NAME = 'ChatLogBatchFilter'
        self.LOG_FORMAT = '[%(asctime)s][%(levelname)s] %(message)s'

# --- 처리 로직 클래스 ---
class ChatLogProcessor:
    """채팅 로그 파일을 처리하는 클래스"""

    def __init__(self, config: Config):
        """프로세서 초기화 및 환경 설정"""
        self.config = config
        self.logger = None # 초기화
        self._prepare_environment()
        self._setup_logger()

    def _prepare_environment(self):
        """입력/출력/로그 디렉토리 준비 및 경로 설정"""
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_dir = os.path.join(self.script_dir, self.config.INPUT_DIR_NAME)
        self.output_dir = os.path.join(self.script_dir, self.config.OUTPUT_DIR_NAME)
        self.logs_dir = os.path.join(self.script_dir, self.config.LOGS_DIR_NAME)

        if not os.path.isdir(self.input_dir):
            # 로거 설정 전이므로 print 사용 또는 예외 발생
            raise FileNotFoundError(f"[ERROR] 입력 디렉토리 '{self.input_dir}'을(를) 찾을 수 없습니다.")

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self.combined_output_path = os.path.join(self.output_dir, self.config.COMBINED_OUTPUT_FILE_NAME)
        self.run_log_path = os.path.join(self.logs_dir, self.config.RUN_LOG_FILE_NAME)

    def _setup_logger(self):
        """로거 설정"""
        self.logger = logging.getLogger(self.config.LOGGER_NAME)
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(self.config.LOG_FORMAT)

        # 파일 핸들러
        file_handler = logging.FileHandler(self.run_log_path, encoding='utf-8', mode='a')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _filter_single_log_file(self, input_path, outfile_handle):
        """
        단일 로그 파일을 필터링하고 결과를 제공된 파일 핸들(outfile_handle)에 씁니다.
        (self를 통해 config 값과 logger에 접근)
        Returns:
            tuple: (처리된 라인 수, 무시된 라인 수, 저장된 메시지 수)
        """
        self.logger.debug(f"파일 처리 시작: {input_path}")
        lines_read = 0
        lines_ignored = 0
        messages_written = 0

        try:
            with open(input_path, 'r', encoding='utf-8') as infile:
                for line in infile:
                    lines_read += 1

                    # 1. 무시 패턴 확인 (self.config 사용)
                    if any(pattern in line for pattern in self.config.DEFAULT_IGNORE_PATTERNS):
                        lines_ignored += 1
                        continue

                    # 2. 구분자 위치 찾기 (self.config 사용)
                    separator_pos = line.find(self.config.SEPARATOR)

                    # 3. 메시지 추출 및 저장
                    if separator_pos != -1:
                        message_start_pos = separator_pos + len(self.config.SEPARATOR)
                        message = line[message_start_pos:]
                        if message.strip():
                            outfile_handle.write(message)
                            messages_written += 1

        except IOError as e:
            self.logger.error(f"파일 읽기 오류 발생 ('{input_path}'): {e}")
            return lines_read, lines_ignored, messages_written
        except Exception as e:
            self.logger.exception(f"파일 처리 중 예상치 못한 오류 발생 ('{input_path}'):")
            return lines_read, lines_ignored, messages_written

        self.logger.debug(f"파일 처리 완료: {input_path} (읽음: {lines_read}, 무시: {lines_ignored}, 저장: {messages_written})")
        return lines_read, lines_ignored, messages_written

    def _process_directory(self):
        """
        지정된 디렉토리에서 패턴과 일치하는 모든 로그 파일을 찾아 필터링하고,
        결과를 단일 출력 파일에 누적하여 저장합니다.
        (self를 통해 필요한 설정과 경로에 접근)
        """
        log_files = glob.glob(os.path.join(self.input_dir, self.config.INPUT_FILE_PATTERN))

        if not log_files:
            self.logger.warning(f"입력 디렉토리 '{self.input_dir}'에서 '{self.config.INPUT_FILE_PATTERN}' 패턴과 일치하는 파일을 찾을 수 없습니다.")
            return False

        self.logger.info(f"총 {len(log_files)}개의 로그 파일을 찾았습니다: {self.input_dir}/{self.config.INPUT_FILE_PATTERN}")
        self.logger.info(f"결과를 다음 파일에 통합하여 저장합니다: {self.combined_output_path}")

        total_lines_processed = 0
        total_lines_ignored = 0
        total_messages_written = 0
        files_processed_count = 0

        try:
            with open(self.combined_output_path, 'a', encoding='utf-8') as outfile:
                for file_path in sorted(log_files):
                    self.logger.info(f"--- 처리 중: {os.path.basename(file_path)} ---")
                    try:
                        # _filter_single_log_file 호출 시 필요한 인자만 전달
                        lines_read, lines_ignored, messages_written = self._filter_single_log_file(
                            input_path=file_path,
                            outfile_handle=outfile
                        )
                        total_lines_processed += lines_read
                        total_lines_ignored += lines_ignored
                        total_messages_written += messages_written
                        files_processed_count += 1
                        self.logger.info(f"--- 완료: {os.path.basename(file_path)} (읽음: {lines_read}, 무시: {lines_ignored}, 저장: {messages_written}) ---")
                    except Exception as e:
                        self.logger.error(f"'{os.path.basename(file_path)}' 처리 중 오류 발생하여 건너<0xEB><01>니다: {e}")
                        continue

            self.logger.info("=" * 30)
            self.logger.info("모든 파일 처리 완료 (요약)")
            self.logger.info(f"  처리된 파일 수: {files_processed_count} / {len(log_files)}")
            self.logger.info(f"  총 읽은 줄 수: {total_lines_processed}")
            self.logger.info(f"  총 무시된 줄 수: {total_lines_ignored}")
            self.logger.info(f"  총 저장된 메시지 수: {total_messages_written}")
            self.logger.info(f"  통합 결과 파일: {self.combined_output_path}")
            self.logger.info("=" * 30)
            return True

        except IOError as e:
            self.logger.error(f"통합 출력 파일 '{self.combined_output_path}' 열기/쓰기 오류: {e}")
            return False
        except Exception as e:
            self.logger.exception("전체 처리 과정 중 예상치 못한 오류 발생:")
            return False

    def run(self):
        """스크립트의 주 실행 로직을 시작합니다."""
        self.logger.info("스크립트 실행 시작 (배치 처리 모드)")
        self.logger.info(f"입력 디렉토리: {self.input_dir}")
        self.logger.info(f"파일 패턴: {self.config.INPUT_FILE_PATTERN}")
        self.logger.info(f"통합 메시지 저장 파일: {self.combined_output_path}")
        self.logger.info(f"실행 로그 파일: {self.run_log_path}")
        self.logger.info(f"무시할 패턴: {self.config.DEFAULT_IGNORE_PATTERNS}")

        success = self._process_directory()

        if not success:
            self.logger.error("처리 과정 중 오류가 발생했습니다.")
            return False # 실패 시 False 반환

        self.logger.info("정상적으로 처리를 완료했습니다.")
        return True # 성공 시 True 반환

# --- 메인 실행 로직 ---
if __name__ == "__main__":
    processor = None # 오류 발생 시 참조 위함
    exit_code = 0    # 기본 종료 코드

    try:
        # 1. 설정 객체 생성
        config = Config()

        # 2. 처리기 객체 생성 (내부적으로 환경 준비 및 로거 설정)
        processor = ChatLogProcessor(config)

        # 3. 처리 실행
        success = processor.run()
        if not success:
            exit_code = 1 # 실패 시 종료 코드 변경

    except FileNotFoundError as e:
        # 초기화 중 파일/디렉토리 못 찾음 오류
        print(f"[초기화 오류] {e}", file=sys.stderr)
        # 로거가 설정되기 전일 수 있으므로 processor.logger 사용 주의
        if processor and processor.logger:
             processor.logger.error(f"초기화 오류: {e}")
        exit_code = 1
    except Exception as e:
        # 예상치 못한 오류 처리
        error_message = f"예상치 못한 오류 발생: {e}"
        print(error_message, file=sys.stderr)
        # 로거가 설정된 후라면 로깅 시도
        if processor and processor.logger:
            processor.logger.exception(error_message)
        exit_code = 1
    finally:
        # 로거가 성공적으로 설정되었다면 종료 로그 남기기
        if processor and processor.logger:
            processor.logger.info("스크립트 실행 종료")
        sys.exit(exit_code) # 설정된 종료 코드로 종료
