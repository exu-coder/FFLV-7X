# -*- coding: utf-8 -*-
"""
Free Fire Level-Up Bot - Web Dashboard
Glass / Prism design, 100% English, auto-refresh every 5 seconds.

Mode policy per account:
  - Matches #1, #2, #3  -> Battle Royale  (needed to unlock Lone Wolf at level 3)
  - Match #4 onwards     -> 50/50 MIX      (alternating Lone Wolf and Battle Royale)
  - Manual override via dashboard dropdown still respected.
"""

import asyncio
import json
import os
import time

from typing import Dict, List, Any, Optional
from aiohttp import web

# Auto-LW level kept for reference (not used for the new rotation logic)
try:
    AUTO_LW_LEVEL = int(os.environ.get("AUTO_LW_LEVEL", "3"))
except Exception:
    AUTO_LW_LEVEL = 3

# Number of mandatory BR matches at account startup (to unlock LW)
try:
    BR_UNLOCK_MATCHES = int(os.environ.get("BR_UNLOCK_MATCHES", "3"))
except Exception:
    BR_UNLOCK_MATCHES = 3

# Default mode for a brand-new account: "MIX", "BR", or "LONE_WOLF"
DEFAULT_MATCH_MODE = os.environ.get("DEFAULT_MATCH_MODE", "MIX").strip().upper()
if DEFAULT_MATCH_MODE not in ("BR", "LONE_WOLF", "MIX"):
    DEFAULT_MATCH_MODE = "MIX"


# ==================== BASE DIRECTORY ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
import glob as _glob


def get_all_account_files_dashboard():
    files = sorted(_glob.glob(os.path.join(BASE_DIR, "accounts*.json")))
    if not files:
        files = [os.path.join(BASE_DIR, "accounts.json")]
    return files


ACCOUNTS_FILE_PATH = os.path.join(BASE_DIR, "accounts.json")


# ==================== EMBEDDED HTML DASHBOARD ====================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="dark">
    <title>AFX LEVEL UP</title>

    <style>
/* ═══════════════════════════════════════════════════════════
   AFX LEVEL UP — Glass Prism Theme
   ═══════════════════════════════════════════════════════════ */
:root {
    --bg: #04060c;
    --bg-2: #070a14;
    --surface: rgba(22, 26, 40, 0.55);
    --surface-2: rgba(30, 36, 54, 0.72);
    --surface-3: rgba(40, 48, 70, 0.85);
    --glass-border: rgba(255, 255, 255, 0.10);
    --glass-hi: rgba(255, 255, 255, 0.06);
    --text: #f4f7ff;
    --muted: #8f97ab;
    --muted-2: #565f75;
    --accent: #6ee7ff;
    --accent-2: #a78bfa;
    --accent-3: #34d399;
    --accent-4: #f472b6;
    --green: #34d399;
    --yellow: #fbbf24;
    --red: #fb7185;
    --orange: #fb923c;
    --radius-sm: 10px;
    --radius-md: 14px;
    --radius-lg: 20px;
    --radius-xl: 24px;
    --ease: cubic-bezier(.22, 1, .36, 1);
    --glow-accent: 0 0 40px rgba(110, 231, 255, 0.20);
    --glow-accent-2: 0 0 40px rgba(167, 139, 250, 0.20);
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }

body {
    min-height: 100vh;
    color: var(--text);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
    background: var(--bg);
    position: relative;
    overflow-x: hidden;
}

/* Ambient prism background */
body::before {
    content: "";
    position: fixed;
    inset: -50%;
    background:
        radial-gradient(circle at 20% 20%, rgba(110,231,255,.12), transparent 42%),
        radial-gradient(circle at 80% 30%, rgba(167,139,250,.12), transparent 45%),
        radial-gradient(circle at 60% 85%, rgba(52,211,153,.10), transparent 42%),
        radial-gradient(circle at 10% 90%, rgba(244,114,182,.10), transparent 42%);
    z-index: -1;
    animation: prismFloat 24s ease-in-out infinite;
}
@keyframes prismFloat {
    0%, 100% { transform: translate(0, 0) rotate(0deg) scale(1); }
    33%      { transform: translate(-2%, 1%) rotate(2deg) scale(1.05); }
    66%      { transform: translate(2%, -1%) rotate(-2deg) scale(1.03); }
}

body.modal-open { overflow: hidden; }
button, input, select { font: inherit; }
button { border: 0; cursor: pointer; }
::selection { background: var(--accent); color: #04060c; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, rgba(110,231,255,.4), rgba(167,139,250,.4));
    border-radius: 999px;
}
::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, rgba(110,231,255,.7), rgba(167,139,250,.7));
}

/* ========= HEADER ========= */
.header {
    position: sticky;
    top: 0;
    z-index: 50;
    height: 68px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px;
    background: rgba(6, 10, 20, 0.72);
    border-bottom: 1px solid var(--glass-border);
    backdrop-filter: blur(28px) saturate(180%);
    -webkit-backdrop-filter: blur(28px) saturate(180%);
}

.brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
.brand-icon {
    width: 30px;
    height: 30px;
    flex: 0 0 auto;
    color: var(--accent);
    filter: drop-shadow(0 0 10px rgba(110,231,255,.7));
    animation: iconPulse 3s ease-in-out infinite;
}
@keyframes iconPulse {
    0%, 100% { filter: drop-shadow(0 0 8px rgba(110,231,255,.5)); }
    50%      { filter: drop-shadow(0 0 16px rgba(167,139,250,.9)); }
}
.brand-text { display: flex; align-items: baseline; gap: 8px; }
.brand-name {
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.02em;
    background: linear-gradient(135deg, #fff 30%, var(--accent) 60%, var(--accent-2) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.brand-by { color: var(--muted-2); font-size: 10px; font-weight: 500; }

.global-controls {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 1;
    justify-content: center;
}

.global-mode-select {
    height: 38px;
    padding: 0 34px 0 14px;
    background: rgba(22,26,40,.75);
    color: #cbd2e0;
    border: 1px solid var(--glass-border);
    border-radius: 11px;
    font-size: 11px;
    font-weight: 650;
    cursor: pointer;
    outline: none;
    appearance: none;
    -webkit-appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%238f97ab' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    transition: all .3s var(--ease);
    min-width: 200px;
}
.global-mode-select:hover {
    border-color: rgba(110,231,255,.4);
    color: #fff;
    box-shadow: 0 0 0 3px rgba(110,231,255,.08);
}
.global-mode-select option { background: #0d1018; color: #ccc; }

/* EXP limit control */
.exp-limit-wrap {
    display: flex;
    align-items: center;
    height: 38px;
    border: 1px solid var(--glass-border);
    border-radius: 11px;
    overflow: hidden;
    background: rgba(22,26,40,.75);
    transition: all .3s var(--ease);
}
.exp-limit-wrap:hover { border-color: rgba(251,146,60,.4); }
.exp-limit-wrap.limit-active { border-color: rgba(251,146,60,.55); box-shadow: 0 0 0 3px rgba(251,146,60,.06); }
.exp-limit-label {
    padding: 0 8px 0 12px;
    font-size: 11px;
    font-weight: 650;
    color: var(--muted);
    white-space: nowrap;
    user-select: none;
}
.exp-limit-wrap.limit-active .exp-limit-label { color: var(--orange); }
.exp-limit-input {
    width: 78px;
    background: transparent;
    border: none;
    outline: none;
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    padding: 0 4px;
    text-align: center;
}
.exp-limit-input::-webkit-inner-spin-button,
.exp-limit-input::-webkit-outer-spin-button { -webkit-appearance: none; }
.exp-limit-btn {
    height: 38px;
    padding: 0 14px;
    background: rgba(251,146,60,.12);
    border: none;
    border-left: 1px solid rgba(251,146,60,.22);
    color: var(--orange);
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
    transition: all .2s var(--ease);
}
.exp-limit-btn:hover { background: var(--orange); color: #000; }
.exp-limit-btn:disabled { opacity: .5; cursor: not-allowed; }

/* Bot toggle */
.toggle-container {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 14px;
    height: 38px;
    background: rgba(22,26,40,.75);
    border: 1px solid var(--glass-border);
    border-radius: 11px;
    cursor: pointer;
    transition: all .3s var(--ease);
}
.toggle-container:hover { border-color: rgba(52,211,153,.4); }
.toggle-label {
    color: var(--muted);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    user-select: none;
}
.toggle-switch { position: relative; display: inline-block; width: 40px; height: 22px; flex: 0 0 auto; }
.toggle-switch input { opacity: 0; width: 0; height: 0; position: absolute; }
.toggle-slider {
    position: absolute;
    cursor: pointer;
    inset: 0;
    background: #2a2f3d;
    border-radius: 999px;
    transition: all .3s var(--ease);
    border: 1px solid #3a4155;
}
.toggle-slider:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 2px;
    top: 2px;
    background: #6b7385;
    border-radius: 50%;
    transition: all .3s var(--ease);
}
.toggle-switch input:checked + .toggle-slider {
    background: rgba(52,211,153,.18);
    border-color: rgba(52,211,153,.45);
}
.toggle-switch input:checked + .toggle-slider:before {
    transform: translateX(18px);
    background: var(--green);
    box-shadow: 0 0 12px rgba(52,211,153,.9), 0 0 4px rgba(52,211,153,1);
}
.toggle-status {
    font-size: 11px;
    font-weight: 800;
    min-width: 24px;
    letter-spacing: .06em;
    user-select: none;
}
.toggle-status.on  { color: var(--green); text-shadow: 0 0 8px rgba(52,211,153,.5); }
.toggle-status.off { color: var(--red); }

/* Header buttons */
.header-actions { display: flex; align-items: center; gap: 10px; }
.add-btn {
    height: 40px;
    padding: 0 18px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #04060c;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
    border-radius: 12px;
    font-size: 12px;
    font-weight: 750;
    letter-spacing: 0.01em;
    transition: all .35s var(--ease);
    box-shadow:
        0 4px 16px rgba(110,231,255,.25),
        inset 0 1px 0 rgba(255,255,255,.2);
}
.add-btn svg { width: 15px; height: 15px; stroke-width: 2.4; }
.add-btn:hover {
    transform: translateY(-2px);
    box-shadow:
        0 10px 32px rgba(167,139,250,.4),
        inset 0 1px 0 rgba(255,255,255,.3);
    filter: brightness(1.08);
}
.add-btn:active { transform: translateY(0) scale(.97); }

#reloadJsonBtn {
    background: rgba(52,211,153,.10) !important;
    color: var(--green) !important;
    border: 1px solid rgba(52,211,153,.30) !important;
    box-shadow: none;
}
#reloadJsonBtn:hover {
    background: rgba(52,211,153,.2) !important;
    box-shadow: 0 8px 24px rgba(52,211,153,.2) !important;
}

/* ========= MAIN ========= */
.main { width: min(1440px, 100%); margin: 0 auto; padding-bottom: 60px; }

/* Stats */
.stats-row {
    display: grid;
    grid-template-columns: repeat(3, minmax(0,1fr));
    gap: 16px;
    padding: 24px 28px 0;
}
.stat-card {
    position: relative;
    min-height: 118px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 22px;
    background: var(--surface);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    overflow: hidden;
    transition: all .4s var(--ease);
}
.stat-card::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, var(--glass-hi), transparent 45%);
    pointer-events: none;
}
.stat-card::after {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, var(--accent), var(--accent-2));
    opacity: 0.7;
    transition: opacity .3s ease;
}
.stat-card:hover {
    transform: translateY(-4px);
    border-color: rgba(110,231,255,.3);
    box-shadow: var(--glow-accent), 0 20px 60px rgba(0,0,0,.5);
}
.stat-card:hover::after { opacity: 1; }
.stat-label {
    margin-bottom: 8px;
    color: var(--muted);
    font-size: 10px;
    font-weight: 650;
    letter-spacing: .14em;
    text-transform: uppercase;
}
.stat-value {
    color: #fff;
    font-size: 30px;
    line-height: 1;
    font-weight: 800;
    letter-spacing: -0.04em;
    font-variant-numeric: tabular-nums;
    transition: color .3s ease;
}
.stat-card:hover .stat-value {
    color: var(--accent);
    text-shadow: 0 0 24px rgba(110,231,255,.4);
}

