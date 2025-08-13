HANDDRAWN_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Patrick+Hand:wght@400&family=Caveat:wght@700&display=swap');

  /* 手繪風格：柔和色、紙張紋理背景、略帶歪斜的邊框 */
  html, body, .main { background-color: #FAF7F2; }
  h1, h2, h3, .sketch-title { font-family: 'Patrick Hand', 'Caveat', ui-rounded, system-ui, -apple-system; letter-spacing: .5px; }
  body, p, label, span, div { color:#1b1b1b; font-size: 16px; }
  .contrast { color:#0d0d0d; font-weight:800; }

  .paper {
    background: #fff url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%228%22 height=%228%22><rect width=%228%22 height=%228%22 fill=%22%23fff%22/><circle cx=%224%22 cy=%224%22 r=%220.2%22 fill=%22%23e5e1dc%22/></svg>') repeat;
    padding: 14px 16px; border: 2px dashed #2f2f2f; border-radius: 16px;
    box-shadow: 4px 4px 0 #2f2f2f; margin-bottom: 14px;
  }

  .sketch-button {
    background: #FDECC8; border: 2px solid #2f2f2f; border-radius: 16px;
    box-shadow: 3px 3px 0 #2f2f2f; color: #1d1d1d; font-weight: 700;
    padding: 6px 12px; display: inline-block;
  }

  .pill {
    display: inline-block; padding: 6px 10px; margin: 4px;
    border: 2px dotted #2f2f2f; border-radius: 999px; background: #FFF9E9;
    box-shadow: 2px 2px 0 #2f2f2f; font-family: 'Patrick Hand', system-ui;
  }

  .sketch-title { font-weight: 900; color: #1b1b1b; }
  .tip { background: #EFF8FF; border-left: 6px solid #7FB3FF; padding: 8px 10px; border-radius: 6px; }
  .small { font-size: 12px; color: #666; }
  .code { background: #272822; color: #f8f8f2; padding: 2px 6px; border-radius: 6px; }

  /* Streamlit 控件輕度手繪化 */
  .stButton > button { border: 2px solid #2f2f2f !important; border-radius: 12px !important; box-shadow: 3px 3px 0 #2f2f2f !important; background: #FDECC8 !important; color: #1d1d1d !important; font-weight: 700; }
  .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb] {
    border: 2px dashed #2f2f2f !important; border-radius: 12px !important;
    background: #fff !important;
    color:#1b1b1b !important;
  }
  /* 修正 multiselect 標籤文字太暗問題 */
  .stMultiSelect [data-baseweb="tag"] {
    background: #FFF9E9 !important; color:#1b1b1b !important; border:2px dotted #2f2f2f !important;
  }
  .stMultiSelect [data-baseweb="tag"] * { color:#1b1b1b !important; }
  .stToggle { border:2px dashed #2f2f2f !important; }
</style>
"""

__all__ = ["HANDDRAWN_CSS"]
