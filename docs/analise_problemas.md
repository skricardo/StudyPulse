# 🔍 Análise de Problemas — StudyPulse

> Gerado em: 2026-05-26 | Versão analisada: 1.1.5

---

## 🔴 Críticos (podem causar bugs agora)

### 1. `focus.py` — Sessão nunca é salva
O timer tem botões de Iniciar/Pausar/Parar, mas **`_stop_timer()` apenas reseta o timer — não chama `db.add_session()`**.  
O `_finish_session()` existe mas **nunca é chamado por nenhum botão**.  
O usuário estuda mas **nenhuma sessão é registrada**, nenhum XP é ganho, nenhum badge é verificado.

- **Arquivo:** `src/pages/focus.py`
- **Função problemática:** `_stop_timer()`, `_finish_session()`
- **Correção sugerida:** Chamar `db.add_session()` dentro de `_stop_timer()` com os dados da sessão atual.

---

### 2. `focus.py` — Thread do timer sem proteção de navegação
O timer roda em `threading.Thread(daemon=True)`. Se o usuário **trocar de aba enquanto o timer está rodando**, a thread continua viva, tenta chamar `page.update()` em um controle que não existe mais e pode:
- Lançar exceções silenciosas
- Corromper o estado da UI

- **Arquivo:** `src/pages/focus.py`
- **Função problemática:** `_timer_loop()`
- **Correção sugerida:** Usar um evento de cancelamento (`threading.Event`) e verificar se a página ainda está ativa antes de chamar `page.update()`.

---

### 3. `badges.py` — Badge "Precisão" com critério errado
A condição compara `total_minutes` (todo o histórico) com `weekly_target_minutes`.  
Um tema estudado **200 minutos no mês inteiro** pode ganhar o badge sem nunca ter atingido a meta semanal.

- **Arquivo:** `src/utils/badges.py`
- **Função problemática:** `_check_condition()` → caso `"precision"`
- **Correção sugerida:** Usar `get_topic_totals_weekly(week_start)` em vez de `get_topic_totals()`.

---

## 🟡 Médios (degradação de experiência)

### 4. Streak Freeze nunca utilizado
`streak_freeze_available` existe na tabela `user_stats` mas **nenhum código o consome ou oferece ao usuário**.  
A coluna é dead code por enquanto.

- **Arquivo:** `src/db.py`
- **Correção sugerida:** Implementar lógica de uso do freeze ao detectar streak em risco, ou remover a coluna se não for usada.

---

### 5. `undo_planner_quick_log` não recalcula streak
Ao desmarcar um slot, o XP é removido, mas `_update_streak()` **não é chamada**.  
O streak pode permanecer incrementado mesmo após desfazer a única sessão do dia.

- **Arquivo:** `src/db.py`
- **Função problemática:** `undo_planner_quick_log()`
- **Correção sugerida:** Recalcular o streak após deletar a sessão.

---

### 6. Sem validação de `topic_id` inválido no Planner
Se um tema for deletado, o `ON DELETE CASCADE` remove os slots — correto.  
Mas se a **página de planner já estava carregada na memória**, pode tentar renderizar dados de um `topic_id` inexistente.

- **Arquivo:** `src/pages/planner.py`
- **Correção sugerida:** Recarregar os dados do planner sempre que voltar para a aba.

---

### 7. `check_badges()` sem paginação
`db.get_sessions(days=365)` é chamado toda vez que `check_badges()` roda.  
Com 1 ano de uso intenso isso pode retornar **milhares de rows** a cada sessão registrada.

- **Arquivo:** `src/utils/badges.py`
- **Correção sugerida:** Cachear resultado ou limitar a janela de busca por badge.

---

## 🟢 Riscos Futuros (escalabilidade / UX)

### 8. Banco de dados sem backup
`studypulse.db` fica na raiz do projeto. Nenhum mecanismo de backup, exportação ou proteção.  
Um `DELETE FROM topics` acidental apaga todo o histórico via `CASCADE`.

- **Correção sugerida:** Backup automático rotativo (cópia diária do `.db`).

---

### 9. Sistema de multi-usuário impossível atualmente
`user_stats` tem `CHECK (id = 1)` — hardcoded para um único usuário.  
Se no futuro quiser suportar perfis, toda a estrutura precisaria ser refatorada.

---

### 10. Planner não avança semanas automaticamente
Os slots do planner são vinculados a `week_start_date`.  
Não há lógica de **"clonar semana anterior"** ou **"repetir slots recorrentes"**.  
O usuário precisa re-criar manualmente todo o planner toda semana.

---

### 11. Sem tratamento de fuso horário
Datas são salvas com `'localtime'` no SQLite, mas o Python usa `datetime.now()` sem `tzinfo`.  
Em máquinas com horário errado, as datas de sessão e streak podem divergir.

---

## 📋 Tabela Resumo

| Severidade | Problema | Arquivo |
|---|---|---|
| 🔴 Crítico | Sessão de foco nunca é salva | `src/pages/focus.py` |
| 🔴 Crítico | Thread do timer sem cleanup ao trocar de aba | `src/pages/focus.py` |
| 🔴 Crítico | Badge "Precisão" com critério errado (histórico vs semanal) | `src/utils/badges.py` |
| 🟡 Médio | Streak freeze nunca utilizado | `src/db.py` |
| 🟡 Médio | Undo de slot não recalcula streak | `src/db.py` |
| 🟡 Médio | Planner não recarrega ao trocar de aba | `src/pages/planner.py` |
| 🟡 Médio | `check_badges` sem limite de sessões carregadas | `src/utils/badges.py` |
| 🟢 Futuro | Sem backup automático do banco de dados | `studypulse.db` |
| 🟢 Futuro | Arquitetura single-user, sem suporte a perfis | `src/db.py` |
| 🟢 Futuro | Planner não repete slots entre semanas | `src/pages/planner.py` |
| 🟢 Futuro | Sem tratamento explícito de fuso horário | `src/db.py` / `src/pages/focus.py` |

---

## ✅ Ordem de Correção Recomendada

1. **Salvar sessão ao parar o timer** (`focus.py`) — impacto direto na funcionalidade core
2. **Corrigir thread do timer** (`focus.py`) — evitar crashes ao trocar de aba
3. **Corrigir badge "Precisão"** (`badges.py`) — critério logicamente incorreto
4. **Implementar ou remover Streak Freeze** (`db.py`)
5. **Recalcular streak no undo** (`db.py`)
6. **Backup automático do DB** — proteção de dados do usuário
