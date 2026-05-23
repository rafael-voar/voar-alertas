from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Demanda(db.Model):
    __tablename__ = 'demandas'

    id = db.Column(db.Integer, primary_key=True)

    # Cliente
    cliente_nome = db.Column(db.String(200), nullable=False)
    cliente_email = db.Column(db.String(200), nullable=False)

    # Voo
    origem = db.Column(db.String(10), nullable=False)       # Código IATA ex: GRU
    destino = db.Column(db.String(10), nullable=False)      # Código IATA ex: MIA
    data_ida = db.Column(db.String(10), nullable=False)     # YYYY-MM-DD
    data_volta = db.Column(db.String(10), nullable=True)    # YYYY-MM-DD (None se só ida)
    adultos = db.Column(db.Integer, default=1)

    # Preferências
    preco_alvo = db.Column(db.Float, nullable=False)        # Preço máximo desejado pelo cliente
    preco_cotado = db.Column(db.Float, nullable=True)       # Último preço cotado pela Voar ao cliente
    flexibilidade = db.Column(db.String(200), nullable=True) # Ex: "±3 dias", "qualquer cia"
    moeda = db.Column(db.String(5), default='BRL')

    # Status
    ativo = db.Column(db.Boolean, default=True)
    preco_atual = db.Column(db.Float, nullable=True)
    ultima_verificacao = db.Column(db.DateTime, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento
    alertas = db.relationship('Alerta', backref='demanda', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Demanda {self.origem}->{self.destino} {self.cliente_nome}>'


class Alerta(db.Model):
    __tablename__ = 'alertas'

    id = db.Column(db.Integer, primary_key=True)
    demanda_id = db.Column(db.Integer, db.ForeignKey('demandas.id'), nullable=False)

    preco_encontrado = db.Column(db.Float, nullable=False)
    companhia = db.Column(db.String(200), nullable=True)
    link_compra = db.Column(db.String(500), nullable=True)
    fonte = db.Column(db.String(50), nullable=True)  # 'skyscanner' ou 'google_flights'
    email_enviado = db.Column(db.Boolean, default=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Alerta R${self.preco_encontrado} para demanda {self.demanda_id}>'
