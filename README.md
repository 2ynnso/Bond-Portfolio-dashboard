# Bond Signal Dashboard

FRED API와 시장 데이터 기반으로 채권/리스크 신호를 시각화하는 Streamlit 대시보드입니다.

## Features

### Signal Board 탭

- **4단계 Regime 분류**: VIX → OAS_Z → PPR 순서의 순차적 룰 기반 분류
- **HY OAS vs VIX 듀얼축 차트**: 하이일드 스프레드와 변동성 지수를 한 차트에서 비교, 1M/3M/6M/1Y/2Y/ALL 버튼 및 드래그 rangeslider로 시계열 자유 조정
- **Treasury Snapshot**: 3M/2Y/3Y/5Y/7Y/10Y/10Y-2Y/HY Yield 최신 금리 및 5일 변화
- **Signal Change Snapshot**: VIX/OAS Z/US 10Y/PPR 단기 변화 요약
- **Signal Focus 차트**: VIX, OAS Z, PPR 개별 시계열 + 임계값 표시
- **Regime History 차트**: 날짜별 Regime 변화 이력
- **Curve and Credit 차트**: 미국채 커브 히스토리 및 하이일드 크레딧 히스토리
- **AGG ETF 벤치마크**: 현재가 및 전일 대비 변동률

### Portfolio 탭 (Google Sheets 연동)

- **포트폴리오 비중 파이 차트**: 현재 평가금액 기준 종목별 비중
- **Intraday 5분봉 차트**: 당일 실시간 포트폴리오 수익률 (yfinance)
- **TWR NAV vs AGG 차트**: 시간가중수익률 기반 NAV와 AGG 벤치마크 비교
- **Daily Return 바차트**: 일별 수익률 히스토리
- **포지션별 손익**: 달러/원화 손익, 수익률, 환율 포함
- **성과 지표 비교**: 총수익률, 연환산 수익률/변동성, 샤프/소르티노 비율, MDD

## Data Sources

| 소스 | 종류 | 갱신 주기 |
|------|------|-----------|
| FRED API | VIX, 미국채 금리, HY OAS/Yield | 30분 캐시 |
| yfinance | AGG, SHYG, 포트폴리오 ETF 일간 가격 | 30분 캐시 |
| yfinance | 포트폴리오 ETF 5분봉 (당일) | 5분 캐시 |
| Google Sheets | 거래 내역 (Trade Ledger) | 실시간 |

## Regime 분류 시스템

점수 합산이 아닌 `VIX → OAS_Z → PPR` 순서의 **순차적 룰 기반 분류**입니다.

| 조건 | 판정 | 의미 |
|------|------|------|
| `VIX > 30` | **Regime 4: Very Risk Off** | 변동성 급등 시 즉시 방어 |
| `OAS_Z >= 0` | **Regime 3: Risk Off** | 신용 스프레드가 평균 이상, 방어 신호 |
| `PPR < 0.2` | **Regime 1: Very Risk On** | 포지셔닝 부담 낮음, 공격적 매수 |
| `PPR > 0.8` | **Regime 4: Very Risk Off** | 포지셔닝 부담 높음, 강한 방어 |
| 나머지 | **Regime 2: Risk On** | 위험자산 선호 유지 |

## Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly
- **Data Sources**: FRED API, yfinance, Google Sheets API
- **Environment**: python-dotenv, certifi

## Project Structure

```
Bond_Portfolio_dashboard/
├── dashboard.py              # 앱 진입점 (사이드바 + 탭 레이아웃)
├── config.py                 # 상수 (FRED 시리즈 ID, 레짐 색상, 임계값 등)
├── data.py                   # FRED API + yfinance 데이터 로딩
├── signals.py                # 신호·레짐 계산 + 포매팅 헬퍼
├── portfolio.py              # 포트폴리오 NAV, 손익, 성과지표 계산
├── ui/
│   ├── theme.py              # CSS 주입, 다크/라이트 테마 dict
│   ├── components.py         # 카드, 히어로, 스냅샷, 테이블 등 공통 컴포넌트
│   ├── charts_signal.py      # 신호 보드 차트 (line, focus, regime history, HY OAS vs VIX)
│   └── charts_portfolio.py   # 포트폴리오 차트 (NAV, daily return, intraday, pie, TWR NAV)
└── utils/
    ├── price_fetcher.py      # yfinance 일간·장중 가격 조회 (공통 유틸)
    └── trade_ledger.py       # Google Sheets 거래 내역 I/O + TWR NAV 계산 + 성과 분해
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

프로젝트 폴더에 `.env` 파일을 만들고 FRED API 키를 넣습니다.

```env
FRED_API_KEY=your_api_key
```

## Run

```bash
streamlit run dashboard.py
```

## Streamlit Cloud 배포

1. 이 저장소를 GitHub에 푸시합니다.
2. [Streamlit Community Cloud](https://share.streamlit.io/)에서 저장소를 연결합니다.
3. Main file path: `dashboard.py`
4. Secrets에 아래 값을 추가합니다.

```toml
FRED_API_KEY = "your_api_key"
```

- Repository: `2ynnso/Bond-signal-dashboard`
- Branch: `main`
- Main file path: `dashboard.py`

로컬 실행은 `.env`의 `FRED_API_KEY`, 배포 환경은 Streamlit Secrets의 `FRED_API_KEY`를 사용합니다.
