import os
import re
import json
import random
import asyncio

import edge_tts
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    concatenate_audioclips,
    CompositeAudioClip
)
from PIL import Image, ImageDraw, ImageFont


PASTA_MUSICAS = "musicas"
ARQUIVO_BANCO_MUSICAS = "musicas_banco.json"
VOLUME_PADRAO_MUSICA = 0.12


class DicionarioPovaoEngine:
    def __init__(self, caminho_dicionario="dicionario.json"):
        self.caminho_dicionario = caminho_dicionario
        self.dados = []
        self._carregar_ou_criar_padrao()

    def _carregar_ou_criar_padrao(self):
        if os.path.exists(self.caminho_dicionario):
            with open(self.caminho_dicionario, "r", encoding="utf-8") as arquivo:
                self.dados = json.load(arquivo)
            return

        self.dados = [
            {
                "id": 1,
                "expressao": "égua",
                "regiao": "Norte",
                "estados": "PA, AM, AP",
                "significado": "expressão de espanto, admiração ou raiva",
                "exemplo": "Égua, esse calor tá demais!",
                "categoria": "interjeição",
                "formalidade": "popular",
                "texto_fala": "é gua",
                "peso": 98
            },
            {
                "id": 2,
                "expressao": "boró",
                "regiao": "Norte",
                "estados": "AM, PA",
                "significado": "dinheiro",
                "exemplo": "Tô sem nenhum boró hoje.",
                "categoria": "substantivo",
                "formalidade": "gíria",
                "texto_fala": "bo ró",
                "peso": 95
            },
            {
                "id": 3,
                "expressao": "oxe",
                "regiao": "Nordeste",
                "estados": "BA, PE, CE, SE, AL, PB, RN",
                "significado": "espanto, estranhamento",
                "exemplo": "Oxe, quem te disse isso?",
                "categoria": "interjeição",
                "formalidade": "popular",
                "texto_fala": "ó xi",
                "peso": 99
            },
            {
                "id": 4,
                "expressao": "arretado",
                "regiao": "Nordeste",
                "estados": "PE, PB, RN, CE",
                "significado": "bravo, irritado ou muito bom",
                "exemplo": "O forró tava arretado ontem!",
                "categoria": "adjetivo",
                "formalidade": "gíria",
                "texto_fala": "a he ta do",
                "peso": 94
            },
            {
                "id": 5,
                "expressao": "mano",
                "regiao": "Sudeste",
                "estados": "SP, RJ, MG, ES",
                "significado": "irmão, amigo, parceiro",
                "exemplo": "Fala, mano, tá suave?",
                "categoria": "vocativo",
                "formalidade": "gíria",
                "texto_fala": "ma nu",
                "peso": 100
            },
            {
                "id": 6,
                "expressao": "trampo",
                "regiao": "Sudeste",
                "estados": "SP, RJ, MG, ES",
                "significado": "trabalho",
                "exemplo": "Tô indo pro trampo.",
                "categoria": "substantivo",
                "formalidade": "gíria",
                "texto_fala": "tram po",
                "peso": 96
            },
            {
                "id": 7,
                "expressao": "bah",
                "regiao": "Sul",
                "estados": "RS, SC, PR",
                "significado": "espanto, admiração, decepção",
                "exemplo": "Bah, nem te conto o que aconteceu.",
                "categoria": "interjeição",
                "formalidade": "popular",
                "texto_fala": "bá",
                "peso": 96
            },
            {
                "id": 8,
                "expressao": "tri",
                "regiao": "Sul",
                "estados": "RS, SC",
                "significado": "muito",
                "exemplo": "Tava tri frio hoje de manhã.",
                "categoria": "advérbio",
                "formalidade": "gíria",
                "texto_fala": "tri",
                "peso": 93
            }
        ]

        with open(self.caminho_dicionario, "w", encoding="utf-8") as arquivo:
            json.dump(self.dados, arquivo, ensure_ascii=False, indent=2)

    def analisar_frase(self, frase):
        frase_lower = frase.lower()
        encontradas = []
        ids_ja_encontrados = set()

        itens_ordenados = sorted(
            self.dados,
            key=lambda item: len(item.get("expressao", "")),
            reverse=True
        )

        for item in itens_ordenados:
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


