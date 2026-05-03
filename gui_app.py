"""
AIE212 — Medical Diagnosis Expert System
gui_app.py

Sleek-themed graphical user interface built with customtkinter.

Entry point:
    python gui_app.py

Design system: Sleek (modern minimalist, 8-pt baseline grid, Inter font,
                       60-30-10 color rule, WCAG 2.2 AA contrast)
"""

import os
import customtkinter as ctk
from tkinter import messagebox
from typing import Optional

from core.inference_engine import InferenceEngine
from interface.action_library import ActionLibrary
from core.explanation_module import ExplanationModule
from utils.data_persistence import DataPersistence
from interface.intake_form import IntakeForm

# ─── Appearance ───────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ─── Sleek Design Tokens ──────────────────────────────────────────────────────
PRIMARY    = "#3B82F6"
SECONDARY  = "#8B5CF6"
SUCCESS    = "#16A34A"
WARNING    = "#D97706"
DANGER     = "#DC2626"
SURFACE    = "#FFFFFF"
TEXT       = "#111827"
TEXT_MUTED = "#6B7280"
BORDER     = "#E5E7EB"
BG         = "#F9FAFB"
SIDEBAR_BG = "#1D3461"

URGENCY_COLORS = {
    "IMMEDIATE":   DANGER,
    "URGENT":      WARNING,
    "SEMI_URGENT": PRIMARY,
    "NON_URGENT":  SUCCESS,
}

FONT = "Inter"   # customtkinter passes this to Tkinter; Tkinter substitutes a
                 # system font if Inter is unavailable (OS-dependent behaviour)

# 8-pt spacing scale
P1, P2, P3, P4, P5, P6, P7 = 4, 8, 12, 16, 24, 32, 48

# ─── Vitals reference ranges ─────────────────────────────────────────────────
# Each entry: list of (lo_inclusive, hi_exclusive, status_label, color)
# The last range's upper bound is treated as inclusive (handles boundary values).
VITAL_STATUS: dict = {
    "Temperature (°C)": [
        (35.0, 36.1, "Low",      WARNING),
        (36.1, 37.5, "Normal",   SUCCESS),
        (37.5, 38.0, "Elevated", WARNING),
        (38.0, 42.0, "Fever",    DANGER),
    ],
    "Heart Rate (bpm)": [
        (30,  60,  "Low",      WARNING),
        (60,  100, "Normal",   SUCCESS),
        (100, 120, "Elevated", WARNING),
        (120, 250, "High",     DANGER),
    ],
    "Systolic BP (mmHg)": [
        (60,  90,  "Low",      WARNING),
        (90,  140, "Normal",   SUCCESS),
        (140, 180, "Elevated", WARNING),
        (180, 260, "High",     DANGER),
    ],
    "Diastolic BP (mmHg)": [
        (40, 60,  "Low",      WARNING),
        (60, 90,  "Normal",   SUCCESS),
        (90, 100, "Elevated", WARNING),
        (100, 160, "High",    DANGER),
    ],
    "SpO₂ (%)": [
        (50, 90,  "Critical", DANGER),
        (90, 94,  "Low",      WARNING),
        (94, 100, "Normal",   SUCCESS),
    ],
    "Resp. Rate (br/min)": [
        (5,  12, "Low",      WARNING),
        (12, 20, "Normal",   SUCCESS),
        (20, 30, "Elevated", WARNING),
        (30, 60, "High",     DANGER),
    ],
}


def _vital_status(label: str, value: float) -> tuple:
    """
    Return (status_text, color) for a vital reading.

    Iterates the VITAL_STATUS ranges for *label* and returns the matching
    bucket.  Inner ranges use a half-open interval [lo, hi) so that shared
    boundary values (e.g. 38.0°C) fall into the higher bucket.  The final
    range uses a closed interval [lo, hi] so that the maximum legal value
    (e.g. SpO2 = 100) is always matched.
    """
    ranges = VITAL_STATUS.get(label, [])
    for i, (lo, hi, text, color) in enumerate(ranges):
        is_last = (i == len(ranges) - 1)
        if lo <= value <= hi if is_last else lo <= value < hi:
            return text, color
    return "", TEXT_MUTED


# ─── Font helper ──────────────────────────────────────────────────────────────
def _f(size: int = 14, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT, size=size, weight=weight)


