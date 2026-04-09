import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Classificação de Textos", layout="wide")
st.title("Classificação de Textos")
st.caption("Entrada unitária de texto e monitoramento de métricas salvas no banco.")


def get_json(endpoint: str):
    response = requests.get(f"{API_URL}{endpoint}", timeout=60)
    response.raise_for_status()
    return response.json()


tab_input, tab_metrics = st.tabs(["Classificação", "Métricas e KPIs"])

with tab_input:
    st.subheader("Classificação unitária")
    text = st.text_area("Texto recebido", height=220, placeholder="Cole aqui a mensagem a ser classificada...")

    col1, col2 = st.columns([1, 1])
    with col1:
        model_type = st.selectbox("Modelo", options=["local_lr", "openai"])
    with col2:
        save_prediction = st.checkbox("Salvar classificação no banco", value=True)

    if st.button("Classificar texto", use_container_width=True):
        if not text.strip():
            st.warning("Informe um texto para classificar.")
        else:
            payload = {
                "text": text,
                "model_type": model_type,
                "save_prediction": save_prediction,
            }
            try:
                response = requests.post(f"{API_URL}/classify", json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()

                st.success("Classificação concluída.")
                metric_cols = st.columns(4)
                metric_cols[0].metric("Macro", data["macro"])
                metric_cols[1].metric("Confiança macro", f"{data['macro_confidence']:.2%}")
                metric_cols[2].metric("Micro", data["micro"])
                metric_cols[3].metric("Confiança micro", f"{data['micro_confidence']:.2%}")

                st.write(f"**Modelo:** {data['model']}")
                st.write(f"**Ambígua:** {'Sim' if data.get('is_ambiguous') else 'Não'}")

                metadata = data.get("metadata") or {}
                justification = metadata.get("justification")
                if justification:
                    st.info(f"Justificativa curta: {justification}")

                macro_candidates = metadata.get("macro_candidates") or []
                micro_candidates = metadata.get("micro_candidates") or []
                if macro_candidates:
                    st.write("**Top macros sugeridas**")
                    st.dataframe(pd.DataFrame(macro_candidates), use_container_width=True, hide_index=True)
                if micro_candidates:
                    st.write("**Top micros sugeridas**")
                    st.dataframe(pd.DataFrame(micro_candidates), use_container_width=True, hide_index=True)
            except requests.HTTPError:
                try:
                    detail = response.json().get("detail", "Erro ao classificar.")
                except Exception:
                    detail = response.text or "Erro ao classificar."
                st.error(detail)
            except Exception as e:
                st.error(f"Erro de comunicação com a API: {e}")

with tab_metrics:
    st.subheader("KPIs e distribuições")
    if st.button("Atualizar métricas", use_container_width=True):
        st.rerun()

    try:
        summary = get_json("/metrics/summary")
        distributions = get_json("/metrics/distributions")
        predictions = get_json("/predictions?limit=200")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total de classificações", summary["total_predictions"])
        c2.metric("Classificações ambíguas", summary["ambiguous_predictions"])
        c3.metric("Taxa de ambiguidade", f"{summary['ambiguity_rate']:.2%}")
        c4.metric("Confiança média macro", f"{summary['avg_macro_confidence']:.2%}")
        c5.metric("Confiança média micro", f"{summary['avg_micro_confidence']:.2%}")

        by_model = pd.DataFrame(summary.get("by_model", []))
        macro_dist = pd.DataFrame(distributions.get("macro_distribution", []))
        micro_dist = pd.DataFrame(distributions.get("micro_distribution", []))
        daily_volume = pd.DataFrame(distributions.get("daily_volume", []))
        predictions_df = pd.DataFrame(predictions)

        if not by_model.empty:
            st.plotly_chart(
                px.pie(by_model, names="label", values="value", title="Distribuição por modelo"),
                use_container_width=True,
            )

        col_left, col_right = st.columns(2)
        if not macro_dist.empty:
            col_left.plotly_chart(
                px.bar(macro_dist, x="label", y="value", title="Classificações por macro"),
                use_container_width=True,
            )
        if not micro_dist.empty:
            col_right.plotly_chart(
                px.bar(micro_dist.head(10), x="label", y="value", title="Top 10 micros"),
                use_container_width=True,
            )

        if not daily_volume.empty:
            daily_volume["date"] = pd.to_datetime(daily_volume["date"])
            st.plotly_chart(
                px.line(daily_volume, x="date", y="value", title="Volume diário de classificações"),
                use_container_width=True,
            )

        if not predictions_df.empty:
            if "created_at" in predictions_df.columns:
                predictions_df["created_at"] = pd.to_datetime(predictions_df["created_at"])
            st.write("**Últimas classificações salvas**")
            st.dataframe(predictions_df, use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há classificações salvas no banco.")
    except Exception as e:
        st.error(f"Não foi possível carregar as métricas: {e}")