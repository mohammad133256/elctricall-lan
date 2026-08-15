# -*- coding: utf-8 -*-
"""
Electrical Industrial Lab
A comprehensive offline educational & engineering app for Industrial Electricity
Built with Python + Kivy + KivyMD
Target: Android (offline-first)
Version: MVP 1.0
"""

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDTextButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationdrawer import MDNavigationDrawer, MDNavigationLayout
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, OneLineIconListItem
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.theming import ThemeManager
from kivymd.uix.snackbar import Snackbar

import math
import json
import os
from datetime import datetime
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path

# ============================================================
# THEME & CONFIG + PERSIAN FONT
# ============================================================
# On Android make it fullscreen (do not force size)
if platform not in ('android', 'ios'):
    Window.size = (400, 700)  # only for desktop testing

# Register Persian-supporting font - tries Android system fonts first (best for Samsung S23)
DEFAULT_FONT = "Roboto"
font_loaded = False

# 1. Try common Android system fonts that support Arabic/Persian
system_fonts = [
    "/system/fonts/NotoNaskhArabic-Regular.ttf",
    "/system/fonts/NotoSansArabic-Regular.ttf",
    "/system/fonts/NotoNaskhArabicUI-Regular.ttf",
    "/system/fonts/NotoNaskhArabic-Bold.ttf",
    "/system/fonts/DroidNaskh-Regular.ttf",
    "/system/fonts/NotoSansCJK-Regular.ttc",
]

for font_path in system_fonts:
    if os.path.exists(font_path):
        try:
            LabelBase.register(name="PersianFont", fn_regular=font_path)
            DEFAULT_FONT = "PersianFont"
            print(f"[FONT] Loaded system font: {font_path}")
            font_loaded = True
            break
        except Exception as e:
            print(f"[FONT] System font failed: {e}")

# 2. Try local Cairo font if system font not found
if not font_loaded:
    local_font_dirs = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
        os.path.join(os.getcwd(), "fonts"),
        "fonts",
        "/sdcard/Download/ElectricalIndustrialLab/fonts",
        "/storage/emulated/0/Download/ElectricalIndustrialLab/fonts",
        "/storage/emulated/0/Android/data/ru.iiec.pydroid3/files/fonts",
        "/storage/emulated/0/Android/data/ru.iiec.pydroid3/files/ElectricalIndustrialLab/fonts",
    ]
    for FONT_DIR in local_font_dirs:
        regular = os.path.join(FONT_DIR, "Cairo-Regular.ttf")
        if os.path.exists(regular):
            try:
                resource_add_path(FONT_DIR)
                LabelBase.register(name="Cairo", fn_regular=regular)
                DEFAULT_FONT = "Cairo"
                print(f"[FONT] Loaded Cairo from: {FONT_DIR}")
                font_loaded = True
                break
            except Exception as e:
                print(f"[FONT] Local failed: {e}")

if not font_loaded:
    print("[FONT] No Persian font found. Text may appear as boxes.")

# ============================================================
# DATA LAYER (Offline Database)
# ============================================================

FORMULAS = {
    "قانون اهم": [
        {
            "name": "ولتاژ",
            "formula": "V = I × R",
            "vars": {"V": "ولتاژ (Volt)", "I": "جریان (Ampere)", "R": "مقاومت (Ohm)"},
            "example": "اگر I=2A و R=10Ω باشد، V = 2×10 = 20V"
        },
        {
            "name": "جریان",
            "formula": "I = V / R",
            "vars": {"I": "جریان (A)", "V": "ولتاژ (V)", "R": "مقاومت (Ω)"},
            "example": "اگر V=220V و R=110Ω باشد، I = 220/110 = 2A"
        },
        {
            "name": "مقاومت",
            "formula": "R = V / I",
            "vars": {"R": "مقاومت (Ω)", "V": "ولتاژ (V)", "I": "جریان (A)"},
            "example": "اگر V=12V و I=0.5A باشد، R = 12/0.5 = 24Ω"
        },
    ],
    "توان": [
        {
            "name": "توان DC",
            "formula": "P = V × I",
            "vars": {"P": "توان (Watt)", "V": "ولتاژ (V)", "I": "جریان (A)"},
            "example": "V=24V ، I=5A → P=120W"
        },
        {
            "name": "توان تک‌فاز AC",
            "formula": "P = V × I × cosφ",
            "vars": {"P": "توان اکتیو (W)", "V": "ولتاژ (V)", "I": "جریان (A)", "cosφ": "ضریب توان"},
            "example": "V=220V ، I=10A ، cosφ=0.8 → P=1760W"
        },
        {
            "name": "توان سه‌فاز",
            "formula": "P = √3 × V_L × I_L × cosφ",
            "vars": {"P": "توان اکتیو (W)", "V_L": "ولتاژ خط (V)", "I_L": "جریان خط (A)", "cosφ": "ضریب توان"},
            "example": "V=400V ، I=20A ، cosφ=0.85 → P ≈ 11785W"
        },
        {
            "name": "توان ظاهری سه‌فاز",
            "formula": "S = √3 × V_L × I_L",
            "vars": {"S": "توان ظاهری (VA)", "V_L": "ولتاژ خط", "I_L": "جریان خط"},
            "example": "V=400 ، I=15 → S ≈ 10392 VA"
        },
        {
            "name": "توان راکتیو سه‌فاز",
            "formula": "Q = √3 × V_L × I_L × sinφ",
            "vars": {"Q": "توان راکتیو (VAR)", "sinφ": "sinφ = √(1-cos²φ)"},
            "example": "با cosφ=0.8 → sinφ=0.6"
        },
        {
            "name": "ضریب توان",
            "formula": "cosφ = P / S",
            "vars": {"cosφ": "ضریب توان", "P": "توان اکتیو", "S": "توان ظاهری"},
            "example": "P=8000W ، S=10000VA → cosφ=0.8"
        },
    ],
    "موتور": [
        {
            "name": "سرعت سنکرون",
            "formula": "Ns = 120 × f / P",
            "vars": {"Ns": "سرعت سنکرون (rpm)", "f": "فرکانس (Hz)", "P": "تعداد قطب"},
            "example": "f=50Hz ، P=4 → Ns=1500 rpm"
        },
        {
            "name": "لغزش",
            "formula": "s = (Ns - Nr) / Ns",
            "vars": {"s": "لغزش (pu)", "Ns": "سرعت سنکرون", "Nr": "سرعت روتور"},
            "example": "Ns=1500 ، Nr=1450 → s=0.0333 (3.33%)"
        },
        {
            "name": "گشتاور",
            "formula": "T = (P_out × 60) / (2π × Nr)",
            "vars": {"T": "گشتاور (N.m)", "P_out": "توان خروجی (W)", "Nr": "سرعت (rpm)"},
            "example": "P=7500W ، Nr=1450 → T ≈ 49.4 N.m"
        },
        {
            "name": "راندمان",
            "formula": "η = P_out / P_in",
            "vars": {"η": "راندمان", "P_out": "توان خروجی", "P_in": "توان ورودی"},
            "example": "P_out=7.5kW ، P_in=8.5kW → η≈0.882"
        },
    ],
    "افت ولتاژ و کابل": [
        {
            "name": "افت ولتاژ تک‌فاز",
            "formula": "ΔV = 2 × I × L × R",
            "vars": {"ΔV": "افت ولتاژ (V)", "I": "جریان", "L": "طول یک طرف (m)", "R": "مقاومت بر متر (Ω/m)"},
            "example": "مقاومت مس ≈ 0.0175 Ω.mm²/m"
        },
        {
            "name": "افت ولتاژ سه‌فاز",
            "formula": "ΔV = √3 × I × L × R × cosφ  (تقریبی مقاومتی)",
            "vars": {"ΔV": "افت ولتاژ خط", "نکته": "برای دقت بالاتر امپدانس کامل استفاده شود"},
            "example": "در عمل جداول استاندارد و ضریب اصلاح دما مهم است"
        },
    ]
}

