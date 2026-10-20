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
    def __init__(self, caminho_dicionario="dicionario.json"):
        self.caminho_dicionario = caminho_dicionario
        self.dados = []
        self._carregar_ou_criar_padrao()

    def _carregar_ou_criar_padrao(self):
        if os.path.exists(self.caminho_dicionario):
            with open(self.caminho_dicionario, "r", encoding="utf-8") as f:
                self.dados = json.load(f)
        else:
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

            with open(self.caminho_dicionario, "w", encoding="utf-8") as f:
                json.dump(self.dados, f, ensure_ascii=False, indent=2)

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
                item_id = item.get("id")

                if item_id in ids_ja_encontrados:
                    continue

                ids_ja_encontrados.add(item_id)
                encontradas.append(item)

        return encontradas


class GeradorVideo:
    def __init__(self, dicionario: DicionarioPovaoEngine):
        self.dicionario = dicionario

    def preprocessar_texto(self, texto):
        texto_proc = texto

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

            texto_proc = re.sub(
                padrao,
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
                "arquivo": output_path,
                "texto_narracao_original": texto_narracao,
                "texto_narracao_tts": texto_para_tts
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e)
            }
