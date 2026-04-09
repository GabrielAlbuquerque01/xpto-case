import os
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Classificação de Textos", layout="wide")
st.title("Classificação de Textos")
st.caption("Entrada de texto e monitoramento de métricas salvas no banco.")


def get_json(endpoint: str):
    response = requests.get(f"{API_URL}{endpoint}", timeout=60)
    response.raise_for_status()
    return response.json()


tab_input, tab_metrics = st.tabs(["Classificação", "Métricas e KPIs"])

with tab_input:
    st.subheader("Classificação unitária")
    text = st.text_area("Texto recebido", height=220, placeholder="Cole aqui a mensagem a ser classificada...")

    classifiers = get_json("/classifiers")
    classifier_options = [item["name"] for item in classifiers]
    classifier = st.selectbox("Classificador", options=classifier_options)

    if st.button("Classificar texto", use_container_width=True):
        if not text.strip():
            st.warning("Informe um texto para classificar.")
        else:
            payload = {
                "text": text,
                "classifier": classifier,
            }
            try:
                response = requests.post(f"{API_URL}/classify", json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()

                st.success("Classificação concluída.")
                metric_cols = st.columns(4)
                metric_cols[0].metric("Macro", data["macro"])
                metric_cols[1].metric("Confiança macro", f"{data['macro_confidence']:.2%}")
                metric_cols[2].metric("Detail", data["detail"])
                metric_cols[3].metric("Confiança detail", f"{data['detail_confidence']:.2%}")

                st.write(f"**Classificador:** {data['classifier']}")

                secondary_predictions = data.get("secondary_predictions", [])
                if secondary_predictions:
                    with st.expander("Possíveis classificações secundárias"):
                        for item in secondary_predictions:
                            st.write(f"- **Macro:** {item['macro']} | **Detail:** {item['detail']}")

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

        c1, c2, c3 = st.columns(3)
        c1.metric("Total de classificações", summary["total_predictions"])
        c2.metric("Confiança média macro", f"{summary['avg_macro_confidence']:.2%}")
        c3.metric("Confiança média detail", f"{summary['avg_detail_confidence']:.2%}")

        by_classifier = pd.DataFrame(summary.get("by_classifier", []))
        macro_dist = pd.DataFrame(distributions.get("macro_distribution", []))
        detail_dist = pd.DataFrame(distributions.get("detail_distribution", []))
        daily_volume = pd.DataFrame(distributions.get("daily_volume", []))
        predictions_df = pd.DataFrame(predictions)

        if not by_classifier.empty:
            st.plotly_chart(
                px.pie(by_classifier, names="label", values="value", title="Distribuição por classificador"),
                use_container_width=True,
            )

        col_left, col_right = st.columns(2)
        if not macro_dist.empty:
            col_left.plotly_chart(
                px.bar(macro_dist, x="label", y="value", title="Classificações por macro"),
                use_container_width=True,
            )
        if not detail_dist.empty:
            col_right.plotly_chart(
                px.bar(detail_dist.head(10), x="label", y="value", title="Top 10 detalhadas"),
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

            if "secondary_predictions" in predictions_df.columns:
                predictions_df["secondary_predictions"] = predictions_df["secondary_predictions"].apply(
                    lambda items: " | ".join(
                        [f"{item['macro']} -> {item['detail']}" for item in items]
                    ) if items else "-"
                )

            st.write("**Últimas classificações salvas**")
            st.dataframe(predictions_df, use_container_width=True, hide_index=True)
        else:
            st.info("Ainda não há classificações salvas no banco.")

    except Exception as e:
        st.error(f"Não foi possível carregar as métricas: {e}")