/* Accounts */
.accounts-section { padding: 32px 28px; }
.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
}
.section-title {
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .16em;
    text-transform: uppercase;
}
.account-count { color: var(--muted-2); font-size: 11px; font-weight: 600; }

.accounts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 22px;
}

/* Account card */
.account-card {
    position: relative;
    padding: 24px;
    background: var(--surface);
    border: 1px solid var(--glass-border);
    border-radius: var(--radius-lg);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    overflow: hidden;
    opacity: 0;
    transform: translateY(12px) scale(.98);
    animation: cardIn .55s var(--ease) forwards;
    animation-delay: calc(var(--index, 0) * 50ms);
    transition: all .4s var(--ease);
}
@keyframes cardIn {
    to { opacity: 1; transform: translateY(0) scale(1); }
}
.account-card::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, var(--glass-hi), transparent 50%);
    pointer-events: none;
    border-radius: inherit;
}
.account-card:hover {
    transform: translateY(-5px);
    background: var(--surface-2);
    border-color: rgba(110,231,255,.25);
    box-shadow:
        0 0 0 1px rgba(110,231,255,.1),
        0 24px 60px rgba(0,0,0,.55),
        var(--glow-accent);
}
.account-card:has(.status.in-match)::after {
    content: "";
    position: absolute;
    top: 14px;
    right: 14px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 14px var(--green);
    animation: livePulse 1.5s ease-in-out infinite;
}
@keyframes livePulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50%      { transform: scale(1.4); opacity: .5; }
}

.account-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
}
.account-identity { display: flex; align-items: center; gap: 14px; min-width: 0; }
.avatar {
    width: 52px;
    height: 52px;
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, rgba(110,231,255,.15), rgba(167,139,250,.15));
    border: 1px solid var(--glass-border);
    border-radius: 15px;
    color: var(--accent);
    transition: all .4s var(--ease);
}
.account-card:hover .avatar {
    transform: scale(1.06) rotate(-3deg);
    border-color: rgba(110,231,255,.4);
    box-shadow: 0 0 28px rgba(110,231,255,.25);
}
.avatar svg { width: 26px; height: 26px; }
.identity-info { min-width: 0; }
.nickname {
    max-width: 220px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 15px;
    font-weight: 750;
    letter-spacing: -0.01em;
}
.uid {
    margin-top: 5px;
    color: var(--muted-2);
    font-size: 11px;
    font-weight: 550;
    font-variant-numeric: tabular-nums;
    letter-spacing: .02em;
}

/* Status */
.status {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 7px 13px;
    border-radius: 999px;
    font-size: 10px;
    font-weight: 750;
    letter-spacing: .1em;
    border: 1px solid transparent;
    white-space: nowrap;
    text-transform: uppercase;
}
.status-dot { width: 6px; height: 6px; border-radius: 50%; flex: 0 0 auto; }
.status.online {
    color: var(--green);
    background: rgba(52,211,153,.08);
    border-color: rgba(52,211,153,.22);
}
.status.online .status-dot {
    background: var(--green);
    box-shadow: 0 0 10px var(--green);
    animation: pulseGreen 1.8s ease-in-out infinite;
}
.status.searching {
    color: var(--yellow);
    background: rgba(251,191,36,.08);
    border-color: rgba(251,191,36,.22);
}
.status.searching .status-dot {
    background: var(--yellow);
    box-shadow: 0 0 10px var(--yellow);
    animation: pulseYellow 1.4s ease-in-out infinite;
}
.status.in-match {
    color: #fff;
    background: linear-gradient(90deg, rgba(110,231,255,.15), rgba(167,139,250,.15));
    border-color: rgba(110,231,255,.35);
}
.status.in-match .status-dot {
    background: var(--accent);
    box-shadow: 0 0 12px var(--accent);
}
.status.offline, .status.error {
    color: var(--red);
    background: rgba(251,113,133,.08);
    border-color: rgba(251,113,133,.22);
}
.status.offline .status-dot, .status.error .status-dot { background: var(--red); }
.status.paused {
    color: var(--orange);
    background: rgba(251,146,60,.08);
    border-color: rgba(251,146,60,.22);
}
.status.paused .status-dot { background: var(--orange); }
@keyframes pulseGreen {
    0%, 100% { opacity: 1; }
    50%      { opacity: .35; }
}
@keyframes pulseYellow {
    0%, 100% { opacity: 1; }
    50%      { opacity: .35; }
}

/* EXP 3-col */
.exp-three-col {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    padding: 16px;
    background: rgba(10,14,24,.55);
    border: 1px solid var(--glass-border);
    border-radius: 14px;
    margin-bottom: 18px;
}
.exp-col { display: flex; flex-direction: column; gap: 6px; }
.exp-col-label {
    color: var(--muted-2);
    font-size: 9px;
    font-weight: 650;
    letter-spacing: .1em;
    text-transform: uppercase;
}
.exp-col-value {
    color: #e8ecf3;
    font-size: 16px;
    font-weight: 800;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
}
.exp-col-value.gained {
    color: var(--green);
    text-shadow: 0 0 14px rgba(52,211,153,.4);
}

