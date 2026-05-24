from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

scheduler = BackgroundScheduler(timezone=pytz.timezone('America/Sao_Paulo'))


def iniciar_scheduler(app):
    """Inicia o agendador de verificações de preços."""

    def verificar_todos_os_precos():
        from models import Demanda, Alerta, db
        from flight_service import verificar_preco_demanda
        from email_service import enviar_alerta

        with app.app_context():
            agora = datetime.utcnow()
            print(f'\n[Scheduler] Iniciando verificação em {agora.strftime("%d/%m/%Y %H:%M")} UTC')

            demandas = Demanda.query.filter_by(ativo=True).all()
            print(f'[Scheduler] {len(demandas)} demanda(s) ativa(s) para verificar')

            for demanda in demandas:
                try:
                    print(f'[Scheduler] Verificando: {demanda.cliente_nome} | {demanda.origem}→{demanda.destino} | alvo R${demanda.preco_alvo}')

                    oferta = verificar_preco_demanda(demanda)

                    if oferta:
                        demanda.preco_atual = oferta['preco']
                        demanda.ultima_verificacao = agora

                        if oferta['preco'] <= demanda.preco_alvo:
                            print(f'[Scheduler] 🎉 PREÇO ATINGIDO! R${oferta["preco"]} <= R${demanda.preco_alvo}')

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
                        else:
                            print(f'[Scheduler] Preço atual R${oferta["preco"]} acima do alvo R${demanda.preco_alvo}')
                    else:
                        demanda.ultima_verificacao = agora
                        print(f'[Scheduler] Nenhuma oferta encontrada para {demanda.origem}→{demanda.destino}')

                    db.session.commit()

                except Exception as e:
                    print(f'[Scheduler] Erro ao verificar demanda {demanda.id}: {e}')
                    db.session.rollback()

            print(f'[Scheduler] Verificação concluída.\n')

    def enviar_resumo():
        from models import Demanda, Alerta, db
        from email_service import enviar_resumo_diario
        from datetime import date

        with app.app_context():
            demandas_ativas = Demanda.query.filter_by(ativo=True).all()
            hoje = date.today()
            alertas_hoje = Alerta.query.filter(
                db.func.date(Alerta.criado_em) == hoje,
                Alerta.email_enviado == True
            ).count()
            enviar_resumo_diario(demandas_ativas, alertas_hoje)

    # Verificar preços a cada 6 horas
    scheduler.add_job(
        verificar_todos_os_precos,
        'interval',
        hours=6,
        id='verificar_precos',
        name='Verificação de Preços de Voos',
        replace_existing=True
    )

    # Resumo diário às 8h (horário de Brasília)
    scheduler.add_job(
        enviar_resumo,
        CronTrigger(hour=8, minute=0, timezone=pytz.timezone('America/Sao_Paulo')),
        id='resumo_diario',
        name='Resumo Diário',
        replace_existing=True
    )

    scheduler.start()
    print('[Scheduler] Agendador iniciado. Verificações a cada 6 horas + resumo diário às 8h.')
    return scheduler
