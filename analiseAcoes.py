import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
#matplotlib.use('TkAgg')
matplotlib.use('Qt5Agg')
import winsound
from datetime import datetime, timedelta
import warnings
from tabulate import tabulate


warnings.simplefilter(action='ignore', category=FutureWarning)

#plt.style.use('seaborn-darkgrid')
plt.style.use('ggplot')
plt.show(block=True)
resultado_alertas = {}

def emitir_alerta(tipo, acao, data, preco):
    try:
        preco_valor = float(preco)
        if tipo == 'compra':
            print(f"🔔 Alerta de COMPRA: {acao} em {data.date()} - R${preco_valor:.2f}")
            winsound.Beep(1000, 500)
            resultado_alertas.setdefault(acao, []).append(data.date())
        elif tipo == 'venda':
            print(f"🔔 Alerta de VENDA: {acao} em {data.date()} - R${preco_valor:.2f}")
            winsound.Beep(600, 500)
    except Exception as e:
        print(f"❌ Erro ao emitir alerta para {acao} em {data}: {e}")


def calcular_macd(df, short=12, long=26, signal=9):
    ema_short = df['Close'].ewm(span=short, adjust=False).mean()
    ema_long = df['Close'].ewm(span=long, adjust=False).mean()
    macd = ema_short - ema_long
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histograma = macd - signal_line
    return macd, signal_line, histograma

def calcular_rsi(df, periodo=14):
    delta = df['Close'].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    media_ganho = ganho.rolling(window=periodo).mean()
    media_perda = perda.rolling(window=periodo).mean()
    rs = media_ganho / media_perda.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def aplicar_indicadores(df):
    df['% Diario'] = ((df['Close'] - df['Close'].shift(1)) / df['Open']) * 100
    df['% Diario'] = df['% Diario'].fillna(0)
    df['MM80'] = df['Close'].rolling(window=80).mean()
    df['MM200'] = df['Close'].rolling(window=200).mean()
    df['RSI'] = calcular_rsi(df)
    macd, signal, hist = calcular_macd(df)
    df['MACD'] = macd
    df['Signal'] = signal
    df['Histograma'] = hist
    df['BB_Media'] = df['Close'].rolling(window=20).mean()
    df['BB_Desvio'] = df['Close'].rolling(window=20).std()
    df['BB_Alta'] = df['BB_Media'] + 2 * df['BB_Desvio']
    df['BB_Baixa'] = df['BB_Media'] - 2 * df['BB_Desvio']

def gerar_sinais(df, acao):
    sinais_compra = (df['MACD'] > df['Signal']) & (df['MACD'].shift(1) < df['Signal'].shift(1)) & (df['RSI'] < 30)
    sinais_venda = (df['MACD'] < df['Signal']) & (df['MACD'].shift(1) > df['Signal'].shift(1)) & (df['RSI'] > 70)

    for i in df.index[sinais_compra]:
        emitir_alerta('compra', acao, i, df.loc[i, 'Close'])

    for i in df.index[sinais_venda]:
        emitir_alerta('venda', acao, i, df.loc[i, 'Close'])

    return sinais_compra, sinais_venda

def plotar_graficos(df, acao, sinais_compra, sinais_venda):
    plt.figure(figsize=(16, 12))

    plt.subplot(4, 1, 1)
    plt.plot(df['Close'], label='Fechamento', linewidth=2)
    plt.plot(df['MM80'], label='MM80', linestyle='--')
    plt.plot(df['MM200'], label='MM200', linestyle='--')
    plt.plot(df['BB_Alta'], label='Bollinger Alta', linestyle=':', color='green')
    plt.plot(df['BB_Baixa'], label='Bollinger Baixa', linestyle=':', color='red')
    plt.scatter(df.index[sinais_compra], df.loc[sinais_compra, 'Close'], marker='^', color='green', label='Compra', s=100)
    plt.scatter(df.index[sinais_venda], df.loc[sinais_venda, 'Close'], marker='v', color='red', label='Venda', s=100)

    for i in df.index[sinais_compra]:
        valor = float(df.loc[i, 'Close'])
        plt.text(i, valor + 0.5, f"{valor:.2f}", color='green', fontsize=8)

    for i in df.index[sinais_venda]:
        valor = float(df.loc[i, 'Close'])
        plt.text(i, valor - 0.5, f"{valor:.2f}", color='red', fontsize=8)

   # plt.title(f'{acao} - Preço, MM, Bollinger e Sinais. NÃO É RECOMENDAÇÃO DE COMPRA/VENDA.', fontsize=16, fontweight='bold')
    plt.title(f'{acao} - Últimos {len(df)} dias - Preço, MM, Bollinger e Sinais. NÃO É RECOMENDAÇÃO DE COMPRA/VENDA.')

    if not df.empty:
        preco_hoje = float(df['Close'].iloc[-1])  # Garante que é float
        plt.title(
            f'{acao} - Últimos {len(df)} dias - Preço atual: R${preco_hoje:.2f} - Preço, MM, Bollinger e Sinais. NÃO É RECOMENDAÇÃO DE COMPRA/VENDA.',
            fontsize=14, fontweight='bold')
    else:
        plt.title(f'{acao} - Dados indisponíveis', fontsize=13, fontweight='bold')

    plt.legend()

    plt.subplot(4, 1, 2)
    plt.bar(df.index, df['% Diario'], label='% Diário')
    plt.axhline(0, color='gray', linestyle='--')
    plt.title('% de valorização diária')
    plt.legend()

    plt.subplot(4, 1, 3)
    plt.plot(df.index, df['MACD'], label='MACD', color='blue')
    plt.plot(df.index, df['Signal'], label='Signal', color='red')
    plt.bar(df.index, df['Histograma'], label='Histograma', color='gray')
    plt.axhline(0, color='black', linestyle='--')
    plt.title('MACD')
    plt.legend()

    plt.subplot(4, 1, 4)
    plt.plot(df['RSI'], label='RSI', color='purple')
    plt.axhline(70, color='red', linestyle='--', label='Sobrecomprado')
    plt.axhline(30, color='green', linestyle='--', label='Sobrevendido')
    plt.title('RSI')
    plt.legend()

    plt.tight_layout()
    plt.show()

