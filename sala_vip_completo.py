"""
SALA VIP COMPLETO - Interface Web + Geração de Voz Real
Um único arquivo que faz tudo!
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import edge_tts
import asyncio
import os
import re
import tempfile

app = Flask(__name__)
CORS(app)

# ============================================================
# BANCO DE DADOS (60 gírias)
# ============================================================
BANCO = [
    {"expressao": "égua", "regiao": "Norte", "significado": "espanto, admiração", "exemplo": "Égua, que calor!", "peso": 98},
    {"expressao": "boró", "regiao": "Norte", "significado": "dinheiro", "exemplo": "Tô sem boró", "peso": 95},
    {"expressao": "leso", "regiao": "Norte", "significado": "lerdo, bobo", "exemplo": "Não seja leso", "peso": 76},
    {"expressao": "oxe", "regiao": "Nordeste", "significado": "espanto, surpresa", "exemplo": "Oxe, cadê meu pedido?", "peso": 99},
    {"expressao": "visse", "regiao": "Nordeste", "significado": "viu? entendeu?", "exemplo": "Ficou pronto, visse?", "peso": 97},
    {"expressao": "arretado", "regiao": "Nordeste", "significado": "muito bom, brabo", "exemplo": "Preço arretado de bom", "peso": 94},
    {"expressao": "mainha", "regiao": "Nordeste", "significado": "minha mãe", "exemplo": "Mainha vai amar", "peso": 88},
    {"expressao": "aperreado", "regiao": "Nordeste", "significado": "agoniado, apressado", "exemplo": "Tô aperreada", "peso": 82},
    {"expressao": "perrengue", "regiao": "Nordeste", "significado": "dificuldade, sufoco", "exemplo": "Tô no perrengue", "peso": 81},
    {"expressao": "bah", "regiao": "Sul", "significado": "espanto, nossa", "exemplo": "Bah, que frio!", "peso": 96},
    {"expressao": "tri", "regiao": "Sul", "significado": "muito, super", "exemplo": "Tri bonita", "peso": 93},
    {"expressao": "guri", "regiao": "Sul", "significado": "menino", "exemplo": "Os guri mandaram bem", "peso": 85},
    {"expressao": "capaz", "regiao": "Sul", "significado": "duvida, claro que não", "exemplo": "Capaz que vou perder", "peso": 90},
    {"expressao": "mano", "regiao": "Sudeste", "significado": "amigo, irmão", "exemplo": "Mano, tô sem boró", "peso": 100},
    {"expressao": "trampo", "regiao": "Sudeste", "significado": "trabalho", "exemplo": "Tô no trampo", "peso": 96},
    {"expressao": "rolê", "regiao": "Sudeste", "significado": "passeio", "exemplo": "Bora dar um rolê", "peso": 89},
    {"expressao": "da hora", "regiao": "Sudeste", "significado": "legal, massa", "exemplo": "Kit da hora", "peso": 87},
    {"expressao": "suave", "regiao": "Sudeste", "significado": "tranquilo", "exemplo": "Suave? Já enviei", "peso": 92},
    {"expressao": "caô", "regiao": "Sudeste", "significado": "mentira", "exemplo": "Isso é caô", "peso": 75},
    {"expressao": "parça", "regiao": "Sudeste", "significado": "parceiro", "exemplo": "Valeu parça", "peso": 83},
    {"expressao": "trem", "regiao": "Sudeste", "significado": "coisa, negócio", "exemplo": "Que trem barato", "peso": 80},
    {"expressao": "uai", "regiao": "Sudeste", "significado": "espanto (MG)", "exemplo": "Uai, sô!", "peso": 78},
    {"expressao": "bolado", "regiao": "Sudeste", "significado": "chateado", "exemplo": "Fiquei bolado", "peso": 71},
    {"expressao": "zica", "regiao": "Sudeste", "significado": "ruim ou bom", "exemplo": "Tá zica de bom", "peso": 70},
    {"expressao": "partiu", "regiao": "Geral", "significado": "vamos embora", "exemplo": "Partiu vender", "peso": 88},
    {"expressao": "lacrar", "regiao": "Geral", "significado": "arrasar", "exemplo": "Você lacrou", "peso": 84},
    {"expressao": "correria", "regiao": "Geral", "significado": "rotina puxada", "exemplo": "Tô na correria", "peso": 82},
    {"expressao": "pindaíba", "regiao": "Geral", "significado": "sem dinheiro", "exemplo": "Tô na pindaíba", "peso": 77},
    {"expressao": "deu ruim", "regiao": "Geral", "significado": "deu errado", "exemplo": "Deu ruim na entrega", "peso": 85},
    {"expressao": "dar um corre", "regiao": "Geral", "significado": "resolver", "exemplo": "Vou dar um corre", "peso": 81},
]

# ============================================================
# FUNÇÕES DE ANÁLISE
# ============================================================
def analisar_frase(frase):
    frase_lower = frase.lower()
    encontradas = []
    for item in sorted(BANCO, key=lambda x: len(x.get('expressao', '')), reverse=True):
        expr = item.get('expressao', '').lower()
        if expr and re.search(r'\b' + re.escape(expr) + r'\b', frase_lower):
            encontradas.append(item)
    return encontradas

# ============================================================
# GERAÇÃO DE ÁUDIO COM EDGE-TTS (VOZ REAL!)
# ============================================================
async def gerar_audio_edge_tts(texto, voz, output_path):
    """Gera áudio usando Microsoft Edge TTS (voz neural gratuita)"""
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(output_path)

@app.route('/api/falar', methods=['POST'])
def falar():
    """Endpoint que gera áudio real e retorna para o navegador"""
    dados = request.json
    texto = dados.get('texto', '')
    voz = dados.get('voz', 'pt-BR-FranciscaNeural')
    
    if not texto:
        return jsonify({"erro": "Texto vazio"}), 400
    
    try:
        # Cria arquivo temporário
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp_path = tmp.name
        
        # Gera o áudio com edge-tts
        asyncio.run(gerar_audio_edge_tts(texto, voz, tmp_path))
        
        # Retorna o arquivo de áudio
        return send_file(tmp_path, mimetype='audio/mpeg', as_attachment=False)
    
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

# ============================================================
# ROTAS DA API
# ============================================================
@app.route('/api/stats')
def stats():
    regioes = list(set(item['regiao'] for item in BANCO))
    return jsonify({
        "total_palavras": len(BANCO),
        "regioes": len(regioes),
        "status": "online"
    })

@app.route('/api/analisar', methods=['POST'])
def analisar():
    dados = request.json
    frase = dados.get('frase', '')
    encontradas = analisar_frase(frase)
    return jsonify({
        "girias": encontradas,
        "total": len(encontradas)
    })

# ============================================================
# HTML EMBUTIDO (Interface Bonita)
# ============================================================
HTML_COMPLETO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sala VIP - Com Voz Real</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }
body { background: #f5f0ff; color: #1a0a2e; padding: 20px; }
.container { max-width: 900px; margin: 0 auto; }
header { background: white; padding: 20px; border-radius: 16px; border: 2px solid #d8b4fe; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
.logo { font-size: 24px; font-weight: 900; color: #7c1dff; }
.status { background: #f5e9ff; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 700; }

.hero { background: linear-gradient(135deg, #7c1dff, #ff2d8f); color: white; padding: 40px; border-radius: 20px; margin-bottom: 20px; }
.hero h1 { font-size: 36px; margin-bottom: 10px; }
.hero p { font-size: 18px; opacity: 0.9; }

.analyzer { background: white; padding: 30px; border-radius: 20px; border: 2px solid #d8b4fe; margin-bottom: 20px; }
.analyzer h2 { color: #7c1dff; margin-bottom: 15px; }
textarea { width: 100%; min-height: 100px; padding: 15px; border: 2px solid #d8b4fe; border-radius: 12px; font-size: 16px; resize: vertical; }
textarea:focus { outline: none; border-color: #7c1dff; }

.btn { background: #7c1dff; color: white; border: none; padding: 12px 24px; border-radius: 10px; font-size: 16px; font-weight: 700; cursor: pointer; margin-top: 10px; margin-right: 10px; }
.btn:hover { background: #6d28e0; }
.btn-audio { background: #ff2d8f; }
.btn-audio:hover { background: #e0267a; }
.btn-stop { background: #6b5a8a; }

.audio-player {
    background: #160a27;
    color: white;
    padding: 15px;
    border-radius: 12px;
    margin-top: 15px;
    display: none;
}
.audio-player.ativo { display: block; }
.audio-player audio { width: 100%; margin-top: 10px; }

.resultado { background: #160a27; color: white; padding: 20px; border-radius: 12px; margin-top: 20px; display: none; }
.resultado.ativo { display: block; }
.giria-card { background: #f5e9ff; border: 2px solid #d8b4fe; padding: 15px; border-radius: 12px; margin-top: 10px; }
.giria-card b { color: #7c1dff; font-size: 18px; }
.regiao-tag { background: #7c1dff; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-left: 10px; }

.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
.stat-card { background: white; padding: 20px; border-radius: 16px; border: 2px solid #d8b4fe; text-align: center; }
.stat-card .numero { font-size: 36px; font-weight: 900; color: #7c1dff; }
.stat-card .label { font-size: 12px; color: #6b5a8a; font-weight: 700; text-transform: uppercase; }
</style>
</head>
<body>
<div class="container">
<header>
<div class="logo">💜 Sala VIP</div>
<div class="status" id="status">Carregando...</div>
</header>

<div class="hero">
<h1>Sala VIP - Com Voz Real</h1>
<p>Digite uma frase, analise as gírias e OUÇA a narração com voz neural!</p>
</div>

<div class="stats">
<div class="stat-card">
<div class="numero" id="totalGirias">-</div>
<div class="label">Total de Gírias</div>
</div>
<div class="stat-card">
<div class="numero" id="totalRegioes">-</div>
<div class="label">Regiões</div>
</div>
<div class="stat-card">
<div class="numero"></div>
<div class="label">Voz Neural</div>
</div>
</div>

<div class="analyzer">
<h2>✍️ Teste sua frase</h2>
<textarea id="fraseInput" placeholder="Ex: mano tô sem boró, deu ruim no trampo, bah visse?">mano tô sem boró, deu ruim</textarea>

<br>
<button class="btn" onclick="analisar()"> Analisar Frase</button>
<button class="btn btn-audio" onclick="gerarAudio()">🔊 Gerar Áudio (Voz Real)</button>
<button class="btn btn-stop" onclick="pararAudio()">️ Parar</button>

<div class="audio-player" id="audioPlayer">
<div id="statusAudio">⏳ Gerando áudio...</div>
<audio id="audioElement" controls></audio>
</div>

<div class="resultado" id="resultado">
<h3>🎯 Gírias detectadas: <span id="contador">0</span></h3>
<div id="listaGirias"></div>
</div>
</div>
</div>

<script>
async function carregarStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('totalGirias').textContent = data.total_palavras;
        document.getElementById('totalRegioes').textContent = data.regioes;
        document.getElementById('status').textContent = '🟢 Online • ' + data.total_palavras + ' palavras';
    } catch(e) {
        document.getElementById('status').textContent = '❌ Erro';
    }
}

async function analisar() {
    const frase = document.getElementById('fraseInput').value;
    if (!frase.trim()) {
        alert('Digite uma frase primeiro!');
        return;
    }
    
    try {
        const res = await fetch('/api/analisar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({frase})
        });
        const data = await res.json();
        
        const resultado = document.getElementById('resultado');
        const contador = document.getElementById('contador');
        const lista = document.getElementById('listaGirias');
        
        resultado.classList.add('ativo');
        contador.textContent = data.total;
        
        if (data.total === 0) {
            lista.innerHTML = '<p style="color:#ffef5e">Nenhuma gíria detectada. Tente: "mano tô sem boró"</p>';
        } else {
            lista.innerHTML = data.girias.map(g => `
                <div class="giria-card">
                    <b>${g.expressao}</b><span class="regiao-tag">${g.regiao}</span>
                    <div style="margin-top:8px">${g.significado}</div>
                    <div style="margin-top:5px;font-size:13px;opacity:0.8">Ex: "${g.exemplo}"</div>
                </div>
            `).join('');
        }
    } catch(e) {
        alert('Erro: ' + e.message);
    }
}

async function gerarAudio() {
    const texto = document.getElementById('fraseInput').value;
    if (!texto.trim()) {
        alert('Digite uma frase primeiro!');
        return;
    }
    
    const audioPlayer = document.getElementById('audioPlayer');
    const statusAudio = document.getElementById('statusAudio');
    const audioElement = document.getElementById('audioElement');
    
    audioPlayer.classList.add('ativo');
    statusAudio.textContent = '⏳ Gerando áudio com voz neural...';
    
    try {
        const res = await fetch('/api/falar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                texto: texto,
                voz: 'pt-BR-FranciscaNeural'
            })
        });
        
        if (!res.ok) {
            throw new Error('Erro ao gerar áudio');
        }
        
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        
        audioElement.src = url;
        statusAudio.textContent = '✅ Áudio pronto! Clique play para ouvir.';
        audioElement.play();
        
    } catch(e) {
        statusAudio.textContent = '❌ Erro: ' + e.message;
    }
}

function pararAudio() {
    const audioElement = document.getElementById('audioElement');
    audioElement.pause();
    audioElement.currentTime = 0;
    document.getElementById('statusAudio').textContent = '⏹️ Parado';
}

carregarStats();
</script>
</body>
</html>"""

@app.route('/')
def index():
    return HTML_COMPLETO, 200, {'Content-Type': 'text/html; charset=utf-8'}

# ============================================================
# INICIAR
# ============================================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 SALA VIP COMPLETO - Interface + Voz Real")
    print("="*60)
    print(f"📚 Gírias: {len(BANCO)}")
    print("\n🌐 Acesse: http://localhost:5000")
    print("🔊 O áudio é gerado com Microsoft Edge TTS (voz neural)")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)