# XPTO Case — Sistema de Classificação de Textos

Sistema de classificação de textos com arquitetura baseada em:

- **FastAPI** para API de classificação e métricas
- **Streamlit** para interface de uso e visualização
- **PostgreSQL** para persistência
- **pgAdmin** para inspeção do banco
- **Modelos locais** (Regressão Logística com TF-IDF)
- **LLM via OpenAI** como classificador alternativo/assistido

O sistema classifica um texto em dois níveis:

- **classe macro**
- **classe micro/detalhada**

Além da classe final, o sistema também registra:

- confiança da macro
- confiança da micro
- indicador de ambiguidade
- metadados auxiliares da classificação

---

## 1. Objetivo do projeto

Este projeto foi construído para classificar mensagens/textos em categorias hierárquicas, combinando duas abordagens:

1. **modelo local tradicional**, mais barato e rápido
2. **modelo com LLM**, mais flexível para casos ambíguos ou complexos

A aplicação também permite:

- salvar classificações no banco
- acompanhar métricas de uso
- visualizar distribuições e indicadores de qualidade

---

## 2. Arquitetura

A arquitetura está dividida em quatro partes principais:

### 2.1 Backend — FastAPI
Responsável por:

- receber textos
- executar o pipeline de classificação
- salvar resultados no banco
- expor endpoints de consulta e métricas

### 2.2 Frontend — Streamlit
Responsável por:

- permitir classificação manual de um texto
- exibir resultado da classificação
- mostrar métricas, KPIs e gráficos

### 2.3 Banco de dados — PostgreSQL
Responsável por persistir:

- categorias macro e micro
- classificações realizadas
- dados usados para dashboard e análise

### 2.4 Serviços de apoio
- **pgAdmin** para administração visual do banco
- **Docker Compose** para orquestrar tudo

---

## 3. Estrutura do projeto

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── pipelines/
│   │   ├── prompts/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   └── .env
├── frontend/
│   └── app.py
├── docker-compose.yaml
├── .env.example
├── requirements.txt
└── README.md