# ─── Base widget factory helpers ──────────────────────────────────────────────
def _card(master, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(
        master, fg_color=SURFACE, corner_radius=12,
        border_width=1, border_color=BORDER, **kw,
    )


def _divider(master) -> ctk.CTkFrame:
    return ctk.CTkFrame(master, height=1, fg_color=BORDER)


def _label(master, text: str, size=14, weight="normal",
           color: str = TEXT, **kw) -> ctk.CTkLabel:
    return ctk.CTkLabel(
        master, text=text, font=_f(size, weight),
        text_color=color, **kw,
    )


def _caption(master, text: str, **kw) -> ctk.CTkLabel:
    return _label(master, text.upper(), size=11, weight="bold",
                  color=TEXT_MUTED, **kw)


def _heading(master, text: str, size=16, **kw) -> ctk.CTkLabel:
    return _label(master, text, size=size, weight="bold", **kw)


def _entry(master, placeholder="", default="", **kw) -> ctk.CTkEntry:
    e = ctk.CTkEntry(
        master,
        placeholder_text=placeholder,
        fg_color=SURFACE,
        border_color=BORDER,
        border_width=1,
        text_color=TEXT,
        placeholder_text_color=TEXT_MUTED,
        font=_f(14),
        corner_radius=8,
        height=40,
        **kw,
    )
    if default:
        e.insert(0, str(default))
    return e


def _combo(master, values: list, default: str = "", **kw) -> ctk.CTkComboBox:
    c = ctk.CTkComboBox(
        master,
        values=values,
        fg_color=SURFACE,
        border_color=BORDER,
        border_width=1,
        text_color=TEXT,
        button_color=BORDER,
        button_hover_color=PRIMARY,
        dropdown_fg_color=SURFACE,
        dropdown_text_color=TEXT,
        dropdown_hover_color=BG,
        font=_f(14),
        corner_radius=8,
        height=40,
        state="readonly",
        **kw,
    )
    if default:
        c.set(default)
    return c


def _btn(master, text: str, cmd=None, variant="primary", **kw) -> ctk.CTkButton:
    colors = {
        "primary":   (PRIMARY,   "#2563EB"),
        "secondary": (SECONDARY, "#7C3AED"),
        "danger":    (DANGER,    "#B91C1C"),
        "success":   (SUCCESS,   "#15803D"),
        "ghost":     (BG,        BORDER),
    }
    fg, hover = colors.get(variant, colors["primary"])
    txt = TEXT if variant == "ghost" else "#FFFFFF"
    height = kw.pop("height", 40)
    return ctk.CTkButton(
        master, text=text, command=cmd,
        fg_color=fg, hover_color=hover, text_color=txt,
        font=_f(14, "bold"), corner_radius=8, height=height,
        **kw,
    )


def _segmented(master, values: list, variable: ctk.StringVar) -> ctk.CTkSegmentedButton:
    return ctk.CTkSegmentedButton(
        master, values=values, variable=variable,
        fg_color=BG,
        selected_color=PRIMARY, selected_hover_color="#2563EB",
        unselected_color=BG, unselected_hover_color=BORDER,
        text_color=TEXT,
        font=_f(14),
    )


def _section_header(card: ctk.CTkFrame, title: str,
                    accent: str = PRIMARY) -> ctk.CTkFrame:
    """Render a section header inside a card and return the body frame."""
    hdr = ctk.CTkFrame(card, fg_color="transparent")
    hdr.pack(fill="x", padx=P5, pady=(P5, P2))
    ctk.CTkFrame(hdr, width=3, height=20, fg_color=accent,
                 corner_radius=2).pack(side="left")
    _heading(hdr, f"  {title}", size=15).pack(side="left")
    _divider(card).pack(fill="x", padx=P5, pady=(0, P4))
    body = ctk.CTkFrame(card, fg_color="transparent")
    body.pack(fill="x", padx=P5, pady=(0, P5))
    return body


# ═══════════════════════════════════════════════════════════════════════════════
# FORM SECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class DemographicsSection(ctk.CTkFrame):
    """[1] Patient name, age, and sex."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        body = _section_header(self, "Patient Demographics")
        body.columnconfigure((0, 1, 2), weight=1)

        # Full Name
        name_f = ctk.CTkFrame(body, fg_color="transparent")
        name_f.grid(row=0, column=0, columnspan=2, sticky="ew",
                    padx=(0, P4), pady=(0, P4))
        _caption(name_f, "Full Name").pack(anchor="w", pady=(0, P1))
        self._name = _entry(name_f, placeholder="e.g. John Smith")
        self._name.pack(fill="x")

        # Age
        age_f = ctk.CTkFrame(body, fg_color="transparent")
        age_f.grid(row=0, column=2, sticky="ew", pady=(0, P4))
        _caption(age_f, "Age (years)").pack(anchor="w", pady=(0, P1))
        self._age = _entry(age_f, placeholder="18–80", default="40")
        self._age.pack(fill="x")

        # Sex
        sex_f = ctk.CTkFrame(body, fg_color="transparent")
        sex_f.grid(row=1, column=0, columnspan=3, sticky="ew")
        _caption(sex_f, "Biological Sex").pack(anchor="w", pady=(0, P1))
        self._sex = ctk.StringVar(value="male")
        _segmented(sex_f, ["male", "female"], self._sex).pack(fill="x")

    def get(self) -> dict:
        try:
            age = max(18, min(80, int(float(self._age.get().strip() or "40"))))
        except ValueError:
            age = 40
        return {
            "name": self._name.get().strip(),
            "age":  age,
            "sex":  self._sex.get(),
        }


class HistorySection(ctk.CTkFrame):
    """[2] Known conditions, smoking, alcohol."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        body = _section_header(self, "Medical History", accent=SECONDARY)

        _caption(body, "Known Conditions").pack(anchor="w", pady=(0, P2))

        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x", pady=(0, P4))

        self._cond_vars: dict[str, ctk.BooleanVar] = {}
        cols = 4
        for i, cond in enumerate(IntakeForm.CONDITION_OPTIONS):
            r, c = divmod(i, cols)
            var = ctk.BooleanVar(value=False)
            self._cond_vars[cond] = var
            ctk.CTkCheckBox(
                grid,
                text=cond.replace("_", " ").title(),
                variable=var,
                fg_color=SECONDARY,
                hover_color="#7C3AED",
                text_color=TEXT,
                font=_f(13),
                border_color=BORDER,
            ).grid(row=r, column=c, sticky="w", padx=P2, pady=P1)

        _divider(body).pack(fill="x", pady=(0, P3))
        _caption(body, "Lifestyle").pack(anchor="w", pady=(0, P2))

        sw_row = ctk.CTkFrame(body, fg_color="transparent")
        sw_row.pack(fill="x")

        self._smoking = ctk.BooleanVar(value=False)
        self._alcohol = ctk.BooleanVar(value=False)

        for text, var in [("Current smoker", self._smoking),
                           ("Regular alcohol use", self._alcohol)]:
            ctk.CTkSwitch(
                sw_row, text=text, variable=var,
                progress_color=SECONDARY, button_color=SURFACE,
                text_color=TEXT, font=_f(14),
            ).pack(side="left", padx=(0, P6))

    def get(self) -> dict:
        return {
            "known_conditions": [c for c, v in self._cond_vars.items() if v.get()],
            "smoking":          self._smoking.get(),
            "alcohol":          self._alcohol.get(),
        }


class VitalsSection(ctk.CTkFrame):
    """[3] Temperature, HR, BP, SpO2, RR, consciousness."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        body = _section_header(self, "Vital Signs", accent=WARNING)
        body.columnconfigure((0, 1, 2), weight=1)

        specs = [
            ("Temperature (°C)", "37.0", "35.0–42.0", 0, 0),
            ("Heart Rate (bpm)", "75",   "30–250",     0, 1),
            ("Systolic BP (mmHg)", "120", "60–260",    0, 2),
            ("Diastolic BP (mmHg)", "80", "40–160",    1, 0),
            ("SpO₂ (%)", "98",       "50–100",         1, 1),
            ("Resp. Rate (br/min)", "16", "5–60",      1, 2),
        ]
        self._entries:    dict[str, ctk.CTkEntry] = {}
        self._indicators: dict[str, ctk.CTkLabel] = {}

        for label, default, placeholder, row, col in specs:
            f = ctk.CTkFrame(body, fg_color="transparent")
            f.grid(row=row, column=col, sticky="ew",
                   padx=(0, P4) if col < 2 else (0, 0), pady=(0, P4))

            # Header row: caption on the left, live status badge on the right
            cap_row = ctk.CTkFrame(f, fg_color="transparent")
            cap_row.pack(fill="x", pady=(0, P1))
            _caption(cap_row, label).pack(side="left")
            ind = ctk.CTkLabel(cap_row, text="", font=_f(11, "bold"),
                               text_color=SUCCESS)
            ind.pack(side="right")
            self._indicators[label] = ind

            e = _entry(f, placeholder=placeholder, default=default)
            e.pack(fill="x")
            e.bind("<KeyRelease>", lambda evt, l=label: self._update_indicator(l))
            e.bind("<FocusOut>",   lambda evt, l=label: self._update_indicator(l))
            self._entries[label] = e

        cons_f = ctk.CTkFrame(body, fg_color="transparent")
        cons_f.grid(row=2, column=0, columnspan=3, sticky="ew")
        _caption(cons_f, "Level of Consciousness").pack(anchor="w", pady=(0, P1))
        self._consciousness = ctk.StringVar(value="alert")
        _segmented(cons_f, ["alert", "confused", "unresponsive"],
                   self._consciousness).pack(fill="x")

        # Seed indicators from default values after the widget tree is ready
        self.after(50, self._update_all_indicators)

    # ── Status indicator helpers ───────────────────────────────────────────────

    def _update_indicator(self, label: str) -> None:
        """Refresh the status badge for one vital field."""
        ind = self._indicators.get(label)
        if ind is None:
            return
        raw = self._entries[label].get().strip()
        try:
            val = float(raw)
        except ValueError:
            ind.configure(text="", text_color=TEXT_MUTED)
            return
        text, color = _vital_status(label, val)
        ind.configure(text=text, text_color=color)

    def _update_all_indicators(self) -> None:
        """Refresh status badges for all vital fields (used on initialisation)."""
        for label in self._entries:
            self._update_indicator(label)

    def _parse(self, label, default, lo, hi, as_int=False):
        raw = self._entries[label].get().strip()
        try:
            v = float(raw) if raw else default
            v = max(lo, min(hi, v))
            return int(round(v)) if as_int else v
        except ValueError:
            return default

    def get(self) -> dict:
        return {
            "temperature":   self._parse("Temperature (°C)", 37.0, 35.0, 42.0),
            "heart_rate":    self._parse("Heart Rate (bpm)", 75, 30, 250, as_int=True),
            "systolic_bp":   self._parse("Systolic BP (mmHg)", 120, 60, 260, as_int=True),
            "diastolic_bp":  self._parse("Diastolic BP (mmHg)", 80, 40, 160, as_int=True),
            "spo2":          self._parse("SpO₂ (%)", 98, 50, 100, as_int=True),
            "resp_rate":     self._parse("Resp. Rate (br/min)", 16, 5, 60, as_int=True),
            "consciousness": self._consciousness.get(),
        }


class SymptomDetailRow(ctk.CTkFrame):
    """Compact detail controls for one symptom (shown when checkbox ticked)."""

    def __init__(self, master, symptom_name: str, **kw):
        super().__init__(master, fg_color=BG, corner_radius=8, **kw)
        self.symptom_name = symptom_name

        # Accent bar
        ctk.CTkFrame(self, width=3, fg_color=PRIMARY,
                     corner_radius=2).pack(side="left", fill="y", padx=(P2, P3))

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(side="left", fill="x", expand=True, pady=P3)

        _label(inner, symptom_name.replace("_", " ").title(),
               size=13, weight="bold").pack(anchor="w", pady=(0, P2))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")
        row.columnconfigure((0, 1, 2, 3), weight=1)

        # Severity slider
        sev_f = ctk.CTkFrame(row, fg_color="transparent")
        sev_f.grid(row=0, column=0, sticky="ew", padx=(0, P3))
        _caption(sev_f, "Severity (1–10)").pack(anchor="w", pady=(0, P1))
        slider_row = ctk.CTkFrame(sev_f, fg_color="transparent")
        slider_row.pack(fill="x")
        self._sev_var = ctk.IntVar(value=5)
        sev_label = _label(slider_row, "5", size=13, weight="bold", color=PRIMARY)
        sev_label.pack(side="right", padx=(P1, 0))

        def on_sev(v):
            iv = int(round(float(v)))
            self._sev_var.set(iv)
            sev_label.configure(text=str(iv))

        ctk.CTkSlider(
            slider_row, from_=1, to=10, command=on_sev,
            progress_color=PRIMARY, button_color=PRIMARY,
            button_hover_color="#2563EB",
        ).pack(side="left", fill="x", expand=True)

        # Duration
        dur_f = ctk.CTkFrame(row, fg_color="transparent")
        dur_f.grid(row=0, column=1, sticky="ew", padx=(0, P3))
        _caption(dur_f, "Duration (days)").pack(anchor="w", pady=(0, P1))
        self._duration = _entry(dur_f, placeholder="0–365", default="1")
        self._duration.pack(fill="x")

        # Onset
        ons_f = ctk.CTkFrame(row, fg_color="transparent")
        ons_f.grid(row=0, column=2, sticky="ew", padx=(0, P3))
        _caption(ons_f, "Onset").pack(anchor="w", pady=(0, P1))
        self._onset = ctk.StringVar(value="gradual")
        _segmented(ons_f, ["sudden", "gradual"], self._onset).pack(fill="x")

        # Progression
        prog_f = ctk.CTkFrame(row, fg_color="transparent")
        prog_f.grid(row=0, column=3, sticky="ew")
        _caption(prog_f, "Progression").pack(anchor="w", pady=(0, P1))
        self._progression = _combo(prog_f,
                                   ["improving", "stable", "worsening"],
                                   default="stable")
        self._progression.pack(fill="x")

    def get(self) -> dict:
        try:
            dur = max(0.0, min(365.0, float(self._duration.get().strip() or "1")))
        except ValueError:
            dur = 1.0
        return {
            "name":          self.symptom_name,
            "severity":      self._sev_var.get(),
            "duration_days": dur,
            "onset":         self._onset.get(),
            "progression":   self._progression.get(),
        }


class SymptomsSection(ctk.CTkFrame):
    """[4] Symptom multi-select + per-symptom detail rows."""

    def __init__(self, master, on_pain_change=None, **kw):
        super().__init__(master, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        self._on_pain_change = on_pain_change
        self._detail_rows: dict[str, SymptomDetailRow] = {}
        self._check_vars:  dict[str, ctk.BooleanVar]   = {}

        body = _section_header(self, "Symptoms", accent=SUCCESS)

        _caption(body, "Select all symptoms present").pack(anchor="w",
                                                           pady=(0, P2))

        # Checkbox grid
        grid = ctk.CTkFrame(body, fg_color="transparent")
        grid.pack(fill="x", pady=(0, P4))
        cols = 4
        for i, sym in enumerate(IntakeForm.SYMPTOM_OPTIONS):
            r, c = divmod(i, cols)
            var = ctk.BooleanVar(value=False)
            self._check_vars[sym] = var
            ctk.CTkCheckBox(
                grid,
                text=sym.replace("_", " ").title(),
                variable=var,
                fg_color=SUCCESS,
                hover_color="#15803D",
                text_color=TEXT,
                font=_f(13),
                border_color=BORDER,
                command=lambda s=sym: self._on_toggle(s),
            ).grid(row=r, column=c, sticky="w", padx=P2, pady=P1)

        _divider(body).pack(fill="x", pady=(P2, P3))
        self._details_label = _caption(body, "Symptom Details")
        self._details_label.pack(anchor="w", pady=(0, P2))
        self._details_label.pack_forget()   # hidden until a symptom is selected

        # Container for detail rows
        self._details_frame = ctk.CTkFrame(body, fg_color="transparent")
        self._details_frame.pack(fill="x")

    def _on_toggle(self, symptom: str) -> None:
        if self._check_vars[symptom].get():
            # Add detail row
            row = SymptomDetailRow(self._details_frame, symptom)
            row.pack(fill="x", pady=(0, P2))
            self._detail_rows[symptom] = row
            self._details_label.pack(anchor="w", pady=(0, P2), before=self._details_frame)
        else:
            # Remove detail row
            if symptom in self._detail_rows:
                self._detail_rows[symptom].destroy()
                del self._detail_rows[symptom]
            if not self._detail_rows:
                self._details_label.pack_forget()

        if self._on_pain_change:
            has_pain = bool(IntakeForm.PAIN_SYMPTOMS & self._get_selected_names())
            self._on_pain_change(has_pain)

    def _get_selected_names(self) -> set:
        return {s for s, v in self._check_vars.items() if v.get()}

    def get(self) -> list:
        return [row.get() for row in self._detail_rows.values()]


class PainDetailSection(ctk.CTkFrame):
    """[5] Pain character and radiation (shown only when a pain symptom selected)."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        body = _section_header(self, "Pain Detail", accent=DANGER)
        body.columnconfigure((0, 1), weight=1)

        char_f = ctk.CTkFrame(body, fg_color="transparent")
        char_f.grid(row=0, column=0, sticky="ew", padx=(0, P4))
        _caption(char_f, "Pain Character").pack(anchor="w", pady=(0, P1))
        self._character = _combo(char_f, IntakeForm.PAIN_CHARACTERS,
                                 default="sharp")
        self._character.pack(fill="x")

        rad_f = ctk.CTkFrame(body, fg_color="transparent")
        rad_f.grid(row=0, column=1, sticky="ew")
        _caption(rad_f, "Pain Radiation").pack(anchor="w", pady=(0, P1))
        self._radiation = _combo(rad_f, IntakeForm.PAIN_RADIATIONS,
                                 default="none")
        self._radiation.pack(fill="x")

    def get(self) -> Optional[dict]:
        return {
            "character": self._character.get(),
            "radiation": self._radiation.get(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ASSESSMENT VIEW (scrollable form)
# ═══════════════════════════════════════════════════════════════════════════════

class AssessmentView(ctk.CTkScrollableFrame):
    """Multi-section patient intake form."""

    def __init__(self, master, on_run, **kw):
        super().__init__(master, fg_color=BG,
                         scrollbar_button_color=BORDER,
                         scrollbar_button_hover_color=PRIMARY, **kw)
        self._on_run = on_run

        inner_pad = dict(fill="x", padx=P5, pady=(0, P4))

        # Page title
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=P5, pady=(P5, P4))
        _heading(title_row, "New Patient Assessment", size=20).pack(side="left")
        _label(title_row, "All fields are validated before running.",
               size=13, color=TEXT_MUTED).pack(side="right")

        # ── Sections ──────────────────────────────────────────────────────────
        self._demographics = DemographicsSection(self)
        self._demographics.pack(**inner_pad)

        self._history = HistorySection(self)
        self._history.pack(**inner_pad)

        self._vitals = VitalsSection(self)
        self._vitals.pack(**inner_pad)

        self._symptoms = SymptomsSection(self, on_pain_change=self._toggle_pain)
        self._symptoms.pack(**inner_pad)

        self._pain_section = PainDetailSection(self)
        # Hidden by default; shown when a pain symptom is selected

        # ── Action bar ────────────────────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=P5, pady=(P2, P7))

        _btn(bar, "  🔍  Run Assessment", cmd=self._run,
             variant="primary", width=200).pack(side="right", padx=(P3, 0))
        _btn(bar, "  ↺  Reset Form", cmd=self._reset,
             variant="ghost", width=140).pack(side="right")

    def _toggle_pain(self, show: bool) -> None:
        if show:
            self._pain_section.pack(fill="x", padx=P5, pady=(0, P4))
        else:
            self._pain_section.pack_forget()

    def _run(self) -> None:
        symptoms = self._symptoms.get()
        data = {
            **self._demographics.get(),
            **self._history.get(),
            **self._vitals.get(),
            "symptoms":   symptoms,
            "pain_detail": (
                self._pain_section.get()
                if self._pain_section.winfo_ismapped() else None
            ),
        }
        self._on_run(data)

    def _reset(self) -> None:
        if messagebox.askyesno("Reset Form",
                               "Clear all entered data and start over?"):
            # Rebuild self — simplest reset strategy
            self._on_run(None)   # signal parent to show fresh form


# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS VIEW
# ═══════════════════════════════════════════════════════════════════════════════

class _UrgencyBadge(ctk.CTkFrame):
    """Coloured urgency pill badge."""

    def __init__(self, master, urgency: str, **kw):
        color = URGENCY_COLORS.get(urgency, PRIMARY)
        super().__init__(master, fg_color=color, corner_radius=20, **kw)
        _label(self, urgency.replace("_", " "), size=12, weight="bold",
               color="#FFFFFF").pack(padx=P3, pady=P1)


class _RedFlagBanner(ctk.CTkFrame):
    """Banner listing all red-flag alerts."""

    def __init__(self, master, red_flags: list, **kw):
        super().__init__(master, fg_color="#FEF2F2", corner_radius=12,
                         border_width=1, border_color="#FECACA", **kw)
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=P5, pady=(P4, P2))
        _label(hdr, "⚠  RED FLAGS DETECTED", size=14, weight="bold",
               color=DANGER).pack(anchor="w")

        for rf in red_flags:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=P5, pady=(0, P2))
            _label(row, f"• {rf['flag'].replace('_', ' ')}",
                   size=13, weight="bold", color=DANGER).pack(anchor="w")
            _label(row, f"  {rf['reason']}", size=13,
                   color="#7F1D1D").pack(anchor="w")

        ctk.CTkFrame(self, height=0, fg_color="transparent").pack(pady=(0, P2))


