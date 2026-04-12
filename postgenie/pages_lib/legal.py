"""
Legal pages for PostGenie
- Terms of Service
- Privacy Policy
- Cookie Policy
- Refund Policy
"""
import streamlit as st


LEGAL_PAGE_CSS = """
<style>
    .legal-container {
        max-width: 800px;
        margin: 40px auto;
        padding: 40px;
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
    }
    .legal-container h1 {
        color: #f1f5f9;
        font-size: 2rem;
        font-weight: 900;
        margin-bottom: 8px;
        background: linear-gradient(135deg, #8b5cf6, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .legal-container .updated {
        color: #64748b;
        font-size: 0.85rem;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .legal-container h2 {
        color: #e2e8f0;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 28px 0 12px;
    }
    .legal-container h3 {
        color: #cbd5e1;
        font-size: 1.05rem;
        font-weight: 600;
        margin: 18px 0 8px;
    }
    .legal-container p {
        color: #94a3b8;
        line-height: 1.8;
        margin-bottom: 14px;
        font-size: 0.95rem;
    }
    .legal-container ul {
        color: #94a3b8;
        line-height: 1.8;
        margin: 8px 0 16px 20px;
        font-size: 0.95rem;
    }
    .legal-container li {
        margin-bottom: 6px;
    }
    .legal-container strong {
        color: #e2e8f0;
    }
    .legal-container a {
        color: #8b5cf6;
        text-decoration: none;
    }
    .legal-container a:hover {
        text-decoration: underline;
    }
    .legal-back {
        display: inline-block;
        margin: 20px 0;
        color: #8b5cf6;
        text-decoration: none;
        font-size: 0.9rem;
    }
</style>
"""


def render_terms():
    st.markdown(LEGAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="legal-container">
        <h1>Terms of Service</h1>
        <div class="updated">최종 업데이트: 2026년 4월 12일 · Last updated: April 12, 2026</div>

        <h2>1. 서비스 이용 조건 (Service Terms)</h2>
        <p>PostGenie("본 서비스")는 AI 기반 블로그 자동화 SaaS 플랫폼입니다.
        본 서비스를 이용함으로써 사용자는 본 약관에 동의하게 됩니다. 본 약관에
        동의하지 않는 경우 서비스를 이용할 수 없습니다.</p>
        <p>본 서비스는 만 14세 이상만 이용 가능합니다.</p>

        <h2>2. 계정 (Account)</h2>
        <ul>
            <li>계정은 Google OAuth를 통해 생성되며, 하나의 Google 계정당 하나의 계정만 생성 가능합니다.</li>
            <li>계정 정보(이메일, 이름, 프로필 사진)는 정확해야 하며, 사용자는 자신의 계정 활동에 대해 책임을 집니다.</li>
            <li>계정 공유, 양도, 판매는 엄격히 금지됩니다.</li>
            <li>보안이 침해되었다고 판단되는 경우 즉시 admin@trytimeback.com으로 연락해주세요.</li>
        </ul>

        <h2>3. AI 생성 콘텐츠 책임 (AI Content Responsibility)</h2>
        <p>PostGenie는 Claude AI를 사용하여 블로그 글을 자동으로 생성합니다. 사용자는 다음 사항에 유의해야 합니다:</p>
        <ul>
            <li>AI가 생성한 콘텐츠의 <strong>최종 책임은 사용자</strong>에게 있습니다.</li>
            <li>생성된 콘텐츠가 <strong>저작권, 상표권, 개인정보 등 제3자의 권리를 침해하지 않도록</strong> 확인할 책임이 있습니다.</li>
            <li>AI는 가끔 부정확하거나 오해의 소지가 있는 정보를 생성할 수 있으며, 민감한 주제(의료, 법률, 금융 등)의 경우 반드시 전문가 검토가 필요합니다.</li>
            <li>생성된 콘텐츠로 인한 법적 분쟁, 손해, 명예훼손 등에 대해 PostGenie는 책임지지 않습니다.</li>
            <li>불법 콘텐츠(저작권 침해, 혐오 발언, 스팸 등)의 생성 및 발행은 금지됩니다.</li>
        </ul>

        <h2>4. 결제 및 구독 (Billing & Subscription)</h2>
        <ul>
            <li>유료 플랜(Basic, Pro, Agency)은 월 단위로 자동 결제됩니다.</li>
            <li>결제는 Paddle을 통해 안전하게 처리되며, Paddle의 이용약관이 함께 적용됩니다.</li>
            <li>구독은 언제든 취소 가능하며, 현재 결제 기간 종료 시까지 서비스를 이용할 수 있습니다.</li>
            <li>환불은 별도 <a href="?page=refund">환불 정책</a>을 따릅니다.</li>
            <li>요금은 사전 고지 후 변경될 수 있으며, 변경 시 다음 결제 주기부터 적용됩니다.</li>
        </ul>

        <h2>5. 서비스 종료 및 해지 (Termination)</h2>
        <ul>
            <li>사용자는 언제든 계정을 삭제할 수 있습니다. 삭제 요청은 admin@trytimeback.com으로 보내주세요.</li>
            <li>PostGenie는 다음의 경우 사전 통지 없이 서비스 이용을 제한하거나 계정을 종료할 수 있습니다:
                <ul>
                    <li>본 약관을 위반한 경우</li>
                    <li>불법 콘텐츠를 생성/발행한 경우</li>
                    <li>서비스 악용 또는 시스템 공격을 시도한 경우</li>
                    <li>타인의 권리를 침해한 경우</li>
                </ul>
            </li>
            <li>서비스 종료 시 데이터는 <a href="?page=privacy">개인정보처리방침</a>에 따라 처리됩니다.</li>
        </ul>

        <h2>6. 면책 조항 (Disclaimer)</h2>
        <p>본 서비스는 "있는 그대로(as-is)" 제공되며, 명시적 또는 묵시적 보증이 없습니다. PostGenie는
        서비스 중단, 데이터 손실, AI 생성 오류 등으로 인한 직접적 또는 간접적 손해에 대해
        책임지지 않습니다.</p>

        <h2>7. 준거법 (Governing Law)</h2>
        <p>본 약관은 대한민국 법률에 따라 해석 및 적용되며, 분쟁 발생 시 대한민국 법원을
        관할 법원으로 합니다.</p>

        <h2>8. 문의 (Contact)</h2>
        <p>약관 관련 문의: <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)


