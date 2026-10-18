"""
SALA VIP - VERSÃO BOTÃO ÚNICO
Um botão faz tudo: analisa + fala + mostra resultado
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
# BANCO DE DADOS (30 gírias principais)
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
# FUNÇÕES
# ============================================================
def analisar_frase(frase):
    frase_lower = frase.lower()
    encontradas = []
    for item in sorted(BANCO, key=lambda x: len(x.get('expressao', '')), reverse=True):
        expr = item.get('expressao', '').lower()
        if expr and re.search(r'\b' + re.escape(expr) + r'\b', frase_lower):
            encontradas.append(item)
    return encontradas

async def gerar_audio_edge_tts(texto, voz, output_path):
    communicate = edge_tts.Communicate(texto, voz)
    await communicate.save(output_path)

@app.route('/api/falar', methods=['POST'])
def falar():
    dados = request.json
    texto = dados.get('texto', '')
    voz = dados.get('voz', 'pt-BR-FranciscaNeural')
    
    if not texto:
        return jsonify({"erro": "Texto vazio"}), 400
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tmp_path = tmp.name
        
        asyncio.run(gerar_audio_edge_tts(texto, voz, tmp_path))
        return send_file(tmp_path, mimetype='audio/mpeg', as_attachment=False)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/analisar', methods=['POST'])
def analisar():
    dados = request.json
    frase = dados.get('frase', '')
    encontradas = analisar_frase(frase)
    return jsonify({
        "girias": encontradas,
        "total": len(encontradas)
    })

@app.route('/api/stats')
def stats():
    regioes = list(set(item['regiao'] for item in BANCO))
    return jsonify({
        "total_palavras": len(BANCO),
        "regioes": len(regioes),
        "status": "online"
    })

# ============================================================
# HTML COMPLETO - BOTÃO ÚNICO
# ============================================================
HTML_COMPLETO = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sala VIP - Botão Único</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }
body { background: #f5f0ff; color: #1a0a2e; padding: 20px; min-height: 100vh; }
.container { max-width: 800px; margin: 0 auto; }

header { 
    background: white; 
    padding: 20px; 
    border-radius: 16px; 
    border: 2px solid #d8b4fe; 
    margin-bottom: 20px; 
    display: flex; 
    justify-content: space-between; 
    align-items: center; 
}
.logo { font-size: 24px; font-weight: 900; color: #7c1dff; }
.status { background: #f5e9ff; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 700; }

.hero { 
    background: linear-gradient(135deg, #7c1dff, #ff2d8f); 
    color: white; 
    padding: 30px; 
    border-radius: 20px; 
    margin-bottom: 20px; 
    text-align: center;
}
.hero h1 { font-size: 32px; margin-bottom: 10px; }
.hero p { font-size: 16px; opacity: 0.9; }

.card { 
    background: white; 
    padding: 30px; 
    border-radius: 20px; 
    border: 2px solid #d8b4fe; 
    margin-bottom: 20px; 
}
.card h2 { color: #7c1dff; margin-bottom: 15px; text-align: center; }

textarea { 
    width: 100%; 
    min-height: 120px; 
    padding: 15px; 
    border: 2px solid #d8b4fe; 
    border-radius: 12px; 
    font-size: 16px; 
    resize: vertical; 
    font-family: inherit;
}
textarea:focus { outline: none; border-color: #7c1dff; }

/* BOTÃO ÚNICO GIGANTE */
.btn-unico {
    width: 100%;
    padding: 20px;
    font-size: 20px;
    font-weight: 900;
    color: white;
    background: linear-gradient(135deg, #7c1dff, #ff2d8f);
    border: none;
    border-radius: 16px;
    cursor: pointer;
    margin-top: 20px;
    transition: all 0.3s;
    box-shadow: 0 8px 20px rgba(124, 29, 255, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}
.btn-unico:hover { 
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(124, 29, 255, 0.4);
}
.btn-unico:active { transform: translateY(0); }
.btn-unico:disabled { 
    opacity: 0.6; 
    cursor: not-allowed;
    transform: none;
}

/* Botão Parar (aparece só quando está falando) */
.btn-parar {
    width: 100%;
    padding: 15px;
    font-size: 16px;
    font-weight: 700;
    color: white;
    background: #6b5a8a;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    margin-top: 10px;
    display: none;
}
.btn-parar.ativo { display: block; }
.btn-parar:hover { background: #5a4a75; }

/* Status */
.status-msg {
    text-align: center;
    padding: 12px;
    border-radius: 12px;
    margin-top: 15px;
    font-weight: 700;
    display: none;
}
.status-msg.ativo { display: block; }
.status-msg.analisando { background: #f5e9ff; color: #7c1dff; }
.status-msg.falando { background: #fff0f5; color: #ff2d8f; }
.status-msg.erro { background: #ffe0e0; color: #c00; }
.status-msg.sucesso { background: #e0ffe0; color: #060; }

/* Player de áudio */
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

/* Resultado */
.resultado { 
    background: #160a27; 
    color: white; 
    padding: 20px; 
    border-radius: 12px; 
    margin-top: 20px; 
    display: none; 
}
.resultado.ativo { display: block; }
.giria-card { 
    background: #f5e9ff; 
    border: 2px solid #d8b4fe; 
    padding: 12px; 
    border-radius: 10px; 
    margin-top: 10px;
    color: #1a0a2e;
}
.giria-card b { color: #7c1dff; font-size: 16px; }
.regiao-tag { 
    background: #7c1dff; 
    color: white; 
    padding: 2px 8px; 
    border-radius: 10px; 
    font-size: 11px; 
    margin-left: 8px; 
}

/* Animação de carregamento */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
.carregando { animation: pulse 1s infinite; }
</style>
</head>
<body>
<div class="container">

<header>
    <div class="logo">💜 Sala VIP</div>
    <div class="status" id="status">Carregando...</div>
</header>

<div class="hero">
    <h1>🎯 Botão Único</h1>
    <p>Digite sua frase e aperte o botão. A IA analisa E fala pra você!</p>
</div>

<div class="card">
    <h2>✍️ Escreva sua frase</h2>
    <textarea id="fraseInput" placeholder="Ex: mano tô sem boró, deu ruim no trampo">mano tô sem boró, deu ruim</textarea>
    
    <!-- BOTÃO ÚNICO -->
    <button class="btn-unico" id="btnUnico" onclick="fazerTudo()">
        <span id="btnIcono">🎯</span>
        <span id="btnTexto">ANALISAR E FALAR</span>
    </button>
    
    <!-- Botão Parar (aparece só quando está falando) -->
    <button class="btn-parar" id="btnParar" onclick="pararTudo()">
        ⏹️ PARAR ÁUDIO
    </button>
    
    <!-- Status -->
    <div class="status-msg" id="statusMsg"></div>
    
    <!-- Player de áudio -->
    <div class="audio-player" id="audioPlayer">
        <div id="statusAudio">🎵 Áudio pronto!</div>
        <audio id="audioElement" controls></audio>
    </div>
    
    <!-- Resultado -->
    <div class="resultado" id="resultado">
        <h3>🎯 Gírias detectadas: <span id="contador">0</span></h3>
        <div id="listaGirias"></div>
    </div>
</div>

</div>

<script>
let audioAtual = null;
let estaFalando = false;

// Carrega stats
async function carregarStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        document.getElementById('status').textContent = '🟢 Online • ' + data.total_palavras + ' palavras';
    } catch(e) {
        document.getElementById('status').textContent = '❌ Erro';
    }
}

// MOSTRA STATUS
function mostrarStatus(msg, tipo) {
    const el = document.getElementById('statusMsg');
    el.textContent = msg;
    el.className = 'status-msg ativo ' + tipo;
}

function esconderStatus() {
    document.getElementById('statusMsg').className = 'status-msg';
}

// BOTÃO ÚNICO - FAZ TUDO!
async function fazerTudo() {
    const frase = document.getElementById('fraseInput').value;
    if (!frase.trim()) {
        mostrarStatus('⚠️ Escreva uma frase primeiro!', 'erro');
        return;
    }
    
    const btn = document.getElementById('btnUnico');
    const btnIcono = document.getElementById('btnIcono');
    const btnTexto = document.getElementById('btnTexto');
    const btnParar = document.getElementById('btnParar');
    
    // Desabilita o botão
    btn.disabled = true;
    estaFalando = true;
    
    // PASSO 1: ANALISAR
    btnIcono.textContent = '🔍';
    btnTexto.textContent = 'ANALISANDO...';
    mostrarStatus('🔍 Analisando gírias...', 'analisando');
    
    try {
        const res = await fetch('/api/analisar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({frase})
        });
        const data = await res.json();
        
        // Mostra resultado
        const resultado = document.getElementById('resultado');
        const contador = document.getElementById('contador');
        const lista = document.getElementById('listaGirias');
        
        resultado.classList.add('ativo');
        contador.textContent = data.total;
        
        if (data.total === 0) {
            lista.innerHTML = '<p style="color:#ffef5e">Nenhuma gíria detectada.</p>';
        } else {
            lista.innerHTML = data.girias.map(g => `
                <div class="giria-card">
                    <b>${g.expressao}</b><span class="regiao-tag">${g.regiao}</span>
                    <div style="margin-top:5px">${g.significado}</div>
                    <div style="margin-top:3px;font-size:12px;opacity:0.8">Ex: "${g.exemplo}"</div>
                </div>
            `).join('');
        }
        
        // PASSO 2: GERAR ÁUDIO
        btnIcono.textContent = '🔊';
        btnTexto.textContent = 'GERANDO ÁUDIO...';
        mostrarStatus('🔊 Gerando voz neural...', 'analisando');
        
        const resAudio = await fetch('/api/falar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                texto: frase,
                voz: 'pt-BR-FranciscaNeural'
            })
        });
        
        if (!resAudio.ok) throw new Error('Erro ao gerar áudio');
        
        const blob = await resAudio.blob();
        const url = URL.createObjectURL(blob);
        
        const audioPlayer = document.getElementById('audioPlayer');
        const audioElement = document.getElementById('audioElement');
        const statusAudio = document.getElementById('statusAudio');
        
        audioElement.src = url;
        audioPlayer.classList.add('ativo');
        statusAudio.textContent = '🎵 Áudio pronto! Tocando...';
        
        // Toca automaticamente
        await audioElement.play();
        
        // Mostra botão parar
        btnParar.classList.add('ativo');
        mostrarStatus('🔊 Falando...', 'falando');
        
        // Quando terminar de tocar
        audioElement.onended = () => {
            estaFalando = false;
            btn.disabled = false;
            btnIcono.textContent = '🎯';
            btnTexto.textContent = 'ANALISAR E FALAR';
            btnParar.classList.remove('ativo');
            mostrarStatus('✅ Concluído!', 'sucesso');
            setTimeout(esconderStatus, 3000);
        };
        
    } catch(e) {
        btn.disabled = false;
        btnIcono.textContent = '🎯';
        btnTexto.textContent = 'ANALISAR E FALAR';
        btnParar.classList.remove('ativo');
        mostrarStatus('❌ Erro: ' + e.message, 'erro');
        estaFalando = false;
    }
}

// PARAR TUDO
function pararTudo() {
    const audioElement = document.getElementById('audioElement');
    audioElement.pause();
    audioElement.currentTime = 0;
    
    const btn = document.getElementById('btnUnico');
    const btnIcono = document.getElementById('btnIcono');
    const btnTexto = document.getElementById('btnTexto');
    const btnParar = document.getElementById('btnParar');
    
    btn.disabled = false;
    btnIcono.textContent = '🎯';
    btnTexto.textContent = 'ANALISAR E FALAR';
    btnParar.classList.remove('ativo');
    estaFalando = false;
    
    mostrarStatus('⏹️ Parado', 'sucesso');
    setTimeout(esconderStatus, 2000);
}

// Inicializa
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
    print("🚀 SALA VIP - BOTÃO ÚNICO")
    print("="*60)
    print(f"📚 Gírias: {len(BANCO)}")
    print("\n🌐 Acesse: http://localhost:5000")
    print(" UM BOTÃO FAZ TUDO!")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)