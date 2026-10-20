import os
import re
import json
import asyncio

import edge_tts
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips
)
from PIL import Image, ImageDraw, ImageFont


class DicionarioPovaoEngine:
    def __init__(self):
        self.dados = []
        self._carregar_ou_criar_padrao()

    def _carregar_ou_criar_padrao(self):
        if os.path.exists("dicionario.json"):
            with open("dicionario.json", "r", encoding="utf-8") as f:
                self.dados = json.load(f)
        else:
            self.dados = [
                {
                    "expressao": "égua",
                    "regiao": "Norte",
                    "significado": "espanto",
                    "texto_fala": "é gua",
                    "peso": 98
                },
                {
                    "expressao": "boró",
                    "regiao": "Norte",
                    "significado": "dinheiro",
                    "texto_fala": "bo ró",
                    "peso": 95
                },
                {
                    "expressao": "oxe",
                    "regiao": "Nordeste",
                    "significado": "espanto",
                    "texto_fala": "ó xi",
                    "peso": 99
                },
                {
                    "expressao": "arretado",
                    "regiao": "Nordeste",
                    "significado": "muito bom",
                    "texto_fala": "a he ta do",
                    "peso": 94
                },
                {
                    "expressao": "mano",
                    "regiao": "Sudeste",
                    "significado": "amigo",
                    "texto_fala": "ma nu",
                    "peso": 100
                },
                {
                    "expressao": "trampo",
                    "regiao": "Sudeste",
                    "significado": "trabalho",
                    "texto_fala": "tram po",
                    "peso": 96
                },
                {
                    "expressao": "bah",
                    "regiao": "Sul",
                    "significado": "espanto",
                    "texto_fala": "bá",
                    "peso": 96
                },
                {
                    "expressao": "tri",
                    "regiao": "Sul",
                    "significado": "muito",
                    "texto_fala": "tri",
                    "peso": 93
                }
            ]

            with open("dicionario.json", "w", encoding="utf-8") as f:
                json.dump(self.dados, f, ensure_ascii=False, indent=2)

    def analisar_frase(self, frase):
        frase_lower = frase.lower()
        encontradas = []

        for item in sorted(
            self.dados,
            key=lambda x: len(x.get("expressao", "")),
            reverse=True
        ):
            expressao = item.get("expressao", "").lower()

            if expressao and re.search(
                r"\b" + re.escape(expressao) + r"\b",
                frase_lower
            ):
                encontradas.append(item)

        return encontradas


class GeradorVideo:
    def __init__(self, dicionario: DicionarioPovaoEngine):
        self.dicionario = dicionario

    def preprocessar_texto(self, texto):
        texto_proc = texto

        for item in sorted(
            self.dicionario.dados,
            key=lambda x: len(x.get("expressao", "")),
            reverse=True
        ):
            expressao = item.get("expressao", "")
            pronuncia = item.get("texto_fala", expressao)

            if not expressao:
                continue

            texto_proc = re.sub(
                r"\b" + re.escape(expressao) + r"\b",
                pronuncia,
                texto_proc,
                flags=re.IGNORECASE
            )

        return texto_proc

    async def gerar_audio(self, texto, voz, rate, output_path):
        communicate = edge_tts.Communicate(
            texto,
            voz,
            rate=rate
        )
        await communicate.save(output_path)

    def gerar(
        self,
        texto_narracao,
        imagens_paths,
        preco,
        cta,
        voz_escolhida,
        velocidade,
        output_path="video_final.mp4"
    ):
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

            audio_clip = AudioFileClip(audio_temp)
            duracao_total = audio_clip.duration
            duracao_img = duracao_total / len(imagens_paths)

            clips = []
            imagens_temporarias = []

            for img_path in imagens_paths:
                img = Image.open(img_path).convert("RGB")
                img = img.resize((1080, 1920))

                draw = ImageDraw.Draw(img)

                if cta:
                    draw.text(
                        (100, 100),
                        cta,
                        fill="white",
                        font_size=60
                    )

                if preco:
                    draw.text(
                        (100, 1800),
                        preco,
                        fill="yellow",
                        font_size=80
                    )

                temp_img = f"temp_{os.path.basename(img_path)}"
                img.save(temp_img)
                imagens_temporarias.append(temp_img)

                clip = ImageClip(temp_img).set_duration(duracao_img)
                clips.append(clip)

            video = concatenate_videoclips(clips, method="compose")

            try:
                video = video.with_audio(audio_clip)
            except AttributeError:
                video = video.set_audio(audio_clip)

            video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                logger=None
            )

            audio_clip.close()
            video.close()

            if os.path.exists(audio_temp):
                os.remove(audio_temp)

            for temp_img in imagens_temporarias:
                if os.path.exists(temp_img):
                    os.remove(temp_img)

            return {
                "sucesso": True,
                "arquivo": output_path
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e)
            }