def render_privacy():
    st.markdown(LEGAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="legal-container">
        <h1>Privacy Policy</h1>
        <div class="updated">최종 업데이트: 2026년 4월 12일 · Last updated: April 12, 2026</div>

        <p>PostGenie("본 서비스")는 사용자의 개인정보를 소중하게 다루며, 관련 법령을 준수하여
        정보를 안전하게 보호합니다. 본 개인정보처리방침은 수집하는 정보, 이용 목적, 보관 기간 등을
        설명합니다.</p>

        <h2>1. 수집하는 정보 (Information We Collect)</h2>

        <h3>A. Google 계정 정보</h3>
        <p>Google OAuth를 통해 로그인할 때 다음 정보를 수집합니다:</p>
        <ul>
            <li>이메일 주소</li>
            <li>이름</li>
            <li>프로필 사진 URL</li>
        </ul>

        <h3>B. 블로그 플랫폼 정보</h3>
        <p>블로그 연결 시 다음 정보를 암호화하여 저장합니다:</p>
        <ul>
            <li>블로그 ID 및 이름 (Blogger, WordPress 등)</li>
            <li>OAuth refresh token (Blogger 연결용)</li>
            <li>Application Password (WordPress 연결용)</li>
        </ul>

        <h3>C. 사용 데이터</h3>
        <ul>
            <li>생성된 블로그 글 내용 및 메타데이터</li>
            <li>스케줄 설정 (주제, 언어, 빈도 등)</li>
            <li>포스팅 성공/실패 기록</li>
            <li>일별 AI 사용량 (토큰 수, 생성 횟수)</li>
        </ul>

        <h2>2. 정보 이용 목적 (How We Use Information)</h2>
        <ul>
            <li>PostGenie 서비스 제공 (블로그 자동 생성/발행)</li>
            <li>사용자 계정 관리 및 인증</li>
            <li>결제 처리 및 구독 관리</li>
            <li>플랜별 사용량 제한 적용</li>
            <li>서비스 품질 개선 및 통계 분석</li>
            <li>고객 지원 및 문의 응대</li>
            <li>법적 의무 이행</li>
        </ul>

        <h2>3. 제3자 서비스 (Third-Party Services)</h2>
        <p>PostGenie는 서비스 제공을 위해 다음 제3자 서비스를 이용합니다:</p>
        <ul>
            <li><strong>Google (OAuth, Blogger API)</strong>: 로그인 및 Blogger 블로그 연결.
                <a href="https://policies.google.com/privacy" target="_blank">Google 개인정보처리방침</a></li>
            <li><strong>Anthropic Claude API</strong>: 블로그 글 AI 생성. 생성 요청 내용(주제, 카테고리)이
                Anthropic 서버로 전송됩니다. <a href="https://www.anthropic.com/privacy" target="_blank">Anthropic Privacy Policy</a></li>
            <li><strong>Paddle</strong>: 결제 처리. 결제 정보는 Paddle이 직접 보관하며, PostGenie는
                결제 정보를 저장하지 않습니다. <a href="https://www.paddle.com/legal/privacy" target="_blank">Paddle Privacy Policy</a></li>
            <li><strong>Supabase</strong>: 데이터베이스 호스팅. 모든 사용자 데이터는 Supabase에
                암호화되어 저장됩니다.</li>
        </ul>

        <h2>4. 데이터 보관 및 삭제 (Data Retention & Deletion)</h2>
        <ul>
            <li>계정이 활성 상태인 동안 데이터는 안전하게 보관됩니다.</li>
            <li>계정 삭제 요청 시 <strong>30일 이내</strong> 모든 개인정보가 완전히 삭제됩니다.</li>
            <li>법적 의무(세금 기록 등)에 따라 일부 데이터는 관련 법령에 따른 기간 동안 보관될 수 있습니다.</li>
            <li>삭제 요청: <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a>으로 연락</li>
        </ul>

        <h2>5. 사용자 권리 (Your Rights)</h2>
        <p>사용자는 다음 권리를 행사할 수 있습니다:</p>
        <ul>
            <li><strong>열람 권리</strong>: 보관된 개인정보를 확인할 수 있습니다.</li>
            <li><strong>수정 권리</strong>: 부정확한 정보의 수정을 요청할 수 있습니다.</li>
            <li><strong>삭제 권리</strong>: 계정 및 개인정보 삭제를 요청할 수 있습니다.</li>
            <li><strong>처리 제한 권리</strong>: 특정 처리 중단을 요청할 수 있습니다.</li>
            <li><strong>이전 권리</strong>: 자신의 데이터를 다른 서비스로 이전할 수 있습니다.</li>
        </ul>

        <h2>6. 데이터 보안 (Data Security)</h2>
        <ul>
            <li>모든 통신은 HTTPS로 암호화됩니다.</li>
            <li>OAuth 토큰 및 비밀번호는 암호화되어 저장됩니다.</li>
            <li>Supabase의 Row Level Security(RLS)로 사용자 간 데이터 격리가 적용됩니다.</li>
            <li>정기적인 보안 감사를 수행합니다.</li>
        </ul>

        <h2>7. 쿠키 사용 (Cookies)</h2>
        <p>쿠키 사용에 대한 자세한 내용은 <a href="?page=cookies">쿠키 정책</a>을 참조해주세요.</p>

        <h2>8. 문의 (Contact)</h2>
        <p>개인정보처리방침 관련 문의: <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)


