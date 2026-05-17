# Changelog

Todas as atualizações notáveis do **StudyPulse** serão documentadas neste arquivo.

O formato baseia-se em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto se baseia livremente em um modelo de [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

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
