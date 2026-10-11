"""Presentation styles for the StockSense dashboard."""

STYLES = """
<style>
.stApp { background: #f5f7fa; color: #172b4d; }
.stMainBlockContainer { max-width: 1320px; padding-top: 1.5rem; padding-bottom: 3rem; }
[data-testid="stHeader"] { background: #f5f7fa; }
.ss-hero { display:flex; align-items:center; justify-content:space-between; gap:24px;
  padding:24px 0 28px; margin-bottom:8px; border-bottom:1px solid #dce3ed; }
.ss-brand { display:flex; align-items:center; gap:18px; }
.ss-mark { display:grid; place-items:center; width:56px; height:56px; flex-shrink:0;
  border-radius:14px; background:#172b4d; color:white; font-weight:750; font-size:20px; }
.ss-eyebrow { color:#607089; font-size:11px; letter-spacing:1.6px; font-weight:700; margin-bottom:6px; }
.ss-hero h1 { color:#172b4d; font-size:32px; font-weight:750; padding:0; margin:0; line-height:1.2; }
.ss-hero p { color:#607089; font-size:14px; margin:8px 0 0; }
.ss-status { white-space:nowrap; border:1px solid #cfe4dd; background:#eaf5f0;
  padding:7px 12px; border-radius:20px; font-size:12px; color:#24654f; }
.ss-kpis { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin:16px 0 24px; }
.ss-kpi { background:white; border:1px solid #dde4ee; border-radius:12px; padding:20px 24px; }
.ss-kpi-label { color:#607089; font-size:12px; font-weight:600; }
.ss-kpi-value { color:#172b4d; font-size:28px; font-weight:750; margin:8px 0 4px; }
.ss-kpi-note { color:#718096; font-size:12px; }
.st-key-forecast_card, .st-key-planner_card, .st-key-assistant_card {
  border-radius:16px; border-color:#dde4ee; background:white; padding:8px;
  box-shadow:0 3px 14px rgba(23,43,77,.025); }
h3 { color:#172b4d; font-size:21px !important; font-weight:700 !important; }
[data-testid="stCaptionContainer"] { color:#607089; }
[data-testid="stForm"] { background:#f8fafc; border-radius:12px; border-color:#e2e8f0; }
[data-testid="stMetric"] { background:#edf5f3; border:1px solid #d7e8e2;
  border-radius:12px; padding:18px 20px; margin-bottom:12px; }
[data-testid="stMetricValue"] { color:#17624e; font-size:30px; }
[data-testid="stMetricLabel"] p { white-space:normal; }
.stButton button, .stFormSubmitButton button { border-radius:10px; font-weight:600; min-height:42px; }
.stButton button:hover { border-color:#23846e; color:#17624e; background:#f1f8f5; }
button:focus-visible, textarea:focus-visible { outline:2px solid #23846e; outline-offset:3px; }
[data-testid="stExpander"] { background:white; border-radius:12px; border-color:#dde4ee; }
.st-key-assistant_card [data-testid="stChatMessage"] { border-radius:12px;
  background:#edf6f2; border:1px solid #daebe3; padding:16px; }
.st-key-assistant_card [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background:#f2f5fa; border-color:#e1e7f0; }
.st-key-assistant_card [data-testid="stChatInput"] { border-radius:12px; border-color:#a8cfc1; }
@media (max-width:850px) {
  [data-testid="stHorizontalBlock"]:has(.st-key-assistant_card) { flex-direction:column; }
  [data-testid="stHorizontalBlock"]:has(.st-key-assistant_card) > [data-testid="stColumn"] { width:100%; flex:1 1 100%; }
}
@media (max-width:640px) {
  .stMainBlockContainer { padding-top:1rem; }
  .ss-hero { align-items:flex-start; flex-direction:column; gap:16px; padding:12px 0 20px; }
  .ss-hero h1 { font-size:26px; }
  .ss-kpis { gap:8px; grid-template-columns:1fr; }
  .ss-kpi { padding:14px 18px; }
  .ss-kpi-value { font-size:24px; }
}
</style>
"""

HERO = """
<header class="ss-hero" aria-label="StockSense AI introduction">
  <div class="ss-brand">
    <div class="ss-mark" aria-hidden="true">SS</div>
    <div><div class="ss-eyebrow">VUT AI SOLUTIONS</div>
      <h1>StockSense AI</h1><p>Sales forecasting &amp; stock planning</p></div>
  </div>
  <span class="ss-status">Historical data · Local demonstration</span>
</header>
"""