class _PrimaryDiagnosisCard(ctk.CTkFrame):
    """Large card for the primary diagnosis result."""

    def __init__(self, master, primary, **kw):
        super().__init__(master, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=P5, pady=(P5, P2))
        _label(hdr, "PRIMARY DIAGNOSIS", size=11, weight="bold",
               color=TEXT_MUTED).pack(side="left")
        _UrgencyBadge(hdr, primary.urgency).pack(side="right")

        _divider(self).pack(fill="x", padx=P5, pady=(0, P4))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=P5, pady=(0, P5))

        _heading(body, primary.display_name, size=22).pack(anchor="w",
                                                            pady=(0, P2))

        # CF confidence progress bar — gives an instant visual read of certainty
        bar_color = URGENCY_COLORS.get(primary.urgency, PRIMARY)
        cf_bar = ctk.CTkProgressBar(body, height=6, corner_radius=3,
                                    progress_color=bar_color, fg_color=BORDER)
        cf_bar.set(primary.cf)
        cf_bar.pack(fill="x", pady=(0, P3))

        meta_row = ctk.CTkFrame(body, fg_color="transparent")
        meta_row.pack(fill="x")

        for label, value, color in [
            ("Confidence",  primary.confidence,             PRIMARY),
            ("CF Score",    f"{primary.cf:.3f}",            TEXT),
            ("Rules Fired", ", ".join(primary.rules_fired), TEXT_MUTED),
        ]:
            pill = ctk.CTkFrame(meta_row, fg_color=BG, corner_radius=8,
                                border_width=1, border_color=BORDER)
            pill.pack(side="left", padx=(0, P2))
            _label(pill, label, size=11, weight="bold",
                   color=TEXT_MUTED).pack(padx=P3, pady=(P2, 0))
            _label(pill, value, size=13, weight="bold",
                   color=color).pack(padx=P3, pady=(0, P2))