LESSONS = {
    "پایه": [
        {
            "title": "ولتاژ، جریان و مقاومت",
            "content": """ولتاژ (Voltage): اختلاف پتانسیل الکتریکی بین دو نقطه است و واحد آن ولت (V) می‌باشد.
جریان (Current): عبور بار الکتریکی در واحد زمان است و واحد آن آمپر (A) می‌باشد.
مقاومت (Resistance): مخالفت ماده در برابر عبور جریان است و واحد آن اهم (Ω) می‌باشد.

قانون اهم: V = I × R
این قانون پایه‌ای‌ترین رابطه در برق است.""",
            "formulas": ["V = I × R", "I = V / R", "R = V / I"],
            "tips": ["همیشه واحدها را یکسان کنید.", "در مدار سری جریان یکسان و ولتاژ تقسیم می‌شود."],
            "mistakes": ["اشتباه گرفتن ولتاژ خط و فاز در سیستم سه‌فاز."]
        },
        {
            "title": "توان و انرژی",
            "content": """توان (Power): نرخ انجام کار یا مصرف انرژی است. واحد وات (W).
انرژی = توان × زمان. واحد ژول یا کیلووات‌ساعت.

در DC: P = V × I
در AC تک‌فاز: P = V × I × cosφ""",
            "formulas": ["P = V × I", "P = V × I × cosφ", "E = P × t"],
            "tips": ["ضریب توان نشان‌دهنده کیفیت مصرف توان اکتیو است."],
            "mistakes": ["نادیده گرفتن ضریب توان در محاسبات AC."]
        },
        {
            "title": "قانون اهم و کیرشهف",
            "content": """قوانین کیرشهف:
KCL: مجموع جریان‌های ورودی به یک گره برابر مجموع جریان‌های خروجی است.
KVL: مجموع ولتاژهای یک حلقه بسته برابر صفر است.""",
            "formulas": ["ΣI_in = ΣI_out", "ΣV = 0"],
            "tips": ["جهت جریان فرضی را مشخص کنید."],
            "mistakes": ["علامت‌گذاری اشتباه ولتاژها."]
        },
    ],
    "متوسط": [
        {
            "title": "مدار سری و موازی",
            "content": """مدار سری: جریان یکسان، ولتاژ تقسیم می‌شود. R_eq = R1+R2+...
مدار موازی: ولتاژ یکسان، جریان تقسیم می‌شود. 1/R_eq = 1/R1 + 1/R2 + ...""",
            "formulas": ["R_series = ΣR", "1/R_parallel = Σ(1/R)"],
            "tips": ["در موازی مقاومت معادل همیشه از کوچک‌ترین مقاومت کمتر است."],
            "mistakes": ["محاسبه اشتباه مقاومت معادل موازی."]
        },
        {
            "title": "سیستم سه‌فاز",
            "content": """در سیستم سه‌فاز، سه ولتاژ با اختلاف فاز ۱۲۰ درجه وجود دارد.
اتصال ستاره (Y): V_L = √3 × V_ph ، I_L = I_ph
اتصال مثلث (Δ): V_L = V_ph ، I_L = √3 × I_ph""",
            "formulas": ["V_L = √3 V_ph (ستاره)", "I_L = √3 I_ph (مثلث)"],
            "tips": ["در اکثر شبکه‌های توزیع از ستاره استفاده می‌شود."],
            "mistakes": ["اشتباه گرفتن جریان خط و فاز."]
        },
        {
            "title": "ترانسفورماتور و موتور القایی",
            "content": """ترانسفورماتور بر اساس القای متقابل کار می‌کند.
موتور القایی سه‌فاز پرکاربردترین موتور صنعتی است. سرعت آن کمی کمتر از سرعت سنکرون است (لغزش).""",
            "formulas": ["Ns = 120f/P", "s = (Ns-Nr)/Ns"],
            "tips": ["لغزش معمولاً بین ۲ تا ۵ درصد است."],
            "mistakes": ["فرض کردن سرعت موتور دقیقاً برابر سرعت سنکرون."]
        },
    ],
    "پیشرفته": [
        {
            "title": "ماشین‌های AC و DC",
            "content": """ماشین‌های DC: کموتاتور دارند و کنترل سرعت ساده‌تری دارند.
ماشین‌های سنکرون: سرعت دقیقاً برابر سنکرون است و می‌توانند ضریب توان را کنترل کنند.
موتور القایی: ساده، ارزان و قابل اعتماد.""",
            "formulas": ["T ∝ Φ × I_a (DC)", "Ns = 120f/P"],
            "tips": ["برای کنترل دقیق سرعت از VFD استفاده می‌شود."],
            "mistakes": ["استفاده از موتور القایی بدون در نظر گرفتن جریان راه‌اندازی بالا."]
        },
        {
            "title": "راه‌اندازی و کنترل موتور",
            "content": """روش‌های راه‌اندازی:
- مستقیم (DOL)
- ستاره-مثلث
- سافت‌استارتر
- درایو فرکانس متغیر (VFD)

VFD بهترین کنترل سرعت و گشتاور را فراهم می‌کند.""",
            "formulas": ["جریان راه‌اندازی DOL ≈ ۵ تا ۷ برابر جریان نامی"],
            "tips": ["برای موتورهای بزرگ از ستاره-مثلث یا سافت‌استارتر استفاده کنید."],
            "mistakes": ["نادیده گرفتن گشتاور بار در انتخاب روش راه‌اندازی."]
        },
    ]
}

QUESTIONS = [
    {
        "category": "برق پایه",
        "level": "آسان",
        "question": "طبق قانون اهم، اگر ولتاژ دو برابر شود و مقاومت ثابت بماند، جریان چه تغییری می‌کند؟",
        "options": ["نصف می‌شود", "دو برابر می‌شود", "چهار برابر می‌شود", "تغییری نمی‌کند"],
        "answer": 1,
        "explanation": "I = V/R → اگر V دو برابر شود، I نیز دو برابر می‌شود.",
        "formula": "I = V / R"
    },
    {
        "category": "سه‌فاز",
        "level": "متوسط",
        "question": "در اتصال ستاره، رابطه ولتاژ خط و فاز چیست؟",
        "options": ["V_L = V_ph", "V_L = √3 V_ph", "V_L = V_ph / √3", "V_L = 3 V_ph"],
        "answer": 1,
        "explanation": "در اتصال ستاره ولتاژ خط √3 برابر ولتاژ فاز است.",
        "formula": "V_L = √3 × V_ph"
    },
    {
        "category": "موتور",
        "level": "متوسط",
        "question": "سرعت سنکرون موتور ۴ قطبی با فرکانس ۵۰ هرتز چقدر است؟",
        "options": ["750 rpm", "1000 rpm", "1500 rpm", "3000 rpm"],
        "answer": 2,
        "explanation": "Ns = 120 × f / P = 120 × 50 / 4 = 1500 rpm",
        "formula": "Ns = 120f / P"
    },
    {
        "category": "موتور",
        "level": "سخت",
        "question": "اگر سرعت سنکرون ۱۵۰۰ rpm و سرعت واقعی ۱۴۵۵ rpm باشد، لغزش چند درصد است؟",
        "options": ["2%", "3%", "4%", "5%"],
        "answer": 1,
        "explanation": "s = (1500-1455)/1500 = 0.03 → 3%",
        "formula": "s = (Ns - Nr)/Ns"
    },
    {
        "category": "محاسبات",
        "level": "متوسط",
        "question": "توان سه‌فاز با V=400V ، I=10A و cosφ=0.8 تقریباً چند کیلووات است؟",
        "options": ["4.0 kW", "5.5 kW", "6.9 kW", "8.0 kW"],
        "answer": 1,
        "explanation": "P = √3 × 400 × 10 × 0.8 ≈ 5542 W ≈ 5.5 kW",
        "formula": "P = √3 × V × I × cosφ"
    },
    {
        "category": "مدار فرمان",
        "level": "آسان",
        "question": "در مدار Start/Stop با Self-Holding، وظیفه کنتاکت کمکی کنتاکتور چیست؟",
        "options": ["حفاظت اضافه جریان", "نگه‌داشتن مدار پس از رها کردن شستی Start", "قطع اضطراری", "تغییر جهت موتور"],
        "answer": 1,
        "explanation": "کنتاکت NO کمکی موازی با شستی Start قرار می‌گیرد و مدار را نگه می‌دارد (Self Holding).",
        "formula": "-"
    },
]

