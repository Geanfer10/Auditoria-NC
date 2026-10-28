# Auditoria-NC

Painel de não conformidades da auditoria de 28/10/2026 da Goiás Verde, em Luziânia-GO.
Os dados vêm do quadro **"Auditoria – Não Conformidades (28/10/2026)"** do Monday (board 18437464951).

## Como funciona

1. A NC é cadastrada no Monday, com a foto na coluna **Foto**.
2. A cada 5 minutos o GitHub Actions roda `scripts/buscar_monday.py`. O script lê o quadro, baixa as fotos para `fotos/` e grava `dados/ncs.json`.
3. O `index.html`, publicado no GitHub Pages, relê o JSON a cada 30 segundos.

Para atualizar na hora: **Actions → Atualizar NCs do Monday → Run workflow**.

## O que vai no painel

- **Rodapé da foto:** é o nome do item no Monday, sem o "NC-xx –" do começo.
- **Classificação, status e demais campos:** vêm das colunas do quadro.
- **Modo TV:** mostra uma NC por vez, em tela cheia, trocando a cada 12 s.
- **Vidro leve:** desliga o desfoque, para TVs e PCs mais fracos.

## Configuração (uma vez)

- **Secret:** em *Settings → Secrets and variables → Actions → New repository secret*, crie `MONDAY_API_TOKEN` com o token do Monday.
- **Pages:** em *Settings → Pages*, escolha *Deploy from a branch*, depois `main` e `/ (root)`.
- **Permissão do robô:** em *Settings → Actions → General → Workflow permissions*, marque *Read and write*.