class _DifferentialsCard(ctk.CTkFrame):
    """Table of differential diagnoses."""

    def __init__(self, master, differentials: list, **kw):
        super().__init__(master, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=P5, pady=(P5, P2))
        _label(hdr, "DIFFERENTIAL DIAGNOSES", size=11, weight="bold",
               color=TEXT_MUTED).pack(anchor="w")
        _divider(self).pack(fill="x", padx=P5, pady=(0, P3))

        # Column headers
        tbl = ctk.CTkFrame(self, fg_color="transparent")
        tbl.pack(fill="x", padx=P5, pady=(0, P4))
        tbl.columnconfigure(0, weight=3)
        tbl.columnconfigure(1, weight=1)
        tbl.columnconfigure(2, weight=1)
        tbl.columnconfigure(3, weight=1)

        for c, (header, anchor) in enumerate(
            [("#  Diagnosis", "w"), ("CF", "center"),
             ("Confidence", "center"), ("Urgency", "center")]
        ):
            _label(tbl, header, size=11, weight="bold", color=TEXT_MUTED,
                   anchor=anchor).grid(row=0, column=c, sticky="ew",
                                       padx=P2, pady=(0, P2))

        _divider(tbl).grid(row=1, column=0, columnspan=4, sticky="ew",
                           padx=P2, pady=(0, P2))

        for i, d in enumerate(differentials, 1):
            bg = BG if i % 2 == 0 else SURFACE
            row_f = ctk.CTkFrame(tbl, fg_color=bg, corner_radius=4)
            row_f.grid(row=i + 1, column=0, columnspan=4, sticky="ew",
                       padx=P1, pady=P1)
            row_f.columnconfigure(0, weight=3)
            row_f.columnconfigure(1, weight=1)
            row_f.columnconfigure(2, weight=1)
            row_f.columnconfigure(3, weight=1)

            color = URGENCY_COLORS.get(d.urgency, PRIMARY)
            for c, (val, col) in enumerate([
                (f"{i}.  {d.display_name}", TEXT),
                (str(d.cf), TEXT_MUTED),
                (d.confidence, PRIMARY),
                (d.urgency.replace("_", " "), color),
            ]):
                _label(row_f, val, size=13, color=col).grid(
                    row=0, column=c, sticky="ew", padx=P3, pady=P2)


