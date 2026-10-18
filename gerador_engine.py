import os
import re
import json
import asyncio
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from PIL import Image, ImageDraw, ImageFont

class DicionarioPovaoEngine:
    def __init__(self):
        self.dados = []
        self._carregar_ou_criar_padrao()

    def _carregar_ou_criar_padrao(self):
        if os.path.exists('dicionario.json'):
            with open('dicionario.json', 'r', encoding='utf-8') as f:
                self.dados = json.load(f)
        else:
            # Banco resumido para o exemplo (você pode colar os 90 itens aqui)
            self.dados = [
                {"expressao": "égua", "regiao": "Norte", "significado": "espanto", "peso": 98},
                {"expressao": "boró", "regiao": "Norte", "significado": "dinheiro", "peso": 95},
                {"expressao": "oxe", "regiao": "Nordeste", "significado": "espanto", "peso": 99},
                {"expressao": "arretado", "regiao": "Nordeste", "significado": "muito bom", "peso": 94},
                {"expressao": "mano", "regiao": "Sudeste", "significado": "amigo", "peso": 100},
                {"expressao": "trampo", "regiao": "Sudeste", "significado": "trabalho", "peso": 96},
                {"expressao": "bah", "regiao": "Sul", "significado": "espanto", "peso": 96},
                {"expressao": "tri", "regiao": "Sul", "significado": "muito", "peso": 93}
            ]
            with open('dicionario.json', 'w', encoding='utf-8') as f:
                json.dump(self.dados, f, ensure_ascii=False, indent=2)

    def analisar_frase(self, frase):
        frase_lower = frase.lower()
        encontradas = []
        for item in sorted(self.dados, key=lambda x: len(x.get('expressao', '')), reverse=True):
            expr = item.get('expressao', '').lower()
            if expr and re.search(r'\b' + re.escape(expr) + r'\b', frase_lower):
                encontradas.append(item)
        return encontradas

class GeradorVideo:
    def __init__(self, dicionario: DicionarioPovaoEngine):
        self.dicionario = dicionario

    def preprocessar_texto(self, texto):
        texto_proc = texto
        for item in self.dicionario.dados:
            expr = item.get('expressao', '')
            if expr and expr.lower() in texto_proc.lower():
                # Substitui pela expressão original para garantir que o TTS leia certo, 
                # ou você pode mapear para uma fonética se tiver no JSON
                pass 
        return texto_proc

    async def gerar_audio(self, texto, voz, rate, output_path):
        communicate = edge_tts.Communicate(texto, voz, rate=rate)
        await communicate.save(output_path)

    def gerar(self, texto_narracao, imagens_paths, preco, cta, voz_escolhida, velocidade, output_path="video_final.mp4"):
        try:
            # 1. Processa texto
            texto_proc = self.preprocessar_texto(texto_narracao)
            
            # 2. Gera Áudio
            rate_map = {"lenta": "-20%", "normal": "+0%", "rapida": "+20%"}
            audio_temp = "temp_narracao.mp3"
            asyncio.run(self.gerar_audio(texto_proc, voz_escolhida, rate_map.get(velocidade, "+0%"), audio_temp))
            
            # 3. Monta Vídeo
            audio_clip = AudioFileClip(audio_temp)
            duracao_total = audio_clip.duration
            duracao_img = duracao_total / len(imagens_paths)
            
            clips = []
            for img_path in imagens_paths:
                # Redimensiona e adiciona texto (simplificado)
                img = Image.open(img_path).convert("RGB").resize((1080, 1920))
                draw = ImageDraw.Draw(img)
                # Adiciona CTA e Preço (lógica simplificada)
                draw.text((100, 100), cta, fill="white", font_size=60)
                draw.text((100, 1800), preco, fill="yellow", font_size=80)
                
                temp_img = f"temp_{os.path.basename(img_path)}"
                img.save(temp_img)
                clips.append(ImageClip(temp_img).set_duration(duracao_img))
            
            video = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)
            video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
            
            # Limpeza
            os.remove(audio_temp)
            for img_path in imagens_paths:
                temp = f"temp_{os.path.basename(img_path)}"
                if os.path.exists(temp): os.remove(temp)
                
            return {"sucesso": True, "arquivo": output_path}
            
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}