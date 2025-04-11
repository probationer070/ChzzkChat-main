# Chzzk Chat Crawler

<img src="figure/logo.svg" width="400">  

파이썬 네이버 치지직 서비스의 채팅을 실시간 크롤링 도구

이 코드는 [kimcore](https://github.com/kimcore/chzzk/tree/main)님의 코드를 기반으로 작성하였습니다.

> [!NOTE]
> 데이터 필터링하는 도구를 추가하였습니다.

## 설치

    # 코드 다운로드
    $ git clone https://github.com/Buddha7771/ChzzkChat .
    $ cd ChzzkChat

    # 가상환경 설치
    $ conda create -n chzzk python=3.9
    $ conda activate chzzk

    # 패키지 설치
    $ pip install -r requirements.txt

## 준비하기

1. 로그인 필수! 웹 브라우저에서 네이버를 키고 개발자 도구(F12)를 킵니다.
2. 쿠키탭에 들어가 `NID_AUT`와 `NID_SES` 값을 찾습니다.
3. 해당 값들을 `cookies.json` 파일에 들어가 붙여 넣습니다.

## 크롤러 사용하기

    # 예시
    python run.py 

    # 특정 채널에 적용하려면 아이디를 찾아 옵션으로 넣습니다
    python run.py --streamer_id 9381e7d6816e6d915a44a13c0195b202

> 출력 내용은 자동으로 chat.log에 저장됩니다.   
> 작동을 중지하려면 `ctrl + c'을 눌러주세요.

## 데이터 선별해 정리하기

    # 예시 1 - chat_samples 폴더에 크롤링한 log 파일들 전체 필터링
    python filter_chat_test.py  

    # 예사 2 - 메인폴더(ChzzkChat-main)에 있는 특정 log 파일 1개만 필터링
    python filter_chat.py

> 오류가 발생될 경우 종료됩니다.
> 또한 로그도 남기 때문에 무엇인 문제인지 알 수 있습니다.

`logs` : 로그가 남는 폴더
`chat_samples` : 크롤링한 `chat*.log` 파일이 들어갈 폴더 (직접 넣어줘야 함)
`outputs` : 데이터를 추출한 값이 남는 폴더

> [!CAUTION]
> 네이버 자동 로그인은 해본 적이 없어서 모르겠으나 만약 없는 경우 `NID_AUT`와 `NID_SES` 값은 모든 치지직 창을 닫게 될 경우 갱신되니 다시 일일히 넣어줘야합니다.