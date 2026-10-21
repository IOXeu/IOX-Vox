"""
SALA VIP COMPLETO — UNIFICADO
Interface Web + Análise de Gírias + Voz Neural + Música de Fundo + Vídeo Reels
Um único arquivo.
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

import edge_tts
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    concatenate_audioclips,
    CompositeAudioClip
)
from PIL import Image, ImageDraw, ImageFont

import asyncio
import json
import os
import random
import re
import uuid


app = Flask(__name__)
CORS(app)

ARQUIVO_DICIONARIO = "dicionario.json"
ARQUIVO_BANCO_MUSICAS = "musicas_banco.json"
PASTA_MUSICAS = "musicas"
PASTA_TEMP = "temp"
PASTA_AUDIOS = "audios"
PASTA_VIDEOS = "videos"

os.makedirs(PASTA_TEMP, exist_ok=True)
os.makedirs(PASTA_AUDIOS, exist_ok=True)
os.makedirs(PASTA_VIDEOS, exist_ok=True)
os.makedirs(PASTA_MUSICAS, exist_ok=True)

VOZ_PADRAO = "pt-BR-FranciscaNeural"
VOLUME_PADRAO_MUSICA = 0.12

RATE_MAP = {
    "lenta": "-20%",
    "normal": "+0%",
    "rapida": "+20%"
}


def carregar_dicionario():
    if os.path.exists(ARQUIVO_DICIONARIO):
        with open(ARQUIVO_DICIONARIO, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    banco_padrao = [
        {"id": 1, "expressao": "égua", "regiao": "Norte", "significado": "espanto", "exemplo": "Égua, que calor!", "texto_fala": "é gua", "peso": 98},
        {"id": 2, "expressao": "boró", "regiao": "Norte", "significado": "dinheiro", "exemplo": "Tô sem boró", "texto_fala": "bo ró", "peso": 95},
        {"id": 3, "expressao": "oxe", "regiao": "Nordeste", "significado": "espanto", "exemplo": "Oxe, cadê meu pedido?", "texto_fala": "ó xi", "peso": 99},
        {"id": 4, "expressao": "arretado", "regiao": "Nordeste", "significado": "muito bom", "exemplo": "Preço arretado de bom", "texto_fala": "a he ta do", "peso": 94},
        {"id": 5, "expressao": "mano", "regiao": "Sudeste", "significado": "amigo", "exemplo": "Mano, tô sem boró", "texto_fala": "ma nu", "peso": 100},
        {"id": 6, "expressao": "trampo", "regiao": "Sudeste", "significado": "trabalho", "exemplo": "Tô no trampo", "texto_fala": "tram po", "peso": 96},
        {"id": 7, "expressao": "bah", "regiao": "Sul", "significado": "espanto", "exemplo": "Bah, que frio!", "texto_fala": "bá", "peso": 96},
        {"id": 8, "expressao": "tri", "regiao": "Sul", "significado": "muito", "exemplo": "Tri bonita", "texto_fala": "tri", "peso": 93}
    ]

    with open(ARQUIVO_DICIONARIO, "w", encoding="utf-8") as arquivo:
        json.dump(banco_padrao, arquivo, ensure_ascii=False, indent=2)

    return banco_padrao


BANCO = carregar_dicionario()


def carregar_banco_musicas():
    if os.path.exists(ARQUIVO_BANCO_MUSICAS):
        with open(ARQUIVO_BANCO_MUSICAS, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    return {
        "pasta_musicas": PASTA_MUSICAS,
        "volume_padrao": VOLUME_PADRAO_MUSICA,
        "usar_musica_por_padrao": True,
        "musicas": []
    }


BANCO_MUSICAS = carregar_banco_musicas()


def analisar_frase(frase):
    frase_lower = frase.lower()
    encontradas = []
    ids_ja_encontrados = set()

    for item in sorted(
        BANCO,
        key=lambda x: len(x.get("expressao", "")),
        reverse=True
    ):
        expressao = item.get("expressao", "").strip().lower()

        if not expressao:
            continue

        padrao = r"\b" + re.escape(expressao) + r"\b"

        if re.search(padrao, frase_lower):
            identificador = item.get("id")

            if identificador in ids_ja_encontrados:
                continue

            ids_ja_encontrados.add(identificador)
            encontradas.append(item)

    return encontradas


def preparar_texto_para_fala(texto):
    texto_fala = texto

    for item in sorted(
        BANCO,
        key=lambda x: len(x.get("expressao", "")),
        reverse=True
    ):
        expressao = item.get("expressao", "").strip()
        pronuncia = item.get("texto_fala", expressao).strip()

        if not expressao or not pronuncia:
            continue

        padrao = r"\b" + re.escape(expressao) + r"\b"

        texto_fala = re.sub(
            padrao,
            pronuncia,
            texto_fala,
            flags=re.IGNORECASE
        )

    return texto_fala


async def gerar_audio_edge_tts(texto, voz, rate, output_path):
    comunicacao = edge_tts.Communicate(texto, voz, rate=rate)
    await comunicacao.save(output_path)


def selecionar_musica_livre():
    pasta_musicas = BANCO_MUSICAS.get("pasta_musicas", PASTA_MUSICAS)

    if not os.path.exists(pasta_musicas):
        return None

    musicas_livres = [
        musica for musica in BANCO_MUSICAS.get("musicas", [])
        if musica.get("atribuicao_obrigatoria") is False
    ]

    if not musicas_livres:
        return None

    musica_escolhida = random.choice(musicas_livres)
    caminho = os.path.join(pasta_musicas, musica_escolhida.get("arquivo", ""))

    return caminho if os.path.exists(caminho) else None


def montar_audio_com_musica(narracao, usar_musica, volume_musica):
    if not usar_musica:
        return narracao

    caminho_musica = selecionar_musica_livre()

    if not caminho_musica:
        return narracao

    volume = volume_musica
    if volume is None:
        volume = BANCO_MUSICAS.get("volume_padrao", VOLUME_PADRAO_MUSICA)

    musica = AudioFileClip(caminho_musica)
    duracao = narracao.duration

    if musica.duration < duracao:
        repeticoes = int(duracao / musica.duration) + 1
        musica = concatenate_audioclips([musica] * repeticoes)

    musica = musica.subclip(0, duracao)
    musica = musica.volumex(volume)

    return CompositeAudioClip([narracao, musica])


@app.route("/api/falar", methods=["POST"])
def falar():
    dados = request.get_json(silent=True) or {}

    texto = dados.get("texto", "").strip()
    voz = dados.get("voz", VOZ_PADRAO)
    velocidade = dados.get("velocidade", "normal")
    usar_musica = dados.get("usar_musica", False)
    volume_musica = dados.get("volume_musica")

    if not texto:
        return jsonify({"erro": "Texto vazio"}), 400

    texto_para_tts = preparar_texto_para_fala(texto)
    rate = RATE_MAP.get(velocidade, "+0%")

    arquivo_audio = f"{uuid.uuid4().hex}.mp3"
    caminho_audio = os.path.join(PASTA_AUDIOS, arquivo_audio)

    try:
        asyncio.run(
            gerar_audio_edge_tts(
                texto_para_tts,
                voz,
                rate,
                caminho_audio
            )
        )

        return send_file(
            caminho_audio,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="sala_vip.mp3"
        )

    except Exception as erro:
        return jsonify({"erro": str(erro)}), 500


@app.route("/api/stats")
def stats():
    regioes = sorted(set(item.get("regiao", "Geral") for item in BANCO))

    return jsonify({
        "total_palavras": len(BANCO),
        "regioes": len(regioes),
        "lista_regioes": regioes,
        "musicas": len(BANCO_MUSICAS.get("musicas", [])),
        "status": "online"
    })


@app.route("/api/analisar", methods=["POST"])
def analisar():
    dados = request.get_json(silent=True) or {}
    frase = dados.get("frase", "").strip()

    if not frase:
        return jsonify({"erro": "Digite uma frase para analisar."}), 400

    girias = analisar_frase(frase)

    return jsonify({
        "frase": frase,
        "girias": girias,
        "total": len(girias)
    })


@app.route("/api/upload-imagem", methods=["POST"])
def upload_imagem():
    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem enviada."}), 400

    imagem = request.files["imagem"]

    if imagem.filename == "":
        return jsonify({"erro": "Nome de arquivo inválido."}), 400

    extensao = os.path.splitext(imagem.filename)[1].lower()

    if extensao not in [".jpg", ".jpeg", ".png", ".webp"]:
        return jsonify({"erro": "Use JPG, PNG ou WEBP."}), 400

    arquivo = f"{uuid.uuid4().hex}{extensao}"
    caminho = os.path.join(PASTA_TEMP, arquivo)
    imagem.save(caminho)

    return jsonify({
        "sucesso": True,
        "arquivo": arquivo,
        "url": f"/temp/{arquivo}"
    })


@app.route("/api/gerar-video", methods=["POST"])
def rota_gerar_video():
    dados = request.get_json(silent=True) or {}

    texto_narracao = dados.get("texto_narracao", "").strip()
    imagens = dados.get("imagens_paths", [])
    preco = dados.get("preco", "")
    cta = dados.get("cta", "")
    voz = dados.get("voz", VOZ_PADRAO)
    velocidade = dados.get("velocidade", "normal")
    usar_musica = dados.get("usar_musica", True)
    volume_musica = dados.get("volume_musica")

    if not texto_narracao:
        return jsonify({"sucesso": False, "erro": "Texto da narração é obrigatório."}), 400

    if not imagens:
        return jsonify({"sucesso": False, "erro": "Envie pelo menos uma imagem."}), 400

    imagens_validas = []

    for imagem in imagens:
        caminho = os.path.join(PASTA_TEMP, os.path.basename(imagem))
        if os.path.exists(caminho):
            imagens_validas.append(caminho)

    if not imagens_validas:
        return jsonify({"sucesso": False, "erro": "Nenhuma imagem válida encontrada."}), 400

    texto_para_tts = preparar_texto_para_fala(texto_narracao)
    rate = RATE_MAP.get(velocidade, "+0%")

    audio_temp = os.path.join(PASTA_TEMP, f"{uuid.uuid4().hex}.mp3")
    arquivo_video = f"{uuid.uuid4().hex}.mp4"
    caminho_video = os.path.join(PASTA_VIDEOS, arquivo_video)

    narracao = None
    imagens_temporarias = []

    try:
        asyncio.run(
            gerar_audio_edge_tts(
                texto_para_tts,
                voz,
                rate,
                audio_temp
            )
        )

        narracao = AudioFileClip(audio_temp)
        duracao_total = narracao.duration
        duracao_imagem = duracao_total / len(imagens_validas)

        audio_final = montar_audio_com_musica(
            narracao,
            usar_musica,
            volume_musica
        )

        clips = []

        for caminho_imagem in imagens_validas:
            imagem = Image.open(caminho_imagem).convert("RGB")
            imagem = imagem.resize((1080, 1920))

            desenho = ImageDraw.Draw(imagem)

            if cta:
                desenho.text((100, 100), cta, fill="white", font_size=60)

            if preco:
                desenho.text((100, 1800), preco, fill="yellow", font_size=80)

            imagem_temp = f"temp_{os.path.basename(caminho_imagem)}"
            imagem.save(imagem_temp)
            imagens_temporarias.append(imagem_temp)

            clipe = ImageClip(imagem_temp).set_duration(duracao_imagem)
            clips.append(clipe)

        video = concatenate_videoclips(clips, method="compose")

        try:
            video = video.with_audio(audio_final)
        except AttributeError:
            video = video.set_audio(audio_final)

        video.write_videofile(
            caminho_video,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            logger=None
        )

        return jsonify({
            "sucesso": True,
            "arquivo": arquivo_video,
            "url_video": f"/videos/{arquivo_video}",
            "texto_narracao_original": texto_narracao,
            "texto_narracao_tts": texto_para_tts,
            "musica_de_fundo": usar_musica
        })

    except Exception as erro:
        return jsonify({"sucesso": False, "erro": str(erro)}), 500

    finally:
        if narracao:
            narracao.close()

        if os.path.exists(audio_temp):
            os.remove(audio_temp)

        for imagem_temp in imagens_temporarias:
            if os.path.exists(imagem_temp):
                os.remove(imagem_temp)


@app.route("/videos/<path:arquivo>")
def servir_video(arquivo):
    return send_from_directory(PASTA_VIDEOS, arquivo)


@app.route("/audios/<path:arquivo>")
def servir_audio(arquivo):
    return send_from_directory(PASTA_AUDIOS, arquivo)


@app.route("/temp/<path:arquivo>")
def servir_temp(arquivo):
    return send_from_directory(PASTA_TEMP, arquivo)


HTML_COMPLETO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sala VIP — Gírias, Voz Neural e Vídeos</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }
body { background: #f5f0ff; color: #1a0a2e; padding: 20px; }
.container { max-width: 980px; margin: 0 auto; }
header { background: white; padding: 20px; border-radius: 16px; border: 2px solid #d8b4fe; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
.logo { font-size: 26px; font-weight: 900; color: #7c1dff; }
.status { background: #f5e9ff; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 700; }
.hero { background: linear-gradient(135deg, #7c1dff, #ff2d8f); color: white; padding: 38px; border-radius: 20px; margin-bottom: 20px; }
.hero h1 { font-size: 34px; margin-bottom: 10px; }
.hero p { font-size: 17px; opacity: .92; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
.stat-card { background: white; padding: 20px; border-radius: 16px; border: 2px solid #d8b4fe; text-align: center; }
.stat-card .numero { font-size: 34px; font-weight: 900; color: #7c1dff; }
.stat-card .label { font-size: 12px; color: #6b5a8a; font-weight: 700; text-transform: uppercase; }
.card { background: white; padding: 28px; border-radius: 20px; border: 2px solid #d8b4fe; margin-bottom: 20px; }
h2 { color: #7c1dff; margin-bottom: 15px; }
textarea, input, select { width: 100%; padding: 14px; border: 2px solid #d8b4fe; border-radius: 12px; font-size: 16px; margin-bottom: 12px; background: white; }
textarea { min-height: 110px; resize: vertical; }
textarea:focus, input:focus, select:focus { outline: none; border-color: #7c1dff; }
.btn { background: #7c1dff; color: white; border: none; padding: 13px 22px; border-radius: 10px; font-size: 16px; font-weight: 700; cursor: pointer; margin: 5px 8px 5px 0; }
.btn:hover { background: #6d28e0; }
.btn-audio { background: #ff2d8f; }
.btn-audio:hover { background: #e0267a; }
.btn-video { background: #111827; }
.btn-video:hover { background: #1f2937; }
.btn-stop { background: #6b5a8a; }
.audio-player, .video-player { background: #160a27; color: white; padding: 15px; border-radius: 12px; margin-top: 15px; display: none; }
.audio-player.ativo, .video-player.ativo { display: block; }
audio, video { width: 100%; margin-top: 10px; border-radius: 10px; }
.resultado { background: #160a27; color: white; padding: 20px; border-radius: 12px; margin-top: 20px; display: none; }
.resultado.ativo { display: block; }
.giria-card { background: #f5e9ff; border: 2px solid #d8b4fe; color: #1a0a2e; padding: 15px; border-radius: 12px; margin-top: 10px; }
.giria-card b { color: #7c1dff; font-size: 18px; }
.tag { background: #7c1dff; color: white; padding: 3px 9px; border-radius: 10px; font-size: 12px; margin-left: 8px; }
.upload-area { border: 2px dashed #d8b4fe; padding: 25px; border-radius: 14px; text-align: center; margin-bottom: 15px; }
.preview-imagens { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
.preview-imagens img { width: 90px; height: 120px; object-fit: cover; border-radius: 10px; border: 2px solid #d8b4fe; }
.aviso { font-size: 13px; color: #6b5a8a; margin-top: 8px; }
</style>
</head>
<body>
<div class="container">
<header>
<div class="logo">💜 Sala VIP</div>
<div class="status" id="status">Carregando...</div>
</header>

<div class="hero">
<h1>Sala VIP — Gírias Regionais com Voz Neural</h1>
<p>Digite uma frase, descubra as gírias, ouça a narração e gere vídeos verticais com música de fundo.</p>
</div>

<div class="stats">
<div class="stat-card"><div class="numero" id="totalGirias">-</div><div class="label">Gírias no banco</div></div>
<div class="stat-card"><div class="numero" id="totalRegioes">-</div><div class="label">Regiões</div></div>
<div class="stat-card"><div class="numero" id="totalMusicas">-</div><div class="label">Músicas livres</div></div>
</div>

<div class="card">
<h2>✍️ Analisar frase</h2>
<textarea id="fraseInput" placeholder="Ex: Oxe, esse kit tá arretado de bom, visse?">Oxe, esse kit tá arretado de bom, visse?</textarea>

<button class="btn" onclick="analisarFrase()">🔍 Analisar Frase</button>
<button class="btn btn-audio" onclick="gerarAudio()">🔊 Gerar Áudio</button>
<button class="btn btn-stop" onclick="pararAudio()">⏹️ Parar</button>

<div class="audio-player" id="audioPlayer">
<div id="statusAudio">⏳ Gerando áudio...</div>
<audio id="audioElement" controls></audio>
</div>

<div class="resultado" id="resultado">
<h3>🎯 Gírias detectadas: <span id="contador">0</span></h3>
<div id="listaGirias"></div>
</div>
</div>

<div class="card">
<h2>🎬 Gerar vídeo vertical</h2>

<div class="upload-area">
<input type="file" id="inputImagens" accept="image/*" multiple>
<p class="aviso">Envie uma ou mais imagens. Elas serão convertidas para 1080x1920.</p>
<div class="preview-imagens" id="previewImagens"></div>
</div>

<input type="text" id="precoInput" placeholder="Preço — ex: R$ 49,90">
<input type="text" id="ctaInput" placeholder="CTA — ex: Chama no WhatsApp">
<input type="text" id="textoVideoInput" placeholder="Texto da narração — ex: Oxe, esse kit tá arretado de bom, visse?">

<select id="vozSelect">
<option value="pt-BR-FranciscaNeural">Francisca — Feminina BR</option>
<option value="pt-BR-AntonioNeural">Antônio — Masculina BR</option>
<option value="pt-BR-BrendaNeural">Brenda — Feminina BR</option>
<option value="pt-BR-ElzaNeural">Elza — Feminina BR</option>
<option value="pt-BR-FabioNeural">Fábio — Masculina BR</option>
<option value="pt-BR-GiovannaNeural">Giovanna — Feminina BR</option>
<option value="pt-BR-LeilaNeural">Leila — Feminina BR</option>
<option value="pt-BR-LeticiaNeural">Letícia — Feminina BR</option>
<option value="pt-BR-ManuelaNeural">Manuela — Feminina BR</option>
<option value="pt-BR-NicolauNeural">Nicolau — Masculina BR</option>
<option value="pt-BR-ValerioNeural">Valério — Masculina BR</option>
<option value="pt-BR-YaraNeural">Yara — Feminina BR</option>
</select>

<select id="velocidadeSelect">
<option value="lenta">Lenta</option>
<option value="normal" selected>Normal</option>
<option value="rapida">Rápida</option>
</select>

<label style="display:block; margin-bottom:10px;">
<input type="checkbox" id="usarMusica" checked>
🎵 Colocar musiquinha de fundo
</label>

<select id="volumeMusica">
<option value="0.08">Música bem baixa</option>
<option value="0.12" selected>Música baixa</option>
<option value="0.18">Música média</option>
</select>

<button class="btn btn-video" onclick="gerarVideo()">🎬 Gerar Vídeo</button>

<div class="video-player" id="videoPlayer">
<div id="statusVideo">⏳ Gerando vídeo...</div>
<video id="videoElement" controls></video>
<a id="linkDownload" href="#" download="sala_vip.mp4" style="display:none; color:#d8b4fe; font-weight:700;">⬇️ Baixar vídeo</a>
</div>
</div>
</div>

<script>
const imagensEnviadas = [];

async function carregarStats() {
try {
const resposta = await fetch('/api/stats');
const dados = await resposta.json();

document.getElementById('totalGirias').textContent = dados.total_palavras;
document.getElementById('totalRegioes').textContent = dados.regioes;
document.getElementById('totalMusicas').textContent = dados.musicas;
document.getElementById('status').textContent = '🟢 Online • ' + dados.total_palavras + ' gírias';
} catch (erro) {
document.getElementById('status').textContent = '❌ Servidor offline';
}
}

async function analisarFrase() {
const frase = document.getElementById('fraseInput').value.trim();

if (!frase) {
alert('Digite uma frase primeiro.');
return;
}

try {
const resposta = await fetch('/api/analisar', {
method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify({frase})
});

const dados = await resposta.json();
const resultado = document.getElementById('resultado');
const contador = document.getElementById('contador');
const lista = document.getElementById('listaGirias');

resultado.classList.add('ativo');
contador.textContent = dados.total;

if (!dados.total) {
lista.innerHTML = '<p style="color:#ffef5e">Nenhuma gíria detectada.</p>';
return;
}

lista.innerHTML = dados.girias.map(giria => `
<div class="giria-card">
<b>${giria.expressao}</b>
<span class="tag">${giria.regiao}</span>
<div style="margin-top:8px;">${giria.significado}</div>
<div style="margin-top:6px; font-size:13px; opacity:.8;">
Exemplo: “${giria.exemplo || ''}”
</div>
</div>
`).join('');

} catch (erro) {
alert('Erro ao analisar a frase.');
}
}

async function gerarAudio() {
const texto = document.getElementById('fraseInput').value.trim();
const voz = document.getElementById('vozSelect').value;
const velocidade = document.getElementById('velocidadeSelect').value;
const usarMusica = document.getElementById('usarMusica').checked;
const volumeMusica = parseFloat(document.getElementById('volumeMusica').value);

if (!texto) {
alert('Digite uma frase primeiro.');
return;
}

const player = document.getElementById('audioPlayer');
const status = document.getElementById('statusAudio');
const audio = document.getElementById('audioElement');

player.classList.add('ativo');
status.textContent = '⏳ Gerando áudio com voz neural...';

try {
const resposta = await fetch('/api/falar', {
method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify({
texto,
voz,
velocidade,
usar_musica: usarMusica,
volume_musica: volumeMusica
})
});

if (!resposta.ok) throw new Error('Falha ao gerar áudio.');

const blob = await resposta.blob();
const url = URL.createObjectURL(blob);

audio.src = url;
status.textContent = '✅ Áudio pronto!';
audio.play();

} catch (erro) {
status.textContent = '❌ Erro: ' + erro.message;
}
}

function pararAudio() {
const audio = document.getElementById('audioElement');
audio.pause();
audio.currentTime = 0;
document.getElementById('statusAudio').textContent = '⏹️ Áudio parado.';
}

document.getElementById('inputImagens').addEventListener('change', async function () {
const arquivos = Array.from(this.files);

for (const arquivo of arquivos) {
await enviarImagem(arquivo);
}
});

async function enviarImagem(arquivo) {
const formulario = new FormData();
formulario.append('imagem', arquivo);

try {
const resposta = await fetch('/api/upload-imagem', {
method: 'POST',
body: formulario
});

const dados = await resposta.json();

if (!dados.sucesso) {
alert(dados.erro || 'Erro no upload.');
return;
}

imagensEnviadas.push(dados.arquivo);

const img = document.createElement('img');
img.src = dados.url;
document.getElementById('previewImagens').appendChild(img);

} catch (erro) {
alert('Erro ao enviar imagem.');
}
}

async function gerarVideo() {
const texto = document.getElementById('textoVideoInput').value.trim();
const preco = document.getElementById('precoInput').value.trim();
const cta = document.getElementById('ctaInput').value.trim();
const voz = document.getElementById('vozSelect').value;
const velocidade = document.getElementById('velocidadeSelect').value;
const usarMusica = document.getElementById('usarMusica').checked;
const volumeMusica = parseFloat(document.getElementById('volumeMusica').value);

if (!texto) {
alert('Digite o texto da narração.');
return;
}

if (!imagensEnviadas.length) {
alert('Envie pelo menos uma imagem.');
return;
}

const player = document.getElementById('videoPlayer');
const status = document.getElementById('statusVideo');
const video = document.getElementById('videoElement');
const link = document.getElementById('linkDownload');

player.classList.add('ativo');
status.textContent = '⏳ Gerando vídeo...';

try {
const resposta = await fetch('/api/gerar-video', {
method: 'POST',
headers: {'Content-Type': 'application/json'},
body: JSON.stringify({
texto_narracao: texto,
imagens_paths: imagensEnviadas,
preco,
cta,
voz,
velocidade,
usar_musica: usarMusica,
volume_musica: volumeMusica
})
});

const dados = await resposta.json();

if (!dados.sucesso) throw new Error(dados.erro || 'Erro ao gerar vídeo.');

video.src = dados.url_video;
link.href = dados.url_video;
link.style.display = 'inline-block';
status.textContent = '✅ Vídeo pronto!';
video.play();

} catch (erro) {
status.textContent = '❌ Erro: ' + erro.message;
}
}

carregarStats();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return HTML_COMPLETO, 200, {"Content-Type": "text/html; charset=utf-8"}


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 SALA VIP COMPLETO — UNIFICADO")
    print("=" * 60)
    print(f"📚 Gírias carregadas: {len(BANCO)}")
    print(f"🎵 Músicas livres cadastradas: {len(BANCO_MUSICAS.get('musicas', []))}")
    print("\n🌐 Acesse: http://localhost:5000")
    print("🔊 Voz neural: Microsoft Edge TTS")
    print("🎬 Vídeos verticais: 1080x1920")
    print("=" * 60 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=True)