.exp-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.exp-label {
    color: var(--accent);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .08em;
    text-transform: uppercase;
}
.exp-value {
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
}
.progress {
    width: 100%;
    height: 8px;
    background: rgba(10,14,24,.8);
    border: 1px solid var(--glass-border);
    border-radius: 999px;
    overflow: hidden;
    position: relative;
}
.progress-bar {
    height: 100%;
    width: 0;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    border-radius: inherit;
    box-shadow: 0 0 18px rgba(110,231,255,.5);
    transition: width .9s var(--ease);
    position: relative;
    overflow: hidden;
}
.progress-bar::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,.5), transparent);
    animation: shimmer 2.2s linear infinite;
}
@keyframes shimmer {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* Footer */
.account-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 18px;
    padding-top: 16px;
    border-top: 1px solid var(--glass-border);
}
.last-match-label {
    color: var(--muted-2);
    font-size: 9px;
    font-weight: 650;
    letter-spacing: .1em;
    text-transform: uppercase;
}
.last-match-value {
    margin-top: 5px;
    color: var(--muted);
    font-size: 11px;
    font-weight: 550;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.acc-info {
    margin: 10px 0 0;
    padding: 10px 12px;
    border-radius: 10px;
    font-size: 11px;
    line-height: 1.5;
    color: #b5bcc9;
    background: rgba(110,231,255,.06);
    border: 1px solid rgba(110,231,255,.15);
    word-break: break-word;
    font-family: ui-monospace, monospace;
}
.acc-error {
    margin: 10px 0 0;
    padding: 10px 12px;
    border-radius: 10px;
    font-size: 11px;
    line-height: 1.5;
    color: var(--red);
    background: rgba(251,113,133,.06);
    border: 1px solid rgba(251,113,133,.18);
    word-break: break-word;
    font-family: ui-monospace, monospace;
}

/* Match type select */
.match-type-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 14px 0 0;
}
.match-type-label {
    color: var(--muted-2);
    font-size: 9px;
    font-weight: 650;
    letter-spacing: .1em;
    text-transform: uppercase;
    white-space: nowrap;
}
.match-type-select {
    flex: 1;
    height: 34px;
    padding: 0 10px;
    background: rgba(10,14,24,.7);
    color: #ccc;
    border: 1px solid var(--glass-border);
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    outline: none;
    appearance: none;
    -webkit-appearance: none;
    transition: all .3s var(--ease);
}
.match-type-select:hover, .match-type-select:focus {
    border-color: var(--accent);
    color: #fff;
}
.match-type-select.br-mode { color: var(--yellow); border-color: rgba(251,191,36,.35); }
.match-type-select.lw-mode { color: var(--green);  border-color: rgba(52,211,153,.3); }
.match-type-select.mix-mode { color: var(--accent); border-color: rgba(110,231,255,.4); }
.match-type-select option { background: #0d1018; color: #ccc; }

.card-actions { display: flex; gap: 8px; }
.icon-btn {
    width: 38px;
    height: 38px;
    display: grid;
    place-items: center;
    color: var(--muted);
    background: rgba(10,14,24,.6);
    border: 1px solid var(--glass-border);
    border-radius: 11px;
    transition: all .3s var(--ease);
}
.icon-btn:hover {
    color: var(--accent);
    background: rgba(110,231,255,.1);
    border-color: rgba(110,231,255,.4);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(110,231,255,.2);
}
.icon-btn.delete:hover {
    color: var(--red);
    background: rgba(251,113,133,.1);
    border-color: rgba(251,113,133,.35);
    box-shadow: 0 6px 20px rgba(251,113,133,.2);
}
.icon-btn:active { transform: scale(.92); }
.icon-btn svg { width: 16px; height: 16px; }

/* Empty */
.empty-state {
    min-height: 260px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px;
    background: var(--surface);
    border: 1px dashed rgba(110,231,255,.2);
    border-radius: var(--radius-lg);
    text-align: center;
    backdrop-filter: blur(20px);
    transition: all .4s var(--ease);
}
.empty-state:hover {
    border-color: rgba(110,231,255,.4);
    background: var(--surface-2);
}
.empty-icon {
    width: 56px;
    height: 56px;
    display: grid;
    place-items: center;
    margin-bottom: 16px;
    color: var(--accent);
    background: rgba(110,231,255,.08);
    border: 1px solid rgba(110,231,255,.25);
    border-radius: 16px;
    box-shadow: var(--glow-accent);
}
.empty-icon svg { width: 26px; height: 26px; }
.empty-title { font-size: 15px; font-weight: 750; }
.empty-text {
    max-width: 360px;
    margin-top: 8px;
    color: var(--muted);
    font-size: 11px;
    line-height: 1.65;
}

/* Modal */
.overlay {
    position: fixed;
    inset: 0;
    z-index: 100;
    display: grid;
    place-items: center;
    padding: 20px;
    background: rgba(2,4,10,.82);
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
    transition: all .35s ease;
}
.overlay.open {
    opacity: 1;
    visibility: visible;
    pointer-events: auto;
}
.modal {
    width: min(480px, 100%);
    max-height: calc(100vh - 40px);
    overflow-y: auto;
    padding: 26px;
    background: linear-gradient(180deg, rgba(22,26,40,.98), rgba(14,18,30,.98));
    border: 1px solid var(--glass-border);
    border-radius: 26px;
    box-shadow:
        0 0 0 1px rgba(255,255,255,.04),
        0 40px 100px rgba(0,0,0,.7),
        var(--glow-accent);
    opacity: 0;
    transform: translateY(20px) scale(.95);
    transition: all .45s var(--ease);
}
.overlay.open .modal {
    opacity: 1;
    transform: translateY(0) scale(1);
}
.modal-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 21px;
}
.modal-title { font-size: 17px; font-weight: 800; letter-spacing: -.02em; }
.modal-subtitle { margin-top: 5px; color: var(--muted); font-size: 10px; line-height: 1.5; }
.modal-close {
    width: 34px;
    height: 34px;
    display: grid;
    place-items: center;
    color: var(--muted);
    background: rgba(10,14,24,.8);
    border: 1px solid var(--glass-border);
    border-radius: 11px;
    transition: all .3s var(--ease);
}
.modal-close:hover {
    color: #fff;
    background: rgba(110,231,255,.12);
    border-color: rgba(110,231,255,.35);
    transform: rotate(90deg);
}
.modal-close svg { width: 15px; height: 15px; }

/* Tabs */
.tabs {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 5px;
    padding: 4px;
    margin-bottom: 20px;
    background: rgba(4,6,12,.8);
    border: 1px solid var(--glass-border);
    border-radius: 14px;
}
.tab {
    height: 37px;
    color: var(--muted);
    background: transparent;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 700;
    transition: all .3s var(--ease);
}
.tab:hover { color: #ccc; }
.tab.active {
    color: #fff;
    background: rgba(110,231,255,.12);
    box-shadow: 0 5px 15px rgba(110,231,255,.15);
}
.tab:active { transform: scale(.97); }

/* Form */
.form-section { display: none; }
.form-section.active { display: block; animation: sectionIn .35s var(--ease); }
@keyframes sectionIn {
    from { opacity: 0; transform: translateY(5px); }
    to   { opacity: 1; transform: translateY(0); }
}
.field { margin-bottom: 15px; }
.field label {
    display: block;
    margin-bottom: 7px;
    color: var(--muted);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
}
.input, .select {
    width: 100%;
    height: 43px;
    padding: 0 13px;
    color: #fff;
    background: rgba(4,6,12,.6);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    outline: none;
    transition: all .3s var(--ease);
}
.input::placeholder { color: var(--muted-2); }
.input:focus, .select:focus {
    background: rgba(4,6,12,.9);
    border-color: rgba(110,231,255,.45);
    box-shadow: 0 0 0 3px rgba(110,231,255,.08);
}
.select {
    appearance: none;
    -webkit-appearance: none;
    cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%238f97ab' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 13px center;
    padding-right: 38px;
}
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 11px; }
.validation-note {
    display: flex;
    align-items: flex-start;
    gap: 9px;
    margin-top: 3px;
    padding: 12px;
    color: var(--muted);
    background: rgba(4,6,12,.5);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    font-size: 9px;
    line-height: 1.55;
}
.validation-note svg {
    width: 14px;
    height: 14px;
    flex: 0 0 auto;
    margin-top: 1px;
    color: var(--muted);
}
.modal-footer { display: flex; gap: 9px; margin-top: 21px; }
.cancel-btn, .submit-btn {
    height: 43px;
    border-radius: 12px;
    font-size: 10px;
    font-weight: 750;
    transition: all .3s var(--ease);
}
.cancel-btn {
    flex: 1;
    color: var(--muted);
    background: rgba(10,14,24,.8);
    border: 1px solid var(--glass-border);
}
.cancel-btn:hover {
    color: #fff;
    background: rgba(110,231,255,.08);
    border-color: rgba(110,231,255,.3);
    transform: translateY(-2px);
}
.submit-btn {
    flex: 1.5;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: #04060c;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
    border: none;
    box-shadow: 0 4px 16px rgba(110,231,255,.25);
}
.submit-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(167,139,250,.4);
    filter: brightness(1.08);
}
.submit-btn:active, .cancel-btn:active { transform: scale(.97); }
.submit-btn:disabled {
    cursor: not-allowed;
    opacity: .55;
    transform: none;
    box-shadow: none;
}
.submit-btn svg { width: 14px; height: 14px; }

/* Spinner */
.spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(0,0,0,.18);
    border-top-color: #000;
    border-radius: 50%;
    animation: spin .7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Toast */
.toast-container {
    position: fixed;
    right: 20px;
    bottom: 20px;
    z-index: 200;
    display: flex;
    flex-direction: column;
    gap: 8px;
    pointer-events: none;
}
.toast {
    min-width: 250px;
    max-width: 360px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px;
    color: #ddd;
    background: rgba(22,26,40,.96);
    border: 1px solid var(--glass-border);
    border-radius: 13px;
    box-shadow: 0 18px 45px rgba(0,0,0,.55);
    opacity: 0;
    transform: translateY(12px) scale(.96);
    transition: all .35s var(--ease);
}
.toast.show { opacity: 1; transform: translateY(0) scale(1); }
.toast-icon {
    width: 18px;
    height: 18px;
    display: grid;
    place-items: center;
    flex: 0 0 auto;
    color: var(--green);
}
.toast.error .toast-icon { color: var(--red); }
.toast-icon svg { width: 16px; height: 16px; }
.toast-message { font-size: 10px; line-height: 1.4; font-weight: 600; }

/* Refresh indicator */
.refresh-indicator {
    position: fixed;
    top: 80px;
    right: 20px;
    z-index: 40;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: rgba(22,26,40,.88);
    border: 1px solid var(--glass-border);
    border-radius: 999px;
    font-size: 10px;
    font-weight: 650;
    color: var(--muted);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: all .3s ease;
    pointer-events: none;
    opacity: 0.9;
}
.refresh-indicator .refresh-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 10px var(--accent);
    animation: refreshPulse 5s ease-in-out infinite;
}
@keyframes refreshPulse {
    0%   { transform: scale(.6); opacity: .5; }
    5%   { transform: scale(1.3); opacity: 1; }
    15%  { transform: scale(1); opacity: 1; }
    100% { transform: scale(.6); opacity: .5; }
}
.refresh-indicator.refreshing {
    border-color: rgba(110,231,255,.45);
    color: var(--accent);
}

/* Responsive */
@media (max-width: 900px) {
    .global-controls { display: none; }
    .refresh-indicator { top: 70px; right: 14px; }
}
@media (max-width: 800px) {
    .header { padding: 0 18px; }
    .stats-row, .accounts-section { padding-left: 18px; padding-right: 18px; }
    .accounts-grid { grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }
}
@media (max-width: 620px) {
    .header { height: 60px; }
    .brand-by { display: none; }
    .add-btn { height: 37px; padding: 0 13px; }
    .stats-row { grid-template-columns: 1fr; gap: 10px; padding-top: 16px; }
    .stat-card { min-height: 92px; }
    .accounts-section { padding-top: 22px; }
    .accounts-grid { grid-template-columns: 1fr; }
    .modal { padding: 20px; border-radius: 22px; }
    .form-grid { grid-template-columns: 1fr; gap: 0; }
    .modal-footer { flex-direction: column-reverse; }
    .cancel-btn, .submit-btn { width: 100%; }
    .toast-container { left: 15px; right: 15px; bottom: 15px; }
    .toast { min-width: 0; width: 100%; }
    .refresh-indicator { top: 68px; right: 10px; font-size: 9px; padding: 5px 10px; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        scroll-behavior: auto !important;
        animation-duration: .01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: .01ms !important;
    }
}
    </style>
</head>