# Standard cable cross sections (mm²)
STANDARD_SECTIONS = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# Approximate resistivity (Ω.mm²/m) at 20°C
RESISTIVITY = {"مس": 0.0175, "آلومینیوم": 0.0285}

# Approximate current carrying capacity (A) for PVC insulated cables in air (simplified)
# These are approximate values for educational purposes only
CURRENT_CAPACITY = {
    1.5: 15, 2.5: 21, 4: 28, 6: 36, 10: 50, 16: 66,
    25: 89, 35: 110, 50: 134, 70: 171, 95: 207,
    120: 239, 150: 275, 185: 314, 240: 369, 300: 424
}

# ============================================================
# CALCULATION ENGINE (Separated from UI)
# ============================================================

class CalcEngine:
    """All engineering calculations live here. Pure logic, no UI."""

    @staticmethod
    def ohm_law(v=None, i=None, r=None):
        try:
            if v is None and i is not None and r is not None:
                return {"V": i * r, "unit": "V"}
            if i is None and v is not None and r is not None and r != 0:
                return {"I": v / r, "unit": "A"}
            if r is None and v is not None and i is not None and i != 0:
                return {"R": v / i, "unit": "Ω"}
            return {"error": "ورودی ناکافی یا نامعتبر"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def power_dc(v, i):
        try:
            return {"P": v * i, "unit": "W"}
        except:
            return {"error": "ورودی نامعتبر"}

    @staticmethod
    def power_1ph(v, i, pf):
        try:
            if not (0 <= pf <= 1):
                return {"error": "ضریب توان باید بین ۰ و ۱ باشد"}
            p = v * i * pf
            s = v * i
            q = v * i * math.sqrt(max(0, 1 - pf**2))
            return {"P": p, "S": s, "Q": q, "unit_P": "W", "unit_S": "VA", "unit_Q": "VAR"}
        except:
            return {"error": "خطا در محاسبه"}

    @staticmethod
    def power_3ph(v_l, i_l, pf):
        try:
            if not (0 <= pf <= 1):
                return {"error": "ضریب توان باید بین ۰ و ۱ باشد"}
            p = math.sqrt(3) * v_l * i_l * pf
            s = math.sqrt(3) * v_l * i_l
            q = math.sqrt(3) * v_l * i_l * math.sqrt(max(0, 1 - pf**2))
            return {"P": p, "S": s, "Q": q, "unit_P": "W", "unit_S": "VA", "unit_Q": "VAR"}
        except:
            return {"error": "خطا در محاسبه"}

    @staticmethod
    def sync_speed(f, poles):
        try:
            if poles <= 0 or poles % 2 != 0:
                return {"error": "تعداد قطب باید عدد زوج مثبت باشد"}
            ns = 120 * f / poles
            return {"Ns": ns, "unit": "rpm"}
        except:
            return {"error": "خطا"}

    @staticmethod
    def slip(ns, nr):
        try:
            if ns == 0:
                return {"error": "سرعت سنکرون نمی‌تواند صفر باشد"}
            s = (ns - nr) / ns
            return {"s": s, "s_percent": s * 100}
        except:
            return {"error": "خطا"}

    @staticmethod
    def motor_full(v, f, p_kw, poles, pf, eff):
        """Full motor calculator for 3-phase induction motor."""
        try:
            if any(x is None for x in [v, f, p_kw, poles, pf, eff]):
                return {"error": "همه ورودی‌ها الزامی است"}
            if poles % 2 != 0 or poles <= 0:
                return {"error": "تعداد قطب باید زوج و مثبت باشد"}
            if not (0 < pf <= 1) or not (0 < eff <= 1):
                return {"error": "ضریب توان و راندمان باید بین ۰ و ۱ باشند"}

            p_out = p_kw * 1000  # W
            p_in = p_out / eff
            i_approx = p_in / (math.sqrt(3) * v * pf)
            ns = 120 * f / poles
            # Assume typical slip 3% if not given
            slip_assumed = 0.03
            nr = ns * (1 - slip_assumed)
            s = math.sqrt(3) * v * i_approx
            q = math.sqrt(3) * v * i_approx * math.sqrt(max(0, 1 - pf**2))
            omega = 2 * math.pi * nr / 60
            torque = p_out / omega if omega > 0 else 0

            return {
                "I": round(i_approx, 2),
                "Ns": round(ns, 1),
                "Nr_approx": round(nr, 1),
                "slip_assumed": slip_assumed,
                "P_in": round(p_in, 1),
                "P_out": round(p_out, 1),
                "S": round(s, 1),
                "Q": round(q, 1),
                "T": round(torque, 2),
                "pf": pf,
                "eff": eff,
                "note": "سرعت واقعی با فرض لغزش ۳٪ محاسبه شده است. برای دقت بیشتر لغزش واقعی را وارد کنید."
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def voltage_drop(v, i, length, section, material, phases, pf=0.85):
        """
        Approximate voltage drop calculation.
        Uses DC resistance approximation + power factor.
        Educational purpose only.
        """
        try:
            if section <= 0 or length <= 0 or i < 0:
                return {"error": "ورودی نامعتبر"}
            rho = RESISTIVITY.get(material, 0.0175)
            r_per_m = rho / section  # Ω/m
            r_total = r_per_m * length

            if phases == 1:
                # Single phase: go and return
                dv = 2 * i * r_total * pf   # simplified
            else:
                # Three phase
                dv = math.sqrt(3) * i * r_total * pf

            dv_percent = (dv / v) * 100 if v > 0 else 0
            v_end = v - dv
            power_loss = (i ** 2) * r_total * (2 if phases == 1 else 3)  # approximate

            status = "مناسب"
            if dv_percent > 5:
                status = "نامناسب"
            elif dv_percent > 3:
                status = "مرزی"

            return {
                "dV": round(dv, 2),
                "dV_percent": round(dv_percent, 2),
                "V_end": round(v_end, 2),
                "P_loss": round(power_loss, 1),
                "status": status,
                "note": "محاسبه تقریبی بر اساس مقاومت DC و ضریب توان. برای طراحی واقعی از جداول استاندارد و امپدانس کامل استفاده کنید."
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def cable_select(v, i_load, length, material, phases, pf, max_drop_percent=3.0, temp_factor=1.0):
        """
        Suggest minimum cable section based on current capacity and voltage drop.
        Educational / preliminary suggestion only.
        """
        try:
            results = []
            for sec in STANDARD_SECTIONS:
                # Check current capacity (simplified, no installation method derating fully applied)
                capacity = CURRENT_CAPACITY.get(sec, 0) * temp_factor
                current_ok = capacity >= i_load

                # Voltage drop
                vd = CalcEngine.voltage_drop(v, i_load, length, sec, material, phases, pf)
                if "error" in vd:
                    continue
                drop_ok = vd["dV_percent"] <= max_drop_percent

                results.append({
                    "section": sec,
                    "capacity": round(capacity, 1),
                    "current_ok": current_ok,
                    "dV_percent": vd["dV_percent"],
                    "drop_ok": drop_ok,
                    "overall_ok": current_ok and drop_ok
                })

            # Find smallest that is overall_ok
            suitable = [r for r in results if r["overall_ok"]]
            recommendation = suitable[0]["section"] if suitable else None

            return {
                "results": results,
                "recommendation": recommendation,
                "warning": "این یک پیشنهاد اولیه آموزشی است. برای انتخاب نهایی کابل باید استاندارد ملی، روش نصب، دمای محیط، تعداد کابل‌ها در کنار هم، و دیتاشیت سازنده بررسی شود."
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def winding_basic(slots, poles, phases=3):
        """
        Basic winding design check and calculation.
        Only supports cases where slots_per_pole_per_phase is integer or simple.
        """
        try:
            slots = int(slots)
            poles = int(poles)
            phases = int(phases)
            if slots <= 0 or poles <= 0 or phases <= 0:
                return {"error": "مقادیر باید مثبت باشند"}
            if poles % 2 != 0:
                return {"error": "تعداد قطب باید زوج باشد"}
            if slots % phases != 0:
                return {"error": "تعداد شیار باید بر تعداد فاز بخش‌پذیر باشد"}

            spp = slots / (poles * phases)  # slots per pole per phase
            pole_pitch = slots / poles
            # For simplicity we support integer SPP or half
            if not (spp == int(spp) or (spp * 2) == int(spp * 2)):
                return {"error": "این ترکیب پارامترها برای الگوریتم فعلی پشتیبانی نمی‌شود. SPP باید عدد صحیح یا نیمه‌صحیح باشد."}

            coil_pitch = int(pole_pitch)  # full pitch for simplicity
            # Simple phase distribution
            phase_order = []
            for p in range(poles):
                for ph in range(phases):
                    for s in range(int(spp) if spp >= 1 else 1):
                        phase_order.append(chr(65 + ph))  # A, B, C

            # Build simple slot map
            slot_map = []
            for i in range(slots):
                slot_map.append({
                    "slot": i + 1,
                    "phase": phase_order[i % len(phase_order)] if phase_order else "?",
                    "direction": "+" if (i // max(1, int(spp))) % 2 == 0 else "-"
                })

            return {
                "slots": slots,
                "poles": poles,
                "phases": phases,
                "spp": spp,
                "pole_pitch": pole_pitch,
                "coil_pitch": coil_pitch,
                "slot_map": slot_map,
                "note": "این یک طراحی پایه و آموزشی است. برای سیم‌پیچی واقعی باید ضریب توزیع، ضریب گام، نوع لایه‌بندی و جهت دقیق کلاف‌ها محاسبه شود."
            }
        except Exception as e:
            return {"error": str(e)}


# ============================================================
# KV LANGUAGE (UI Layout)
# ============================================================

KV = """
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<CardButton@MDCard>:
    orientation: "vertical"
    padding: dp(12)
    spacing: dp(6)
    size_hint_y: None
    height: dp(110)
    radius: [12]
    elevation: 2
    ripple_behavior: True
    md_bg_color: app.theme_cls.bg_normal

<CalcField@MDTextField>:
    mode: "rectangle"
    size_hint_x: 1
    font_size: "14sp"

MDScreen:
    md_bg_color: app.theme_cls.bg_dark

    MDNavigationLayout:
        ScreenManager:
            id: screen_manager

            # ==================== HOME ====================
            MDScreen:
                name: "home"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "Electrical Industrial Lab"
                        elevation: 2
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                        right_action_items: [["information-outline", lambda x: app.show_about()]]

                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(16)
                            spacing: dp(16)
                            adaptive_height: True

                            MDLabel:
                                text: "داشبورد"
                                font_style: "H5"
                                bold: True
                                size_hint_y: None
                                height: self.texture_size[1]
                                theme_text_color: "Primary"

                            MDLabel:
                                text: "برق صنعتی • ماشین‌های الکتریکی • محاسبات • شبیه‌سازی"
                                font_style: "Caption"
                                theme_text_color: "Secondary"
                                size_hint_y: None
                                height: self.texture_size[1]

                            # Quick Access Grid
                            MDGridLayout:
                                cols: 2
                                spacing: dp(12)
                                adaptive_height: True
                                size_hint_y: None

                                CardButton:
                                    on_release: app.change_screen("education")
                                    MDIcon:
                                        icon: "book-open-page-variant"
                                        font_size: "32sp"
                                        theme_text_color: "Custom"
                                        text_color: app.theme_cls.primary_color
                                        pos_hint: {"center_x": 0.5}
                                    MDLabel:
                                        text: "آموزش"
                                        halign: "center"
                                        font_style: "Button"
                                    MDLabel:
                                        text: "دروس پایه تا پیشرفته"
                                        halign: "center"
                                        font_style: "Caption"
                                        theme_text_color: "Secondary"

                                CardButton:
                                    on_release: app.change_screen("formulas")
                                    MDIcon:
                                        icon: "function-variant"
                                        font_size: "32sp"
                                        theme_text_color: "Custom"
                                        text_color: 0.2, 0.7, 0.9, 1
                                        pos_hint: {"center_x": 0.5}
                                    MDLabel:
                                        text: "فرمول‌نامه"
                                        halign: "center"
                                        font_style: "Button"
                                    MDLabel:
                                        text: "کتابخانه فرمول‌ها"
                                        halign: "center"
                                        font_style: "Caption"
                                        theme_text_color: "Secondary"

                                CardButton:
                                    on_release: app.change_screen("tools")
                                    MDIcon:
                                        icon: "calculator-variant"
                                        font_size: "32sp"
                                        theme_text_color: "Custom"
                                        text_color: 0.9, 0.6, 0.1, 1
                                        pos_hint: {"center_x": 0.5}
                                    MDLabel:
                                        text: "ابزارها"
                                        halign: "center"
                                        font_style: "Button"
                                    MDLabel:
                                        text: "ماشین‌حساب‌های مهندسی"
                                        halign: "center"
                                        font_style: "Caption"
                                        theme_text_color: "Secondary"

                                CardButton:
                                    on_release: app.change_screen("motor_lab")
                                    MDIcon:
                                        icon: "engine"
                                        font_size: "32sp"
                                        theme_text_color: "Custom"
                                        text_color: 0.3, 0.8, 0.4, 1
                                        pos_hint: {"center_x": 0.5}
                                    MDLabel:
                                        text: "موتور لب"
                                        halign: "center"
                                        font_style: "Button"
                                    MDLabel:
                                        text: "محاسبات موتور"
                                        halign: "center"
                                        font_style: "Caption"
                                        theme_text_color: "Secondary"

                                CardButton:
                                    on_release: app.change_screen("cable")
                                    MDIcon:
                                        icon: "cable-data"
                                        font_size: "32sp"
                                        theme_text_color: "Custom"
                                        text_color: 0.8, 0.3, 0.3, 1
                                        pos_hint: {"center_x": 0.5}
                                    MDLabel:
                                        text: "کابل"
                                        halign: "center"
                                        font_style: "Button"
                                    MDLabel:
                                        text: "انتخاب سطح مقطع"
                                        halign: "center"
                                        font_style: "Caption"
                                        theme_text_color: "Secondary"

                                CardButton:
                                    on_release: app.change_screen("winding")
                                    MDIcon:
                                        icon: "sine-wave"
                                        font_size: "32sp"
                                        theme_text_color: "Custom"
                                        text_color: 0.6, 0.4, 0.9, 1
                                        pos_hint: {"center_x": 0.5}
                                    MDLabel:
                                        text: "سیم‌پیچی"
                                        halign: "center"
                                        font_style: "Button"
                                    MDLabel:
                                        text: "طراح سیم‌پیچی"
                                        halign: "center"
                                        font_style: "Caption"
                                        theme_text_color: "Secondary"

                                CardButton:
                                    on_release: app.change_screen("quiz")
                                    MDIcon:
                                        icon: "help-circle"
                                        font_size: "32sp"
                                        theme_text_color: "Custom"
                                        text_color: 0.9, 0.4, 0.6, 1
                                        pos_hint: {"center_x": 0.5}
                                    MDLabel:
                                        text: "تمرین و آزمون"
                                        halign: "center"
                                        font_style: "Button"
                                    MDLabel:
                                        text: "سوالات آفلاین"
                                        halign: "center"
                                        font_style: "Caption"
                                        theme_text_color: "Secondary"

                                CardButton:
                                    on_release: app.change_screen("circuit")
                                    MDIcon:
                                        icon: "electric-switch"
                                        font_size: "32sp"
                                        theme_text_color: "Custom"
                                        text_color: 0.2, 0.6, 0.8, 1
                                        pos_hint: {"center_x": 0.5}
                                    MDLabel:
                                        text: "مدار فرمان"
                                        halign: "center"
                                        font_style: "Button"
                                    MDLabel:
                                        text: "آزمایشگاه مدار"
                                        halign: "center"
                                        font_style: "Caption"
                                        theme_text_color: "Secondary"

                            MDLabel:
                                text: "هشدار مهندسی"
                                font_style: "Subtitle1"
                                bold: True
                                size_hint_y: None
                                height: self.texture_size[1]
                                theme_text_color: "Primary"
                                padding: [0, dp(8), 0, 0]

                            MDCard:
                                orientation: "vertical"
                                padding: dp(12)
                                size_hint_y: None
                                height: dp(90)
                                radius: [10]
                                md_bg_color: 0.25, 0.15, 0.1, 1
                                MDLabel:
                                    text: "این نرم‌افزار آموزشی و محاسباتی است. نتایج باید با استانداردها، دیتاشیت سازنده و مقررات محلی تأیید شوند."
                                    font_style: "Caption"
                                    theme_text_color: "Custom"
                                    text_color: 1, 0.85, 0.6, 1

            # ==================== EDUCATION ====================
            MDScreen:
                name: "education"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "آموزش برق صنعتی"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("home")]]

                    MDScrollView:
                        MDBoxLayout:
                            id: education_list
                            orientation: "vertical"
                            padding: dp(12)
                            spacing: dp(10)
                            adaptive_height: True

            # ==================== FORMULAS ====================
            MDScreen:
                name: "formulas"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "فرمول‌نامه"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("home")]]

                    MDScrollView:
                        MDBoxLayout:
                            id: formulas_list
                            orientation: "vertical"
                            padding: dp(12)
                            spacing: dp(10)
                            adaptive_height: True

            # ==================== TOOLS HUB ====================
            MDScreen:
                name: "tools"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "ابزارهای مهندسی"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("home")]]

                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(12)
                            spacing: dp(10)
                            adaptive_height: True

                            MDRaisedButton:
                                text: "قانون اهم"
                                size_hint_x: 1
                                on_release: app.change_screen("ohm")
                            MDRaisedButton:
                                text: "توان تک‌فاز و سه‌فاز"
                                size_hint_x: 1
                                on_release: app.change_screen("power")
                            MDRaisedButton:
                                text: "ماشین‌حساب موتور سه‌فاز"
                                size_hint_x: 1
                                on_release: app.change_screen("motor_lab")
                            MDRaisedButton:
                                text: "افت ولتاژ"
                                size_hint_x: 1
                                on_release: app.change_screen("vdrop")
                            MDRaisedButton:
                                text: "انتخاب کابل"
                                size_hint_x: 1
                                on_release: app.change_screen("cable")
                            MDRaisedButton:
                                text: "سرعت سنکرون و لغزش"
                                size_hint_x: 1
                                on_release: app.change_screen("speed")

            # ==================== OHM CALCULATOR ====================
            MDScreen:
                name: "ohm"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "قانون اهم"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("tools")]]
                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(16)
                            spacing: dp(12)
                            adaptive_height: True
                            MDLabel:
                                text: "دو مقدار را وارد کنید، سومی محاسبه می‌شود"
                                theme_text_color: "Secondary"
                            CalcField:
                                id: ohm_v
                                hint_text: "ولتاژ V (ولت)"
                            CalcField:
                                id: ohm_i
                                hint_text: "جریان I (آمپر)"
                            CalcField:
                                id: ohm_r
                                hint_text: "مقاومت R (اهم)"
                            MDRaisedButton:
                                text: "محاسبه"
                                size_hint_x: 1
                                on_release: app.calc_ohm()
                            MDLabel:
                                id: ohm_result
                                text: ""
                                theme_text_color: "Primary"
                                size_hint_y: None
                                height: self.texture_size[1] + dp(20)

            # ==================== POWER CALCULATOR ====================
            MDScreen:
                name: "power"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "محاسبه توان"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("tools")]]
                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(16)
                            spacing: dp(10)
                            adaptive_height: True
                            MDLabel:
                                text: "سه‌فاز"
                                bold: True
                            CalcField:
                                id: p3_v
                                hint_text: "ولتاژ خط (V)"
                                text: "400"
                            CalcField:
                                id: p3_i
                                hint_text: "جریان خط (A)"
                            CalcField:
                                id: p3_pf
                                hint_text: "ضریب توان (0-1)"
                                text: "0.85"
                            MDRaisedButton:
                                text: "محاسبه سه‌فاز"
                                size_hint_x: 1
                                on_release: app.calc_power3()
                            MDLabel:
                                id: p3_result
                                text: ""
                                size_hint_y: None
                                height: self.texture_size[1] + dp(10)

                            MDLabel:
                                text: "تک‌فاز"
                                bold: True
                                padding: [0, dp(16), 0, 0]
                            CalcField:
                                id: p1_v
                                hint_text: "ولتاژ (V)"
                                text: "220"
                            CalcField:
                                id: p1_i
                                hint_text: "جریان (A)"
                            CalcField:
                                id: p1_pf
                                hint_text: "ضریب توان"
                                text: "0.9"
                            MDRaisedButton:
                                text: "محاسبه تک‌فاز"
                                size_hint_x: 1
                                on_release: app.calc_power1()
                            MDLabel:
                                id: p1_result
                                text: ""
                                size_hint_y: None
                                height: self.texture_size[1] + dp(10)

            # ==================== MOTOR LAB ====================
            MDScreen:
                name: "motor_lab"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "ماشین‌حساب موتور سه‌فاز"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("home")]]
                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(16)
                            spacing: dp(8)
                            adaptive_height: True
                            CalcField:
                                id: mot_v
                                hint_text: "ولتاژ خط (V)"
                                text: "400"
                            CalcField:
                                id: mot_f
                                hint_text: "فرکانس (Hz)"
                                text: "50"
                            CalcField:
                                id: mot_p
                                hint_text: "توان خروجی (kW)"
                                text: "7.5"
                            CalcField:
                                id: mot_poles
                                hint_text: "تعداد قطب"
                                text: "4"
                            CalcField:
                                id: mot_pf
                                hint_text: "ضریب توان"
                                text: "0.85"
                            CalcField:
                                id: mot_eff
                                hint_text: "راندمان (0-1)"
                                text: "0.9"
                            MDRaisedButton:
                                text: "محاسبه کامل موتور"
                                size_hint_x: 1
                                on_release: app.calc_motor()
                            MDLabel:
                                id: mot_result
                                text: ""
                                size_hint_y: None
                                height: self.texture_size[1] + dp(20)
                            MDLabel:
                                text: "هشدار: نتایج تقریبی و آموزشی هستند. برای طراحی واقعی به کاتالوگ سازنده مراجعه کنید."
                                font_style: "Caption"
                                theme_text_color: "Hint"

            # ==================== VOLTAGE DROP ====================
            MDScreen:
                name: "vdrop"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "افت ولتاژ"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("tools")]]
                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(16)
                            spacing: dp(8)
                            adaptive_height: True
                            CalcField:
                                id: vd_v
                                hint_text: "ولتاژ نامی (V)"
                                text: "400"
                            CalcField:
                                id: vd_i
                                hint_text: "جریان (A)"
                            CalcField:
                                id: vd_l
                                hint_text: "طول مسیر (m)"
                            CalcField:
                                id: vd_sec
                                hint_text: "سطح مقطع (mm²)"
                            CalcField:
                                id: vd_pf
                                hint_text: "ضریب توان"
                                text: "0.85"
                            MDLabel:
                                text: "جنس هادی:"
                            MDBoxLayout:
                                adaptive_height: True
                                spacing: dp(8)
                                MDRaisedButton:
                                    text: "مس"
                                    on_release: app.set_material("مس")
                                MDRaisedButton:
                                    text: "آلومینیوم"
                                    on_release: app.set_material("آلومینیوم")
                            MDLabel:
                                id: vd_mat_label
                                text: "انتخاب‌شده: مس"
                            MDLabel:
                                text: "نوع سیستم:"
                            MDBoxLayout:
                                adaptive_height: True
                                spacing: dp(8)
                                MDRaisedButton:
                                    text: "تک‌فاز"
                                    on_release: app.set_phases(1)
                                MDRaisedButton:
                                    text: "سه‌فاز"
                                    on_release: app.set_phases(3)
                            MDLabel:
                                id: vd_ph_label
                                text: "انتخاب‌شده: سه‌فاز"
                            MDRaisedButton:
                                text: "محاسبه افت ولتاژ"
                                size_hint_x: 1
                                on_release: app.calc_vdrop()
                            MDLabel:
                                id: vd_result
                                text: ""
                                size_hint_y: None
                                height: self.texture_size[1] + dp(20)

            # ==================== CABLE CALCULATOR ====================
            MDScreen:
                name: "cable"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "انتخاب سطح مقطع کابل"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("home")]]
                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(16)
                            spacing: dp(8)
                            adaptive_height: True
                            CalcField:
                                id: cab_v
                                hint_text: "ولتاژ (V)"
                                text: "400"
                            CalcField:
                                id: cab_i
                                hint_text: "جریان بار (A)"
                            CalcField:
                                id: cab_l
                                hint_text: "طول مسیر (m)"
                            CalcField:
                                id: cab_pf
                                hint_text: "ضریب توان"
                                text: "0.85"
                            CalcField:
                                id: cab_drop
                                hint_text: "حداکثر افت ولتاژ مجاز (%)"
                                text: "3"
                            MDLabel:
                                text: "جنس هادی:"
                            MDBoxLayout:
                                adaptive_height: True
                                MDRaisedButton:
                                    text: "مس"
                                    on_release: app.set_cab_mat("مس")
                                MDRaisedButton:
                                    text: "آلومینیوم"
                                    on_release: app.set_cab_mat("آلومینیوم")
                            MDLabel:
                                id: cab_mat_label
                                text: "مس"
                            MDLabel:
                                text: "سیستم:"
                            MDBoxLayout:
                                adaptive_height: True
                                MDRaisedButton:
                                    text: "تک‌فاز"
                                    on_release: app.set_cab_ph(1)
                                MDRaisedButton:
                                    text: "سه‌فاز"
                                    on_release: app.set_cab_ph(3)
                            MDLabel:
                                id: cab_ph_label
                                text: "سه‌فاز"
                            MDRaisedButton:
                                text: "محاسبه و پیشنهاد کابل"
                                size_hint_x: 1
                                on_release: app.calc_cable()
                            MDLabel:
                                id: cab_result
                                text: ""
                                size_hint_y: None
                                height: self.texture_size[1] + dp(30)
                            MDLabel:
                                text: "هشدار مهندسی: نتیجه پیشنهاد اولیه است و باید با استاندارد و شرایط نصب واقعی بررسی شود."
                                font_style: "Caption"
                                theme_text_color: "Hint"

            # ==================== WINDING DESIGNER ====================
            MDScreen:
                name: "winding"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "طراح سیم‌پیچی موتور"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("home")]]
                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(16)
                            spacing: dp(8)
                            adaptive_height: True
                            MDLabel:
                                text: "طراحی پایه سیم‌پیچی (آموزشی)"
                                bold: True
                            CalcField:
                                id: win_slots
                                hint_text: "تعداد شیارها (Slots)"
                                text: "36"
                            CalcField:
                                id: win_poles
                                hint_text: "تعداد قطب‌ها (Poles)"
                                text: "4"
                            CalcField:
                                id: win_phases
                                hint_text: "تعداد فازها"
                                text: "3"
                            MDRaisedButton:
                                text: "محاسبه و بررسی طراحی"
                                size_hint_x: 1
                                on_release: app.calc_winding()
                            MDLabel:
                                id: win_result
                                text: ""
                                size_hint_y: None
                                height: self.texture_size[1] + dp(20)
                            MDLabel:
                                text: "اگر ترکیب پارامترها پشتیبانی نشود، پیام خطا نمایش داده می‌شود و نقشه جعلی تولید نمی‌گردد."
                                font_style: "Caption"
                                theme_text_color: "Hint"

            # ==================== SPEED / SLIP ====================
            MDScreen:
                name: "speed"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "سرعت و لغزش"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("tools")]]
                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(16)
                            spacing: dp(10)
                            adaptive_height: True
                            CalcField:
                                id: sp_f
                                hint_text: "فرکانس (Hz)"
                                text: "50"
                            CalcField:
                                id: sp_poles
                                hint_text: "تعداد قطب"
                                text: "4"
                            MDRaisedButton:
                                text: "محاسبه سرعت سنکرون"
                                size_hint_x: 1
                                on_release: app.calc_sync()
                            MDLabel:
                                id: sp_ns_result
                                text: ""
                            CalcField:
                                id: sp_ns
                                hint_text: "سرعت سنکرون (rpm)"
                            CalcField:
                                id: sp_nr
                                hint_text: "سرعت روتور (rpm)"
                            MDRaisedButton:
                                text: "محاسبه لغزش"
                                size_hint_x: 1
                                on_release: app.calc_slip()
                            MDLabel:
                                id: sp_slip_result
                                text: ""

            # ==================== QUIZ ====================
            MDScreen:
                name: "quiz"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "تمرین و آزمون"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("home")]]
                    MDBoxLayout:
                        orientation: "vertical"
                        padding: dp(16)
                        spacing: dp(12)
                        MDLabel:
                            id: quiz_question
                            text: ""
                            size_hint_y: None
                            height: self.texture_size[1] + dp(10)
                            bold: True
                        MDBoxLayout:
                            id: quiz_options
                            orientation: "vertical"
                            adaptive_height: True
                            spacing: dp(8)
                        MDLabel:
                            id: quiz_feedback
                            text: ""
                            size_hint_y: None
                            height: self.texture_size[1] + dp(10)
                        MDRaisedButton:
                            text: "سوال بعدی"
                            size_hint_x: 1
                            on_release: app.next_question()

            # ==================== CIRCUIT LAB (Basic) ====================
            MDScreen:
                name: "circuit"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "مدار فرمان (پایه)"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("home")]]
                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(16)
                            spacing: dp(12)
                            adaptive_height: True
                            MDLabel:
                                text: "مدارهای رایج فرمان"
                                bold: True
                                font_style: "H6"
                            MDCard:
                                orientation: "vertical"
                                padding: dp(12)
                                size_hint_y: None
                                height: dp(140)
                                radius: [10]
                                MDLabel:
                                    text: "Start / Stop با Self-Holding"
                                    bold: True
                                MDLabel:
                                    text: "شستی Start → کنتاکتور فعال → کنتاکت کمکی موازی Start مدار را نگه می‌دارد. شستی Stop مدار را قطع می‌کند."
                                    font_style: "Caption"
                            MDCard:
                                orientation: "vertical"
                                padding: dp(12)
                                size_hint_y: None
                                height: dp(140)
                                radius: [10]
                                MDLabel:
                                    text: "Forward / Reverse"
                                    bold: True
                                MDLabel:
                                    text: "دو کنتاکتور با اینترلاک مکانیکی و الکتریکی. هرگز هر دو نباید همزمان فعال شوند."
                                    font_style: "Caption"
                            MDCard:
                                orientation: "vertical"
                                padding: dp(12)
                                size_hint_y: None
                                height: dp(160)
                                radius: [10]
                                MDLabel:
                                    text: "Star-Delta"
                                    bold: True
                                MDLabel:
                                    text: "راه‌اندازی با اتصال ستاره (جریان کمتر) سپس بعد از تأخیر زمانی به مثلث تغییر می‌کند. از تایمر استفاده می‌شود."
                                    font_style: "Caption"
                            MDLabel:
                                text: "نسخه شبیه‌ساز تعاملی کامل در به‌روزرسانی‌های بعدی اضافه خواهد شد. منطق پایه در موتور محاسباتی آماده است."
                                font_style: "Caption"
                                theme_text_color: "Hint"

            # ==================== ABOUT / PROFILE ====================
            MDScreen:
                name: "about"
                MDBoxLayout:
                    orientation: "vertical"
                    MDTopAppBar:
                        title: "درباره برنامه"
                        elevation: 2
                        left_action_items: [["arrow-left", lambda x: app.change_screen("home")]]
                    MDScrollView:
                        MDBoxLayout:
                            orientation: "vertical"
                            padding: dp(20)
                            spacing: dp(12)
                            adaptive_height: True
                            MDLabel:
                                text: "Electrical Industrial Lab"
                                font_style: "H4"
                                bold: True
                                halign: "center"
                            MDLabel:
                                text: "نسخه MVP 1.0"
                                halign: "center"
                                theme_text_color: "Secondary"
                            MDLabel:
                                text: "یک نرم‌افزار آموزشی، محاسباتی و آزمایشگاهی کاملاً آفلاین برای برق صنعتی.\\n\\nطراحی شده برای دانش‌آموز، هنرجو، تکنسین و دانشجوی برق.\\n\\nتمام محاسبات داخل برنامه انجام می‌شود و نیازی به اینترنت ندارد."
                                halign: "center"
                            MDLabel:
                                text: "هشدار مهم"
                                bold: True
                                theme_text_color: "Error"
                            MDLabel:
                                text: "نتایج این برنامه جنبه آموزشی دارد. برای انتخاب تجهیزات واقعی صنعتی حتماً به استانداردها، دیتاشیت سازنده و مقررات محلی مراجعه کنید."

        MDNavigationDrawer:
            id: nav_drawer
            radius: (0, 16, 16, 0)
            MDBoxLayout:
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(8)
                MDLabel:
                    text: "منو"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(40)
                OneLineIconListItem:
                    text: "خانه"
                    on_release: app.change_screen("home"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "home"
                OneLineIconListItem:
                    text: "آموزش"
                    on_release: app.change_screen("education"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "book-open-variant"
                OneLineIconListItem:
                    text: "فرمول‌نامه"
                    on_release: app.change_screen("formulas"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "function"
                OneLineIconListItem:
                    text: "ابزارها"
                    on_release: app.change_screen("tools"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "calculator"
                OneLineIconListItem:
                    text: "موتور لب"
                    on_release: app.change_screen("motor_lab"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "engine"
                OneLineIconListItem:
                    text: "سیم‌پیچی"
                    on_release: app.change_screen("winding"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "sine-wave"
                OneLineIconListItem:
                    text: "کابل و افت ولتاژ"
                    on_release: app.change_screen("cable"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "cable-data"
                OneLineIconListItem:
                    text: "تمرین"
                    on_release: app.change_screen("quiz"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "help-circle"
                OneLineIconListItem:
                    text: "مدار فرمان"
                    on_release: app.change_screen("circuit"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "electric-switch"
                OneLineIconListItem:
                    text: "درباره"
                    on_release: app.change_screen("about"); nav_drawer.set_state("close")
                    IconLeftWidget:
                        icon: "information"
"""

# ============================================================
# MAIN APP
# ============================================================

class ElectricalIndustrialLabApp(MDApp):
    material = StringProperty("مس")
    phases = NumericProperty(3)
    cab_material = StringProperty("مس")
    cab_phases = NumericProperty(3)
    current_q_index = NumericProperty(0)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.font_styles.update({
            "H1": [DEFAULT_FONT, 96, False, -1.5],
            "H2": [DEFAULT_FONT, 60, False, -0.5],
            "H3": [DEFAULT_FONT, 48, False, 0],
            "H4": [DEFAULT_FONT, 34, False, 0.25],
            "H5": [DEFAULT_FONT, 24, False, 0],
            "H6": [DEFAULT_FONT, 20, False, 0.15],
            "Subtitle1": [DEFAULT_FONT, 16, False, 0.15],
            "Subtitle2": [DEFAULT_FONT, 14, False, 0.1],
            "Body1": [DEFAULT_FONT, 16, False, 0.5],
            "Body2": [DEFAULT_FONT, 14, False, 0.25],
            "Button": [DEFAULT_FONT, 14, True, 1.25],
            "Caption": [DEFAULT_FONT, 12, False, 0.4],
            "Overline": [DEFAULT_FONT, 10, True, 1.5],
        })
        self.title = "Electrical Industrial Lab"
        return Builder.load_string(KV)

    def on_start(self):
        self.populate_education()
        self.populate_formulas()
        self.next_question()

    def change_screen(self, name):
        self.root.ids.screen_manager.current = name

    def show_about(self):
        self.change_screen("about")

    # ---------- Population ----------
    def populate_education(self):
        container = self.root.ids.education_list
        container.clear_widgets()
        for level, lessons in LESSONS.items():
            container.add_widget(MDLabel(
                text=f"سطح {level}",
                font_style="H6",
                bold=True,
                size_hint_y=None,
                height=dp(40),
                theme_text_color="Primary"
            ))
            for les in lessons:
                card = MDCard(
                    orientation="vertical",
                    padding=dp(12),
                    spacing=dp(6),
                    size_hint_y=None,
                    height=dp(160),
                    radius=[12],
                    ripple_behavior=True,
                    on_release=lambda x, l=les: self.show_lesson(l)
                )
                card.add_widget(MDLabel(text=les["title"], bold=True, font_style="Subtitle1"))
                card.add_widget(MDLabel(
                    text=les["content"][:120] + "...",
                    font_style="Caption",
                    theme_text_color="Secondary"
                ))
                container.add_widget(card)

    def show_lesson(self, lesson):
        content = f"{lesson['content']}\n\n"
        content += "فرمول‌ها:\n" + "\n".join(lesson.get("formulas", [])) + "\n\n"
        content += "نکات مهم:\n• " + "\n• ".join(lesson.get("tips", [])) + "\n\n"
        content += "خطاهای رایج:\n• " + "\n• ".join(lesson.get("mistakes", []))
        dialog = MDDialog(
            title=lesson["title"],
            text=content,
            size_hint=(0.95, None),
            buttons=[MDFlatButton(text="بستن", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

    def populate_formulas(self):
        container = self.root.ids.formulas_list
        container.clear_widgets()
        for cat, items in FORMULAS.items():
            container.add_widget(MDLabel(
                text=cat,
                font_style="H6",
                bold=True,
                size_hint_y=None,
                height=dp(36)
            ))
            for f in items:
                card = MDCard(
                    orientation="vertical",
                    padding=dp(12),
                    size_hint_y=None,
                    height=dp(130),
                    radius=[10]
                )
                card.add_widget(MDLabel(text=f["name"], bold=True))
                card.add_widget(MDLabel(text=f["formula"], theme_text_color="Custom",
                                        text_color=(0.3, 0.8, 1, 1), font_style="H6"))
                card.add_widget(MDLabel(text=f["example"], font_style="Caption",
                                        theme_text_color="Secondary"))
                container.add_widget(card)

    # ---------- Calculators ----------
    def _get_float(self, field_id, default=None):
        try:
            txt = self.root.ids[field_id].text.strip()
            if not txt:
                return default
            return float(txt.replace(",", "."))
        except:
            return None

    def calc_ohm(self):
        v = self._get_float("ohm_v")
        i = self._get_float("ohm_i")
        r = self._get_float("ohm_r")
        res = CalcEngine.ohm_law(v, i, r)
        if "error" in res:
            self.root.ids.ohm_result.text = f"خطا: {res['error']}"
        else:
            key = list(res.keys())[0]
            if key == "error":
                self.root.ids.ohm_result.text = res["error"]
            else:
                self.root.ids.ohm_result.text = f"نتیجه: {key} = {res[key]:.4g} {res.get('unit', '')}"

    def calc_power3(self):
        v = self._get_float("p3_v")
        i = self._get_float("p3_i")
        pf = self._get_float("p3_pf")
        if None in (v, i, pf):
            self.root.ids.p3_result.text = "لطفاً همه مقادیر را وارد کنید"
            return
        res = CalcEngine.power_3ph(v, i, pf)
        if "error" in res:
            self.root.ids.p3_result.text = res["error"]
        else:
            self.root.ids.p3_result.text = (
                f"توان اکتیو P = {res['P']:.1f} W ({res['P']/1000:.2f} kW)\n"
                f"توان ظاهری S = {res['S']:.1f} VA\n"
                f"توان راکتیو Q = {res['Q']:.1f} VAR"
            )

    def calc_power1(self):
        v = self._get_float("p1_v")
        i = self._get_float("p1_i")
        pf = self._get_float("p1_pf")
        if None in (v, i, pf):
            self.root.ids.p1_result.text = "لطفاً همه مقادیر را وارد کنید"
            return
        res = CalcEngine.power_1ph(v, i, pf)
        if "error" in res:
            self.root.ids.p1_result.text = res["error"]
        else:
            self.root.ids.p1_result.text = (
                f"P = {res['P']:.1f} W\nS = {res['S']:.1f} VA\nQ = {res['Q']:.1f} VAR"
            )

    def calc_motor(self):
        v = self._get_float("mot_v")
        f = self._get_float("mot_f")
        p = self._get_float("mot_p")
        poles = self._get_float("mot_poles")
        pf = self._get_float("mot_pf")
        eff = self._get_float("mot_eff")
        res = CalcEngine.motor_full(v, f, p, int(poles) if poles else None, pf, eff)
        if "error" in res:
            self.root.ids.mot_result.text = res["error"]
        else:
            self.root.ids.mot_result.text = (
                f"جریان تقریبی: {res['I']} A\n"
                f"سرعت سنکرون: {res['Ns']} rpm\n"
                f"سرعت تقریبی (لغزش ۳٪): {res['Nr_approx']} rpm\n"
                f"توان ورودی: {res['P_in']} W\n"
                f"توان خروجی: {res['P_out']} W\n"
                f"توان ظاهری: {res['S']} VA\n"
                f"توان راکتیو: {res['Q']} VAR\n"
                f"گشتاور تقریبی: {res['T']} N.m\n\n"
                f"{res['note']}"
            )

    def set_material(self, mat):
        self.material = mat
        self.root.ids.vd_mat_label.text = f"انتخاب‌شده: {mat}"

    def set_phases(self, ph):
        self.phases = ph
        self.root.ids.vd_ph_label.text = f"انتخاب‌شده: {'تک‌فاز' if ph == 1 else 'سه‌فاز'}"

    def calc_vdrop(self):
        v = self._get_float("vd_v")
        i = self._get_float("vd_i")
        length = self._get_float("vd_l")
        sec = self._get_float("vd_sec")
        pf = self._get_float("vd_pf", 0.85)
        if None in (v, i, length, sec):
            self.root.ids.vd_result.text = "لطفاً همه مقادیر را وارد کنید"
            return
        res = CalcEngine.voltage_drop(v, i, length, sec, self.material, self.phases, pf)
        if "error" in res:
            self.root.ids.vd_result.text = res["error"]
        else:
            self.root.ids.vd_result.text = (
                f"افت ولتاژ: {res['dV']} V\n"
                f"درصد افت: {res['dV_percent']} %\n"
                f"ولتاژ انتها: {res['V_end']} V\n"
                f"توان تلف‌شده تقریبی: {res['P_loss']} W\n"
                f"وضعیت: {res['status']}\n\n"
                f"{res['note']}"
            )

    def set_cab_mat(self, mat):
        self.cab_material = mat
        self.root.ids.cab_mat_label.text = mat

    def set_cab_ph(self, ph):
        self.cab_phases = ph
        self.root.ids.cab_ph_label.text = "تک‌فاز" if ph == 1 else "سه‌فاز"

    def calc_cable(self):
        v = self._get_float("cab_v")
        i = self._get_float("cab_i")
        length = self._get_float("cab_l")
        pf = self._get_float("cab_pf", 0.85)
        max_drop = self._get_float("cab_drop", 3.0)
        if None in (v, i, length):
            self.root.ids.cab_result.text = "لطفاً ولتاژ، جریان و طول را وارد کنید"
            return
        res = CalcEngine.cable_select(v, i, length, self.cab_material, self.cab_phases, pf, max_drop)
        if "error" in res:
            self.root.ids.cab_result.text = res["error"]
            return
        text = ""
        if res["recommendation"]:
            text += f"پیشنهاد سطح مقطع: {res['recommendation']} mm²\n\n"
        else:
            text += "هیچ سطح مقطعی با شرایط داده‌شده پیدا نشد (جریان یا افت ولتاژ خیلی بالا).\n\n"
        text += "جزئیات:\n"
        for r in res["results"][:8]:  # show first few
            status = "✓" if r["overall_ok"] else "✗"
            text += f"{status} {r['section']} mm² | ظرفیت≈{r['capacity']}A | افت={r['dV_percent']}%\n"
        text += f"\n{res['warning']}"
        self.root.ids.cab_result.text = text

    def calc_winding(self):
        slots = self._get_float("win_slots")
        poles = self._get_float("win_poles")
        phases = self._get_float("win_phases", 3)
        if None in (slots, poles):
            self.root.ids.win_result.text = "تعداد شیار و قطب را وارد کنید"
            return
        res = CalcEngine.winding_basic(slots, poles, phases)
        if "error" in res:
            self.root.ids.win_result.text = f"خطا: {res['error']}"
        else:
            text = (
                f"تعداد شیار: {res['slots']}\n"
                f"تعداد قطب: {res['poles']}\n"
                f"فاز: {res['phases']}\n"
                f"Slots per Pole per Phase (SPP): {res['spp']}\n"
                f"Pole Pitch: {res['pole_pitch']}\n"
                f"Coil Pitch (فرض کامل): {res['coil_pitch']}\n\n"
                f"نمونه توزیع شیارها (۱۰ تای اول):\n"
            )
            for s in res["slot_map"][:10]:
                text += f"  شیار {s['slot']}: فاز {s['phase']} ({s['direction']})\n"
            text += f"\n{res['note']}"
            self.root.ids.win_result.text = text

    def calc_sync(self):
        f = self._get_float("sp_f")
        poles = self._get_float("sp_poles")
        if None in (f, poles):
            self.root.ids.sp_ns_result.text = "مقادیر را وارد کنید"
            return
        res = CalcEngine.sync_speed(f, int(poles))
        if "error" in res:
            self.root.ids.sp_ns_result.text = res["error"]
        else:
            self.root.ids.sp_ns_result.text = f"سرعت سنکرون Ns = {res['Ns']:.1f} rpm"
            self.root.ids.sp_ns.text = str(round(res["Ns"], 1))

    def calc_slip(self):
        ns = self._get_float("sp_ns")
        nr = self._get_float("sp_nr")
        if None in (ns, nr):
            self.root.ids.sp_slip_result.text = "مقادیر را وارد کنید"
            return
        res = CalcEngine.slip(ns, nr)
        if "error" in res:
            self.root.ids.sp_slip_result.text = res["error"]
        else:
            self.root.ids.sp_slip_result.text = f"لغزش = {res['s']:.4f} ({res['s_percent']:.2f} %)"

    # ---------- Quiz ----------
    def next_question(self):
        if not QUESTIONS:
            return
        self.current_q_index = (self.current_q_index + 1) % len(QUESTIONS)
        q = QUESTIONS[self.current_q_index]
        self.root.ids.quiz_question.text = f"[{q['level']}] {q['question']}"
        self.root.ids.quiz_feedback.text = ""
        opts = self.root.ids.quiz_options
        opts.clear_widgets()
        for idx, opt in enumerate(q["options"]):
            btn = MDRaisedButton(
                text=opt,
                size_hint_x=1,
                on_release=lambda x, i=idx, qq=q: self.check_answer(i, qq)
            )
            opts.add_widget(btn)

    def check_answer(self, selected, q):
        if selected == q["answer"]:
            feedback = f"درست ✓\n\nتوضیح: {q['explanation']}\nفرمول: {q['formula']}"
        else:
            correct = q["options"][q["answer"]]
            feedback = f"غلط ✗\nپاسخ صحیح: {correct}\n\nتوضیح: {q['explanation']}\nفرمول: {q['formula']}"
        self.root.ids.quiz_feedback.text = feedback


# ============================================================
# UNIT TESTS (simple self-check)
# ============================================================
def run_self_tests():
    print("Running calculation self-tests...")
    assert abs(CalcEngine.ohm_law(i=2, r=10)["V"] - 20) < 1e-6
    assert abs(CalcEngine.power_3ph(400, 10, 0.8)["P"] - (math.sqrt(3)*400*10*0.8)) < 1e-6
    assert abs(CalcEngine.sync_speed(50, 4)["Ns"] - 1500) < 1e-6
    assert abs(CalcEngine.slip(1500, 1455)["s_percent"] - 3.0) < 1e-6
    print("All basic tests passed.")


if __name__ == "__main__":
    run_self_tests()
    ElectricalIndustrialLabApp().run()