class _ActionsCard(ctk.CTkFrame):
    """Recommended clinical actions."""

    def __init__(self, master, primary, **kw):
        super().__init__(master, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=P5, pady=(P5, P2))
        _label(hdr, "RECOMMENDED ACTIONS", size=11, weight="bold",
               color=TEXT_MUTED).pack(anchor="w")
        _divider(self).pack(fill="x", padx=P5, pady=(0, P3))

        actions = ActionLibrary.get(primary.diagnosis)
        for action in actions:
            urgent = action.startswith("CALL") or action.startswith("ADMINISTER")
            row = ctk.CTkFrame(
                self,
                fg_color="#FEF2F2" if urgent else BG,
                corner_radius=8,
                border_width=1 if urgent else 0,
                border_color="#FECACA" if urgent else BG,
            )
            row.pack(fill="x", padx=P5, pady=(0, P2))
            icon = "🚨" if urgent else "✓"
            _label(row, f"  {icon}  {action}", size=13,
                   color=DANGER if urgent else TEXT).pack(
                       anchor="w", padx=P3, pady=P2)

        ctk.CTkFrame(self, fg_color="transparent").pack(pady=(0, P2))


class _ExplanationCard(ctk.CTkFrame):
    """Reasoning explanation with expandable trace."""

    def __init__(self, master, results: dict, **kw):
        super().__init__(master, fg_color=SURFACE, corner_radius=12,
                         border_width=1, border_color=BORDER, **kw)
        self._results  = results
        self._explainer = ExplanationModule()
        self._trace_shown = False

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=P5, pady=(P5, P2))
        _label(hdr, "HOW THE SYSTEM DETERMINED THE ILLNESS", size=11, weight="bold",
               color=TEXT_MUTED).pack(side="left")
        self._trace_btn = _btn(
            hdr, "Show Full Trace ›", cmd=self._toggle_trace,
            variant="ghost", height=30, width=165,
        )
        self._trace_btn.pack(side="right")
        _divider(self).pack(fill="x", padx=P5, pady=(0, P3))

        summary = self._explainer.summary(results)
        self._summary_box = ctk.CTkTextbox(
            self, height=230, fg_color=BG, text_color=TEXT,
            font=_f(13), corner_radius=8, border_width=0,
            wrap="word",
        )
        self._summary_box.pack(fill="x", padx=P5, pady=(0, P3))
        self._summary_box.insert("1.0", summary)
        self._summary_box.configure(state="disabled")

        # Trace box (hidden initially); uses a monospace font for aligned output
        self._trace_box = ctk.CTkTextbox(
            self, height=360, fg_color=BG, text_color=TEXT_MUTED,
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            corner_radius=8, border_width=0, wrap="none",
        )
        ctk.CTkFrame(self, fg_color="transparent").pack(pady=(0, P2))

    def _toggle_trace(self) -> None:
        if self._trace_shown:
            self._trace_box.pack_forget()
            self._trace_btn.configure(text="Show Full Trace ›")
        else:
            detailed = self._explainer.detailed(self._results)
            self._trace_box.configure(state="normal")
            self._trace_box.delete("1.0", "end")
            self._trace_box.insert("1.0", detailed)
            self._trace_box.configure(state="disabled")
            self._trace_box.pack(fill="x", padx=P5, pady=(0, P3))
            self._trace_btn.configure(text="‹ Hide Trace")
        self._trace_shown = not self._trace_shown