def render_cookies():
    st.markdown(LEGAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="legal-container">
        <h1>Cookie Policy</h1>
        <div class="updated">최종 업데이트: 2026년 4월 12일 · Last updated: April 12, 2026</div>

        <p>PostGenie("본 서비스")는 서비스 품질 개선과 사용자 경험 향상을 위해 쿠키를
        사용합니다. 본 쿠키 정책은 사용되는 쿠키의 종류, 목적, 관리 방법을 설명합니다.</p>

        <h2>1. 쿠키란? (What Are Cookies?)</h2>
        <p>쿠키는 사용자가 웹사이트를 방문할 때 사용자의 기기에 저장되는 작은 텍스트 파일입니다.
        쿠키는 사용자를 식별하고, 로그인 상태를 유지하며, 사용 패턴을 분석하는 데 사용됩니다.</p>

        <h2>2. 필수 쿠키 (Essential Cookies)</h2>
        <p>다음 쿠키는 서비스의 기본 기능을 제공하기 위해 필수적이며, 사용자 동의 없이 사용됩니다:</p>
        <ul>
            <li><strong>세션 쿠키</strong>: 로그인 세션을 유지하고 사용자를 식별합니다. 브라우저 종료 시 삭제됩니다.</li>
            <li><strong>인증 쿠키</strong>: Google OAuth 로그인 상태를 유지합니다.</li>
            <li><strong>보안 쿠키</strong>: CSRF 공격 방지 및 보안 토큰 관리에 사용됩니다.</li>
            <li><strong>설정 쿠키</strong>: 언어, 테마 등 사용자 설정을 저장합니다.</li>
        </ul>

        <h2>3. 분석 쿠키 (Analytics Cookies)</h2>
        <p>서비스 개선을 위해 사용 패턴을 익명으로 분석하는 쿠키입니다. 이 쿠키는
        개인을 식별하지 않으며, 통계 목적으로만 사용됩니다:</p>
        <ul>
            <li><strong>사용 통계</strong>: 방문 페이지, 사용 시간, 기능 사용 빈도 등</li>
            <li><strong>성능 측정</strong>: 페이지 로드 시간, 오류 발생률 등</li>
            <li><strong>A/B 테스트</strong>: 서비스 개선을 위한 기능 비교 테스트</li>
        </ul>

        <h2>4. 제3자 쿠키 (Third-Party Cookies)</h2>
        <p>일부 쿠키는 제3자 서비스(Google OAuth, Paddle 결제 등)에 의해 설정될 수 있습니다.
        이러한 쿠키는 해당 제3자 서비스의 개인정보처리방침을 따릅니다.</p>

        <h2>5. 쿠키 관리 (Managing Cookies)</h2>
        <p>사용자는 브라우저 설정을 통해 쿠키를 관리할 수 있습니다:</p>
        <ul>
            <li>모든 쿠키 차단</li>
            <li>특정 사이트의 쿠키만 차단</li>
            <li>저장된 쿠키 삭제</li>
            <li>쿠키 저장 시 알림 받기</li>
        </ul>
        <p><strong>주의</strong>: 필수 쿠키를 차단하면 로그인 등 서비스의 일부 기능이 정상 작동하지
        않을 수 있습니다.</p>

        <h3>주요 브라우저 쿠키 설정 안내</h3>
        <ul>
            <li><a href="https://support.google.com/chrome/answer/95647" target="_blank">Chrome</a></li>
            <li><a href="https://support.mozilla.org/ko/kb/enhanced-tracking-protection-firefox-desktop" target="_blank">Firefox</a></li>
            <li><a href="https://support.apple.com/ko-kr/guide/safari/sfri11471/mac" target="_blank">Safari</a></li>
            <li><a href="https://support.microsoft.com/ko-kr/microsoft-edge" target="_blank">Edge</a></li>
        </ul>

        <h2>6. 정책 변경 (Changes to This Policy)</h2>
        <p>본 쿠키 정책은 서비스 업데이트에 따라 변경될 수 있으며, 중요한 변경이 있을 경우
        이메일 또는 서비스 내 공지를 통해 알려드립니다.</p>

        <h2>7. 문의 (Contact)</h2>
        <p>쿠키 정책 관련 문의: <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)


