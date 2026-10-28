"""
Busca as não conformidades no quadro do Monday e gera:
  - dados/ncs.json   -> lido pelo index.html
  - fotos/<item>.jpg -> foto de cada NC (baixada da coluna "Foto")

Roda no GitHub Actions. O token fica no secret MONDAY_API_TOKEN.
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone, timedelta

BOARD_ID = 18437464951
TOKEN = os.environ.get("MONDAY_API_TOKEN", "").strip()
API = "https://api.monday.com/v2"

# ids das colunas do quadro "Auditoria – Não Conformidades (28/10/2026)"
COL = {
    "num": "text_mm8jg74s",
    "setor": "dropdown_mm8jdv8v",
    "classificacao": "color_mm8j8q60",
    "status": "color_mm8jf2s",
    "descricao": "long_text_mm8jqkpt",
    "requisito": "text_mm8j529c",
    "acao": "long_text_mm8j20vn",
    "responsavel": "text_mm8jw5md",
    "prazo": "date_mm8jdern",
    "abertura": "date_mm8jv61d",
}

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.path.join(RAIZ, "dados")
PASTA_FOTOS = os.path.join(RAIZ, "fotos")
EXT_IMG = (".jpg", ".jpeg", ".png", ".webp", ".heic")


def gql(query, variables=None):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": TOKEN, "Content-Type": "application/json", "API-Version": "2024-10"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


QUERY = """
query ($board: [ID!], $cursor: String) {
  boards(ids: $board) {
    items_page(limit: 200, cursor: $cursor) {
      cursor
      items {
        id name created_at updated_at
        column_values { id text }
        assets { id name file_extension public_url created_at }
      }
    }
  }
}
"""


def buscar_itens():
    itens, cursor = [], None
    while True:
        page = gql(QUERY, {"board": [BOARD_ID], "cursor": cursor})["boards"][0]["items_page"]
        itens += page["items"]
        cursor = page["cursor"]
        if not cursor:
            return itens


def baixar_foto(item):
    """Baixa a imagem mais recente do item. Mantém a que já existe se não houver nova."""
    imagens = [a for a in (item.get("assets") or [])
               if (a.get("file_extension") or "").lower() in EXT_IMG and a.get("public_url")]
    destino = os.path.join(PASTA_FOTOS, f"{item['id']}.jpg")
    marca = os.path.join(PASTA_FOTOS, f".{item['id']}.asset")
    if imagens:
        a = sorted(imagens, key=lambda x: x.get("created_at") or "")[-1]
        ja_tem = os.path.exists(marca) and open(marca).read().strip() == str(a["id"])
        if not (ja_tem and os.path.exists(destino)):
            try:
                with urllib.request.urlopen(a["public_url"], timeout=60) as r, open(destino, "wb") as f:
                    f.write(r.read())
                with open(marca, "w") as f:
                    f.write(str(a["id"]))
                print(f"  foto baixada: {item['name']}")
            except Exception as e:  # foto falhou não derruba o painel
                print(f"  aviso: não baixou a foto de {item['name']}: {e}")
    return f"fotos/{item['id']}.jpg" if os.path.exists(destino) else ""


def main():
    if not TOKEN:
        sys.exit("Falta o secret MONDAY_API_TOKEN")
    os.makedirs(PASTA_DADOS, exist_ok=True)
    os.makedirs(PASTA_FOTOS, exist_ok=True)

    ncs = []
    for it in buscar_itens():
        v = {c["id"]: (c["text"] or "").strip() for c in it["column_values"]}
        nome = it["name"]
        num = v.get(COL["num"]) or nome.split("–")[0].strip()
        # rodapé = nome do item sem o "NC-xx – " do começo
        titulo = nome.split("–", 1)[1].strip() if "–" in nome else nome
        ncs.append({
            "id": it["id"],
            "num": num,
            "titulo": titulo,
            "setor": v.get(COL["setor"], ""),
            "classificacao": v.get(COL["classificacao"], "") or "Sem classificação",
            "status": v.get(COL["status"], "") or "Aberta",
            "descricao": v.get(COL["descricao"], ""),
            "requisito": v.get(COL["requisito"], ""),
            "acao": v.get(COL["acao"], ""),
            "responsavel": v.get(COL["responsavel"], ""),
            "prazo": v.get(COL["prazo"], ""),
            "abertura": v.get(COL["abertura"], ""),
            "foto": baixar_foto(it),
            "criadoEm": it["created_at"],
        })

    ncs.sort(key=lambda n: n["criadoEm"], reverse=True)

    caminho = os.path.join(PASTA_DADOS, "ncs.json")
    antigo = None
    if os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            antigo = json.load(f).get("ncs")
    if antigo == ncs:
        print("Sem mudanças no Monday.")
        return

    agora = datetime.now(timezone(timedelta(hours=-3))).strftime("%Y-%m-%dT%H:%M:%S-03:00")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"atualizado": agora, "ncs": ncs}, f, ensure_ascii=False, indent=1)
    print(f"{len(ncs)} NCs gravadas em dados/ncs.json")


if __name__ == "__main__":
    main()
