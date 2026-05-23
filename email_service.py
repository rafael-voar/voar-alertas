import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE', '')
EMAIL_SENHA = os.getenv('EMAIL_SENHA', '')
EMAIL_VOAR = os.getenv('EMAIL_VOAR', '')  # Seu email da Voar para receber cópia


def enviar_alerta(demanda, oferta):
    """
    Envia email de alerta de preço para o cliente e para a Voar.
    """
    if not EMAIL_REMETENTE or not EMAIL_SENHA:
        print('[Email] Credenciais não configuradas.')
        return False

    try:
        preco_fmt = f"R$ {oferta['preco']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        preco_alvo_fmt = f"R$ {demanda.preco_alvo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        economia = demanda.preco_alvo - oferta['preco']
        economia_fmt = f"R$ {economia:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        data_ida_fmt = datetime.strptime(demanda.data_ida, '%Y-%m-%d').strftime('%d/%m/%Y')
        data_volta_fmt = ''
        if demanda.data_volta:
            data_volta_fmt = datetime.strptime(demanda.data_volta, '%Y-%m-%d').strftime('%d/%m/%Y')

        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }}
  .container {{ background: white; max-width: 600px; margin: 0 auto; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
  .header {{ background: linear-gradient(135deg, #1a73e8, #0d47a1); color: white; padding: 30px; text-align: center; }}
  .header h1 {{ margin: 0; font-size: 28px; }}
  .header p {{ margin: 5px 0 0; opacity: 0.9; }}
  .badge {{ background: #4CAF50; color: white; padding: 6px 16px; border-radius: 20px; font-size: 13px; display: inline-block; margin-top: 10px; }}
  .body {{ padding: 30px; }}
  .preco-box {{ background: #e8f5e9; border: 2px solid #4CAF50; border-radius: 10px; padding: 20px; text-align: center; margin: 20px 0; }}
  .preco-box .preco {{ font-size: 42px; font-weight: bold; color: #2e7d32; }}
  .preco-box .economia {{ color: #388e3c; font-size: 15px; margin-top: 5px; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
  .info-item {{ background: #f8f9fa; border-radius: 8px; padding: 15px; }}
  .info-item .label {{ font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; }}
  .info-item .value {{ font-size: 16px; font-weight: bold; color: #333; margin-top: 4px; }}
  .btn {{ display: block; background: #1a73e8; color: white; text-decoration: none; padding: 15px 30px; border-radius: 8px; text-align: center; font-size: 16px; font-weight: bold; margin: 25px 0; }}
  .footer {{ background: #f8f9fa; padding: 20px; text-align: center; color: #999; font-size: 12px; }}
  .alerta-preco {{ background: #fff3e0; border-left: 4px solid #ff9800; padding: 12px 16px; border-radius: 4px; margin: 10px 0; font-size: 14px; color: #e65100; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>✈️ Voar Passagens Aéreas</h1>
    <p>Encontramos uma passagem dentro do seu orçamento!</p>
    <span class="badge">🎉 Alerta de Preço</span>
  </div>
  <div class="body">
    <p>Olá, <strong>{demanda.cliente_nome}</strong>!</p>
    <p>Boa notícia! Encontramos uma passagem para a sua rota desejada dentro do seu orçamento:</p>

    <div class="preco-box">
      <div class="preco">{preco_fmt}</div>
      <div class="economia">💰 Economia de {economia_fmt} em relação ao seu orçamento de {preco_alvo_fmt}</div>
    </div>

    <div class="info-grid">
      <div class="info-item">
        <div class="label">🛫 Origem</div>
        <div class="value">{demanda.origem}</div>
      </div>
      <div class="info-item">
        <div class="label">🛬 Destino</div>
        <div class="value">{demanda.destino}</div>
      </div>
      <div class="info-item">
        <div class="label">📅 Data de Ida</div>
        <div class="value">{data_ida_fmt}</div>
      </div>
      <div class="info-item">
        <div class="label">📅 Data de Volta</div>
        <div class="value">{data_volta_fmt if data_volta_fmt else 'Somente Ida'}</div>
      </div>
      <div class="info-item">
        <div class="label">✈️ Companhia</div>
        <div class="value">{oferta.get('companhia', 'N/D')}</div>
      </div>
      <div class="info-item">
        <div class="label">🔍 Fonte</div>
        <div class="value">{oferta.get('fonte', 'N/D').title()}</div>
      </div>
    </div>

    {'<div class="alerta-preco">📋 Flexibilidade: ' + demanda.flexibilidade + '</div>' if demanda.flexibilidade else ''}

    <a href="{oferta.get('link', '#')}" class="btn">🔎 Ver Passagem e Comprar</a>

    <p style="font-size: 13px; color: #666;">
      ⚡ <strong>Atenção:</strong> Preços de passagens aéreas variam constantemente.
      Recomendamos verificar e comprar o quanto antes para garantir este valor.
    </p>
  </div>
  <div class="footer">
    <p>Este alerta foi gerado automaticamente pela <strong>Voar Passagens Aéreas</strong></p>
    <p>Para cancelar este alerta, entre em contato conosco.</p>
  </div>
</div>
</body>
</html>
"""

        destinatarios = [demanda.cliente_email]
        if EMAIL_VOAR and EMAIL_VOAR != demanda.cliente_email:
            destinatarios.append(EMAIL_VOAR)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'✈️ Passagem encontrada! {demanda.origem} → {demanda.destino} por {preco_fmt}'
        msg['From'] = f'Voar Passagens Aéreas <{EMAIL_REMETENTE}>'
        msg['To'] = demanda.cliente_email
        if EMAIL_VOAR and EMAIL_VOAR != demanda.cliente_email:
            msg['Cc'] = EMAIL_VOAR

        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_REMETENTE, EMAIL_SENHA)
            smtp.sendmail(EMAIL_REMETENTE, destinatarios, msg.as_string())

        print(f'[Email] Alerta enviado para {destinatarios}')
        return True

    except Exception as e:
        print(f'[Email] Erro ao enviar: {e}')
        return False


def enviar_resumo_diario(demandas_ativas, alertas_hoje):
    """
    Envia um resumo diário para a Voar com o status de todas as demandas.
    """
    if not EMAIL_VOAR or not EMAIL_REMETENTE or not EMAIL_SENHA:
        return False

    try:
        linhas = ''
        for d in demandas_ativas:
            preco_atual = f"R$ {d.preco_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if d.preco_atual else '–'
            preco_alvo = f"R$ {d.preco_alvo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            status = '🟢 Dentro do orçamento' if d.preco_atual and d.preco_atual <= d.preco_alvo else '🔴 Acima do orçamento'
            linhas += f"""
            <tr>
              <td style="padding:8px;border-bottom:1px solid #eee">{d.cliente_nome}</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{d.origem} → {d.destino}</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{d.data_ida}</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{preco_alvo}</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{preco_atual}</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{status}</td>
            </tr>"""

        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px">
<div style="background:white;max-width:800px;margin:0 auto;border-radius:10px;overflow:hidden">
  <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);color:white;padding:25px;text-align:center">
    <h1 style="margin:0">📊 Resumo Diário — Voar</h1>
    <p style="margin:5px 0 0;opacity:0.9">{datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
  </div>
  <div style="padding:25px">
    <p>📬 <strong>{alertas_hoje} alertas</strong> enviados hoje |
       ✈️ <strong>{len(demandas_ativas)} demandas</strong> ativas monitoradas</p>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
      <thead>
        <tr style="background:#f0f4ff">
          <th style="padding:10px;text-align:left">Cliente</th>
          <th style="padding:10px;text-align:left">Rota</th>
          <th style="padding:10px;text-align:left">Data Ida</th>
          <th style="padding:10px;text-align:left">Orçamento</th>
          <th style="padding:10px;text-align:left">Preço Atual</th>
          <th style="padding:10px;text-align:left">Status</th>
        </tr>
      </thead>
      <tbody>{linhas}</tbody>
    </table>
  </div>
  <div style="background:#f8f9fa;padding:15px;text-align:center;color:#999;font-size:12px">
    Voar Passagens Aéreas — Sistema de Alertas Automáticos
  </div>
</div>
</body>
</html>"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'📊 Resumo Diário Voar — {datetime.now().strftime("%d/%m/%Y")}'
        msg['From'] = f'Voar Sistema <{EMAIL_REMETENTE}>'
        msg['To'] = EMAIL_VOAR
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_REMETENTE, EMAIL_SENHA)
            smtp.sendmail(EMAIL_REMETENTE, [EMAIL_VOAR], msg.as_string())

        print(f'[Email] Resumo diário enviado para {EMAIL_VOAR}')
        return True

    except Exception as e:
        print(f'[Email] Erro no resumo diário: {e}')
        return False