class GeradorVideo:
    def __init__(self, dicionario: DicionarioPovaoEngine):
        self.dicionario = dicionario

    def preprocessar_texto(self, texto):
        texto_processado = texto

        itens_ordenados = sorted(
            self.dicionario.dados,
            key=lambda item: len(item.get("expressao", "")),
            reverse=True
        )

        for item in itens_ordenados:
            expressao = item.get("expressao", "").strip()
            pronuncia = item.get("texto_fala", expressao).strip()

            if not expressao or not pronuncia:
                continue

            padrao = r"\b" + re.escape(expressao) + r"\b"

            texto_processado = re.sub(
                padrao,
                pronuncia,
                texto_processado,
                flags=re.IGNORECASE
            )

        return texto_processado

    async def gerar_audio(self, texto, voz, rate, output_path):
        comunicacao = edge_tts.Communicate(
            texto,
            voz,
            rate=rate
        )
        await comunicacao.save(output_path)

    def _carregar_banco_musicas(self):
        if not os.path.exists(ARQUIVO_BANCO_MUSICAS):
            return {
                "pasta_musicas": PASTA_MUSICAS,
                "volume_padrao": VOLUME_PADRAO_MUSICA,
                "usar_musica_por_padrao": True,
                "musicas": []
            }

        with open(ARQUIVO_BANCO_MUSICAS, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def _selecionar_musica(self):
        banco = self._carregar_banco_musicas()
        pasta_musicas = banco.get("pasta_musicas", PASTA_MUSICAS)

        if not os.path.exists(pasta_musicas):
            return None, banco.get("volume_padrao", VOLUME_PADRAO_MUSICA)

        musicas_livres = [
            musica for musica in banco.get("musicas", [])
            if musica.get("atribuicao_obrigatoria") is False
        ]

        if not musicas_livres:
            return None, banco.get("volume_padrao", VOLUME_PADRAO_MUSICA)

        musica_escolhida = random.choice(musicas_livres)
        caminho_musica = os.path.join(
            pasta_musicas,
            musica_escolhida.get("arquivo", "")
        )

        if not os.path.exists(caminho_musica):
            return None, banco.get("volume_padrao", VOLUME_PADRAO_MUSICA)

        return caminho_musica, banco.get("volume_padrao", VOLUME_PADRAO_MUSICA)

    def _montar_audio_final(self, narracao, usar_musica, volume_musica):
        if not usar_musica:
            return narracao, None

        caminho_musica, volume_padrao = self._selecionar_musica()

        if not caminho_musica:
            return narracao, None

        volume_final = volume_musica if volume_musica is not None else volume_padrao

        musica = AudioFileClip(caminho_musica)
        duracao_narracao = narracao.duration

        if musica.duration < duracao_narracao:
            repeticoes = int(duracao_narracao / musica.duration) + 1
            musica = concatenate_audioclips([musica] * repeticoes)

        musica = musica.subclip(0, duracao_narracao)
        musica = musica.volumex(volume_final)

        audio_final = CompositeAudioClip([
            narracao,
            musica
        ])

        return audio_final, musica

    def gerar(
        self,
        texto_narracao,
        imagens_paths,
        preco,
        cta,
        voz_escolhida,
        velocidade,
        usar_musica=True,
        volume_musica=None,
        output_path="video_final.mp4"
    ):
        narracao = None
        musica = None
        imagens_temporarias = []

        try:
            if not imagens_paths:
                raise ValueError("Nenhuma imagem foi enviada.")

            texto_para_tts = self.preprocessar_texto(texto_narracao)

            rate_map = {
                "lenta": "-20%",
                "normal": "+0%",
                "rapida": "+20%"
            }

            audio_temp = "temp_narracao.mp3"

            asyncio.run(
                self.gerar_audio(
                    texto_para_tts,
                    voz_escolhida,
                    rate_map.get(velocidade, "+0%"),
                    audio_temp
                )
            )

            narracao = AudioFileClip(audio_temp)
            duracao_total = narracao.duration
            duracao_imagem = duracao_total / len(imagens_paths)

            audio_final, musica = self._montar_audio_final(
                narracao,
                usar_musica,
                volume_musica
            )

            clips = []

            for caminho_imagem in imagens_paths:
                imagem = Image.open(caminho_imagem).convert("RGB")
                imagem = imagem.resize((1080, 1920))

                desenho = ImageDraw.Draw(imagem)

                if cta:
                    desenho.text(
                        (100, 100),
                        cta,
                        fill="white",
                        font_size=60
                    )

                if preco:
                    desenho.text(
                        (100, 1800),
                        preco,
                        fill="yellow",
                        font_size=80
                    )

                imagem_temporaria = f"temp_{os.path.basename(caminho_imagem)}"
                imagem.save(imagem_temporaria)
                imagens_temporarias.append(imagem_temporaria)

                clipe = ImageClip(imagem_temporaria).set_duration(duracao_imagem)
                clips.append(clipe)

            video = concatenate_videoclips(clips, method="compose")

            try:
                video = video.with_audio(audio_final)
            except AttributeError:
                video = video.set_audio(audio_final)

            video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None
            )

            return {
                "sucesso": True,
                "arquivo": output_path,
                "texto_narracao_original": texto_narracao,
                "texto_narracao_tts": texto_para_tts,
                "musica_de_fundo": bool(musica),
                "usar_musica": usar_musica
            }

        except Exception as erro:
            return {
                "sucesso": False,
                "erro": str(erro)
            }

        finally:
            if narracao:
                narracao.close()

            if musica:
                musica.close()

            if os.path.exists("temp_narracao.mp3"):
                os.remove("temp_narracao.mp3")

            for imagem_temporaria in imagens_temporarias:
                if os.path.exists(imagem_temporaria):
                    os.remove(imagem_temporaria)
