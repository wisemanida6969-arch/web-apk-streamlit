"""
PostGenie 사용자 가이드 PDF 생성기
Generates a Korean user manual for PostGenie.

Usage:
    python generate_guide.py

Output: docs/PostGenie_Guide.pdf
"""
import os
from pathlib import Path
from fpdf import FPDF


# ─── Paths ───
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
FONT_DIR = PROJECT_ROOT.parent  # /home/user/web-apk-streamlit/ has fonts
OUTPUT_DIR = PROJECT_ROOT / "docs"
OUTPUT_FILE = OUTPUT_DIR / "PostGenie_Guide.pdf"

FONT_REGULAR = FONT_DIR / "NotoSansKR-Regular.ttf"
FONT_BOLD = FONT_DIR / "NotoSansKR-Bold.ttf"

# ─── Colors ───
BRAND_PURPLE = (139, 92, 246)
BRAND_BLUE = (59, 130, 246)
TEXT_DARK = (30, 41, 59)
TEXT_MUTED = (100, 116, 139)
BG_LIGHT = (248, 250, 252)
ACCENT = (34, 197, 94)


class PostGenieGuide(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)

        # Fonts
        self.add_font("Noto", "", str(FONT_REGULAR))
        self.add_font("Noto", "B", str(FONT_BOLD))

    def header(self):
        if self.page_no() == 1:
            return  # No header on cover
        self.set_font("Noto", "", 9)
        self.set_text_color(*TEXT_MUTED)
        self.cell(0, 10, "PostGenie  사용자 가이드", align="L")
        self.set_y(15)
        # Purple line
        self.set_draw_color(*BRAND_PURPLE)
        self.set_line_width(0.5)
        self.line(20, 18, 190, 18)
        self.set_y(22)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("Noto", "", 8)
        self.set_text_color(*TEXT_MUTED)
        self.cell(0, 10, f"Page {self.page_no()} / {{nb}}", align="C")

    def cover_page(self):
        self.add_page()
        self.set_fill_color(*TEXT_DARK)
        self.rect(0, 0, 210, 297, style="F")

        # Logo
        self.set_y(80)
        self.set_font("Noto", "B", 48)
        self.set_text_color(255, 255, 255)
        self.cell(0, 20, "PostGenie", align="C")

        self.set_y(110)
        self.set_font("Noto", "", 14)
        self.set_text_color(200, 200, 220)
        self.cell(0, 10, "AI 블로그 자동화 서비스", align="C")

        self.set_y(130)
        self.set_font("Noto", "B", 20)
        self.set_text_color(*BRAND_PURPLE)
        self.cell(0, 10, "사용자 가이드", align="C")

        self.set_y(170)
        self.set_font("Noto", "", 11)
        self.set_text_color(180, 180, 200)
        self.multi_cell(
            0,
            7,
            "블로그 글쓰기에 지치셨나요?\nPostGenie가 AI로 매일 자동으로 블로그 글을 작성하고 발행합니다.\n\n이 가이드에서 처음 가입부터 자동 발행까지 \n단계별로 안내해드립니다.",
            align="C",
        )

        self.set_y(250)
        self.set_font("Noto", "", 9)
        self.set_text_color(120, 120, 140)
        self.cell(0, 5, "https://postgenie.trytimeback.com", align="C")
        self.set_y(256)
        self.cell(0, 5, "Version 1.0 · 2026", align="C")

    def chapter_title(self, num: str, title: str):
        self.set_y(self.get_y() + 5)
        self.set_font("Noto", "B", 18)
        self.set_text_color(*TEXT_DARK)
        self.cell(0, 12, f"{num}. {title}")
        self.ln(13)
        self.set_draw_color(*BRAND_PURPLE)
        self.set_line_width(1.2)
        self.line(20, self.get_y(), 60, self.get_y())
        self.ln(8)

    def section_title(self, title: str):
        self.set_font("Noto", "B", 13)
        self.set_text_color(*BRAND_BLUE)
        self.cell(0, 8, f"▶ {title}")
        self.ln(10)

    def paragraph(self, text: str):
        self.set_font("Noto", "", 11)
        self.set_text_color(*TEXT_DARK)
        self.multi_cell(0, 6.5, text)
        self.ln(3)

    def bullet(self, text: str, level: int = 0):
        indent = 5 + level * 5
        self.set_font("Noto", "", 10.5)
        self.set_text_color(*TEXT_DARK)
        self.set_x(20 + indent)
        self.cell(5, 6, "•")
        self.set_x(25 + indent)
        self.multi_cell(0, 6, text)
        self.ln(0.5)

    def step(self, num: int, text: str):
        x_start = self.get_x()
        y_start = self.get_y()
        # Step number circle
        self.set_fill_color(*BRAND_PURPLE)
        self.set_text_color(255, 255, 255)
        self.set_font("Noto", "B", 10)
        self.ellipse(x_start, y_start, 7, 7, style="F")
        self.set_xy(x_start, y_start + 0.5)
        self.cell(7, 6, str(num), align="C")
        # Step text
        self.set_xy(x_start + 10, y_start)
        self.set_text_color(*TEXT_DARK)
        self.set_font("Noto", "", 10.5)
        self.multi_cell(165, 6, text)
        self.ln(2)

    def info_box(self, title: str, text: str, color=None):
        if color is None:
            color = BRAND_BLUE
        y_start = self.get_y()
        self.set_fill_color(*BG_LIGHT)
        self.set_draw_color(*color)
        self.set_line_width(0.8)
        # Calculate box height
        self.set_font("Noto", "", 10)
        # Estimate lines
        line_count = len(text) // 70 + text.count("\n") + 1
        box_height = 8 + line_count * 5.5
        self.rect(20, y_start, 170, box_height, style="DF")
        # Left border accent
        self.set_fill_color(*color)
        self.rect(20, y_start, 1.5, box_height, style="F")
        # Title
        self.set_xy(25, y_start + 2)
        self.set_font("Noto", "B", 10.5)
        self.set_text_color(*color)
        self.cell(0, 5, title)
        # Body
        self.set_xy(25, y_start + 8)
        self.set_font("Noto", "", 9.5)
        self.set_text_color(*TEXT_DARK)
        self.multi_cell(160, 5, text)
        self.set_y(y_start + box_height + 4)

    def table_row(self, cells: list, widths: list, header: bool = False):
        if header:
            self.set_fill_color(*BRAND_PURPLE)
            self.set_text_color(255, 255, 255)
            self.set_font("Noto", "B", 10)
        else:
            self.set_fill_color(255, 255, 255)
            self.set_text_color(*TEXT_DARK)
            self.set_font("Noto", "", 10)
        self.set_draw_color(200, 200, 210)
        for cell, width in zip(cells, widths):
            self.cell(width, 8, cell, border=1, align="C",
                      fill=True if header else False)
        self.ln()