class ResultsView(ctk.CTkScrollableFrame):
    """Full assessment results display."""

    def __init__(self, master, results: dict, patient_data: dict,
                 on_back, on_save, **kw):
        super().__init__(master, fg_color=BG,
                         scrollbar_button_color=BORDER,
                         scrollbar_button_hover_color=PRIMARY, **kw)
        self._results      = results
        self._patient_data = patient_data
        self._persistence  = DataPersistence()

        inner_pad = dict(fill="x", padx=P5, pady=(0, P4))

        # ── Page title bar ─────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=P5, pady=(P5, P4))
        _heading(top, "Assessment Results", size=20).pack(side="left")
        name = patient_data.get("name") or "Patient"
        _label(top, f"For {name}", size=13, color=TEXT_MUTED).pack(
            side="left", padx=(P3, 0))

        # Back / Save buttons
        btn_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_row.pack(side="right")
        _btn(btn_row, "  ← New Assessment", cmd=on_back,
             variant="ghost", width=170).pack(side="left", padx=(0, P2))
        _btn(btn_row, "  💾  Save", cmd=lambda: self._save(on_save),
             variant="primary", width=120).pack(side="left")

        # ── Red flags ─────────────────────────────────────────────────────
        if results["red_flags"]:
            _RedFlagBanner(self, results["red_flags"]).pack(**inner_pad)

        # ── Primary diagnosis ──────────────────────────────────────────────
        if results["primary"]:
            _PrimaryDiagnosisCard(self, results["primary"]).pack(**inner_pad)
        else:
            no_diag = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=12,
                                   border_width=1, border_color=BORDER)
            no_diag.pack(**inner_pad)
            _label(no_diag,
                   "No matching diagnosis found. Check inputs or consult a clinician.",
                   size=14, color=TEXT_MUTED).pack(padx=P5, pady=P5)

        # ── Differentials ──────────────────────────────────────────────────
        if results["differentials"]:
            _DifferentialsCard(self, results["differentials"]).pack(**inner_pad)

        # ── Recommended actions ────────────────────────────────────────────
        if results["primary"]:
            _ActionsCard(self, results["primary"]).pack(**inner_pad)

        # ── Explanation ────────────────────────────────────────────────────
        _ExplanationCard(self, results).pack(**inner_pad)

        # ── Disclaimer ────────────────────────────────────────────────────
        disc = ctk.CTkFrame(self, fg_color="#FFFBEB", corner_radius=12,
                            border_width=1, border_color="#FDE68A")
        disc.pack(**inner_pad)
        _label(disc,
               "⚠  DISCLAIMER: This system is a decision-support tool only. "
               "All outputs must be reviewed by a licensed clinician. "
               "Do not act on these results without professional oversight.",
               size=12, color="#92400E", wraplength=700).pack(
                   padx=P5, pady=P4)

    def _save(self, callback) -> None:
        try:
            fname = self._persistence.save_assessment(
                self._patient_data, self._results,
            )
            messagebox.showinfo("Saved",
                                f"Assessment saved to:\n{fname}")
            if callback:
                callback()
        except Exception as exc:
            messagebox.showerror("Save Failed", str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# SAVED PATIENTS VIEW
# ═══════════════════════════════════════════════════════════════════════════════

class SavedPatientsView(ctk.CTkFrame):
    """List of saved assessments with detail preview."""

    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG, **kw)
        self._persistence = DataPersistence()

        # ── Header ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=P5, pady=(P5, P4))
        _heading(hdr, "Saved Assessments", size=20).pack(side="left")
        _btn(hdr, "  ↺  Refresh", cmd=self._load_list,
             variant="ghost", width=120).pack(side="right")

        # ── Two-pane layout ───────────────────────────────────────────────
        panes = ctk.CTkFrame(self, fg_color="transparent")
        panes.pack(fill="both", expand=True, padx=P5, pady=(0, P5))
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(1, weight=3)

        # Left: list
        list_card = _card(panes)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, P3))
        _caption(list_card, "Patients").pack(anchor="w", padx=P4, pady=(P4, P2))
        self._list_frame = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent",
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=PRIMARY,
        )
        self._list_frame.pack(fill="both", expand=True, padx=P2, pady=(0, P2))

        # Right: detail
        self._detail_card = _card(panes)
        self._detail_card.grid(row=0, column=1, sticky="nsew")
        self._detail_text = ctk.CTkTextbox(
            self._detail_card, fg_color=BG, text_color=TEXT,
            font=_f(13), corner_radius=8, border_width=0, wrap="word",
        )
        self._detail_text.pack(fill="both", expand=True, padx=P4, pady=P4)
        self._show_placeholder()

        self._load_list()

    def _load_list(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        patients = DataPersistence.list_saved_patients()
        if not patients:
            _label(self._list_frame, "No saved assessments.",
                   size=13, color=TEXT_MUTED).pack(padx=P4, pady=P4)
        for name in patients:
            row = ctk.CTkFrame(self._list_frame, fg_color="transparent")
            row.pack(fill="x", pady=P1)
            row.columnconfigure(0, weight=1)

            ctk.CTkButton(
                row,
                text=name.replace("_", " ").title(),
                command=lambda n=name: self._load_patient(n),
                fg_color="transparent",
                hover_color=BG,
                text_color=TEXT,
                anchor="w",
                font=_f(13),
                height=36,
                corner_radius=6,
            ).grid(row=0, column=0, sticky="ew")

            # Delete button — shown inline, only acts after confirmation
            ctk.CTkButton(
                row,
                text="🗑",
                command=lambda n=name: self._delete_patient(n),
                fg_color="transparent",
                hover_color="#FEE2E2",
                text_color=DANGER,
                width=34,
                height=34,
                corner_radius=6,
            ).grid(row=0, column=1, padx=(P1, 0))

    def _show_placeholder(self) -> None:
        self._detail_text.configure(state="normal")
        self._detail_text.delete("1.0", "end")
        self._detail_text.insert(
            "1.0", "Select a patient from the list to view their assessment.",
        )
        self._detail_text.configure(state="disabled")

    def _load_patient(self, name: str) -> None:
        try:
            data = DataPersistence.load_assessment(name)
        except FileNotFoundError:
            messagebox.showerror("Not Found",
                                 f"No assessment file found for '{name}'.")
            return
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            return

        pd_  = data.get("patient_data", {})
        res  = data.get("results", {})
        pri  = res.get("primary") or {}
        difs = res.get("differentials", [])
        flags = res.get("red_flags", [])

        lines = [
            f"Patient:    {pd_.get('name', 'Unknown')}",
            f"Age / Sex:  {pd_.get('age', '—')} yrs, {pd_.get('sex', '—')}",
            f"Timestamp:  {data.get('timestamp', '—')}",
            "",
            "─" * 48,
            "PRIMARY DIAGNOSIS",
            f"  Diagnosis : {pri.get('diagnosis', 'None').replace('_', ' ')}",
            f"  CF Score  : {pri.get('cf', '—')}",
            f"  Confidence: {pri.get('confidence', '—')}",
            f"  Urgency   : {pri.get('urgency', '—')}",
        ]

        if flags:
            lines += ["", "─" * 48, "RED FLAGS"]
            for rf in flags:
                lines.append(f"  • {rf.get('flag', '').replace('_', ' ')}")
                lines.append(f"    {rf.get('reason', '')}")

        if difs:
            lines += ["", "─" * 48, "DIFFERENTIALS"]
            for i, d in enumerate(difs, 1):
                lines.append(
                    f"  {i}. {d.get('diagnosis', '').replace('_', ' ')}"
                    f"  (CF={d.get('cf', '—')}, {d.get('urgency', '—')})"
                )

        conds = pd_.get("known_conditions", [])
        if conds:
            lines += ["", "─" * 48, "KNOWN CONDITIONS"]
            for c in conds:
                lines.append(f"  • {c.replace('_', ' ').title()}")

        text = "\n".join(lines)
        self._detail_text.configure(state="normal")
        self._detail_text.delete("1.0", "end")
        self._detail_text.insert("1.0", text)
        self._detail_text.configure(state="disabled")

    def _delete_patient(self, name: str) -> None:
        """Permanently delete a saved assessment file after confirmation."""
        display = name.replace("_", " ").title()
        if not messagebox.askyesno(
            "Delete Assessment",
            f"Permanently delete the assessment for '{display}'?\n\nThis cannot be undone.",
        ):
            return
        try:
            DataPersistence.delete_assessment(name)
        except FileNotFoundError as exc:
            messagebox.showerror("Not Found", str(exc))
            return
        except Exception as exc:
            messagebox.showerror("Delete Failed", str(exc))
            return
        self._show_placeholder()
        self._load_list()


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

class Sidebar(ctk.CTkFrame):
    """Navigation sidebar with branded header."""

    NAV_ITEMS = [
        ("🩺  New Assessment",   "assessment"),
        ("📋  Saved Patients",   "saved"),
    ]

    def __init__(self, master, on_navigate, **kw):
        super().__init__(master, fg_color=SIDEBAR_BG, corner_radius=0,
                         width=220, **kw)
        self.pack_propagate(False)
        self._on_nav  = on_navigate
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._active  = ""

        # ── Logo / title ──────────────────────────────────────────────────
        logo = ctk.CTkFrame(self, fg_color="transparent")
        logo.pack(fill="x", padx=P4, pady=(P6, P5))
        ctk.CTkLabel(
            logo, text="⚕",
            font=_f(32), text_color="#FFFFFF",
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo, text="MedDiag\nExpert System",
            font=_f(14, "bold"), text_color="#FFFFFF",
            justify="left",
        ).pack(anchor="w", pady=(P1, 0))
        ctk.CTkLabel(
            logo, text="AIE212 · Clinical Triage",
            font=_f(11), text_color="#93C5FD",
            justify="left",
        ).pack(anchor="w", pady=(P1, 0))

        divider = _divider(self)
        divider.configure(fg_color="#2D4A7A")
        divider.pack(fill="x", padx=P4, pady=(0, P4))

        # ── Nav items ─────────────────────────────────────────────────────
        nav_label = ctk.CTkLabel(
            self, text="MENU",
            font=_f(10, "bold"), text_color="#93C5FD",
            anchor="w",
        )
        nav_label.pack(fill="x", padx=P4, pady=(0, P2))

        for label, key in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                self, text=label,
                command=lambda k=key: self._navigate(k),
                fg_color="transparent",
                hover_color="#2D4A7A",
                text_color="#FFFFFF",
                text_color_disabled="#93C5FD",
                anchor="w",
                font=_f(14),
                height=44,
                corner_radius=8,
            )
            btn.pack(fill="x", padx=P2, pady=P1)
            self._buttons[key] = btn

        # Spacer
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)

        # ── Footer disclaimer ─────────────────────────────────────────────
        divider = _divider(self)
        divider.configure(fg_color="#2D4A7A")
        divider.pack(fill="x", padx=P4, pady=(0, P3))
        ctk.CTkLabel(
            self,
            text="Decision-support tool only.\nConsult a licensed clinician.",
            font=_f(10), text_color="#93C5FD",
            justify="left", wraplength=180,
        ).pack(padx=P4, pady=(0, P5), anchor="w")

    def _navigate(self, key: str) -> None:
        if key == self._active:
            return
        for k, btn in self._buttons.items():
            btn.configure(
                fg_color=PRIMARY if k == key else "transparent",
            )
        self._active = key
        self._on_nav(key)

    def set_active(self, key: str) -> None:
        self._navigate(key)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class GUIApp(ctk.CTk):
    """
    Main application window.

    Composes a Sidebar + scrollable content area.
    Manages three views: AssessmentView, ResultsView, SavedPatientsView.
    """

    def __init__(self):
        super().__init__()
        self._engine = InferenceEngine()

        self.title("Medical Diagnosis Expert System")
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(fg_color=BG)

        self._build_layout()
        self._sidebar.set_active("assessment")

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._sidebar = Sidebar(self, on_navigate=self._navigate)
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        self._content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._views: dict[str, ctk.CTkBaseClass] = {}
        self._current_view: Optional[str] = None

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate(self, key: str) -> None:
        if key == "assessment":
            self._show_assessment_form()
        elif key == "saved":
            self._show_saved()
        elif key == "results":
            pass  # already shown

    def _show_assessment_form(self) -> None:
        self._clear_content()
        view = AssessmentView(self._content, on_run=self._run_assessment)
        view.grid(row=0, column=0, sticky="nsew")
        self._views["assessment"] = view
        self._current_view = "assessment"

    def _show_saved(self) -> None:
        self._clear_content()
        view = SavedPatientsView(self._content)
        view.grid(row=0, column=0, sticky="nsew")
        self._views["saved"] = view
        self._current_view = "saved"

    def _show_results(self, results: dict, patient_data: dict) -> None:
        self._clear_content()
        view = ResultsView(
            self._content,
            results=results,
            patient_data=patient_data,
            on_back=self._back_to_form,
            on_save=None,
        )
        view.grid(row=0, column=0, sticky="nsew")
        self._views["results"] = view
        self._current_view = "results"

    def _back_to_form(self) -> None:
        self._show_assessment_form()
        self._sidebar._active = "assessment"

    def _clear_content(self) -> None:
        for w in self._content.winfo_children():
            w.destroy()
        self._views.clear()

    # ── Inference ─────────────────────────────────────────────────────────────

    def _run_assessment(self, patient_data: Optional[dict]) -> None:
        """Called by AssessmentView when the user clicks Run Assessment."""
        if patient_data is None:
            # Reset request — rebuild the form
            self._show_assessment_form()
            return

        # Validate that at least one symptom or a vitals abnormality is present
        has_symptoms = bool(patient_data.get("symptoms"))
        if not has_symptoms:
            ok = messagebox.askyesno(
                "No Symptoms Entered",
                "No symptoms have been selected.\n\n"
                "The engine will still run based on vital signs only.\n"
                "Continue?",
            )
            if not ok:
                return

        # Show a brief loading overlay
        overlay = ctk.CTkFrame(self._content, fg_color=BG, corner_radius=0)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        _label(overlay, "Running inference engine…",
               size=16, color=TEXT_MUTED).place(relx=0.5, rely=0.5,
                                                 anchor="center")
        self.update()

        try:
            results = self._engine.run(patient_data)
        except Exception as exc:
            overlay.destroy()
            messagebox.showerror("Engine Error",
                                 f"An error occurred during inference:\n{exc}")
            return

        overlay.destroy()
        self._show_results(results, patient_data)


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = GUIApp()
    app.mainloop()
