"""
PostGenie English User Guide PDF Generator

Usage:
    python generate_guide_en.py

Output: docs/PostGenie_Guide_EN.pdf
"""
import os
from pathlib import Path
from fpdf import FPDF


SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
FONT_DIR = PROJECT_ROOT.parent
OUTPUT_DIR = PROJECT_ROOT / "docs"
OUTPUT_FILE = OUTPUT_DIR / "PostGenie_Guide_EN.pdf"

FONT_REGULAR = FONT_DIR / "NotoSansKR-Regular.ttf"
FONT_BOLD = FONT_DIR / "NotoSansKR-Bold.ttf"

BRAND_PURPLE = (139, 92, 246)
BRAND_BLUE = (59, 130, 246)
TEXT_DARK = (30, 41, 59)
TEXT_MUTED = (100, 116, 139)
BG_LIGHT = (248, 250, 252)
ACCENT = (34, 197, 94)


class PostGenieGuideEN(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(20, 20, 20)
        self.add_font("Noto", "", str(FONT_REGULAR))
        self.add_font("Noto", "B", str(FONT_BOLD))

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Noto", "", 9)
        self.set_text_color(*TEXT_MUTED)
        self.cell(0, 10, "PostGenie  User Guide", align="L")
        self.set_y(15)
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

        self.set_y(80)
        self.set_font("Noto", "B", 48)
        self.set_text_color(255, 255, 255)
        self.cell(0, 20, "PostGenie", align="C")

        self.set_y(110)
        self.set_font("Noto", "", 14)
        self.set_text_color(200, 200, 220)
        self.cell(0, 10, "AI-Powered Blog Automation", align="C")

        self.set_y(130)
        self.set_font("Noto", "B", 20)
        self.set_text_color(*BRAND_PURPLE)
        self.cell(0, 10, "User Guide", align="C")

        self.set_y(170)
        self.set_font("Noto", "", 11)
        self.set_text_color(180, 180, 200)
        self.multi_cell(
            0,
            7,
            "Tired of writing blog posts every day?\nPostGenie automatically writes and publishes SEO blog\nposts to your blog using AI.\n\nThis guide walks you through everything\nfrom sign-up to automated publishing.",
            align="C",
        )

        self.set_y(250)
        self.set_font("Noto", "", 9)
        self.set_text_color(120, 120, 140)
        self.cell(0, 5, "https://postgenie.trytimeback.com", align="C")
        self.set_y(256)
        self.cell(0, 5, "Version 1.0 - 2026", align="C")

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
        self.cell(0, 8, f"> {title}")
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
        self.cell(5, 6, "-")
        self.set_x(25 + indent)
        self.multi_cell(0, 6, text)
        self.ln(0.5)

    def step(self, num: int, text: str):
        x_start = self.get_x()
        y_start = self.get_y()
        self.set_fill_color(*BRAND_PURPLE)
        self.set_text_color(255, 255, 255)
        self.set_font("Noto", "B", 10)
        self.ellipse(x_start, y_start, 7, 7, style="F")
        self.set_xy(x_start, y_start + 0.5)
        self.cell(7, 6, str(num), align="C")
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
        line_count = len(text) // 80 + text.count("\n") + 1
        box_height = 8 + line_count * 5.5
        self.rect(20, y_start, 170, box_height, style="DF")
        self.set_fill_color(*color)
        self.rect(20, y_start, 1.5, box_height, style="F")
        self.set_xy(25, y_start + 2)
        self.set_font("Noto", "B", 10.5)
        self.set_text_color(*color)
        self.cell(0, 5, title)
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

    pdf = PostGenieGuideEN()
    pdf.alias_nb_pages()

    # Cover
    pdf.cover_page()

    # Table of Contents
    pdf.add_page()
    pdf.set_font("Noto", "B", 24)
    pdf.set_text_color(*TEXT_DARK)
    pdf.cell(0, 15, "Table of Contents")
    pdf.ln(20)

    toc_items = [
        ("1", "What is PostGenie?", "3"),
        ("2", "Getting Started - Sign Up", "4"),
        ("3", "Connecting Your Blog", "5"),
        ("4", "Creating Auto-Posting Schedules", "7"),
        ("5", "Viewing and Managing Posts", "9"),
        ("6", "Plans and Pricing", "10"),
        ("7", "Frequently Asked Questions", "11"),
        ("8", "Support and Contact", "12"),
    ]
    for num, title, page in toc_items:
        pdf.set_font("Noto", "B", 11)
        pdf.set_text_color(*BRAND_PURPLE)
        pdf.cell(12, 10, num)
        pdf.set_font("Noto", "", 11)
        pdf.set_text_color(*TEXT_DARK)
        pdf.cell(150, 10, title)
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(0, 10, f"page {page}", align="R")
        pdf.ln(8)
        pdf.set_draw_color(220, 220, 230)
        pdf.set_line_width(0.2)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(3)

    # Chapter 1
    pdf.add_page()
    pdf.chapter_title("1", "What is PostGenie?")

    pdf.paragraph(
        "PostGenie is an AI-powered service that automatically writes and publishes "
        "blog posts to your blog every day. Set it up once, and Claude AI will analyze "
        "trending topics, generate SEO-optimized content, and publish it to your blog - "
        "completely hands-free."
    )

    pdf.section_title("Key Features")
    pdf.bullet("AI Content Writing - Claude AI creates high-quality SEO blog posts")
    pdf.bullet("Real-Time Trending Topics - Auto-fetches latest news from Google News")
    pdf.bullet("Multi-Language Support - English, Korean, Japanese, Spanish")
    pdf.bullet("Auto Publishing - Supports Blogger, WordPress, and more")
    pdf.bullet("Flexible Scheduling - 1-30 posts per day, or weekly")
    pdf.bullet("Category Selection - Trending news, tech, food, entertainment, etc.")

    pdf.section_title("How It Works")
    pdf.info_box(
        "Step 1 -> Step 2 -> Step 3",
        "1. Sign in with your Google account\n"
        "2. Connect your blog (Blogger or WordPress)\n"
        "3. Set your schedule - Posts publish automatically every day!",
    )

    pdf.section_title("Who Is It For?")
    pdf.bullet("Bloggers who don't have time to write every day")
    pdf.bullet("Individuals or businesses looking to grow SEO traffic")
    pdf.bullet("Bloggers targeting AdSense revenue")
    pdf.bullet("Anyone managing multiple blogs on different topics")

    # Chapter 2
    pdf.add_page()
    pdf.chapter_title("2", "Getting Started - Sign Up")

    pdf.paragraph(
        "PostGenie has no separate sign-up process. Just log in once with your "
        "Google account, and your account is created automatically."
    )

    pdf.section_title("How to Sign In")
    pdf.step(1, "Open https://postgenie.trytimeback.com in your browser")
    pdf.step(2, "Click the \"Sign in with Google\" button on the main page")
    pdf.step(3, "Select your Google account and grant permissions")
    pdf.step(4, "You'll be redirected to the dashboard - Sign-up complete!")

    pdf.ln(4)
    pdf.info_box(
        "[Privacy Note]",
        "PostGenie only reads your email, name, and profile picture from your\n"
        "Google account. No other information is accessed, and you can revoke\n"
        "permissions at any time from your Google account settings.",
        color=BRAND_BLUE,
    )

    pdf.section_title("Your First View")
    pdf.paragraph(
        "After logging in, you'll see your personal dashboard. The left sidebar "
        "shows your profile, current plan, and menu items (Dashboard, Connect Blog, "
        "Schedules, Posts, Upgrade). All metrics start at 0."
    )

    # Chapter 3
    pdf.add_page()
    pdf.chapter_title("3", "Connecting Your Blog")

    pdf.paragraph(
        "PostGenie supports Google Blogger and WordPress (self-hosted). "
        "The easiest option is Blogger."
    )

    pdf.section_title("Connecting Blogger (Recommended)")
    pdf.step(1, "Click \"Connect Blog\" in the sidebar")
    pdf.step(2, "Select \"Google Blogger\" as the platform")
    pdf.step(3, "Click the \"Authorize Blogger\" button")
    pdf.step(4, "Grant Blogger access in the Google permission screen")
    pdf.step(5, "You'll be redirected back and your blog list will appear")
    pdf.step(6, "Select the blog to connect -> Click \"Connect This Blog\"")
    pdf.step(7, "Done! The blog is now in your Connected Blogs list")

    pdf.ln(3)
    pdf.info_box(
        "[Don't have a Blogger?]",
        "You can create a free Blogger blog at blogger.com with your Google account.\n"
        "One account can have multiple blogs, and you can connect all of them to PostGenie.",
        color=ACCENT,
    )

    pdf.add_page()
    pdf.section_title("Connecting WordPress")
    pdf.paragraph(
        "WordPress uses an \"Application Password\", which is different from your "
        "regular login password."
    )

    pdf.step(1, "Access your WordPress admin panel (yourblog.com/wp-admin)")
    pdf.step(2, "Navigate to Users -> Profile from the left menu")
    pdf.step(3, "Scroll down to find the \"Application Passwords\" section")
    pdf.step(4, "Enter a name (e.g., PostGenie) -> Click \"Add New Application Password\"")
    pdf.step(5, "Copy the generated password (shown only once!)")
    pdf.step(6, "In PostGenie, go to Connect Blog -> Select WordPress")
    pdf.step(7, "Enter Site URL, Username, and Application Password to connect")

    pdf.ln(3)
    pdf.info_box(
        "[Important]",
        "Tistory and Naver Blog APIs are closed, so automatic connection\n"
        "is not possible. We recommend using Blogger or WordPress instead.",
        color=(239, 68, 68),
    )

    # Chapter 4
    pdf.add_page()
    pdf.chapter_title("4", "Creating Auto-Posting Schedules")

    pdf.paragraph(
        "A schedule defines \"when, with what topic, and to which blog\" posts "
        "will be published. Each schedule publishes one post per run."
    )

    pdf.section_title("Steps to Create a Schedule")
    pdf.step(1, "Click \"Schedules\" in the sidebar")
    pdf.step(2, "Enter a schedule name (e.g., Daily Tech News)")
    pdf.step(3, "Select Target Blog from your connected blogs")
    pdf.step(4, "Select Content Language - English / Korean / Japanese / Spanish")
    pdf.step(5, "Select Content Categories - shows categories matching your language")
    pdf.step(6, "Choose Posting Frequency - Daily / Twice Daily / Weekly")
    pdf.step(7, "Select Writing Tone - friendly / professional / casual, etc.")
    pdf.step(8, "Set Target Word Count - 500~2000 words (default 1000)")
    pdf.step(9, "Click \"Create Schedule\" - Done!")

    pdf.ln(3)
    pdf.section_title("Available Categories")
    pdf.paragraph("Categories depend on the selected language:")
    pdf.bullet("English: Trending News, Technology, Business, Entertainment, Health")
    pdf.bullet("Korean: Korean Trending, TV Food/Mukbang, K-POP/Entertainment, Lifestyle/Tips")

    pdf.add_page()
    pdf.section_title("Using Custom Topics")
    pdf.paragraph(
        "If you want to write on specific topics instead of trending news, enter "
        "topics one per line in the \"Custom Topics\" field. Posts will be randomly "
        "selected from your custom topics."
    )

    pdf.info_box(
        "Custom Topics Example",
        "Best diet tips for beginners\n"
        "How to invest for the first time\n"
        "Top 10 travel destinations in Europe\n"
        "Home coffee recipe collection",
        color=ACCENT,
    )

    pdf.section_title("Managing Schedules")
    pdf.paragraph(
        "Created schedules can be managed on the Schedules page:"
    )
    pdf.bullet("Active/Inactive toggle - Temporarily pause or resume")
    pdf.bullet("Delete - Permanently remove the schedule")
    pdf.bullet("View next run time")

    # Chapter 5
    pdf.add_page()
    pdf.chapter_title("5", "Viewing and Managing Posts")

    pdf.paragraph(
        "All posts automatically generated and published by PostGenie can be viewed "
        "on the \"Posts\" page."
    )

    pdf.section_title("Posts Page")
    pdf.paragraph("Posts are organized into 3 tabs:")
    pdf.bullet("[Published] - Successfully published posts (live on your blog)")
    pdf.bullet("[Pending] - Generated but awaiting publication")
    pdf.bullet("[Failed] - Failed posts (with error messages)")

    pdf.section_title("Information for Each Post")
    pdf.bullet("Title and creation date")
    pdf.bullet("Blog link (click to view the actual blog post)")
    pdf.bullet("Category and language")
    pdf.bullet("Tokens used")
    pdf.bullet("Full HTML content preview")

    pdf.section_title("Automatic Run Schedule")
    pdf.info_box(
        "[Schedule Run Time]",
        "PostGenie's automatic posting runs within 15 minutes past every hour.\n"
        "When you create a new schedule, the first post will be published within 1 hour.\n\n"
        "Example: Schedule created at 2:30 PM -> First post published at 3:15 PM",
        color=BRAND_PURPLE,
    )

    # Chapter 6
    pdf.add_page()
    pdf.chapter_title("6", "Plans and Pricing")

    pdf.paragraph(
        "PostGenie offers 4 plans from free trial to agency level."
    )

    pdf.ln(3)
    widths = [30, 30, 30, 40, 40]
    headers = ["Plan", "Price", "Blogs", "Frequency", "For"]
    rows = [
        ["Free", "$0", "1", "1/week", "Trial"],
        ["Basic", "$9/mo", "1", "1/day", "Personal"],
        ["Pro", "$29/mo", "3", "3/day", "Professional"],
        ["Agency", "$99/mo", "10", "30/day", "Agency"],
    ]

    pdf.table_row(headers, widths, header=True)
    for row in rows:
        pdf.table_row(row, widths)

    pdf.ln(5)
    pdf.section_title("How to Upgrade")
    pdf.step(1, "Click \"Upgrade\" in the sidebar")
    pdf.step(2, "Click the \"Upgrade\" button on your desired plan card")
    pdf.step(3, "Enter your card details in the Paddle checkout")
    pdf.step(4, "Payment complete - Your plan is upgraded automatically")

    pdf.ln(3)
    pdf.info_box(
        "[Payment Info]",
        "Payments are processed securely via Paddle.\n"
        "Prices include VAT where applicable. Cancel anytime.\n"
        "Manage your subscription via the customer portal in your Paddle email.",
        color=BRAND_BLUE,
    )

    # Chapter 7
    pdf.add_page()
    pdf.chapter_title("7", "Frequently Asked Questions")

    faqs = [
        (
            "Q. What's the quality of AI-written posts?",
            "Claude AI writes posts at professional blogger quality. They are "
            "SEO-optimized with natural sentence structure and practical information. "
            "However, we recommend reviewing sensitive topics that require fact-checking "
            "before publishing.",
        ),
        (
            "Q. Are there copyright concerns with AI posts?",
            "AI-generated posts are original content. While news headlines are used as "
            "topics, the actual content is written fresh by AI, so there are no "
            "copyright issues. Images must be added separately.",
        ),
        (
            "Q. How many posts can I publish per day?",
            "Depends on your plan. Free allows 1/week, Basic 1/day, Pro 3/day, "
            "and Agency 30/day.",
        ),
        (
            "Q. Can I edit published posts?",
            "Yes. You can edit posts directly on your blog platform (Blogger/WordPress). "
            "PostGenie only automates the initial publication - post-management is up to you.",
        ),
        (
            "Q. Can I run multiple blogs simultaneously?",
            "Yes, with the Pro plan or higher. You can create different schedules with "
            "different topics and languages for each blog.",
        ),
        (
            "Q. Can I use Korean and English together?",
            "Yes. You can set a different language for each schedule. For example, "
            "one blog can have a Korean schedule while another has an English schedule.",
        ),
        (
            "Q. Can I cancel anytime?",
            "Yes. You can cancel your subscription anytime, and you'll continue to "
            "have access until the end of your billing period.",
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

    # Chapter 8
    pdf.add_page()
    pdf.chapter_title("8", "Support and Contact")

    pdf.paragraph(
        "If you have questions or encounter issues, please contact us anytime."
    )

    pdf.section_title("Contact")
    pdf.bullet("Email: admin@trytimeback.com")
    pdf.bullet("Website: https://postgenie.trytimeback.com")

    pdf.section_title("Feedback Welcome")
    pdf.paragraph(
        "PostGenie is continuously improving. If you have feature requests or "
        "improvement ideas, please send them via email. User feedback shapes the "
        "direction of our next updates."
    )

    pdf.ln(10)
    pdf.set_font("Noto", "B", 14)
    pdf.set_text_color(*BRAND_PURPLE)
    pdf.cell(0, 10, "Get Started Now!", align="C")
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
    pdf.cell(0, 5, "(c) 2026 PostGenie. AI-Powered Blog Automation.", align="C")

    pdf.output(str(OUTPUT_FILE))
    print(f"[done] Generated: {OUTPUT_FILE}")
    print(f"   Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_guide()