def render_refund():
    st.markdown(LEGAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="legal-container">
        <h1>Refund Policy</h1>
        <div class="updated">최종 업데이트: 2026년 4월 12일 · Last updated: April 12, 2026</div>

        <p>PostGenie는 사용자가 서비스에 만족하시길 바랍니다. 본 환불 정책은 유료 구독의
        환불 조건 및 절차를 설명합니다.</p>

        <h2>1. 7일 환불 보장 (7-Day Refund Guarantee)</h2>
        <p>유료 플랜을 처음 결제한 사용자는 <strong>결제일로부터 7일 이내</strong>에 환불을 요청할 수 있습니다.
        단, 다음 조건을 모두 충족해야 합니다:</p>
        <ul>
            <li>최초 결제 후 <strong>7일 이내</strong>의 환불 요청</li>
            <li>결제 후 <strong>블로그 글이 단 1개도 발행되지 않은 상태</strong></li>
            <li>이용약관 위반 없음</li>
        </ul>

        <h2>2. 환불 불가 조건 (Non-Refundable Cases)</h2>
        <p>다음의 경우에는 환불이 불가합니다:</p>
        <ul>
            <li><strong>블로그 글이 1개라도 자동 발행된 경우</strong> (AI 사용량이 소비되었기 때문)</li>
            <li>결제 후 7일이 지난 경우</li>
            <li>갱신 결제(2회차 이후)의 경우 - 첫 결제에만 환불 보장이 적용됩니다</li>
            <li>부정 사용, 남용, 이용약관 위반으로 인한 계정 정지 시</li>
            <li>서비스 일시 중단(정기 점검, 장애 등)으로 인한 이용 불가</li>
        </ul>

        <h2>3. 환불 요청 방법 (How to Request a Refund)</h2>
        <p>환불을 요청하려면 다음 정보를 포함하여
        <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a>으로 이메일을 보내주세요:</p>
        <ul>
            <li>계정 이메일 (Google 로그인 이메일)</li>
            <li>결제 일시 및 금액</li>
            <li>Paddle 주문 번호 (결제 확인 이메일에서 확인)</li>
            <li>환불 사유</li>
        </ul>
        <p>요청은 영업일 기준 <strong>3~5일 이내</strong>에 처리됩니다. 환불이 승인되면
        원래 결제 수단으로 환불되며, 환불이 계좌에 반영되는 데 카드사/은행에 따라
        추가 3~10 영업일이 소요될 수 있습니다.</p>

        <h2>4. 구독 취소 (Cancellation)</h2>
        <p>구독은 언제든 취소할 수 있습니다:</p>
        <ul>
            <li>Paddle 고객 포털에서 직접 취소 (결제 이메일의 링크)</li>
            <li>또는 admin@trytimeback.com으로 취소 요청</li>
            <li>취소 후에도 현재 결제 기간이 끝날 때까지 서비스를 이용할 수 있습니다</li>
            <li>다음 결제 주기부터 자동 결제가 중단됩니다</li>
            <li>취소는 환불이 아닙니다 - 이미 결제된 금액은 별도의 환불 요청이 필요합니다</li>
        </ul>

        <h2>5. 부분 환불 (Partial Refunds)</h2>
        <p>원칙적으로 부분 환불은 제공하지 않습니다. 월 중간에 구독을 취소하더라도
        남은 기간에 대한 환불은 이루어지지 않으며, 결제 기간 종료 시까지 서비스를
        이용할 수 있습니다.</p>

        <h2>6. 서비스 중단으로 인한 환불 (Service Outage Refunds)</h2>
        <p>PostGenie의 귀책 사유로 <strong>48시간 이상 연속된 서비스 중단</strong>이 발생한 경우,
        해당 기간에 비례한 환불 또는 서비스 이용 기간 연장을 요청할 수 있습니다.</p>

        <h2>7. 결제 분쟁 (Payment Disputes)</h2>
        <p>결제에 문제가 있다고 판단되면 카드사에 직접 이의를 제기하기 전에 먼저 저희에게
        연락해주세요. 대부분의 문제는 이메일로 빠르게 해결할 수 있습니다.</p>

        <h2>8. 정책 변경 (Changes to This Policy)</h2>
        <p>본 환불 정책은 변경될 수 있으며, 변경 시 이메일 또는 서비스 내 공지로 알려드립니다.
        변경된 정책은 변경 후의 결제에 적용됩니다.</p>

        <h2>9. 문의 (Contact)</h2>
        <p>환불 및 결제 관련 문의:
        <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)


