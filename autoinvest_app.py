
import streamlit as st
import json
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from groq import Groq

st.set_page_config(
    page_title="AutoInvest AI",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #0a0f1e; }
  h1 { font-family: 'Space Mono', monospace; color: #00e5a0 !important; }
  h2, h3 { color: #c8d8f0 !important; }
  .signal-buy  { background:#0d3b2a; border:1.5px solid #00e5a0; border-radius:12px; padding:20px; text-align:center; }
  .signal-sell { background:#3b0d0d; border:1.5px solid #ff4d6d; border-radius:12px; padding:20px; text-align:center; }
  .signal-hold { background:#2a2a0d; border:1.5px solid #ffd700; border-radius:12px; padding:20px; text-align:center; }
  .signal-label { font-family:'Space Mono',monospace; font-size:2rem; font-weight:700; letter-spacing:4px; }
  .buy-label  { color:#00e5a0; }
  .sell-label { color:#ff4d6d; }
  .hold-label { color:#ffd700; }
  .info-card { background:#111827; border-radius:10px; padding:16px; border:1px solid #1f2d45; margin-bottom:10px; }
  .mono { font-family:'Space Mono',monospace; font-size:0.85rem; color:#8ab4f8; }
  .metric-card { background:#111827; border-radius:10px; padding:14px; border:1px solid #1f2d45; text-align:center; }
  div[data-testid="stButton"] button {
    background: linear-gradient(135deg,#00e5a0,#0088cc);
    color: #0a0f1e; font-weight:700; border:none;
    font-family:'Space Mono',monospace; letter-spacing:2px;
    padding: 0.6rem 2rem; border-radius:8px; width:100%; font-size:1rem;
  }
  .disclaimer { font-size:0.75rem; color:#4a5568; text-align:center; margin-top:1rem; }
  .risk-badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:600; margin:2px; }
  .risk-high   { background:#3b0d0d; color:#ff4d6d; border:1px solid #ff4d6d; }
  .risk-medium { background:#2a2a0d; color:#ffd700; border:1px solid #ffd700; }
  .risk-low    { background:#0d3b2a; color:#00e5a0; border:1px solid #00e5a0; }
  .hist-buy  { color:#00e5a0; font-weight:700; }
  .hist-sell { color:#ff4d6d; font-weight:700; }
  .hist-hold { color:#ffd700; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ── Inisialisasi session state ────────────────────────────────────────────────
if "signal_history" not in st.session_state:
    st.session_state.signal_history = []

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 📈 AutoInvest AI")
st.markdown(
    "<p style='color:#8ab4f8;font-size:1rem;margin-top:-10px;'>"
    "Algorithmic Trading Signal Generator · Powered by Groq AI + Yahoo Finance</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Konfigurasi")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Dapatkan gratis di console.groq.com",
    )
    st.markdown("---")
    st.markdown("**Daftar Saham BEI Populer**")
    st.markdown("""
<small style='color:#8ab4f8;'>
BBCA.JK · BBRI.JK · TLKM.JK<br>
GOTO.JK · BMRI.JK · ASII.JK<br>
UNVR.JK · INDF.JK · KLBF.JK
</small>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        "<small style='color:#4a5568;'>Tugas Inovasi & Entrepreneur KA · UGM 2026</small>",
        unsafe_allow_html=True,
    )

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 Analisis Sinyal", "📊 Multi Saham", "📋 Histori Sinyal"])

# ════════════════════════════════════════════════════════════════
# TAB 1 — Analisis Sinyal + Candlestick
# ════════════════════════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### 📊 Input Data Saham")
        saham = st.text_input(
            "Kode Saham (format Yahoo Finance)",
            value="BBCA.JK",
            placeholder="Contoh: BBCA.JK, TLKM.JK, GOTO.JK",
            help="Tambahkan .JK untuk saham BEI",
        )
        periode = st.selectbox(
            "Periode Data Historis",
            ["1mo", "3mo", "6mo"],
            format_func=lambda x: {"1mo":"1 Bulan","3mo":"3 Bulan","6mo":"6 Bulan"}[x],
        )
        risk_tolerance = st.select_slider(
            "Toleransi Risiko Investor",
            options=["Sangat Konservatif","Konservatif","Moderat","Agresif","Sangat Agresif"],
            value="Moderat",
        )
        horizon = st.selectbox("Horizon Trading", [
            "Intraday (< 1 hari)",
            "Swing (2–5 hari)",
            "Jangka Menengah (1–4 minggu)",
        ])

    with col_right:
        st.markdown("### 📡 Data Real-time")
        if saham:
            try:
                ticker = yf.Ticker(saham)
                info   = ticker.info
                hist   = ticker.history(period=periode)

                if not hist.empty:
                    harga_terakhir = hist["Close"].iloc[-1]
                    harga_kemarin  = hist["Close"].iloc[-2]
                    volume_terakhir = hist["Volume"].iloc[-1]
                    perubahan = ((harga_terakhir - harga_kemarin) / harga_kemarin) * 100

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#8ab4f8;font-size:0.8rem;margin:0;'>Harga Terakhir</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#00e5a0;font-size:1.4rem;font-weight:700;margin:0;'>Rp {harga_terakhir:,.0f}</p>", unsafe_allow_html=True)
                        warna = "#00e5a0" if perubahan >= 0 else "#ff4d6d"
                        st.markdown(f"<p style='color:{warna};font-size:0.9rem;margin:0;'>{perubahan:+.2f}%</p>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    with c2:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#8ab4f8;font-size:0.8rem;margin:0;'>Volume</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#c8d8f0;font-size:1.1rem;font-weight:700;margin:0;'>{volume_terakhir:,.0f}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#8ab4f8;font-size:0.8rem;margin:0;'>{saham.upper()}</p>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Hitung RSI
                    delta  = hist["Close"].diff()
                    gain   = delta.clip(lower=0).rolling(14).mean()
                    loss   = (-delta.clip(upper=0)).rolling(14).mean()
                    rs     = gain / loss
                    rsi_val = float(100 - (100 / (1 + rs.iloc[-1])))

                    # Hitung MA
                    ma20 = hist["Close"].rolling(20).mean().iloc[-1]
                    ma50 = hist["Close"].rolling(50).mean().iloc[-1] if len(hist) >= 50 else None

                    st.markdown("<br>", unsafe_allow_html=True)
                    c3, c4 = st.columns(2)
                    with c3:
                        rsi_color = "#ff4d6d" if rsi_val > 70 else "#00e5a0" if rsi_val < 30 else "#ffd700"
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#8ab4f8;font-size:0.8rem;margin:0;'>RSI (14)</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:{rsi_color};font-size:1.4rem;font-weight:700;margin:0;'>{rsi_val:.1f}</p>", unsafe_allow_html=True)
                        label = "Overbought" if rsi_val > 70 else "Oversold" if rsi_val < 30 else "Normal"
                        st.markdown(f"<p style='color:{rsi_color};font-size:0.8rem;margin:0;'>{label}</p>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    with c4:
                        if ma50:
                            ma_label = "Bullish" if ma20 > ma50 else "Bearish"
                            ma_color = "#00e5a0" if ma20 > ma50 else "#ff4d6d"
                        else:
                            ma_label = "Data kurang"
                            ma_color = "#ffd700"
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#8ab4f8;font-size:0.8rem;margin:0;'>MA Trend</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:{ma_color};font-size:1.4rem;font-weight:700;margin:0;'>{ma_label}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:#8ab4f8;font-size:0.8rem;margin:0;'>MA20 vs MA50</p>", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                else:
                    st.warning("⚠️ Data tidak ditemukan. Pastikan kode saham benar (contoh: BBCA.JK)")
                    harga_terakhir = harga_kemarin = volume_terakhir = rsi_val = 0
                    ma20 = ma50 = None
                    hist = pd.DataFrame()

            except Exception as e:
                st.error(f"❌ Gagal fetch data: {str(e)}")
                harga_terakhir = harga_kemarin = volume_terakhir = rsi_val = 0
                ma20 = ma50 = None
                hist = pd.DataFrame()

    # ── Grafik Candlestick ────────────────────────────────────────
    if not hist.empty:
        st.markdown("### 🕯️ Grafik Candlestick")
        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist["Open"], high=hist["High"],
            low=hist["Low"],   close=hist["Close"],
            name="Harga",
            increasing_line_color="#00e5a0",
            decreasing_line_color="#ff4d6d",
        ))

        # MA20
        ma20_line = hist["Close"].rolling(20).mean()
        fig.add_trace(go.Scatter(
            x=hist.index, y=ma20_line,
            name="MA20", line=dict(color="#ffd700", width=1.5),
        ))

        # MA50
        if len(hist) >= 50:
            ma50_line = hist["Close"].rolling(50).mean()
            fig.add_trace(go.Scatter(
                x=hist.index, y=ma50_line,
                name="MA50", line=dict(color="#8ab4f8", width=1.5),
            ))

        fig.update_layout(
            paper_bgcolor="#0a0f1e",
            plot_bgcolor="#0a0f1e",
            font=dict(color="#c8d8f0"),
            xaxis=dict(gridcolor="#1f2d45", rangeslider_visible=False),
            yaxis=dict(gridcolor="#1f2d45"),
            legend=dict(bgcolor="#111827", bordercolor="#1f2d45"),
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Tombol Generate ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("🤖 GENERATE TRADING SIGNAL", use_container_width=True, key="btn_single")

    # ── Fungsi AI ─────────────────────────────────────────────────
    def build_prompt(saham, harga_terakhir, harga_kemarin, volume, rsi, ma_trend, risk_tolerance, horizon):
        perubahan = ((harga_terakhir - harga_kemarin) / harga_kemarin) * 100 if harga_kemarin else 0
        return f"""Kamu adalah sistem AI algorithmic trading (AutoInvest AI) untuk Bursa Efek Indonesia.
Analisislah data pasar berikut dan hasilkan sinyal trading yang tepat.

DATA PASAR:
- Kode Saham: {saham}
- Harga Terakhir: Rp {harga_terakhir:,.0f}
- Harga Kemarin: Rp {harga_kemarin:,.0f}
- Perubahan: {perubahan:+.2f}%
- Volume: {volume:,.0f}
- RSI (14): {rsi:.1f} {'(Overbought)' if rsi > 70 else '(Oversold)' if rsi < 30 else '(Normal)'}
- Tren MA: {ma_trend}

PARAMETER INVESTOR:
- Toleransi Risiko: {risk_tolerance}
- Horizon: {horizon}

Format JSON PERSIS (hanya JSON):
{{
  "signal": "BUY" atau "SELL" atau "HOLD",
  "confidence": angka 1-100,
  "reasoning": "Penjelasan 2-3 kalimat",
  "key_factors": ["faktor 1", "faktor 2", "faktor 3"],
  "risk_level": "LOW" atau "MEDIUM" atau "HIGH",
  "risk_warning": "Satu kalimat peringatan risiko",
  "suggested_action": "Satu kalimat saran konkret"
}}"""

    def call_groq(prompt, api_key):
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            max_tokens=600,
        )
        return resp.choices[0].message.content

    def parse_json(raw):
        clean = raw.strip()
        if "```" in clean:
            for part in clean.split("```"):
                part = part.strip().lstrip("json").strip()
                if part.startswith("{"):
                    clean = part
                    break
        start, end = clean.find("{"), clean.rfind("}") + 1
        if start != -1 and end > start:
            clean = clean[start:end]
        return json.loads(clean), clean

    def show_result(result, saham, clean):
        signal     = result.get("signal", "HOLD").upper()
        confidence = result.get("confidence", 0)
        risk_level = result.get("risk_level", "MEDIUM").upper()
        css_class   = {"BUY":"signal-buy","SELL":"signal-sell"}.get(signal,"signal-hold")
        label_class = {"BUY":"buy-label","SELL":"sell-label"}.get(signal,"hold-label")
        emoji       = {"BUY":"🟢","SELL":"🔴"}.get(signal,"🟡")

        st.markdown(f"""
<div class="{css_class}">
  <div class="signal-label {label_class}">{emoji} {signal}</div>
  <div style="color:#c8d8f0;margin-top:8px;font-size:0.9rem;">
    Confidence: <strong>{confidence}%</strong> &nbsp;|&nbsp;
    Saham: <strong>{saham.upper()}</strong> &nbsp;|&nbsp;
    {datetime.now().strftime("%d %b %Y, %H:%M")}
  </div>
</div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown("**📝 Reasoning AI**")
            st.markdown(f"<p style='color:#c8d8f0;font-size:0.9rem;'>{result.get('reasoning','')}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with cb:
            st.markdown('<div class="info-card">', unsafe_allow_html=True)
            st.markdown("**⚡ Faktor Kunci**")
            for f in result.get("key_factors", []):
                st.markdown(f"<p class='mono'>▸ {f}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        risk_color = {"HIGH":"risk-high","MEDIUM":"risk-medium","LOW":"risk-low"}.get(risk_level,"risk-medium")
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown(f"**🛡️ Level Risiko:** <span class='risk-badge {risk_color}'>{risk_level}</span>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#ffd700;font-size:0.88rem;margin-top:6px;'>⚠️ {result.get('risk_warning','')}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#00e5a0;font-size:0.88rem;'>💡 {result.get('suggested_action','')}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("🔍 Raw Response AI"):
            st.code(clean, language="json")
        st.markdown("<p class='disclaimer'>⚠️ Prototipe akademis. Bukan rekomendasi investasi nyata.</p>", unsafe_allow_html=True)
        return signal, confidence, risk_level

    if run:
        if not api_key:
            st.error("⚠️ Masukkan Groq API Key di sidebar!")
            st.stop()
        if hist.empty:
            st.error("⚠️ Data saham tidak tersedia. Cek kode saham!")
            st.stop()

        with st.spinner("🔄 Menganalisis data pasar..."):
            try:
                ma_trend_str = "Bullish (MA20 > MA50)" if (ma50 and ma20 > ma50) else "Bearish (MA20 < MA50)" if ma50 else "Sideways"
                prompt = build_prompt(saham, harga_terakhir, harga_kemarin,
                                      volume_terakhir, rsi_val, ma_trend_str,
                                      risk_tolerance, horizon)
                raw = call_groq(prompt, api_key)
                result, clean = parse_json(raw)

                st.markdown("---")
                st.markdown("### 🎯 Hasil Analisis")
                signal, confidence, risk_level = show_result(result, saham, clean)

                # Simpan ke histori
                st.session_state.signal_history.append({
                    "waktu": datetime.now().strftime("%d %b %Y, %H:%M"),
                    "saham": saham.upper(),
                    "signal": signal,
                    "confidence": confidence,
                    "risk": risk_level,
                    "harga": f"Rp {harga_terakhir:,.0f}",
                    "reasoning": result.get("reasoning", ""),
                })

            except json.JSONDecodeError:
                st.error("❌ Parsing error. Coba klik tombol lagi.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# ════════════════════════════════════════════════════════════════
# TAB 2 — Multi Saham
# ════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📊 Perbandingan Multi Saham")
    st.markdown("<p style='color:#8ab4f8;'>Analisis beberapa saham sekaligus dan bandingkan sinyalnya.</p>", unsafe_allow_html=True)

    daftar_saham = st.text_input(
        "Masukkan kode saham (pisahkan dengan koma)",
        value="BBCA.JK, TLKM.JK, BBRI.JK",
        placeholder="BBCA.JK, TLKM.JK, GOTO.JK",
    )
    risk_multi = st.select_slider(
        "Toleransi Risiko",
        options=["Sangat Konservatif","Konservatif","Moderat","Agresif","Sangat Agresif"],
        value="Moderat",
        key="risk_multi",
    )

    run_multi = st.button("🤖 ANALISIS SEMUA SAHAM", use_container_width=True, key="btn_multi")

    if run_multi:
        if not api_key:
            st.error("⚠️ Masukkan Groq API Key di sidebar!")
            st.stop()

        saham_list = [s.strip().upper() for s in daftar_saham.split(",") if s.strip()]
        if not saham_list:
            st.error("⚠️ Masukkan minimal 1 kode saham!")
            st.stop()

        hasil_multi = []
        progress = st.progress(0)
        status   = st.empty()

        for i, kode in enumerate(saham_list):
            status.markdown(f"<p style='color:#8ab4f8;'>🔄 Menganalisis {kode}...</p>", unsafe_allow_html=True)
            try:
                t    = yf.Ticker(kode)
                h    = t.history(period="1mo")
                if h.empty:
                    hasil_multi.append({"Saham": kode, "Signal": "ERROR", "Confidence": "-",
                                        "Harga": "-", "Perubahan": "-", "RSI": "-", "Risiko": "-"})
                    continue

                hp   = float(h["Close"].iloc[-1])
                hk   = float(h["Close"].iloc[-2])
                vol  = float(h["Volume"].iloc[-1])
                pct  = ((hp - hk) / hk) * 100

                delta_h = h["Close"].diff()
                gain_h  = delta_h.clip(lower=0).rolling(14).mean()
                loss_h  = (-delta_h.clip(upper=0)).rolling(14).mean()
                rs_h    = gain_h / loss_h
                rsi_h   = float(100 - (100 / (1 + rs_h.iloc[-1])))

                ma20_h  = float(h["Close"].rolling(20).mean().iloc[-1])
                ma50_h  = float(h["Close"].rolling(50).mean().iloc[-1]) if len(h) >= 50 else None
                ma_str  = "Bullish (MA20 > MA50)" if (ma50_h and ma20_h > ma50_h) else "Bearish" if ma50_h else "Sideways"

                prompt_m = f"""Sistem AI trading AutoInvest AI. Analisis cepat untuk {kode}:
Harga: Rp {hp:,.0f} ({pct:+.2f}%), Volume: {vol:,.0f}, RSI: {rsi_h:.1f}, MA Trend: {ma_str}
Toleransi risiko investor: {risk_multi}
Jawab HANYA JSON: {{"signal":"BUY/SELL/HOLD","confidence":0-100,"risk_level":"LOW/MEDIUM/HIGH","one_line":"satu kalimat alasan"}}"""

                client_m = Groq(api_key=api_key)
                resp_m   = client_m.chat.completions.create(
                    messages=[{"role":"user","content":prompt_m}],
                    model="llama-3.1-8b-instant",
                    max_tokens=150,
                )
                raw_m  = resp_m.choices[0].message.content
                clean_m = raw_m.strip()
                s, e   = clean_m.find("{"), clean_m.rfind("}") + 1
                if s != -1 and e > s:
                    clean_m = clean_m[s:e]
                res_m  = json.loads(clean_m)

                sig_m = res_m.get("signal","HOLD").upper()
                hasil_multi.append({
                    "Saham": kode,
                    "Signal": sig_m,
                    "Confidence": f"{res_m.get('confidence',0)}%",
                    "Harga": f"Rp {hp:,.0f}",
                    "Perubahan": f"{pct:+.2f}%",
                    "RSI": f"{rsi_h:.1f}",
                    "Risiko": res_m.get("risk_level","MEDIUM"),
                    "Alasan": res_m.get("one_line",""),
                })

                # Simpan ke histori
                st.session_state.signal_history.append({
                    "waktu": datetime.now().strftime("%d %b %Y, %H:%M"),
                    "saham": kode,
                    "signal": sig_m,
                    "confidence": res_m.get("confidence", 0),
                    "risk": res_m.get("risk_level","MEDIUM"),
                    "harga": f"Rp {hp:,.0f}",
                    "reasoning": res_m.get("one_line",""),
                })

            except Exception as ex:
                hasil_multi.append({"Saham": kode, "Signal": "ERROR", "Confidence": "-",
                                    "Harga": "-", "Perubahan": "-", "RSI": "-", "Risiko": "-"})

            progress.progress((i + 1) / len(saham_list))

        status.empty()
        progress.empty()

        if hasil_multi:
            st.markdown("### 📋 Hasil Perbandingan")
            for item in hasil_multi:
                sig   = item.get("Signal","HOLD")
                emoji = {"BUY":"🟢","SELL":"🔴"}.get(sig,"🟡")
                warna = {"BUY":"#00e5a0","SELL":"#ff4d6d"}.get(sig,"#ffd700")
                st.markdown(f"""
<div class="info-card" style="border-left: 4px solid {warna};">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <span style="color:#c8d8f0;font-weight:700;font-size:1rem;">{item['Saham']}</span>
    <span style="color:{warna};font-family:'Space Mono',monospace;font-weight:700;font-size:1.1rem;">{emoji} {sig}</span>
    <span style="color:#8ab4f8;font-size:0.85rem;">Confidence: {item.get('Confidence','-')}</span>
  </div>
  <div style="display:flex; gap:16px; margin-top:8px; flex-wrap:wrap;">
    <span class="mono">💰 {item.get('Harga','-')}</span>
    <span class="mono">📈 {item.get('Perubahan','-')}</span>
    <span class="mono">RSI: {item.get('RSI','-')}</span>
    <span class="mono">Risiko: {item.get('Risiko','-')}</span>
  </div>
  <p style="color:#8ab4f8;font-size:0.82rem;margin-top:6px;margin-bottom:0;">{item.get('Alasan','')}</p>
</div>""", unsafe_allow_html=True)

        st.markdown("<p class='disclaimer'>⚠️ Prototipe akademis. Bukan rekomendasi investasi nyata.</p>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# TAB 3 — Histori Sinyal
# ════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📋 Histori Sinyal")

    if not st.session_state.signal_history:
        st.markdown("""
<div class="info-card" style="text-align:center;">
  <p style="color:#8ab4f8;font-size:1rem;">Belum ada sinyal yang di-generate.</p>
  <p style="color:#4a5568;font-size:0.85rem;">Generate sinyal di tab Analisis Sinyal atau Multi Saham.</p>
</div>""", unsafe_allow_html=True)
    else:
        col_info, col_btn = st.columns([3,1])
        with col_info:
            st.markdown(f"<p style='color:#8ab4f8;'>Total sinyal tercatat: <strong>{len(st.session_state.signal_history)}</strong></p>", unsafe_allow_html=True)
        with col_btn:
            if st.button("🗑️ Hapus Histori", key="clear_hist"):
                st.session_state.signal_history = []
                st.rerun()

        for item in reversed(st.session_state.signal_history):
            sig   = item.get("signal","HOLD")
            emoji = {"BUY":"🟢","SELL":"🔴"}.get(sig,"🟡")
            warna = {"BUY":"#00e5a0","SELL":"#ff4d6d"}.get(sig,"#ffd700")
            st.markdown(f"""
<div class="info-card" style="border-left:4px solid {warna};">
  <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
    <span style="color:#c8d8f0;font-weight:700;">{item.get('saham','-')}</span>
    <span style="color:{warna};font-family:'Space Mono',monospace;font-weight:700;">{emoji} {sig}</span>
    <span class="mono">{item.get('harga','-')}</span>
    <span class="mono">Confidence: {item.get('confidence','-')}%</span>
    <span class="mono">Risiko: {item.get('risk','-')}</span>
    <span style="color:#4a5568;font-size:0.8rem;">{item.get('waktu','-')}</span>
  </div>
  <p style="color:#8ab4f8;font-size:0.82rem;margin-top:6px;margin-bottom:0;">{item.get('reasoning','')}</p>
</div>""", unsafe_allow_html=True)