<body>

    <div class="refresh-indicator" id="refreshIndicator">
        <span class="refresh-dot"></span>
        <span id="refreshText">Auto 5s</span>
    </div>

    <header class="header">
        <div class="brand">
            <svg class="brand-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M13 2L4 13H11L10 22L20 10H13L13 2Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div class="brand-text">
                <span class="brand-name">AFX LEVEL UP</span>
                <span class="brand-by">by NexZone</span>
            </div>
        </div>

        <div class="global-controls">
            <select class="global-mode-select" id="globalModeSelect" onchange="setGlobalMode(this.value, this)" title="Change mode for all accounts">
                <option value="">Select mode for all</option>
                <option value="MIX">All: 50/50 Mix (LW + BR)</option>
                <option value="BR">All: Battle Royale</option>
                <option value="LONE_WOLF">All: Lone Wolf</option>
            </select>

            <div class="exp-limit-wrap limit-active" id="expLimitWrap" title="Auto-delete the account when it gains this many EXP. Set 0 to disable.">
                <span class="exp-limit-label">EXP:</span>
                <input type="number" class="exp-limit-input" id="expLimitInput" placeholder="45000" min="0" step="1000" onkeydown="expLimitKeydown(event)" title="Auto-delete threshold (EXP gained)">
                <button class="exp-limit-btn" id="expLimitBtn" type="button" onclick="setExpLimit()">Set</button>
            </div>

            <div class="toggle-container" onclick="document.getElementById('globalToggle').click()">
                <span class="toggle-label">BOT</span>
                <label class="toggle-switch" onclick="event.stopPropagation()">
                    <input type="checkbox" id="globalToggle" checked onchange="toggleGlobal(this)" title="ON: start matches / OFF: pause all">
                    <span class="toggle-slider"></span>
                </label>
                <span id="toggleStatus" class="toggle-status on">ON</span>
            </div>
        </div>

        <div class="header-actions">
            <button class="add-btn" id="reloadJsonBtn" type="button" title="Reload accounts from accounts*.json (clears blacklist)">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" width="15" height="15" stroke-width="2.2" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
                    <path d="M3 3v5h5"/>
                </svg>
                <span>Reload JSON</span>
            </button>

            <button class="add-btn" id="openModalBtn" type="button">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 5V19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <path d="M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <span>Add Bot</span>
            </button>
        </div>
    </header>

    <main class="main">
        <section class="stats-row">
            <div class="stat-card">
                <span class="stat-label">Total Accounts</span>
                <span class="stat-value" id="totalAccounts">0</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Matches Played</span>
                <span class="stat-value" id="matchesPlayed">0</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">EXP Gained</span>
                <span class="stat-value" id="expGained">0</span>
            </div>
        </section>

        <section class="accounts-section">
            <div class="section-header">
                <span class="section-title">Accounts</span>
                <span class="account-count" id="accountCountText">0 / 1</span>
            </div>
            <div class="accounts-grid" id="accountsGrid"></div>
        </section>
    </main>

    <div class="overlay" id="modalOverlay" aria-hidden="true">
        <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
            <div class="modal-header">
                <div>
                    <h2 class="modal-title" id="modalTitle">Add New Bot</h2>
                    <p class="modal-subtitle">Connect a Free Fire account to start monitoring.</p>
                </div>
                <button class="modal-close" id="closeModalBtn" type="button" aria-label="Close">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        <path d="M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>

            <div class="tabs">
                <button class="tab active" data-tab="guest" type="button">Guest Account</button>
                <button class="tab" data-tab="token" type="button">Access Token</button>
            </div>

            <form class="form-section active" id="guestForm" data-form="guest">
                <div class="field">
                    <label for="uid">UID</label>
                    <input class="input" id="uid" name="uid" type="text" inputmode="numeric" autocomplete="off" placeholder="Enter player UID">
                </div>
                <div class="field">
                    <label for="password">Password</label>
                    <input class="input" id="password" name="password" type="password" autocomplete="off" placeholder="Enter account password">
                </div>
                <div class="field">
                    <label for="guestRegion">Server Region</label>
                    <select class="select" id="guestRegion" name="region">
                        <option value="BD">Bangladesh</option>
                        <option value="IND">India</option>
                        <option value="SG">Singapore</option>
                        <option value="ID">Indonesia</option>
                        <option value="BR">Brazil</option>
                        <option value="US">United States</option>
                    </select>
                </div>
            </form>

            <form class="form-section" id="tokenForm" data-form="token">
                <div class="field">
                    <label for="accessToken">Access Token</label>
                    <input class="input" id="accessToken" name="token" type="text" autocomplete="off" placeholder="Paste access token">
                </div>
                <div class="field">
                    <label for="tokenRegion">Server Region</label>
                    <select class="select" id="tokenRegion" name="region">
                        <option value="BD">Bangladesh</option>
                        <option value="IND">India</option>
                        <option value="SG">Singapore</option>
                        <option value="ID">Indonesia</option>
                        <option value="BR">Brazil</option>
                        <option value="US">United States</option>
                    </select>
                </div>
            </form>

            <div class="validation-note">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.7"/>
                    <path d="M12 10V16" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
                    <circle cx="12" cy="7" r="1" fill="currentColor"/>
                </svg>
                <span>Credentials are validated before the bot starts. Only one active slot is available per account.</span>
            </div>

            <div class="modal-footer">
                <button class="cancel-btn" id="cancelBtn" type="button">Cancel</button>
                <button class="submit-btn" id="submitBtn" type="button">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 3V21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                        <path d="M5 12H19" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    </svg>
                    <span>Validate & Start</span>
                </button>
            </div>
        </div>
    </div>

    <div class="toast-container" id="toastContainer"></div>

    <script>
        const EXP_LIST = [
            {level:1,exp:0},{level:2,exp:48},{level:3,exp:202},{level:4,exp:544},
            {level:5,exp:1012},{level:6,exp:1844},{level:7,exp:2792},{level:8,exp:3800},
            {level:9,exp:4870},{level:10,exp:6004},{level:11,exp:7192},{level:12,exp:8448},
            {level:13,exp:9760},{level:14,exp:11140},{level:15,exp:12566},{level:16,exp:14060},
            {level:17,exp:15610},{level:18,exp:17224},{level:19,exp:18902},{level:20,exp:20632},
            {level:21,exp:22424},{level:22,exp:24278},{level:23,exp:26192},{level:24,exp:28166},
            {level:25,exp:30200},{level:26,exp:32294},{level:27,exp:34448},{level:28,exp:37804},
            {level:29,exp:41274},{level:30,exp:44870},{level:31,exp:48582},{level:32,exp:53394},
            {level:33,exp:58566},{level:34,exp:64096},{level:35,exp:69994},{level:36,exp:76260},
            {level:37,exp:83506},{level:38,exp:91128},{level:39,exp:99322},{level:40,exp:108092},
            {level:41,exp:120144},{level:42,exp:133266},{level:43,exp:147472},{level:44,exp:162760},
            {level:45,exp:179126},{level:46,exp:196572},{level:47,exp:215368},{level:48,exp:235316},
            {level:49,exp:257010},{level:50,exp:279860},{level:51,exp:304056},{level:52,exp:348318},
            {level:53,exp:394982},{level:54,exp:444044},{level:55,exp:495508},{level:56,exp:549364},
            {level:57,exp:633756},{level:58,exp:721744},{level:59,exp:813336},{level:60,exp:908522},
            {level:61,exp:1041438},{level:62,exp:1180352},{level:63,exp:1325266},{level:64,exp:1476184},
            {level:65,exp:1634300},{level:66,exp:1840946},{level:67,exp:2056594},{level:68,exp:2281242},
            {level:69,exp:2514880},{level:70,exp:2757530},{level:71,exp:3059506},{level:72,exp:3372284},
            {level:73,exp:3699456},{level:74,exp:4041030},{level:75,exp:4397002},{level:76,exp:4829104},
            {level:77,exp:5282204},{level:78,exp:5756304},{level:79,exp:6251404},{level:80,exp:6767502},
            {level:81,exp:7381324},{level:82,exp:8043154},{level:83,exp:8752982},{level:84,exp:9510808},
            {level:85,exp:10316638},{level:86,exp:11277190},{level:87,exp:12291748},{level:88,exp:13360304},
            {level:89,exp:14482858},{level:90,exp:15659418},{level:91,exp:17026708},{level:92,exp:18453990},
            {level:93,exp:19941280},{level:94,exp:21488570},{level:95,exp:23095858},{level:96,exp:24763138},
            {level:97,exp:26490428},{level:98,exp:28277708},{level:99,exp:30124996},{level:100,exp:32032284}
        ];

        const API = {
            stats: "/api/stats",
            add: "/api/account/add",
            delete: "/api/account/delete",
            refresh: "/api/account/refresh",
            reload: "/api/accounts/reload",
            matchType: "/api/account/match-type",
            toggleGlobal: "/api/bot/toggle",
            setAllMode: "/api/accounts/set-all-mode",
            setExpLimit: "/api/settings/exp-limit"
        };

        const REFRESH_INTERVAL_MS = 5000;

        let currentTab = "guest";
        let refreshTimer = null;
        let _globalRunning = true;
        let _refreshCountdown = 5;

        const modalOverlay = document.getElementById("modalOverlay");
        const openModalBtn = document.getElementById("openModalBtn");
        const closeModalBtn = document.getElementById("closeModalBtn");
        const cancelBtn = document.getElementById("cancelBtn");
        const submitBtn = document.getElementById("submitBtn");
        const accountsGrid = document.getElementById("accountsGrid");
        const totalAccounts = document.getElementById("totalAccounts");
        const matchesPlayed = document.getElementById("matchesPlayed");
        const expGained = document.getElementById("expGained");
        const accountCountText = document.getElementById("accountCountText");
        const refreshIndicator = document.getElementById("refreshIndicator");
        const refreshText = document.getElementById("refreshText");

        function escapeHTML(value) {
            return String(value ?? "")
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function formatNumber(value) {
            const number = Number(value);
            if (!Number.isFinite(number)) return "0";
            return number.toLocaleString();
        }

        function normalizeStatus(status) {
            const value = String(status || "ONLINE").toUpperCase().replace(/\\s+/g, "_");
            if (value === "CONNECTING") return { label: "CONNECTING", className: "searching" };
            if (value === "SEARCHING" || value === "SEARCH") return { label: "SEARCHING", className: "searching" };
            if (value === "IN_MATCH" || value === "MATCH" || value === "PLAYING") return { label: "IN MATCH", className: "in-match" };
            if (value === "OFFLINE" || value === "DISCONNECTED") return { label: "OFFLINE", className: "offline" };
            if (value === "ERROR" || value === "FAILED") return { label: "ERROR", className: "error" };
            if (value === "PAUSED" || value === "STOPPED") return { label: "PAUSED", className: "paused" };
            return { label: "ONLINE", className: "online" };
        }

        function openModal() {
            modalOverlay.classList.add("open");
            modalOverlay.setAttribute("aria-hidden", "false");
            document.body.classList.add("modal-open");
            setTimeout(() => {
                const input = currentTab === "guest" ? document.getElementById("uid") : document.getElementById("accessToken");
                input?.focus();
            }, 180);
        }

        function closeModal() {
            modalOverlay.classList.remove("open");
            modalOverlay.setAttribute("aria-hidden", "true");
            document.body.classList.remove("modal-open");
            resetForms();
        }

        function resetForms() {
            document.getElementById("guestForm").reset();
            document.getElementById("tokenForm").reset();
            currentTab = "guest";
            document.querySelectorAll(".tab").forEach(tab => {
                tab.classList.toggle("active", tab.dataset.tab === "guest");
            });
            document.querySelectorAll(".form-section").forEach(section => {
                section.classList.toggle("active", section.dataset.form === "guest");
            });
            setSubmitLoading(false);
        }

        openModalBtn.addEventListener("click", openModal);
        closeModalBtn.addEventListener("click", closeModal);
        cancelBtn.addEventListener("click", closeModal);

        document.getElementById("reloadJsonBtn").addEventListener("click", async () => {
            const btn = document.getElementById("reloadJsonBtn");
            const originalText = btn.querySelector("span").textContent;
            btn.disabled = true;
            btn.querySelector("span").textContent = "Reloading...";
            try {
                const response = await fetch(API.reload, { method: "POST" });
                const data = await response.json().catch(() => ({}));
                if (data.status === "ok") {
                    showToast(data.message || "Accounts reloaded from JSON.");
                } else {
                    showToast(data.error || "Reload failed.", true);
                }
                await fetchStats();
            } catch (err) {
                showToast("Reload request failed.", true);
            } finally {
                btn.disabled = false;
                btn.querySelector("span").textContent = originalText;
            }
        });

        modalOverlay.addEventListener("click", event => {
            if (event.target === modalOverlay) closeModal();
        });

        document.addEventListener("keydown", event => {
            if (event.key === "Escape" && modalOverlay.classList.contains("open")) closeModal();
        });

        document.querySelectorAll(".tab").forEach(tab => {
            tab.addEventListener("click", () => {
                currentTab = tab.dataset.tab;
                document.querySelectorAll(".tab").forEach(item => {
                    item.classList.toggle("active", item === tab);
                });
                document.querySelectorAll(".form-section").forEach(section => {
                    section.classList.toggle("active", section.dataset.form === currentTab);
                });
            });
        });

        function setSubmitLoading(loading) {
            submitBtn.disabled = loading;
            if (loading) {
                submitBtn.innerHTML = '<span class="spinner"></span><span>Validating...</span>';
            } else {
                submitBtn.innerHTML = `
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 3V21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                        <path d="M5 12H19" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    </svg>
                    <span>Validate & Start</span>`;
            }
        }

        submitBtn.addEventListener("click", async () => {
            const payload = {};
            if (currentTab === "guest") {
                const uid = document.getElementById("uid").value.trim();
                const password = document.getElementById("password").value.trim();
                const region = document.getElementById("guestRegion").value;
                if (!uid) { showToast("Please enter the UID.", true); return; }
                if (!password) { showToast("Please enter the password.", true); return; }
                payload.type = "guest"; payload.uid = uid; payload.password = password; payload.region = region;
            } else {
                const token = document.getElementById("accessToken").value.trim();
                const region = document.getElementById("tokenRegion").value;
                if (!token) { showToast("Please enter the access token.", true); return; }
                payload.type = "token"; payload.token = token; payload.region = region;
            }
            setSubmitLoading(true);
            try {
                const response = await fetch(API.add, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || data.success === false) {
                    throw new Error(data.message || data.error || "Failed to add account.");
                }
                showToast(data.message || "Bot added successfully.");
                closeModal();
                await fetchStats();
            } catch (error) {
                showToast(error.message || "Something went wrong.", true);
            } finally {
                setSubmitLoading(false);
            }
        });

        async function fetchStats() {
            try {
                refreshIndicator.classList.add("refreshing");
                const response = await fetch(API.stats, { cache: "no-store" });
                if (!response.ok) throw new Error("Failed to fetch stats.");
                const data = await response.json();
                const accounts = Array.isArray(data.accounts) ? data.accounts : [];

                totalAccounts.textContent = formatNumber(data.total_accounts ?? data.totalAccounts ?? accounts.length);
                matchesPlayed.textContent = formatNumber(data.total_matches ?? data.matches_played ?? data.matchesPlayed ?? 0);
                expGained.textContent = formatNumber(data.total_gained_exp ?? data.exp_gained ?? data.expGained ?? 0);

                const totalAcc = data.total_accounts ?? data.totalAccounts ?? accounts.length;
                accountCountText.textContent = `${accounts.length} / ${totalAcc}`;

                renderAccounts(accounts);

                if (data.global_running !== undefined && data.global_running !== _globalRunning) {
                    _globalRunning = data.global_running;
                    const toggle = document.getElementById("globalToggle");
                    const statusEl = document.getElementById("toggleStatus");
                    if (toggle) toggle.checked = _globalRunning;
                    if (statusEl) {
                        statusEl.textContent = _globalRunning ? "ON" : "OFF";
                        statusEl.className = "toggle-status " + (_globalRunning ? "on" : "off");
                    }
                }

                if (data.exp_limit !== undefined) {
                    const input = document.getElementById("expLimitInput");
                    if (input && input.dataset.saved === undefined) {
                        input.value = data.exp_limit;
                        input.dataset.saved = data.exp_limit;
                        updateExpLimitStyle(data.exp_limit);
                    }
                }

                _refreshCountdown = 5;
                refreshText.textContent = "Auto 5s";
            } catch (error) {
                console.error("Stats error:", error);
            } finally {
                setTimeout(() => refreshIndicator.classList.remove("refreshing"), 400);
            }
        }

        function updateCardInPlace(card, account) {
            const rawStatus = account.status;
            const status = normalizeStatus(rawStatus);
            const statusEl = card.querySelector(".status");
            if (statusEl) {
                statusEl.className = "status " + status.className;
                const lblEl = statusEl.querySelector("span:last-child");
                if (lblEl) lblEl.textContent = status.label;
            }

            const expCurrent = account.current_exp ?? account.exp_current ?? account.exp ?? 0;
            const expInitial = account.initial_exp ?? 0;
            const expGainedAcc = account.gained_exp ?? Math.max(0, expCurrent - expInitial);
            const cols = card.querySelectorAll(".exp-col-value");
            if (cols[0]) cols[0].textContent = formatNumber(expInitial);
            if (cols[1]) cols[1].textContent = formatNumber(expCurrent);
            if (cols[2]) cols[2].textContent = "+" + formatNumber(expGainedAcc) + " EXP";

            const level = account.level ?? account.lvl ?? 0;
            const matches = account.matches_played ?? account.matches ?? 0;
            const lvNum = Number(level);
            const expLabelEl = card.querySelector(".exp-label");
            if (expLabelEl) expLabelEl.textContent = "Level " + escapeHTML(level);
            const expValEl = card.querySelector(".exp-value");
            if (expValEl) expValEl.textContent = "Matches: " + formatNumber(matches);

            const curEntry = EXP_LIST.find(e => e.level === lvNum);
            const nextEntry = EXP_LIST.find(e => e.level === lvNum + 1);
            let percentage = 0;
            if (curEntry && nextEntry) {
                const rangeTotal = nextEntry.exp - curEntry.exp;
                const rangeProgress = Number(expCurrent) - curEntry.exp;
                percentage = rangeTotal > 0 ? Math.min(100, Math.max(0, (rangeProgress / rangeTotal) * 100)) : 0;
            } else if (curEntry && !nextEntry) {
                percentage = 100;
            }
            const progressBar = card.querySelector(".progress-bar");
            if (progressBar) progressBar.style.width = percentage + "%";

            let errEl = card.querySelector(".acc-error");
            if (account.last_error) {
                if (!errEl) {
                    errEl = document.createElement("div");
                    errEl.className = "acc-error";
                    const matchRow = card.querySelector(".match-type-row");
                    if (matchRow) matchRow.before(errEl);
                }
                errEl.textContent = account.last_error;
            } else if (errEl) {
                errEl.remove();
            }
            let infoEl = card.querySelector(".acc-info");
            if (account.last_info) {
                if (!infoEl) {
                    infoEl = document.createElement("div");
                    infoEl.className = "acc-info";
                    const matchRow = card.querySelector(".match-type-row");
                    if (matchRow) matchRow.before(infoEl);
                }
                infoEl.textContent = account.last_info;
            } else if (infoEl) {
                infoEl.remove();
            }

            const sel = card.querySelector(".match-type-select");
            if (sel) {
                const mt = account.match_type || "LONE_WOLF";
                if (sel.value !== mt) sel.value = mt;
                sel.className = "match-type-select " + (mt === "BR" ? "br-mode" : (mt === "MIX" ? "mix-mode" : "lw-mode"));
            }

            const lastMatchVal = card.querySelector(".last-match-value");
            if (lastMatchVal) {
                const lm = account.last_match_time ?? account.last_match ?? account.lastMatch ?? "No match yet";
                lastMatchVal.textContent = escapeHTML(lm);
            }
        }

        function renderAccounts(accounts) {
            if (!accounts.length) {
                accountsGrid.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" stroke="currentColor" stroke-width="1.7"/>
                                <path d="M4.5 20C5.4 16.8 8.1 15 12 15C15.9 15 18.6 16.8 19.5 20" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
                            </svg>
                        </div>
                        <div class="empty-title">No bots connected</div>
                        <div class="empty-text">Add a Free Fire account to start monitoring matches and EXP.</div>
                    </div>`;
                return;
            }

            const sorted = [...accounts].sort((a, b) => Number(b.level ?? 0) - Number(a.level ?? 0));

            const existingCards = {};
            accountsGrid.querySelectorAll(".account-card[data-card-uid]").forEach(card => {
                existingCards[card.dataset.cardUid] = card;
            });

            const newUidSet = new Set(sorted.map(acc =>
                String(acc.uid ?? acc.player_uid ?? acc.playerId ?? "")
            ));

            Object.keys(existingCards).forEach(uid => {
                if (!newUidSet.has(uid)) existingCards[uid].remove();
            });

            sorted.forEach((account, index) => {
                const uid = String(account.uid ?? account.player_uid ?? account.playerId ?? "");
                if (existingCards[uid]) {
                    updateCardInPlace(existingCards[uid], account);
                } else {
                    const tmpl = document.createElement("template");
                    tmpl.innerHTML = createAccountCard(account, index).trim();
                    const newCard = tmpl.content.firstElementChild;
                    accountsGrid.appendChild(newCard);
                }
            });
        }

        function createAccountCard(account, index) {
            const rawStatus = account.status;
            const status = normalizeStatus(rawStatus);

            const level = account.level ?? account.lvl ?? 0;
            const matches = account.matches_played ?? account.matches ?? 0;
            const exp = account.exp ?? account.experience ?? 0;
            const expCurrent = account.current_exp ?? account.exp_current ?? exp;
            const expInitial = account.initial_exp ?? 0;
            const expGainedAcc = account.gained_exp ?? Math.max(0, expCurrent - expInitial);

            const lvNum = Number(level);
            const curEntry = EXP_LIST.find(e => e.level === lvNum);
            const nextEntry = EXP_LIST.find(e => e.level === lvNum + 1);
            let percentage = 0;
            if (curEntry && nextEntry) {
                const rangeTotal = nextEntry.exp - curEntry.exp;
                const rangeProgress = Number(expCurrent) - curEntry.exp;
                percentage = rangeTotal > 0 ? Math.min(100, Math.max(0, (rangeProgress / rangeTotal) * 100)) : 0;
            } else if (curEntry && !nextEntry) {
                percentage = 100;
            }

            const nickname = escapeHTML(account.nickname ?? account.name ?? "Unknown");
            const uid = escapeHTML(account.uid ?? account.player_uid ?? account.playerId ?? "-");
            const lastMatch = escapeHTML(account.last_match_time ?? account.last_match ?? account.lastMatch ?? "No match yet");
            const safeUid = encodeURIComponent(account.uid ?? account.player_uid ?? account.playerId ?? "");
            const mt = account.match_type || "LONE_WOLF";

            return `
                <article class="account-card" data-card-uid="${uid}" style="--index:${index}">
                    <div class="account-top">
                        <div class="account-identity">
                            <div class="avatar">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" stroke="currentColor" stroke-width="1.7"/>
                                    <path d="M4.5 20C5.4 16.8 8.1 15 12 15C15.9 15 18.6 16.8 19.5 20" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>
                                </svg>
                            </div>
                            <div class="identity-info">
                                <div class="nickname">${nickname}</div>
                                <div class="uid">UID ${uid}</div>
                            </div>
                        </div>
                        <div class="status ${status.className}">
                            <span class="status-dot"></span>
                            <span>${status.label}</span>
                        </div>
                    </div>

                    <div class="exp-three-col">
                        <div class="exp-col">
                            <div class="exp-col-label">Initial EXP</div>
                            <div class="exp-col-value">${formatNumber(expInitial)}</div>
                        </div>
                        <div class="exp-col">
                            <div class="exp-col-label">Current EXP</div>
                            <div class="exp-col-value">${formatNumber(expCurrent)}</div>
                        </div>
                        <div class="exp-col">
                            <div class="exp-col-label">EXP Gained</div>
                            <div class="exp-col-value gained">+${formatNumber(expGainedAcc)} EXP</div>
                        </div>
                    </div>

                    <div class="exp-header">
                        <span class="exp-label">Level ${escapeHTML(level)}</span>
                        <span class="exp-value">Matches: ${formatNumber(matches)}</span>
                    </div>

                    <div class="progress">
                        <div class="progress-bar" style="width:${percentage}%"></div>
                    </div>

                    ${account.last_error ? `<div class="acc-error">${escapeHTML(account.last_error)}</div>` : ""}
                    ${account.last_info ? `<div class="acc-info">${escapeHTML(account.last_info)}</div>` : ""}

                    <div class="match-type-row">
                        <span class="match-type-label">Match</span>
                        <select class="match-type-select ${mt === 'BR' ? 'br-mode' : (mt === 'MIX' ? 'mix-mode' : 'lw-mode')}"
                                data-uid="${safeUid}"
                                onchange="setMatchType('${safeUid}', this.value, this)"
                                title="Select match mode">
                            <option value="LONE_WOLF" ${mt === 'LONE_WOLF' ? 'selected' : ''}>Lone Wolf</option>
                            <option value="BR" ${mt === 'BR' ? 'selected' : ''}>Battle Royale</option>
                            <option value="MIX" ${mt === 'MIX' ? 'selected' : ''}>50/50 Mix (LW + BR)</option>
                        </select>
                    </div>

                    <div class="account-footer">
                        <div class="last-match">
                            <div class="last-match-label">Last Match</div>
                            <div class="last-match-value">${lastMatch}</div>
                        </div>
                        <div class="card-actions">
                            <button class="icon-btn" type="button" title="Refresh" aria-label="Refresh account" onclick="refreshAccount('${safeUid}')">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M20 11A8.1 8.1 0 0 0 5.5 6.5L4 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M4 4V8H8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M4 13A8.1 8.1 0 0 0 18.5 17.5L20 16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M20 20V16H16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            </button>
                            <button class="icon-btn delete" type="button" title="Delete" aria-label="Delete account" onclick="deleteAccount('${safeUid}')">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M4 7H20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                                    <path d="M9 7V4H15V7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                                    <path d="M7 7L8 20H16L17 7" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
                                    <path d="M10 11V16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                    <path d="M14 11V16" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </article>`;
        }

        async function toggleGlobal(checkbox) {
            const running = checkbox.checked;
            const statusEl = document.getElementById("toggleStatus");
            const prevChecked = !running;
            try {
                const response = await fetch(API.toggleGlobal, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ running })
                });
                const data = await response.json().catch(() => ({}));
                if (data.status === "ok") {
                    _globalRunning = running;
                    statusEl.textContent = running ? "ON" : "OFF";
                    statusEl.className = "toggle-status " + (running ? "on" : "off");
                    showToast(running ? "All bots resumed." : "All bots paused.");
                    await fetchStats();
                } else {
                    checkbox.checked = prevChecked;
                    showToast("Toggle failed: " + (data.error || "unknown"), true);
                }
            } catch (e) {
                checkbox.checked = prevChecked;
                showToast("Network error: " + e.message, true);
            }
        }

        async function setGlobalMode(mode, selectEl) {
            if (!mode) return;
            try {
                const response = await fetch(API.setAllMode, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ mode })
                });
                const data = await response.json().catch(() => ({}));
                if (data.status === "ok") {
                    const label = mode === "BR" ? "All: Battle Royale"
                                : mode === "LONE_WOLF" ? "All: Lone Wolf"
                                : "All: 50/50 Mix";
                    showToast("Mode updated: " + label);
                    await fetchStats();
                } else {
                    showToast("Mode change failed: " + (data.error || "unknown"), true);
                    if (selectEl) selectEl.value = "";
                }
            } catch (e) {
                showToast("Network error: " + e.message, true);
                if (selectEl) selectEl.value = "";
            }
        }

        async function setExpLimit() {
            const input = document.getElementById("expLimitInput");
            const btn = document.getElementById("expLimitBtn");
            if (!input) return;
            const raw = input.value.trim().replace(/,/g, "");
            const limit = parseInt(raw, 10);
            if (isNaN(limit) || limit < 0) {
                showToast("Enter a valid number (0 = disable).", true);
                return;
            }
            btn.disabled = true;
            btn.textContent = "...";
            try {
                const res = await fetch(API.setExpLimit, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ exp_limit: limit })
                });
                const data = await res.json().catch(() => ({}));
                if (data.status === "ok") {
                    const msg = limit === 0
                        ? "EXP limit disabled."
                        : `EXP limit set to ${limit.toLocaleString()}.`;
                    showToast(msg);
                    input.dataset.saved = limit;
                    updateExpLimitStyle(limit);
                } else {
                    showToast(data.error || "Unknown error", true);
                }
            } catch (e) {
                showToast("Network error: " + e.message, true);
            } finally {
                btn.disabled = false;
                btn.textContent = "Set";
            }
        }

        function updateExpLimitStyle(limit) {
            const wrap = document.getElementById("expLimitWrap");
            const input = document.getElementById("expLimitInput");
            if (!wrap || !input) return;
            wrap.classList.remove("limit-active", "limit-off");
            if (limit > 0) {
                wrap.classList.add("limit-active");
                input.title = `Auto-delete at ${Number(limit).toLocaleString()} EXP gained`;
            } else {
                wrap.classList.add("limit-off");
                input.title = "EXP limit disabled (0 = no limit)";
            }
        }

        function expLimitKeydown(e) {
            if (e.key === "Enter") setExpLimit();
        }

        async function setMatchType(uid, matchType, selectEl) {
            try {
                const response = await fetch(API.matchType, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        uid: decodeURIComponent(uid),
                        match_type: matchType
                    })
                });
                const data = await response.json();
                if (data.status === "ok") {
                    if (selectEl) {
                        selectEl.classList.remove("br-mode", "lw-mode", "mix-mode");
                        selectEl.classList.add(matchType === "BR" ? "br-mode" : (matchType === "MIX" ? "mix-mode" : "lw-mode"));
                    }
                    const label = matchType === "BR" ? "Battle Royale"
                                : matchType === "MIX" ? "50/50 Mix"
                                : "Lone Wolf";
                    showToast(`UID ${decodeURIComponent(uid)} set to ${label}.`);
                } else {
                    showToast("Match type change failed: " + (data.error || "unknown"), true);
                    if (selectEl) selectEl.value = "LONE_WOLF";
                }
            } catch (e) {
                showToast("Network error: " + e.message, true);
            }
        }

        async function refreshAccount(uid) {
            try {
                const response = await fetch(API.refresh, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ uid: decodeURIComponent(uid) })
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || data.success === false) {
                    throw new Error(data.message || data.error || "Failed to refresh account.");
                }
                showToast(data.message || "Account refreshed.");
                await fetchStats();
            } catch (error) {
                showToast(error.message || "Refresh failed.", true);
            }
        }

        async function deleteAccount(uid) {
            const decodedUid = decodeURIComponent(uid);
            const confirmed = window.confirm("Delete this bot account?");
            if (!confirmed) return;
            try {
                const response = await fetch(API.delete, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ uid: decodedUid })
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || data.success === false) {
                    throw new Error(data.message || data.error || "Failed to delete account.");
                }
                showToast(data.message || "Account deleted.");
                await fetchStats();
            } catch (error) {
                showToast(error.message || "Delete failed.", true);
            }
        }

        function showToast(message, isError = false) {
            const toast = document.createElement("div");
            toast.className = `toast${isError ? " error" : ""}`;
            toast.innerHTML = `
                <div class="toast-icon">
                    ${isError
                        ? '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8"/><path d="M12 8V13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="16.5" r="1" fill="currentColor"/></svg>'
                        : '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'}
                </div>
                <div class="toast-message">${escapeHTML(message)}</div>`;
            document.getElementById("toastContainer").appendChild(toast);
            requestAnimationFrame(() => toast.classList.add("show"));
            setTimeout(() => {
                toast.classList.remove("show");
                setTimeout(() => toast.remove(), 400);
            }, 3200);
        }

        function startCountdownTicker() {
            setInterval(() => {
                _refreshCountdown--;
                if (_refreshCountdown <= 0) _refreshCountdown = 5;
                if (refreshText) refreshText.textContent = `Auto ${_refreshCountdown}s`;
            }, 1000);
        }

        fetchStats();
        startCountdownTicker();
        refreshTimer = setInterval(fetchStats, REFRESH_INTERVAL_MS);
    </script>