def render_legal_page(page_name: str):
    """Render a legal page based on query param."""
    renderers = {
        "terms": render_terms,
        "privacy": render_privacy,
        "cookies": render_cookies,
        "refund": render_refund,
    }
    renderer = renderers.get(page_name)
    if renderer:
        renderer()
        return True
    return False


def render_footer():
    """Render shared footer with legal links (used on all pages)."""
    st.markdown("""
    <style>
        .legal-footer {
            text-align: center;
            padding: 30px 20px 20px;
            margin-top: 50px;
            border-top: 1px solid rgba(255,255,255,0.05);
        }
        .legal-footer a {
            color: #64748b;
            font-size: 0.82rem;
            text-decoration: none;
            margin: 0 10px;
            transition: color 0.2s;
        }
        .legal-footer a:hover {
            color: #94a3b8;
        }
        .legal-footer .separator {
            color: #334155;
            margin: 0 4px;
        }
        .legal-footer .copyright {
            color: #475569;
            font-size: 0.75rem;
            margin-top: 12px;
        }
    </style>
    <div class="legal-footer">
        <a href="?page=terms">Terms of Service</a>
        <span class="separator">|</span>
        <a href="?page=privacy">Privacy Policy</a>
        <span class="separator">|</span>
        <a href="?page=cookies">Cookie Policy</a>
        <span class="separator">|</span>
        <a href="?page=refund">Refund Policy</a>
        <div class="copyright">© 2026 PostGenie. AI-Powered Blog Automation.</div>
    </div>
    """, unsafe_allow_html=True)
