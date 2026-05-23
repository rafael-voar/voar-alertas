import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
from models import db, Demanda, Alerta
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'voar-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///voar.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Inicia o agendador de verificações automáticas
from scheduler import iniciar_scheduler
iniciar_scheduler(app)


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    demandas = Demanda.query.order_by(Demanda.criado_em.desc()).all()
    total_alertas = Alerta.query.filter_by(email_enviado=True).count()
    demandas_ativas = Demanda.query.filter_by(ativo=True).count()
    return render_template('index.html',
                           demandas=demandas,
                           total_alertas=total_alertas,
                           demandas_ativas=demandas_ativas)


# ─── ADICIONAR DEMANDA ────────────────────────────────────────────────────────

@app.route('/nova', methods=['GET', 'POST'])
def nova_demanda():
    if request.method == 'POST':
        try:
            demanda = Demanda(
                cliente_nome=request.form['cliente_nome'].strip(),
                cliente_email=request.form['cliente_email'].strip().lower(),
                origem=request.form['origem'].strip().upper(),
                destino=request.form['destino'].strip().upper(),
                data_ida=request.form['data_ida'],
                data_volta=request.form.get('data_volta') or None,
                adultos=int(request.form.get('adultos', 1)),
                preco_alvo=float(request.form['preco_alvo'].replace(',', '.')),
                flexibilidade=request.form.get('flexibilidade', '').strip() or None,
                moeda=request.form.get('moeda', 'BRL')
            )
            db.session.add(demanda)
            db.session.commit()
            flash(f'✅ Demanda de {demanda.cliente_nome} cadastrada com sucesso! Monitoramento iniciado.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'❌ Erro ao cadastrar demanda: {str(e)}', 'error')

    return render_template('nova_demanda.html')


# ─── DETALHES DA DEMANDA ──────────────────────────────────────────────────────

@app.route('/demanda/<int:id>')
def ver_demanda(id):
    demanda = Demanda.query.get_or_404(id)
    alertas = Alerta.query.filter_by(demanda_id=id).order_by(Alerta.criado_em.desc()).all()
    return render_template('ver_demanda.html', demanda=demanda, alertas=alertas)


# ─── EDITAR DEMANDA ───────────────────────────────────────────────────────────

@app.route('/demanda/<int:id>/editar', methods=['GET', 'POST'])
def editar_demanda(id):
    demanda = Demanda.query.get_or_404(id)
    if request.method == 'POST':
        demanda.cliente_nome = request.form['cliente_nome'].strip()
        demanda.cliente_email = request.form['cliente_email'].strip().lower()
        demanda.origem = request.form['origem'].strip().upper()
        demanda.destino = request.form['destino'].strip().upper()
        demanda.data_ida = request.form['data_ida']
        demanda.data_volta = request.form.get('data_volta') or None
        demanda.adultos = int(request.form.get('adultos', 1))
        demanda.preco_alvo = float(request.form['preco_alvo'].replace(',', '.'))
        demanda.flexibilidade = request.form.get('flexibilidade', '').strip() or None
        db.session.commit()
        flash('✅ Demanda atualizada!', 'success')
        return redirect(url_for('ver_demanda', id=id))
    return render_template('nova_demanda.html', demanda=demanda)


# ─── PAUSAR / REATIVAR ────────────────────────────────────────────────────────

@app.route('/demanda/<int:id>/toggle', methods=['POST'])
def toggle_demanda(id):
    demanda = Demanda.query.get_or_404(id)
    demanda.ativo = not demanda.ativo
    db.session.commit()
    status = 'reativada' if demanda.ativo else 'pausada'
    flash(f'Demanda {status} com sucesso.', 'success')
    return redirect(url_for('index'))


# ─── EXCLUIR DEMANDA ──────────────────────────────────────────────────────────

@app.route('/demanda/<int:id>/excluir', methods=['POST'])
def excluir_demanda(id):
    demanda = Demanda.query.get_or_404(id)
    db.session.delete(demanda)
    db.session.commit()
    flash('Demanda excluída.', 'success')
    return redirect(url_for('index'))


# ─── VERIFICAÇÃO MANUAL ───────────────────────────────────────────────────────

@app.route('/verificar/<int:id>', methods=['POST'])
def verificar_agora(id):
    from flight_service import verificar_preco_demanda
    from email_service import enviar_alerta

    demanda = Demanda.query.get_or_404(id)
    oferta = verificar_preco_demanda(demanda)

    if oferta:
        demanda.preco_atual = oferta['preco']
        demanda.ultima_verificacao = datetime.utcnow()

        if oferta['preco'] <= demanda.preco_alvo:
            alerta = Alerta(
                demanda_id=demanda.id,
                preco_encontrado=oferta['preco'],
                companhia=oferta.get('companhia', ''),
                link_compra=oferta.get('link', ''),
                fonte=oferta.get('fonte', ''),
            )
            enviado = enviar_alerta(demanda, oferta)
            alerta.email_enviado = enviado
            db.session.add(alerta)
            flash(f'🎉 Preço atingido! R${oferta["preco"]:.2f} — Email {"enviado" if enviado else "com erro"}.', 'success')
        else:
            flash(f'Preço atual: R${oferta["preco"]:.2f} — ainda acima do alvo de R${demanda.preco_alvo:.2f}.', 'info')

        db.session.commit()
    else:
        flash('Não foi possível obter preços agora. Tente novamente.', 'warning')

    return redirect(url_for('ver_demanda', id=id))


# ─── BUSCAR AEROPORTO (AJAX) ──────────────────────────────────────────────────

@app.route('/api/aeroportos')
def buscar_aeroportos():
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify([])
    from flight_service import buscar_aeroporto
    resultado = buscar_aeroporto(q)
    return jsonify(resultado)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
