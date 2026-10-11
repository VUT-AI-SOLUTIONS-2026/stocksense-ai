"""Small, static presentation styles for the Streamlit dashboard."""

STYLES = """
<style>
.stApp { background: #f3f6f8; }
.stMainBlockContainer { max-width: 1240px; padding-top: 2rem; padding-bottom: 3rem; }
[data-testid="stHeader"] { background: transparent; }
.ss-hero { background: #153b45; border-radius: 20px; padding: 32px 36px;
    margin-bottom: 24px; color: #fff; }
.ss-eyebrow { color: #99ded5; font-size: 12px; font-weight: 700;
    letter-spacing: 2px; margin-bottom: 12px; }
.ss-hero h1 { color: #fff; font-size: 42px; font-weight: 750; padding: 0;
    line-height: 1.15; margin: 0 0 12px; }
.ss-hero p { color: #dae9ec; font-size: 17px; margin: 0; }
.ss-badges { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }
.ss-badges span { background: #284e57; border: 1px solid #456770;
    border-radius: 24px; padding: 5px 12px; font-size: 12px; color: #edf9f7; }
.st-key-forecast_card, .st-key-planner_card, .st-key-assistant_card {
    border-radius: 16px; border-color: #dde5e9; background: #fff; }
[data-testid="stForm"] { background: #f8fafb; border-radius: 12px; }
[data-testid="stMetric"] { background: #eaf5f2; border: 1px solid #d2e9e1;
    border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; }
[data-testid="stMetricValue"] { color: #145c51; font-size: 30px; }
[data-testid="stMetricLabel"] p { white-space: normal; }
h3 { color: #183b45; font-size: 22px !important; }
.stButton button, .stFormSubmitButton button { border-radius: 9px; font-weight: 600; }
[data-testid="stExpander"] { background: #fff; border-radius: 12px; }
@media (max-width: 640px) {
  .stMainBlockContainer { padding-top: 1rem; }
  .ss-hero { padding: 24px; border-radius: 14px; }
  .ss-hero h1 { font-size: 32px; }
}
</style>
"""

HERO = """
<section class="ss-hero" aria-label="StockSense AI introduction">
  <div class="ss-eyebrow">VUT AI SOLUTIONS · RETAIL PLANNING</div>
  <h1>StockSense AI</h1>
  <p>See the demand ahead. Make your next stock decision.</p>
  <div class="ss-badges"><span>Store 1</span><span>5 items</span>
    <span>7-day forecasts</span><span>Historical demonstration</span></div>
</section>
"""