def build_guide():
    OUTPUT_DIR.mkdir(exist_ok=True)

    pdf = PostGenieGuide()
    pdf.alias_nb_pages()

    # ─── Cover ───
    pdf.cover_page()

    # ─── Table of Contents ───
    pdf.add_page()
    pdf.set_font("Noto", "B", 24)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(0, 15, "목차")
    pdf.ln(20)

    toc_items = [
        ("1", "PostGenie란?", "3"),
        ("2", "시작하기 — 회원가입", "4"),
        ("3", "블로그 연결하기", "5"),
        ("4", "자동 포스팅 스케줄 만들기", "7"),
        ("5", "포스팅 확인 및 관리", "9"),
        ("6", "플랜 및 가격 안내", "10"),
        ("7", "자주 묻는 질문 (FAQ)", "11"),
        ("8", "문의 및 지원", "12"),
    ]
    for num, title, page in toc_items:
        pdf.set_font("Noto", "B", 11)
        pdf.set_text_color(*BRAND_PURPLE)
        pdf.cell(12, 10, num)
        pdf.set_font("Noto", "", 11)
        pdf.set_text_color(*TEXT_DARK)
        pdf.cell(150, 10, title)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(0, 10, f"{page} 페이지", align="R")
        pdf.ln(8)
        pdf.set_draw_color(220, 220, 230)
        pdf.set_line_width(0.2)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(3)

    # ─── Chapter 1: PostGenie란? ───
    pdf.add_page()
    pdf.chapter_title("1", "PostGenie란?")

    pdf.paragraph(
        "PostGenie는 AI가 여러분의 블로그에 매일 자동으로 글을 작성하고 발행해주는 "
        "서비스입니다. 한 번만 설정해두면 Claude AI가 트렌딩 뉴스와 주제를 분석해서 "
        "SEO에 최적화된 블로그 글을 생성하고, 여러분의 블로그에 자동으로 올려드립니다."
    )

    pdf.section_title("주요 기능")
    pdf.bullet("AI 자동 글 작성 — Claude AI가 고품질 SEO 블로그 글 생성")
    pdf.bullet("실시간 트렌딩 주제 — Google News에서 최신 이슈 자동 선정")
    pdf.bullet("다국어 지원 — 한국어, 영어, 일본어, 스페인어")
    pdf.bullet("자동 발행 — Blogger, WordPress 등 주요 플랫폼 지원")
    pdf.bullet("유연한 스케줄 — 일 1~30회, 주 1회 등 자유 설정")
    pdf.bullet("카테고리 선택 — 트렌딩 뉴스, 기술, 맛집, 연예 등")

    pdf.section_title("작동 원리")
    pdf.info_box(
        "1단계 → 2단계 → 3단계",
        "1. 구글 계정으로 로그인\n"
        "2. 블로그 연결 (Blogger 또는 WordPress)\n"
        "3. 스케줄 설정 → 매일 자동으로 글 발행!",
    )

    pdf.section_title("누구에게 적합한가요?")
    pdf.bullet("블로그 운영 중인데 글 쓸 시간이 부족한 분")
    pdf.bullet("SEO 트래픽을 늘리고 싶은 개인/사업자")
    pdf.bullet("애드센스 수익화를 노리는 블로거")
    pdf.bullet("여러 주제의 블로그를 동시에 운영하고 싶은 분")

    # ─── Chapter 2: 시작하기 ───
    pdf.add_page()
    pdf.chapter_title("2", "시작하기 — 회원가입")

    pdf.paragraph(
        "PostGenie는 별도의 회원가입 절차가 없습니다. 구글 계정으로 한 번에 "
        "로그인하면 자동으로 계정이 생성됩니다."
    )

    pdf.section_title("로그인 방법")
    pdf.step(1, "브라우저에서 https://postgenie.trytimeback.com 접속")
    pdf.step(2, "메인 페이지에서 \"Sign in with Google\" 버튼 클릭")
    pdf.step(3, "구글 계정 선택 및 권한 허용")
    pdf.step(4, "대시보드로 자동 이동 — 가입 완료!")

    pdf.ln(4)
    pdf.info_box(
        "[참고]",
        "PostGenie는 구글 계정의 이메일, 이름, 프로필 사진만 읽어옵니다.\n"
        "다른 정보는 접근하지 않으며, 언제든 구글 계정 설정에서\n"
        "권한을 철회할 수 있습니다.",
        color=BRAND_BLUE,
    )

    pdf.section_title("가입 후 첫 화면")
    pdf.paragraph(
        "로그인하면 개인 대시보드로 이동합니다. 왼쪽 사이드바에 프로필, "
        "현재 플랜, 메뉴(대시보드/블로그 연결/스케줄/포스트/업그레이드)가 "
        "표시됩니다. 처음에는 모든 수치가 0으로 시작합니다."
    )

    # ─── Chapter 3: 블로그 연결 ───
    pdf.add_page()
    pdf.chapter_title("3", "블로그 연결하기")

    pdf.paragraph(
        "PostGenie는 Google Blogger와 WordPress(셀프 호스팅)를 지원합니다. "
        "가장 쉬운 방법은 Blogger를 사용하는 것입니다."
    )

    pdf.section_title("Blogger 연결하기 (추천)")
    pdf.step(1, "사이드바에서 \"Connect Blog\" 메뉴 클릭")
    pdf.step(2, "Platform을 \"Google Blogger\" 로 선택")
    pdf.step(3, "\"Authorize Blogger\" 버튼 클릭")
    pdf.step(4, "Google 권한 요청 화면에서 Blogger 접근 허용")
    pdf.step(5, "자동으로 돌아와서 블로그 목록이 표시됨")
    pdf.step(6, "연결할 블로그 선택 → \"Connect This Blog\" 클릭")
    pdf.step(7, "완료! Connected Blogs 목록에 추가됨")

    pdf.ln(3)
    pdf.info_box(
        "[안내] Blogger가 없다면",
        "blogger.com 에서 구글 계정으로 무료로 블로그를 만들 수 있습니다.\n"
        "한 계정으로 여러 블로그를 만들 수 있으며, 모두 PostGenie에 연결 가능합니다.",
        color=ACCENT,
    )

    pdf.add_page()
    pdf.section_title("WordPress 연결하기")
    pdf.paragraph(
        "WordPress는 \"Application Password\"를 사용합니다. "
        "로그인 비밀번호와는 다른 전용 비밀번호입니다."
    )

    pdf.step(1, "WordPress 관리자 페이지 접속 (yourblog.com/wp-admin)")
    pdf.step(2, "좌측 메뉴: 사용자 → 프로필")
    pdf.step(3, "스크롤 내려서 \"Application Passwords\" 섹션 찾기")
    pdf.step(4, "이름 입력 (예: PostGenie) → \"Add New Application Password\" 클릭")
    pdf.step(5, "생성된 비밀번호 복사 (한 번만 표시됨!)")
    pdf.step(6, "PostGenie → Connect Blog → Platform을 WordPress로 선택")
    pdf.step(7, "Site URL, Username, Application Password 입력 후 연결")

    pdf.ln(3)
    pdf.info_box(
        "[주의 사항]",
        "티스토리와 네이버 블로그는 API가 닫혀 있어 자동 연결이 불가능합니다.\n"
        "대안으로 Blogger나 WordPress를 사용하시는 것을 권장합니다.",
        color=(239, 68, 68),
    )

    # ─── Chapter 4: 스케줄 만들기 ───
    pdf.add_page()
    pdf.chapter_title("4", "자동 포스팅 스케줄 만들기")

    pdf.paragraph(
        "스케줄은 \"언제, 어떤 주제로, 어떤 블로그에 글을 올릴지\" 정하는 설정입니다. "
        "하나의 스케줄은 한 번 실행될 때마다 글을 1개 발행합니다."
    )

    pdf.section_title("스케줄 생성 단계")
    pdf.step(1, "사이드바에서 \"Schedules\" 클릭")
    pdf.step(2, "스케줄 이름 입력 (예: 매일 맛집 블로그)")
    pdf.step(3, "Target Blog 선택 — 연결된 블로그 중 하나")
    pdf.step(4, "Content Language 선택 — 한국어 / English / 日本語 / Español")
    pdf.step(5, "Content Categories 선택 — 언어에 맞는 카테고리들이 표시됨")
    pdf.step(6, "Posting Frequency 선택 — 일 1회 / 일 2회 / 주 1회")
    pdf.step(7, "Writing Tone 선택 — friendly / professional / casual 등")
    pdf.step(8, "Target Word Count 설정 — 500~2000자 (기본 1000)")
    pdf.step(9, "\"Create Schedule\" 버튼 클릭 → 완료!")

    pdf.ln(3)
    pdf.section_title("카테고리 안내")
    pdf.paragraph("언어에 따라 선택 가능한 카테고리가 다릅니다:")
    pdf.bullet("한국어: 한국 트렌딩, TV 맛집/먹방, K-POP/연예, 생활/꿀팁")
    pdf.bullet("영어: Trending News, Technology, Business, Entertainment, Health")

    pdf.add_page()
    pdf.section_title("커스텀 주제 사용하기")
    pdf.paragraph(
        "트렌딩 뉴스 대신 원하는 주제로 글을 쓰고 싶다면 \"Custom Topics\" "
        "필드에 주제를 한 줄씩 입력하세요. 입력한 주제들 중에서 무작위로 "
        "선택되어 글이 작성됩니다."
    )

    pdf.info_box(
        "Custom Topics 예시",
        "다이어트 식단 추천\n"
        "재테크 초보를 위한 가이드\n"
        "서울 데이트 코스 BEST 10\n"
        "홈카페 레시피 모음",
        color=ACCENT,
    )

    pdf.section_title("스케줄 관리")
    pdf.paragraph(
        "생성된 스케줄은 Schedules 페이지에서 확인/관리할 수 있습니다:"
    )
    pdf.bullet("활성/비활성 토글 — 일시적으로 중단/재개")
    pdf.bullet("삭제 — 스케줄 완전 제거")
    pdf.bullet("다음 실행 시간 확인")

    # ─── Chapter 5: 포스트 확인 ───
    pdf.add_page()
    pdf.chapter_title("5", "포스팅 확인 및 관리")

    pdf.paragraph(
        "PostGenie가 자동으로 생성하고 발행한 모든 글은 \"Posts\" 페이지에서 "
        "확인할 수 있습니다."
    )

    pdf.section_title("Posts 페이지")
    pdf.paragraph("3가지 탭으로 분류됩니다:")
    pdf.bullet("[완료] Published — 정상 발행된 글 (블로그에 업로드 완료)")
    pdf.bullet("[대기] Pending — 생성되었지만 아직 발행 대기 중")
    pdf.bullet("[실패] Failed — 발행 실패한 글 (오류 메시지 확인 가능)")

    pdf.section_title("각 포스트에서 확인 가능한 정보")
    pdf.bullet("제목과 생성 날짜")
    pdf.bullet("블로그 링크 (클릭하면 실제 블로그 글로 이동)")
    pdf.bullet("카테고리 및 언어")
    pdf.bullet("사용된 토큰 수")
    pdf.bullet("전체 HTML 본문 미리보기")

    pdf.section_title("자동 실행 주기")
    pdf.info_box(
        "[스케줄 실행 시간]",
        "PostGenie의 자동 포스팅은 매시간 정각부터 15분 이내에 실행됩니다.\n"
        "새 스케줄을 만들면 최대 1시간 이내에 첫 글이 발행됩니다.\n\n"
        "예시: 오후 2시 30분에 스케줄 생성 → 오후 3:15에 첫 글 자동 발행",
        color=BRAND_PURPLE,
    )

    # ─── Chapter 6: 플랜 ───
    pdf.add_page()
    pdf.chapter_title("6", "플랜 및 가격 안내")

    pdf.paragraph(
        "PostGenie는 무료 체험부터 에이전시 플랜까지 4가지 요금제를 제공합니다."
    )

    pdf.ln(3)
    widths = [30, 30, 30, 40, 40]
    headers = ["플랜", "가격", "블로그 수", "포스팅 빈도", "대상"]
    rows = [
        ["Free", "$0", "1개", "주 1회", "체험용"],
        ["Basic", "$9/월", "1개", "일 1회", "개인 블로거"],
        ["Pro", "$29/월", "3개", "일 3회", "전문 블로거"],
        ["Agency", "$99/월", "10개", "일 30회", "에이전시"],
    ]

    pdf.table_row(headers, widths, header=True)
    for row in rows:
        pdf.table_row(row, widths)

    pdf.ln(5)
    pdf.section_title("업그레이드 방법")
    pdf.step(1, "사이드바에서 \"Upgrade\" 클릭")
    pdf.step(2, "원하는 플랜 카드의 \"Upgrade\" 버튼 클릭")
    pdf.step(3, "Paddle 결제 창에서 카드 정보 입력")
    pdf.step(4, "결제 완료 → 자동으로 플랜이 업그레이드됨")

    pdf.ln(3)
    pdf.info_box(
        "[결제 안내]",
        "결제는 Paddle을 통해 안전하게 처리됩니다.\n"
        "VAT가 포함된 가격으로 표시되며, 언제든 취소 가능합니다.\n"
        "구독 관리는 Paddle 이메일의 고객 포털에서 가능합니다.",
        color=BRAND_BLUE,
    )

    # ─── Chapter 7: FAQ ───
    pdf.add_page()
    pdf.chapter_title("7", "자주 묻는 질문 (FAQ)")

    faqs = [
        (
            "Q. AI가 쓴 글의 품질은 어느 정도인가요?",
            "Claude AI가 작성하는 글은 전문 블로거 수준의 품질입니다. "
            "SEO에 최적화되어 있고, 자연스러운 문장 구조와 실용적인 "
            "정보를 포함합니다. 다만 사실 검증이 필요한 민감한 주제는 "
            "사용 전 확인을 권장합니다.",
        ),
        (
            "Q. 글이 저작권 문제가 될 수 있나요?",
            "AI가 생성하는 글은 원본입니다. 뉴스 제목을 주제로 삼지만 "
            "내용 자체는 AI가 새로 작성하므로 저작권 문제는 없습니다. "
            "다만 이미지는 별도로 추가해야 합니다.",
        ),
        (
            "Q. 하루에 몇 개의 글을 발행할 수 있나요?",
            "플랜에 따라 다릅니다. Free는 주 1회, Basic은 일 1회, "
            "Pro는 일 3회, Agency는 일 30회까지 가능합니다.",
        ),
        (
            "Q. 발행된 글을 수정할 수 있나요?",
            "네. 블로그 플랫폼(Blogger/WordPress)에서 직접 편집하시면 "
            "됩니다. PostGenie는 최초 발행만 자동화하고, 이후 관리는 "
            "사용자가 직접 하실 수 있습니다.",
        ),
        (
            "Q. 여러 블로그를 동시에 운영할 수 있나요?",
            "Pro 플랜부터 가능합니다. 각 블로그마다 다른 주제와 언어의 "
            "스케줄을 만들 수 있습니다.",
        ),
        (
            "Q. 한국어와 영어를 동시에 쓸 수 있나요?",
            "네. 각 스케줄마다 언어를 다르게 설정할 수 있습니다. "
            "예를 들어 블로그 1에는 한국어 스케줄, 블로그 2에는 영어 "
            "스케줄을 만들 수 있습니다.",
        ),
        (
            "Q. 언제든 취소할 수 있나요?",
            "네. 구독은 언제든 취소 가능하며, 취소 후에도 결제 기간이 "
            "끝날 때까지 서비스를 이용할 수 있습니다.",
        ),
    ]

    for q, a in faqs:
        pdf.set_font("Noto", "B", 11)
        pdf.set_text_color(*BRAND_PURPLE)
        pdf.multi_cell(0, 7, q)
        pdf.ln(1)
        pdf.set_font("Noto", "", 10)
        pdf.set_text_color(*TEXT_DARK)
        pdf.multi_cell(0, 6, a)
        pdf.ln(5)

    # ─── Chapter 8: Support ───
    pdf.add_page()
    pdf.chapter_title("8", "문의 및 지원")

    pdf.paragraph(
        "사용 중 궁금한 점이나 문제가 있으면 언제든 연락 주세요."
    )

    pdf.section_title("연락처")
    pdf.bullet("이메일: admin@trytimeback.com")
    pdf.bullet("웹사이트: https://postgenie.trytimeback.com")

    pdf.section_title("피드백 환영")
    pdf.paragraph(
        "PostGenie는 지속적으로 개선되고 있습니다. 새 기능 요청이나 "
        "개선 아이디어가 있다면 이메일로 보내주세요. 사용자 피드백이 "
        "다음 업데이트의 방향을 결정합니다."
    )

    pdf.ln(10)
    pdf.set_font("Noto", "B", 14)
    pdf.set_text_color(*BRAND_PURPLE)
    pdf.cell(0, 10, "지금 시작하세요!", align="C")
    pdf.ln(10)
    pdf.set_font("Noto", "", 11)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(0, 8, "https://postgenie.trytimeback.com", align="C")

    pdf.ln(20)
    pdf.set_draw_color(*BRAND_PURPLE)
    pdf.set_line_width(0.3)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Noto", "", 9)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(0, 5, "© 2026 PostGenie. AI-Powered Blog Automation.", align="C")

    # Save
    pdf.output(str(OUTPUT_FILE))
    print(f"[완료] Generated: {OUTPUT_FILE}")
    print(f"   Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_guide()