</body>
</html>
"""


# ==================== GLOBAL BOT STATE ====================
class BotState:
    def __init__(self):
        self.accounts: Dict[str, Dict[str, Any]] = {}
        self.logs: List[Dict[str, Any]] = []
        self.max_logs = 200
        self.total_matches = 0
        self.total_gained_exp = 0
        self.start_time = time.time()
        self.account_workers: Dict[str, asyncio.Task] = {}
        self.refresh_callbacks: Dict[str, Any] = {}
        self.account_credentials: Dict[str, Dict[str, Any]] = {}
        # Blacklist (deleted UIDs)
        self.deleted_uids: set = set()
        # Per-UID forced mode ("BR", "LONE_WOLF", "MIX")
        self.match_types: Dict[str, str] = {}
        # MIX rotation cursor: uid -> "LONE_WOLF" | "BR"
        self._current_mode: Dict[str, str] = {}
        # Global ON/OFF
        self.global_running: bool = True
        # Auto-delete threshold
        self.exp_limit: int = 45000
        self.auto_delete_queue: set = set()

    # ---------- MODE MANAGEMENT ----------
    def set_match_type(self, uid: str, match_type: str):
        """Force a specific mode for a UID: 'BR', 'LONE_WOLF', or 'MIX'."""
        uid_str = str(uid)
        allowed = {"BR", "LONE_WOLF", "MIX"}
        if match_type not in allowed:
            match_type = "LONE_WOLF"
        self.match_types[uid_str] = match_type
        if uid_str in self.accounts:
            self.accounts[uid_str]["match_type"] = match_type
            self.accounts[uid_str]["last_updated"] = time.strftime("%H:%M:%S")
        # Fresh MIX rotation starts from LONE_WOLF
        if match_type == "MIX":
            self._current_mode[uid_str] = "LONE_WOLF"

    def get_match_type(self, uid: str) -> str:
        """
        Returns the mode for the NEXT match search.

        Priority order:
          1) matches_played < BR_UNLOCK_MATCHES  -> BR  (LW is locked until level 3)
          2) account has explicit MIX mode       -> alternate LW / BR
          3) account has explicit BR / LONE_WOLF -> that mode
          4) default                              -> LONE_WOLF
        """
        uid_str = str(uid)

        # Rule #1: mandatory BR at startup
        played = 0
        if uid_str in self.accounts:
            played = int(self.accounts[uid_str].get("matches_played", 0) or 0)
        if played < BR_UNLOCK_MATCHES:
            return "BR"

        # Rule #2 and #3
        mt = self.match_types.get(uid_str, DEFAULT_MATCH_MODE)
        if mt == "MIX":
            return self._current_mode.get(uid_str, "LONE_WOLF")
        return mt

    def advance_match_mode(self, uid: str) -> None:
        """Called when a match actually begins; flips MIX cursor if applicable."""
        uid_str = str(uid)
        mt = self.match_types.get(uid_str, DEFAULT_MATCH_MODE)
        if mt != "MIX":
            return
        current = self._current_mode.get(uid_str, "LONE_WOLF")
        self._current_mode[uid_str] = "BR" if current == "LONE_WOLF" else "LONE_WOLF"

    def get_account_level(self, uid: str) -> int:
        uid_str = str(uid)
        if uid_str in self.accounts:
            return int(self.accounts[uid_str].get("level", 1) or 1)
        return 1

    # ---------- AUTO-DELETE ----------
    async def _async_auto_delete(self, uid_str: str):
        try:
            short_key = uid_str.replace("tok_", "")[:10]
            self.accounts.pop(uid_str, None)
            self.recalc_totals()

            for accounts_file in get_all_account_files_dashboard():
                if not os.path.exists(accounts_file):
                    continue
                try:
                    with open(accounts_file, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                    if not isinstance(existing, list):
                        continue
                    new_list = [
                        acc for acc in existing
                        if str(acc.get("uid", "")).strip() != uid_str
                        and str(acc.get("token", ""))[:10] != short_key
                    ]
                    if len(new_list) < len(existing):
                        tmp_file = accounts_file + ".tmp"
                        with open(tmp_file, "w", encoding="utf-8") as f:
                            json.dump(new_list, f, indent=2, ensure_ascii=False)
                        os.replace(tmp_file, accounts_file)
                except Exception:
                    pass

            for worker_key in [uid_str, short_key]:
                if worker_key in self.account_workers:
                    task = self.account_workers.pop(worker_key)
                    task.cancel()
                    try:
                        await asyncio.wait_for(asyncio.shield(task), timeout=3.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                        pass

            self.auto_delete_queue.discard(uid_str)
            self.log(f"[AUTO-DELETE] UID {uid_str} reached the EXP limit and was removed.", "warning", uid_str)
        except Exception as e:
            self.log(f"[AUTO-DELETE ERROR] UID {uid_str}: {e}", "error", uid_str)

    # ---------- LOGGING ----------
    def log(self, message: str, level: str = "info", uid: Optional[str] = None):
        entry = {
            "time": time.strftime("%H:%M:%S"),
            "level": level,
            "message": message,
            "uid": uid,
        }
        self.logs.append(entry)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

    # ---------- REGISTRATION ----------
    def register_account(self, uid: str, nickname: str, region: str, level: int, exp: int, likes: int = 0):
        uid_str = str(uid)
        if uid_str in self.deleted_uids:
            return
        if uid_str not in self.accounts:
            self.accounts[uid_str] = {
                "uid": uid_str,
                "nickname": nickname or f"Player_{uid_str[:6]}",
                "region": region or "BD",
                "level": level or 1,
                "initial_exp": exp,
                "current_exp": exp,
                "gained_exp": 0,
                "likes": likes or 0,
                "status": "ONLINE",
                "matches_played": 0,
                "active_matches": 0,
                "last_match_time": None,
                "last_updated": time.strftime("%H:%M:%S"),
                "match_type": self.match_types.get(uid_str, DEFAULT_MATCH_MODE),
            }
        else:
            acc = self.accounts[uid_str]
            if nickname:
                acc["nickname"] = nickname
            if region:
                acc["region"] = region
            if level:
                acc["level"] = level
            acc["current_exp"] = exp
            acc["gained_exp"] = max(0, exp - acc["initial_exp"])
            acc["likes"] = likes
            acc["status"] = "ONLINE"
            acc["last_updated"] = time.strftime("%H:%M:%S")
        self.recalc_totals()

    def update_exp(self, uid: str, current_exp: int, level: Optional[int] = None):
        uid_str = str(uid)
        if uid_str in self.deleted_uids:
            return
        if uid_str in self.accounts:
            acc = self.accounts[uid_str]
            old_exp = acc["current_exp"]
            acc["current_exp"] = current_exp
            if level is not None and level > 0:
                acc["level"] = level
            acc["gained_exp"] = max(0, current_exp - acc["initial_exp"])
            acc["last_updated"] = time.strftime("%H:%M:%S")
            diff = current_exp - old_exp
            if diff > 0:
                self.log(f"{acc['nickname']} ({uid_str}) gained +{diff} EXP (total +{acc['gained_exp']}).", "success", uid_str)
            self.recalc_totals()

            if self.exp_limit > 0 and acc["gained_exp"] >= self.exp_limit and uid_str not in self.auto_delete_queue:
                self.auto_delete_queue.add(uid_str)
                nickname = acc.get("nickname", uid_str)
                self.log(
                    f"[AUTO-DELETE] {nickname} ({uid_str}) reached {acc['gained_exp']} EXP (limit: {self.exp_limit}). Deleting...",
                    "warning", uid_str,
                )
                self.deleted_uids.add(uid_str)
                self.match_types.pop(uid_str, None)
                self._current_mode.pop(uid_str, None)
                try:
                    asyncio.get_event_loop().create_task(self._async_auto_delete(uid_str))
                except RuntimeError:
                    pass

    def update_status(self, uid: str, status: str, active_matches: Optional[int] = None):
        uid_str = str(uid)
        if uid_str in self.deleted_uids:
            return
        if uid_str in self.accounts:
            self.accounts[uid_str]["status"] = status
            if status in ("ONLINE", "IN_MATCH", "SEARCHING"):
                self.accounts[uid_str].pop("last_error", None)
            if active_matches is not None:
                self.accounts[uid_str]["active_matches"] = active_matches
            self.accounts[uid_str]["last_updated"] = time.strftime("%H:%M:%S")

    def set_error(self, uid: str, message: str):
        uid_str = str(uid)
        if uid_str in self.deleted_uids:
            return
        if uid_str in self.accounts:
            self.accounts[uid_str]["last_error"] = f"{time.strftime('%H:%M:%S')} - {message}"[:300]

    def set_info(self, uid: str, message: str):
        uid_str = str(uid)
        if uid_str in self.deleted_uids:
            return
        if uid_str in self.accounts:
            self.accounts[uid_str]["last_info"] = f"{time.strftime('%H:%M:%S')} - {message}"[:300]

    def increment_match(self, uid: str):
        uid_str = str(uid)
        self.total_matches += 1
        if uid_str in self.accounts:
            self.accounts[uid_str]["matches_played"] += 1
            self.accounts[uid_str]["last_match_time"] = time.strftime("%H:%M:%S")
            self.accounts[uid_str]["last_updated"] = time.strftime("%H:%M:%S")
            self.log(f"{self.accounts[uid_str]['nickname']} finished match #{self.accounts[uid_str]['matches_played']}.", "info", uid_str)

    def recalc_totals(self):
        self.total_gained_exp = sum(acc.get("gained_exp", 0) for acc in self.accounts.values())


bot_state = BotState()


# ==================== HTTP HANDLERS ====================
async def handle_index(request: web.Request) -> web.Response:
    return web.Response(text=DASHBOARD_HTML, content_type="text/html", charset="utf-8")


async def handle_get_stats(request: web.Request) -> web.Response:
    accounts_data = list(bot_state.accounts.values())
    accounts_data.sort(key=lambda x: x.get("gained_exp", 0), reverse=True)
    return web.json_response({
        "total_accounts": len(bot_state.accounts),
        "total_matches": bot_state.total_matches,
        "total_gained_exp": bot_state.total_gained_exp,
        "accounts": accounts_data,
        "logs": bot_state.logs[-60:],
        "uptime": int(time.time() - bot_state.start_time),
        "global_running": bot_state.global_running,
        "exp_limit": bot_state.exp_limit,
    })


async def handle_add_account(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        accounts_file = ACCOUNTS_FILE_PATH
        existing = []
        if os.path.exists(accounts_file):
            try:
                with open(accounts_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        if "uid" in data and "password" in data:
            uid = str(data["uid"]).strip()
            pwd = str(data["password"]).strip()
            if not uid or not pwd:
                return web.json_response({"status": "error", "error": "UID and Password are required"})
            existing = [acc for acc in existing if str(acc.get("uid")) != uid]
            existing.append({"uid": uid, "password": pwd})
            bot_state.deleted_uids.discard(uid)
        elif "token" in data:
            token = str(data["token"]).strip()
            if not token:
                return web.json_response({"status": "error", "error": "Token is required"})
            existing = [acc for acc in existing if acc.get("token") != token]
            existing.append({"token": token})
            bot_state.deleted_uids.discard(token[:10])
            bot_state.deleted_uids.discard(f"tok_{token[:10]}")
        else:
            return web.json_response({"status": "error", "error": "Invalid payload"})

        with open(accounts_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        bot_state.log(f"New account added: {data.get('uid') or 'Token'}", "success")

        if "on_account_added" in bot_state.refresh_callbacks:
            asyncio.create_task(bot_state.refresh_callbacks["on_account_added"](data))

        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


async def handle_delete_account(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        uid = str(data.get("uid", "")).strip()
        if not uid:
            return web.json_response({"status": "error", "error": "uid missing"})

        short_key = uid.replace("tok_", "")[:10]

        for accounts_file in get_all_account_files_dashboard():
            if not os.path.exists(accounts_file):
                continue
            try:
                with open(accounts_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if not isinstance(existing, list):
                    continue
                new_list = [
                    acc for acc in existing
                    if str(acc.get("uid", "")).strip() != uid
                    and str(acc.get("token", ""))[:10] != short_key
                ]
                if len(new_list) < len(existing):
                    tmp_file = accounts_file + ".tmp"
                    with open(tmp_file, "w", encoding="utf-8") as f:
                        json.dump(new_list, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_file, accounts_file)
            except Exception:
                pass

        bot_state.deleted_uids.add(uid)
        bot_state.deleted_uids.add(short_key)

        if uid in bot_state.accounts:
            del bot_state.accounts[uid]
            bot_state.recalc_totals()

        for worker_key in [uid, short_key]:
            if worker_key in bot_state.account_workers:
                task = bot_state.account_workers.pop(worker_key)
                task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=3.0)
                except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
                    pass

        bot_state.log(f"Account {uid} deleted.", "warning", uid)
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


async def handle_refresh_account(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        uid = str(data.get("uid")).strip()
        if "on_refresh_account" in bot_state.refresh_callbacks:
            asyncio.create_task(bot_state.refresh_callbacks["on_refresh_account"](uid))
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


async def handle_reload_accounts(request: web.Request) -> web.Response:
    try:
        cleared = len(bot_state.deleted_uids)
        bot_state.deleted_uids.clear()

        added = 0
        if "on_reload_accounts" in bot_state.refresh_callbacks:
            added = await bot_state.refresh_callbacks["on_reload_accounts"]()

        msg = f"Reload complete: {cleared} blacklisted UID(s) cleared, {added} new account(s) started."
        bot_state.log(msg, "success")
        return web.json_response({"status": "ok", "message": msg, "cleared": cleared, "started": added})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})


async def handle_set_match_type(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        uid = str(data.get("uid", "")).strip()
        match_type = str(data.get("match_type", "LONE_WOLF")).strip().upper()
        if not uid:
            return web.json_response({"status": "error", "error": "UID required"}, status=400)
        if match_type not in ("BR", "LONE_WOLF", "MIX"):
            return web.json_response({"status": "error", "error": "Invalid match_type. Use BR, LONE_WOLF, or MIX."}, status=400)
        bot_state.set_match_type(uid, match_type)
        label = "Battle Royale" if match_type == "BR" else ("50/50 Mix" if match_type == "MIX" else "Lone Wolf")
        bot_state.log(f"[MODE] UID {uid} -> {label}", "info", uid)
        return web.json_response({"status": "ok", "uid": uid, "match_type": match_type})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_toggle_global(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        running = bool(data.get("running", True))
        bot_state.global_running = running
        state_str = "ON" if running else "OFF"
        bot_state.log(f"[GLOBAL] Bot state set to {state_str}.", "success" if running else "warning")

        if not running:
            for uid_str in list(bot_state.accounts.keys()):
                if uid_str not in bot_state.deleted_uids:
                    status = bot_state.accounts[uid_str].get("status", "ONLINE")
                    if status not in ("OFFLINE", "ERROR", "CONNECTING"):
                        bot_state.accounts[uid_str]["status"] = "PAUSED"
        else:
            for uid_str in list(bot_state.accounts.keys()):
                if uid_str not in bot_state.deleted_uids:
                    if bot_state.accounts[uid_str].get("status") == "PAUSED":
                        bot_state.accounts[uid_str]["status"] = "ONLINE"

        return web.json_response({"status": "ok", "running": running})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_all_mode(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        mode = str(data.get("mode", "LONE_WOLF")).strip().upper()
        if mode not in ("BR", "LONE_WOLF", "MIX"):
            return web.json_response({"status": "error", "error": "Invalid mode. Use BR, LONE_WOLF, or MIX."}, status=400)

        changed = 0
        for uid_str in list(bot_state.accounts.keys()):
            if uid_str not in bot_state.deleted_uids:
                bot_state.set_match_type(uid_str, mode)
                changed += 1
        label = "Battle Royale" if mode == "BR" else ("50/50 Mix" if mode == "MIX" else "Lone Wolf")
        bot_state.log(f"[GLOBAL MODE] All {changed} account(s) -> {label}.", "success")
        return web.json_response({"status": "ok", "mode": mode, "changed": changed})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def handle_set_exp_limit(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        raw = data.get("exp_limit", None)
        if raw is None:
            return web.json_response({"status": "error", "error": "exp_limit missing"}, status=400)
        try:
            limit = int(str(raw).strip().replace(",", ""))
        except (ValueError, TypeError):
            return web.json_response({"status": "error", "error": "exp_limit must be a number"}, status=400)
        if limit < 0:
            return web.json_response({"status": "error", "error": "exp_limit cannot be negative"}, status=400)
        bot_state.exp_limit = limit
        msg = f"EXP limit set to {limit:,}." if limit > 0 else "EXP limit disabled."
        bot_state.log(f"[EXP LIMIT] {msg}", "success")
        return web.json_response({"status": "ok", "exp_limit": limit})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500)


async def start_web_dashboard(host: str = "0.0.0.0", port: int = 5000):
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/stats", handle_get_stats)
    app.router.add_post("/api/account/add", handle_add_account)
    app.router.add_post("/api/account/delete", handle_delete_account)
    app.router.add_post("/api/account/refresh", handle_refresh_account)
    app.router.add_post("/api/accounts/reload", handle_reload_accounts)
    app.router.add_post("/api/account/match-type", handle_set_match_type)
    app.router.add_post("/api/bot/toggle", handle_toggle_global)
    app.router.add_post("/api/accounts/set-all-mode", handle_set_all_mode)
    app.router.add_post("/api/settings/exp-limit", handle_set_exp_limit)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    print(f"\033[92m[+] Web Dashboard running on http://localhost:{port}\033[0m")
