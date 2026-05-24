# Changelog

Todas as atualizações notáveis do **StudyPulse** serão documentadas neste arquivo.

O formato baseia-se em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto se baseia livremente em um modelo de [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [1.1.3] - 2026-05-24
### Adicionado
- **Reordenação automática de slots concluídos (`planner.py`, `today.py`, `db.py`)**: Ao marcar um slot como ✅ no Planner ou na aba Hoje, o item sobe automaticamente para o topo do dia, agrupando todos os concluídos em ordem de clique. Ao desmarcar, o item desce para o fim da lista de pendentes.
  - `db.py` — Nova função `get_completed_count_for_day` para calcular a posição correta de cada slot concluído.
  - `db.py` — Função `update_planner_slot` passou a aceitar o campo `sort_order`.
  - `db.py` — Queries `get_planner_slots` e `get_day_planner_slots` agora ordenam concluídos antes dos pendentes (`ORDER BY completed DESC`).
  - `planner.py` / `today.py` — Ao marcar ✅: atribui `sort_order` posicional dentro do grupo de concluídos. Ao desmarcar ☐: envia para `sort_order=9999` (fim da lista).
### Corrigido
- **Bug de `session_date` ausente no fluxo de desmarcar (`planner.py`, `today.py`)**: Ao desmarcar um slot, a chamada a `undo_planner_quick_log` não passava a data do slot, podendo deletar sessão de outro dia. Agora a `session_date` é calculada e repassada corretamente também no fluxo de desmarcar.

## [1.1.2] - 2026-05-24
### Corrigido
- **Bug de sobreposição de sessões entre dias (`db.py`, `planner.py`, `today.py`)**: Ao marcar um slot como concluído, a função `undo_planner_quick_log` buscava e apagava a sessão mais recente do tema sem filtrar por data. Isso fazia com que marcar um slot em um dia (ex: Sábado) deletasse a sessão de outro dia anterior (ex: Sexta), zerando os dados desse dia nas estatísticas.
  - `db.py` — Função `undo_planner_quick_log` passou a aceitar o parâmetro opcional `session_date`, filtrando a busca pela data exata do slot.
  - `planner.py` / `today.py` — Chamada a `undo_planner_quick_log` no fluxo de **marcar** ✅ atualizada para passar `session_date=slot_date`.

## [1.1.1] - 2026-05-24
### Corrigido
- **Bug de data nas sessões do Planner (`planner.py`, `db.py`)**: Ao marcar um slot como concluído no Planner, a sessão de estudo era sempre registrada com a data e hora atuais (`datetime.now()`), em vez da data real do dia planejado. Isso causava divergência nas estatísticas: a aba "Esta Semana" exibia 0 minutos para dias já concluídos quando o slot era marcado em outro dia da semana.
  - `db.py` — Função `add_session` passou a aceitar o parâmetro opcional `session_date`, permitindo salvar a sessão com a data correta do slot.
  - `planner.py` — Função `_toggle_slot` agora calcula a data real do slot (`week_start_date + day_of_week`) e a repassa para `add_session`.


## [1.1.0] - 2026-05-17

### Adicionado
- **Página "Hoje" (`today.py`)**: Implementada a página diária de estudos para um acompanhamento ágil do que deve ser feito no dia.
- **Página "Temas" (`topics.py`)**: Interface de gerenciamento dinâmico para as categorias e disciplinas.
- **Reordenação Drag-and-Drop**: Adicionada a capacidade interativa de reordenar categorias de estudo arrastando os elementos na tela.
- **Diálogos de Confirmação**: Implementados alertas de segurança antes de deletar temas e categorias para evitar perdas acidentais de dados.

### Modificado
- **Banco de Dados (`db.py`)**: Estrutura e funções atualizadas para suportar as novas lógicas de ordenação de interface.
- **Planner (`planner.py`) e Main (`main.py`)**: Refinamentos na integração entre blocos de estudo, rotas do menu e correção de layouts no visual da agenda.

---

## [1.0.0] - 2026-05-16

### Adicionado
- **Lançamento Inicial**: Criação da base do aplicativo em Python.
- **Sistema de Gamificação**: 
  - `xp_system.py`: Lógica de pontos de experiência (XP) baseada em tempo e peso do estudo.
  - `badges.py`: Sistema de recompensas e insígnias para engajamento.
- **Página de Foco (`focus.py`)**: Cronômetro e ambiente livre de distrações para contabilizar o tempo real de estudo.
- **Página de Conquistas (`achievements.py`)**: Galeria do usuário com seu nível atual e medalhas alcançadas.
- **Página de Estatísticas (`stats.py`)**: Heatmaps (estilo GitHub) e gráficos baseados no desempenho e histórico das sessões de estudo.
- **Sincronização Bidirecional**: Sistema automático que liga os horários planejados às sessões reais executadas.
- **Sistema de Frases (`quotes.py`)**: Citações motivacionais rotativas na interface.
- **Tematização (`theme.py`)**: Padronização da interface gráfica usando cores modernas.
- **Atalho do Windows (`Abrir_StudyPulse.bat`)**: Script rápido para abrir o sistema e ativar o ambiente virtual sem precisar de comandos.
