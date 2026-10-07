import os
import streamlit as st
import chromadb
from typing import Dict, Any

from services.ai_parliament.parliament import AIParliamentConsensus
from strategies.market_maker_agent import OrderBookDepth

st.set_page_config(
    page_title="AI Quant Fund Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🏛️ برلمان الذكاء الاصطناعي والذاكرة المتجهة (XAI Dashboard)")

chroma_host = os.getenv("CHROMA_HOST", "chromadb")
chroma_port = int(os.getenv("CHROMA_PORT", 8000))

@st.cache_resource
def get_chroma_client():
    try:
        return chromadb.HttpClient(host=chroma_host, port=chroma_port)
    except Exception as e:
        st.error(f"خطأ في الاتصال بـ ChromaDB: {e}")
        return None

chroma_client = get_chroma_client()

st.sidebar.header("⚙️ إعدادات الاختبار")
symbol = st.sidebar.selectbox("الزوج التداولي", ["BTC/USDT", "ETH/USDT", "SOL/USDT"])
macro_trend = st.sidebar.radio("الاتجاه العام (Macro Trend)", ["BULL_TREND", "BEAR_TREND", "SIDEWAYS"])

st.sidebar.subheader("📊 L2 Order Book Depth")
bid_vol = st.sidebar.number_input("حجم طلبات الشراء (Bid Volume)", value=50.0, step=5.0)
ask_vol = st.sidebar.number_input("حجم طلبات البيع (Ask Volume)", value=10.0, step=5.0)

tab1, tab2, tab3 = st.tabs(["🏛️ استجواب البرلمان", "🧠 ذاكرة ChromaDB", "📊 حالة الخدمات"])

with tab1:
    st.subheader("إرسال طلب قرار إلى برلمان الذكاء الاصطناعي")
    if st.button("🚀 تشغيل تصويت البرلمان"):
        mid_price = 65000.0
        depth_data = OrderBookDepth(
            bids=[[mid_price - 10, bid_vol / 2], [mid_price - 20, bid_vol / 2]],
            asks=[[mid_price + 10, ask_vol / 2], [mid_price + 20, ask_vol / 2]]
        )

        parliament = AIParliamentConsensus()
        decision = parliament.get_parliament_decision(symbol, depth_data, macro_trend)

        st.success("تم إصدار قرار البرلمان بنجاح!")
        col1, col2, col3 = st.columns(3)
        col1.metric("القرار النهائي (Consensus)", decision["consensus_action"])
        col2.metric("نسبة الثقة (Confidence)", f"{decision['confidence_score'] * 100:.1f}%")
        col3.metric("مؤشر OBI", decision["mm_agent_signal"]["obi_score"])

        st.json(decision)

        if chroma_client:
            try:
                collection = chroma_client.get_or_create_collection(name="parliament_decisions")
                collection.add(
                    documents=[f"Decision: {decision['consensus_action']} for {symbol} with confidence {decision['confidence_score']}. Reason: {decision['mm_agent_signal']['reasoning']}"],
                    metadatas=[{"symbol": symbol, "action": decision["consensus_action"]}],
                    ids=[f"dec_{os.urandom(4).hex()}"]
                )
                st.info("💾 تم حفظ القرار واستراتيجية التداول في ذاكرة ChromaDB بنجاح!")
            except Exception as e:
                st.warning(f"لم يتم الحفظ في ChromaDB: {e}")

with tab2:
    st.subheader("🔍 استعلام الذاكرة المتجهة (Vector Database Search)")
    search_query = st.text_input("أدخل كلمة البحث في سجل القرارات السابقة:", "Strong Bid Imbalance")
    if st.button("بحث في الذاكرة"):
        if chroma_client:
            try:
                collection = chroma_client.get_or_create_collection(name="parliament_decisions")
                results = collection.query(
                    query_texts=[search_query],
                    n_results=5
                )
                st.write("📋 نتائج البحث من ChromaDB:")
                st.write(results)
            except Exception as e:
                st.error(f"فشل الاستعلام: {e}")

with tab3:
    st.subheader("🔌 حالة الاتصالات الحية")
    if chroma_client:
        try:
            hb = chroma_client.heartbeat()
            st.success(f"ChromaDB Online 🟢 (Heartbeat: {hb})")
        except Exception as e:
            st.error(f"ChromaDB Offline 🔴 ({e})")