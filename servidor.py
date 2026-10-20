from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

import os
import uuid
import asyncio

from gerador_engine import DicionarioPovaoEngine, GeradorVideo
import edge_tts


app = Flask(__name__)
CORS(app)

PASTA_TEMP = "temp"
PASTA_VIDEOS = "videos"
PASTA_AUDIOS = "audios"

os.makedirs(PASTA_TEMP, exist_ok=True)
os.makedirs(PASTA_VIDEOS, exist_ok=True)
os.makedirs(PASTA_AUDIOS, exist_ok=True)

dicionario = DicionarioPovaoEngine()
gerador = GeradorVideo(dicionario)


def nome_unico(extensao):
    return f"{uuid.uuid4().hex}{extensao}"


async def gerar_audio_edge_tts(texto, voz, rate, output_path):
    communicate = edge_tts.Communicate(
        texto,
        voz,
        rate=rate
    )
    await communicate.save(output_path)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/stats")
def stats():
    regioes = sorted(set(item.get("regiao", "Geral") for item in dicionario.dados))

    return jsonify({
        "total_palavras": len(dicionario.dados),
        "regioes": len(regioes),
        "lista_regioes": regioes,
        "status": "online"
    })


@app.route("/api/analisar", methods=["POST"])
def analisar():
    dados = request.get_json(silent=True) or {}
    frase = dados.get("frase", "").strip()

    if not frase:
        return jsonify({
            "erro": "Digite uma frase para analisar."
        }), 400

    girias = dicionario.analisar_frase(frase)

    return jsonify({
        "frase": frase,
        "girias": girias,
        "total": len(girias)
    })


@app.route("/api/falar", methods=["POST"])
def falar():
    dados = request.get_json(silent=True) or {}

    texto = dados.get("texto", "").strip()
    voz = dados.get("voz", "pt-BR-FranciscaNeural")
    velocidade = dados.get("velocidade", "normal")

    if not texto:
        return jsonify({
            "erro": "Texto vazio."
        }), 400

    rate_map = {
        "lenta": "-20%",
        "normal": "+0%",
        "rapida": "+20%"
    }

    rate = rate_map.get(velocidade, "+0%")
    texto_para_tts = gerador.preprocessar_texto(texto)

    arquivo_audio = nome_unico(".mp3")
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

    except Exception as e:
        return jsonify({
            "erro": f"Erro ao gerar áudio: {str(e)}"
        }), 500


@app.route("/api/gerar-video", methods=["POST"])
def gerar_video():
    dados = request.get_json(silent=True) or {}

    texto_narracao = dados.get("texto_narracao", "").strip()
    imagens_paths = dados.get("imagens_paths", [])
    preco = dados.get("preco", "")
    cta = dados.get("cta", "")
    voz_escolhida = dados.get("voz", "pt-BR-FranciscaNeural")
    velocidade = dados.get("velocidade", "normal")

    if not texto_narracao:
        return jsonify({
            "sucesso": False,
            "erro": "Texto da narração é obrigatório."
        }), 400

    if not imagens_paths:
        return jsonify({
            "sucesso": False,
            "erro": "Envie pelo menos uma imagem."
        }), 400

    imagens_validas = []

    for imagem in imagens_paths:
        caminho = os.path.join(PASTA_TEMP, os.path.basename(imagem))

        if os.path.exists(caminho):
            imagens_validas.append(caminho)

    if not imagens_validas:
        return jsonify({
            "sucesso": False,
            "erro": "Nenhuma imagem válida foi encontrada."
        }), 400

    arquivo_video = nome_unico(".mp4")
    caminho_video = os.path.join(PASTA_VIDEOS, arquivo_video)

    resultado = gerador.gerar(
        texto_narracao=texto_narracao,
        imagens_paths=imagens_validas,
        preco=preco,
        cta=cta,
        voz_escolhida=voz_escolhida,
        velocidade=velocidade,
        output_path=caminho_video
    )

    if not resultado.get("sucesso"):
        return jsonify(resultado), 500

    return jsonify({
        "sucesso": True,
        "arquivo": arquivo_video,
        "url_video": f"/videos/{arquivo_video}",
        "texto_narracao_original": resultado.get("texto_narracao_original"),
        "texto_narracao_tts": resultado.get("texto_narracao_tts")
    })


@app.route("/api/upload-imagem", methods=["POST"])
def upload_imagem():
    if "imagem" not in request.files:
        return jsonify({
            "erro": "Nenhuma imagem enviada."
        }), 400

    imagem = request.files["imagem"]

    if imagem.filename == "":
        return jsonify({
            "erro": "Nome de arquivo inválido."
        }), 400

    extensao = os.path.splitext(imagem.filename)[1].lower()

    if extensao not in [".jpg", ".jpeg", ".png", ".webp"]:
        return jsonify({
            "erro": "Formato inválido. Use JPG, PNG ou WEBP."
        }), 400

    arquivo = nome_unico(extensao)
    caminho = os.path.join(PASTA_TEMP, arquivo)

    imagem.save(caminho)

    return jsonify({
        "sucesso": True,
        "arquivo": arquivo,
        "url": f"/temp/{arquivo}"
    })


@app.route("/videos/<path:arquivo>")
def servir_video(arquivo):
    return send_from_directory(PASTA_VIDEOS, arquivo)


@app.route("/audios/<path:arquivo>")
def servir_audio(arquivo):
    return send_from_directory(PASTA_AUDIOS, arquivo)


@app.route("/temp/<path:arquivo>")
def servir_temp(arquivo):
    return send_from_directory(PASTA_TEMP, arquivo)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 SALA VIP — SERVIDOR COMPLETO")
    print("=" * 60)
    print(f"📚 Gírias carregadas: {len(dicionario.dados)}")
    print("🌐 Acesse: http://localhost:5000")
    print("🔊 Voz neural: Microsoft Edge TTS")
    print("=" * 60 + "\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
