# StudyPulse
> Aplicativo desktop de gestão de estudos com gamificação, planejamento semanal e estatísticas detalhadas.
Desenvolvido em **Python + Flet**, com banco de dados **SQLite** local. Interface moderna, dark mode nativo e sem dependência de internet para uso.
---
## Funcionalidades
### Hoje
- Dashboard diário com resumo do que está planejado para o dia
- KPIs em tempo real: tempo estudado, sessões realizadas, XP ganho e progresso
- Marcar slots do Planner como concluídos diretamente pela aba
- Registro de lembretes rápidos com categorias
###  Planner
- Grade semanal com colunas por dia (Segunda → Domingo)
- Adicionar temas com tempo planejado por dia
- Drag-and-drop para reorganizar slots entre dias
- Slots concluídos sobem automaticamente ao topo em ordem de clique
- Navegação entre semanas (passadas e futuras)
- Repetição automática de slots pelas próximas 4 semanas
###  Temas
- Gerenciamento de categorias e disciplinas de estudo
- Configuração de prioridade, cor, ícone e meta semanal
- Reordenação drag-and-drop de categorias
- Arquivamento de temas inativos
###  Foco
- Cronômetro e modo Pomodoro para sessões reais de estudo
- Registro automático da sessão ao finalizar com XP calculado
###  Stats
- Heatmap anual no estilo GitHub
- Gráfico mensal com desempenho por mês
- Gráfico semanal com tempo realizado por dia
- Distribuição de tempo por tema
- KPIs globais: total estudado, streak, média diária, tema favorito
###  Conquistas
- Sistema de XP e níveis
- Medalhas desbloqueáveis por marcos de estudo
- Barra de progresso para o próximo nível
---
##  Tecnologias
| Tecnologia | Uso |
|---|---|
| [Python 3.11+](https://python.org) | Linguagem principal |
| [Flet](https://flet.dev) | Framework de UI (Flutter via Python) |
| SQLite | Banco de dados local |
| `requests` | Requisições HTTP (futuras integrações) |
---
## Como executar
### Pré-requisitos
- Python 3.11 ou superior
- Git
### Instalação
```bash
# 1. Clone o repositório
git clone https://github.com/skricardo/StudyPulse.git
cd StudyPulse
# 2. Crie o ambiente virtual
python -m venv .venv
# 3. Ative o ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
# 4. Instale as dependências
pip install -r requirements.txt
# 5. Execute o app
python main.py
Atalho rápido (Windows)
Dê um duplo clique no arquivo Abrir_StudyPulse.bat — ele ativa o ambiente virtual e abre o app automaticamente.

StudyPulse/
├── main.py                  # Ponto de entrada, navegação e header
├── requirements.txt
├── Abrir_StudyPulse.bat     # Atalho Windows
├── studypulse.db            # Banco de dados SQLite (gerado automaticamente)
├── CHANGELOG.md
└── src/
    ├── db.py                # Camada de banco de dados
    ├── theme.py             # Sistema de cores e estilos
    ├── pages/
    │   ├── today.py         # Aba: Hoje
    │   ├── planner.py       # Aba: Planner
    │   ├── topics.py        # Aba: Temas
    │   ├── focus.py         # Aba: Foco
    │   ├── stats.py         # Aba: Stats
    │   └── achievements.py  # Aba: Conquistas
    └── utils/
        ├── xp_system.py     # Lógica de XP e níveis
        ├── badges.py        # Sistema de conquistas
        └── quotes.py        # Frases motivacionais

##  Changelog
Veja o histórico completo de versões em [CHANGELOG.md](./CHANGELOG.md).
---
##  Licença
Este projeto é de uso pessoal. Sinta-se à vontade para adaptar para suas necessidades.