def analisar_acao(acao):
    print(f"\n📊 Analisando {acao}...")
    fim = datetime.now()
    inicio = fim - timedelta(days=380) #TROQUE AQUI OS DIAS
    df = yf.download(acao, start=inicio, end=fim, auto_adjust=True)
    if df.empty:
        print(f"⚠️ Dados não encontrados para {acao}")
        return

    df.dropna(inplace=True)
    aplicar_indicadores(df)

    print("\n📅 Período: {days} DIAS")

    sinais_compra, sinais_venda = gerar_sinais(df, acao)
    plotar_graficos(df.copy(), acao, sinais_compra, sinais_venda)

def buscar_cenario_externo():
    print("\n🌍 Analisando Cenário Externo...")

    indices = {
        'S&P500': '^GSPC',
        'Dow Jones': '^DJI',
        'Nasdaq': '^IXIC',
        'Dólar (USD/BRL)': 'BRL=X',
        'Euro (EUR/BRL)': 'EURBRL=X',
        'Petróleo Brent': 'BZ=F',
        'Petróleo WTI': 'CL=F',
        'Ouro': 'GC=F',
        'Bitcoin': 'BTC-USD',
        'Ibovespa': '^BVSP',
        'Índice VIX': '^VIX'
    }

    dados = []
    for nome, ticker in indices.items():
        try:
            df = yf.download(ticker, period='5d', progress=False)
            if df.empty:
                continue

            ultimo = float(df['Close'].iloc[-1])
            variacao = (ultimo / float(df['Close'].iloc[-2]) - 1) * 100

            if 'Dólar' in nome or 'Euro' in nome:
                valor = f"R${ultimo:.2f}"
            elif any(x in nome for x in ['S&P500', 'Dow Jones', 'Nasdaq', 'Ibovespa']):
                valor = f"{ultimo:,.2f}"
            else:
                valor = f"{ultimo:.2f}"

            dados.append([
                nome,
                valor,
                f"{variacao:+.2f}%",
                "🟢" if variacao > 0 else "🔴"
            ])
        except Exception as e:
            print(f"⚠️ Erro ao processar {nome}: {str(e)}")

    print("\n📊 Desempenho dos Principais Índices:")
    if dados:
        print(tabulate(dados, headers=["Índice", "Valor", "Variação", "Tendência"], tablefmt="pretty"))
    else:
        print("Nenhum dado disponível para exibir")

    # Análise qualitativa
    try:
        df_ibov = yf.download('^BVSP', period='1mo')
        df_dolar = yf.download('BRL=X', period='1mo')

        if not df_ibov.empty and not df_dolar.empty:
            var_ibov = (float(df_ibov['Close'].iloc[-1]) / float(df_ibov['Close'].iloc[0]) - 1) * 100
            var_dolar = (float(df_dolar['Close'].iloc[-1]) / float(df_dolar['Close'].iloc[0]) - 1) * 100

            print("\n🧠 Análise do Cenário Atual:")
            if var_ibov > 2 and var_dolar < -1:
                print("📈 Cenário Positivo: Ibovespa em alta e dólar em queda")
            elif var_ibov < -2 and var_dolar > 1:
                print("📉 Cenário Negativo: Ibovespa em queda e dólar em alta")
            else:
                print("⚖️ Cenário Neutro: Mercado em equilíbrio")
    except Exception as e:
        print(f"\n⚠️ Não foi possível completar a análise do cenário: {str(e)}")

def main():
    print("""
    ██╗    ██╗███████╗██╗     ██╗     
    ██║    ██║██╔════╝██║     ██║     
    ██║ █╗ ██║█████╗  ██║     ██║     
    ██║███╗██║██╔══╝  ██║     ██║     
    ╚███╔███╔╝███████╗███████╗███████╗
     ╚══╝╚══╝ ╚══════╝╚══════╝╚══════╝
    """)

    # Lista de ações para análise
    acoes = [
        'VALE3.SA',
    ]

    # Primeiro verifica conexão
    teste = yf.download('VALE3.SA', period='5d')
    if teste.empty:
        print("⚠️ Não foi possível conectar ao Yahoo Finance. Verifique sua internet.")
        return

    buscar_cenario_externo()

    for acao in acoes:
        analisar_acao(acao)

    if resultado_alertas:
        print("\n📈 Relatório de Alertas:")
        ranking = sorted(resultado_alertas.items(), key=lambda x: len(x[1]), reverse=True)
        for acao, alertas in ranking:
            datas = ", ".join([f"{a.strftime('%d/%m')}" for a in alertas])
            print(f"🔔 {acao}: {len(alertas)} alertas - Datas: {datas}")
    else:
        print("\n⚠️ Nenhum alerta gerado durante a análise.")

    print("\n✅ Análise concluída!")

if __name__ == '__main__':
    main()