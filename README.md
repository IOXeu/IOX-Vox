# IOX-Vox
# 💜 Sala VIP — Gírias Regionais com Voz Neural

O **Sala VIP** é uma aplicação web para analisar gírias brasileiras, gerar narração com voz neural e criar vídeos verticais para Reels, TikTok e Shorts.

O sistema mantém o texto regional original na interface, mas utiliza uma versão fonética no Edge TTS para melhorar a pronúncia.

## ✨ Recursos

- Banco com mais de 100 gírias do Norte, Nordeste, Sudeste, Sul e expressões gerais.
- Detecção de expressões simples e compostas.
- Pronúncia ajustada com o campo `texto_fala`.
- Geração de áudio com Microsoft Edge TTS.
- 12 vozes brasileiras disponíveis.
- Geração de vídeo vertical 1080x1920.
- Upload de imagens.
- Inserção de preço e CTA no vídeo.
- Interface web completa.

## 📁 Estrutura do projeto

```text
SalaVIP_Projeto/
├── servidor.py
├── gerador_engine.py
├── dicionario.json
├── requirements.txt
├── index.html
├── .gitignore
├── README.md
├── temp/
├── audios/
└── videos/
```

As pastas `temp`, `audios` e `videos` são criadas automaticamente.

## ⚙️ Instalação

1. Instale o Python 3.10 ou superior.
2. Abra o terminal na pasta do projeto.
3. Crie um ambiente virtual:

```bash
python -m venv venv
```

4. Ative o ambiente virtual:

No Windows:

```bash
venv\Scripts\activate
```

No Linux ou macOS:

```bash
source venv/bin/activate
```

5. Instale as dependências:

```bash
pip install -r requirements.txt
```

6. Inicie o servidor:

```bash
python servidor.py
```

7. Acesse:

```text
http://localhost:5000
```

## 🎯 Como usar

### Analisar frase

Digite algo como:

```text
Oxe, esse kit tá arretado de bom, visse?
```

O sistema identifica as gírias e mostra região, significado e exemplo.

### Gerar áudio

Clique em **Gerar Áudio**.  
O texto regional permanece visível, mas o Edge TTS recebe a pronúncia ajustada.

Exemplo:

```text
Texto exibido: Oxe, esse kit tá arretado de bom, visse?
Texto para TTS: Ó xi, esse kit tá a he ta do de bom, vi se?
```

### Gerar vídeo

1. Envie uma ou mais imagens.
2. Escreva o preço.
3. Escreva o CTA.
4. Digite o texto da narração.
5. Escolha a voz e a velocidade.
6. Clique em **Gerar Vídeo**.

O vídeo será salvo na pasta `videos/`.

## 🔌 Principais rotas

| Rota | Método | Função |
|---|---|---|
| `/` | GET | Interface web |
| `/api/stats` | GET | Estatísticas do dicionário |
| `/api/analisar` | POST | Detecta gírias em uma frase |
| `/api/falar` | POST | Gera áudio com Edge TTS |
| `/api/upload-imagem` | POST | Envia imagem para o vídeo |
| `/api/gerar-video` | POST | Gera vídeo vertical |

## 🗂️ Formato do dicionário

Cada gíria usa este formato:

```json
{
  "id": 11,
  "expressao": "oxe",
  "regiao": "Nordeste",
  "estados": "BA, PE, CE, SE, AL, PB, RN",
  "significado": "espanto, estranhamento",
  "exemplo": "Oxe, quem te disse isso?",
  "categoria": "interjeição",
  "formalidade": "popular",
  "texto_fala": "ó xi",
  "peso": 99
}
```

O campo `texto_fala` é usado apenas pelo Edge TTS.

## 🚫 Arquivos que não devem ir ao GitHub

Não suba:

- `__pycache__/`
- `*.pyc`
- `temp/`
- `audios/`
- `videos/`
- `.env`
- arquivos MP3, MP4 ou imagens temporárias

O `.gitignore` já bloqueia esses arquivos.

## 📄 Licença

Uso interno e educacional.  
Você pode adaptar o projeto para seu negócio, adicionando novas gírias, vozes, templates de vídeo e integrações.
