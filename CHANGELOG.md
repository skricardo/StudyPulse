# Changelog

Todas as atualizações notáveis do **StudyPulse** serão documentadas neste arquivo.

O formato baseia-se em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto se baseia livremente em um modelo de [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---
## [1.3.2] - 2026-06-01
### Corrigido - BUG QUE FIQUE MAIS PREOCUPADO EM TER PERDIDO TODOS OS DADOS JÁ SALVOS
- **Migração segura do banco de dados legado (`db.py`)**: A lógica de migração anterior renomeava `studypulse.db` para o banco do primeiro usuário a fazer login após a atualização, mesmo que o banco não pertencesse a ele — causando perda de acesso ao usuário original.
  - `db.py` — `set_user_db` agora consulta a tabela `users` do banco legado antes de renomear, verificando se o usuário em questão realmente existe naquele banco. Só realiza a migração se a verificação for positiva, preservando os dados corretamente.

## [1.3.1] - 2026-06-01
### Corrigido
- **Isolamento de dados por usuário (`db.py`, `auth.py`)**: Ao criar um segundo usuário, os dados do usuário principal eram carregados incorretamente. Cada usuário agora possui seu próprio banco de dados isolado.
  - `db.py` — `DB_PATH` substituído por `_current_db` (referência mutável) + `BASE_DIR` e `_DEFAULT_DB` como constantes base.
  - `db.py` — Nova função `set_user_db(username)`: define o banco de dados ativo para o usuário logado. Se o banco legado `studypulse.db` existir e o banco do usuário não existir, realiza a migração automática via `os.rename`, preservando todos os dados existentes.
  - `auth.py` — `save_session` passa a salvar o campo `username` no arquivo `.session`.
  - `auth.py` — `load_session` lê `username` do `.session` e chama `db.set_user_db()` + `db.init_db()` antes de validar o token.
  - `auth.py` — `login` e `register` chamam `db.set_user_db()` + `db.init_db()` antes de qualquer acesso ao banco, garantindo que o banco correto esteja ativo.
  - `main.py` — Chamada direta `db.init_db()` removida; a inicialização do banco agora é responsabilidade das funções de autenticação.

## [1.3.0] - 2026-06-01
### Adicionado
- **Sistema de Recuperação de Senha — Pergunta Secreta (`db.py`, `auth.py`, `login.py`)**: Novo fluxo "Esqueci a senha" na tela de login. O usuário define uma pergunta secreta no cadastro e pode usá-la para redefinir a senha sem precisar de e-mail ou servidor externo.
  - `db.py` — Migração automática: colunas `security_question` e `security_answer_hash` adicionadas à tabela `users` via `ALTER TABLE … IF NOT EXISTS`.
  - `db.py` — Novas funções: `get_security_question(username)` e `update_user_security_question(user_id, question, answer_hash)`.
  - `auth.py` — Lista `SECURITY_QUESTIONS` com 8 opções de pergunta centralizada no módulo.
  - `auth.py` — Novas funções: `hash_answer` (normaliza resposta para minúsculas antes do hash), `verify_security_answer`, `reset_password` e `set_security_question`.
  - `src/pages/login.py` — Nova view de recuperação de senha: digita usuário → pergunta secreta exibida automaticamente → resposta + nova senha → senha redefinida.
  - `src/pages/login.py` — Aviso em destaque (⚠️) na tela de cadastro alertando sobre a importância de guardar a resposta.
- **Configuração de Pergunta Secreta dentro do App (`main.py`)**: Usuários existentes (criados antes da versão 1.3.0) podem cadastrar sua pergunta secreta sem precisar criar nova conta.
  - `main.py` — Ícone 👤 (`MANAGE_ACCOUNTS_OUTLINED`) adicionado ao header.
  - `main.py` — Dialog "Pergunta Secreta" com validação da senha atual antes de salvar, aviso de importância e feedback de sucesso/erro.
- **Confirmação ao desmarcar atividade de dia anterior (`planner.py`)**: Ao tentar desmarcar um slot concluído em dias anteriores, exibe dialog de confirmação avisando que a sessão e o XP ganho serão removidos, evitando ações acidentais.
  - `planner.py` — `_toggle_slot` detecta automaticamente se o slot pertence a um dia passado.
  - `planner.py` — Novo `dlg_confirm_uncheck` com botões "Cancelar" e "Sim, desfazer".
---

## [1.2.0] - 2026-06-01
### Adicionado
- **Sistema de Autenticação com Sessão Persistente (`auth.py`, `db.py`, `main.py`, `pages/login.py`)**: Implementado sistema de login e cadastro de usuário, com sessão que permanece ativa por 30 dias — o app não exige senha a cada abertura.
  - `db.py` — Novas tabelas `users` (armazena `username`, `password_hash`, `display_name`) e `sessions` (armazena `token`, `user_id`, `expires_at`) criadas via `CREATE TABLE IF NOT EXISTS`, preservando todos os dados existentes.
  - `db.py` — Novas funções: `create_user`, `get_user_by_username`, `create_session`, `get_session_by_token`, `delete_session_by_token`.
  - `src/auth.py` — Novo módulo de autenticação com: `hash_password` (PBKDF2-HMAC-SHA256, sem dependências externas), `verify_password` (resistente a timing attack via `secrets.compare_digest`), `save_session` / `load_session` / `clear_session` (arquivo `.session` na raiz), `login` e `register`.
  - `src/pages/login.py` — Nova tela de login/cadastro com design dark mode, campos com ícone e toggle de visibilidade de senha, alternância entre modos "Login" e "Criar conta", e feedback visual de erros.
  - `main.py` — Lógica de autenticação integrada: ao abrir o app, verifica sessão salva; se válida, entra direto; caso contrário, exibe tela de login. Botão de logout discreto adicionado no header.
---

## [1.1.7] - 2026-05-30
### Adicionado
- **Filtro por categoria ao adicionar tema no Planner (`planner.py`)**: Ao abrir o dialog de "Adicionar ao Planner", agora é exibido primeiro um dropdown de **Categoria**. Ao selecionar uma categoria, o dropdown de **Tema** é filtrado automaticamente, exibindo apenas os temas pertencentes àquela categoria.
  - `planner.py` — Adicionado `dd_category_filter` (Dropdown de categoria) no dialog de adição de slot.
  - `planner.py` — Função `_open_add_slot` reescrita com a função interna `_update_topics_by_category`, que filtra os temas por categoria em tempo real via `on_change`.
- **Confirmação ao remover tema do Planner (`planner.py`)**: Ao clicar no ❌ de um slot no planner, agora é exibido um dialog de confirmação antes de excluir, evitando remoções acidentais.
  - `planner.py` — Adicionado `dlg_confirm_slot` (AlertDialog) com botões "Cancelar" e "Remover".
  - `planner.py` — Função `_delete_slot` atualizada para abrir o dialog de confirmação em vez de deletar diretamente.
---

## [1.1.6] - 2026-05-27
### Adicionado
- **Card "Semanas do Mês" na página de Estatísticas (`stats.py`)**: Nova métrica no dashboard exibindo o desempenho de cada semana do mês vigente em formato de gráfico de barras, com navegação entre meses passados.
  - `stats.py` — Nova função `_build_monthly_weeks_chart`: calcula as semanas do mês (Seg–Dom) recortadas ao período do mês, soma os minutos por semana e renderiza as barras com label `Semana 01`, `Semana 02`... e intervalo de datas `dias: 25–31`.
  - `stats.py` — Semana atual destacada com cor diferenciada e texto em negrito; seta de avançar (`>`) desabilitada no mês atual para impedir navegação futura.
  - `stats.py` — Ampliado o histórico de `get_daily_minutes` de 365 para 730 dias, permitindo exibir dados de até 2 anos atrás na navegação de meses.
---

## [1.1.5] - 2026-05-25
### Adicionado
- **Stats por período na aba Temas (`topics.py`, `db.py`)**: Os cards de tema passaram a exibir três mini-estatísticas de histórico — **Última semana**, **Este mês** e **Total** — além de indicar o tempo estudado na semana atual.
  - `topics.py` — Adicionado import de `date` e `timedelta`.
  - `topics.py` — Dict `_stats` pré-carregado em `_refresh()` com os quatro períodos por `topic_id`: `weekly`, `last_week`, `monthly`, `all_time`.
  - `topics.py` — `_build_topic_card` reescrito: usa `weekly_min` para a barra de progresso (reseta toda segunda-feira), e exibe linha de mini-stats com `_fmt` e `_mini_stat` helpers internos.
  - `db.py` — Funções `get_topic_totals_weekly` e `get_topic_totals_monthly` (introduzidas em 1.1.4) reutilizadas para os períodos semanal e mensal; `get_topic_totals` para o total histórico.
### Corrigido
- **Meta semanal dos temas não resetava (`topics.py`)**: A barra de progresso usava o total histórico de minutos (`all_time`) em vez dos minutos da semana corrente, fazendo com que a meta nunca "zerasse" na segunda-feira. Agora usa exclusivamente os minutos da semana atual.

---

## [1.1.4] - 2026-05-25
### Adicionado
- **Abas de período na Distribuição por Tema (`stats.py`, `db.py`)**: A seção "Distribuição por Tema" passou a exibir três abas — **Geral** (todo o histórico), **Mensal** (mês corrente) e **Semanal** (semana atual).
  - `db.py` — Nova função `get_topic_totals_monthly`: minutos por tema no mês corrente.
  - `db.py` — Nova função `get_topic_totals_weekly(week_start)`: minutos por tema na semana informada.
  - `db.py` — Função `get_topic_totals` restaurada (havia sido deletada acidentalmente).
  - `stats.py` — `stats_page` busca os três conjuntos de dados e os repassa para `_build_topic_bars`.
  - `stats.py` — `_build_topic_bars` reescrita com `ft.Tabs` (height=350) e `_make_bars` com `scroll=AUTO`.
### Corrigido
- **Temas sem sessões apareciam na Distribuição por Tema (`stats.py`, `db.py`)**: Temas com 0 minutos eram listados e o corte em 10 itens ocultava temas com estudo real.
  - `db.py` — `get_topic_totals` passou a usar `HAVING total_minutes > 0`.
  - `stats.py` — Removido o slice `[:10]` de `_build_topic_bars`.
  
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
