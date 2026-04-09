REQUIRED_COLS_CSV = [
    "id_registro",
    "texto",
    "canal_origem",
    "data",
    "classe_macro",
    "classe_detalhada",
]

MACRO_MICRO_MAP = {
    "Problemas Técnicos": [
        "Erro de Autenticação e Acesso",
        "Erro de Exportação / Relatórios",
        "Erro de Sistema / Aplicação",
        "Falha de Banco de Dados",
        "Indisponibilidade / Queda do Serviço",
        "Problemas de Performance / Lentidão",
    ],
    "Solicitações Operacionais": [
        "Alteração de Plano / Contrato",
        "Atualização Cadastral",
        "Criação / Gestão de Usuários",
        "Customização de Relatórios",
        "Integração com Sistemas Externos",
        "Reprocessamento / Correção de Dados",
        "Solicitação de Treinamento",
    ],
    "Financeiro e Cobrança": [
        "Cobrança Indevida / Duplicada",
        "Dúvidas sobre Fatura / Valores",
        "Juros e Encargos",
        "Pagamento Realizado mas Não Compensado",
        "Reembolso / Estorno",
        "Segunda Via de Boleto",
    ],
    "Feedback e Experiência": [
        "Crítica de Usabilidade",
        "Feedback Positivo",
        "Sugestão de Melhoria",
        "Sugestão de Nova Funcionalidade",
    ],
    "Outros": [
        "Agradecimento Simples",
        "Mensagem Genérica",
        "Registro Automático",
    ],
}