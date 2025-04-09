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

    plt.title(f'{acao} - Preço, MM, Bollinger e Sinais', fontsize=16, fontweight='bold')

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
    inicio = fim - timedelta(days=730)
    df = yf.download(acao, start=inicio, end=fim, auto_adjust=True)
    if df.empty:
        print(f"⚠️ Dados não encontrados para {acao}")
        return

    df.dropna(inplace=True)
    aplicar_indicadores(df)

    print("\n📅 Período: 2 anos")
    sinais_compra, sinais_venda = gerar_sinais(df, acao)
    plotar_graficos(df.copy(), acao, sinais_compra, sinais_venda)


def buscar_cenario_externo():
    print("\n🌍 Cenário Externo:")
    indices = {
        'S&P500': '^GSPC',
        'Dow Jones': '^DJI',
        'Nasdaq': '^IXIC',
        'Dólar (USD/BRL)': 'USDBRL=X',
        'Euro (EUR/BRL)': 'EURBRL=X',
        'Petróleo Brent': 'BZ=F',
        'Petróleo WTI': 'CL=F',
        'Ouro': 'GC=F',
        'Bitcoin': 'BTC-USD',
        'Ibovespa': '^BVSP',
    }

    variacoes = {}

    for nome, ticker in indices.items():
        df = yf.download(ticker, period='5d', interval='1d', auto_adjust=True, progress=False)
        if not df.empty:
            fechamento = float(df['Close'].iloc[-1])
            variacao = float(df['Close'].pct_change().iloc[-1]) * 100
            variacoes[nome] = variacao
            print(f"{nome}: {fechamento:.2f} ({variacao:+.2f}%)")
        else:
            print(f"{nome}: dados não encontrados.")

    # 🎯 Análise simples com base nas variações
    print("\n🧠 Análise do Cenário Externo:")
    try:
        sp500 = variacoes.get('S&P500', 0)
        dolar = variacoes.get('Dólar (USD/BRL)', 0)
        ibov = variacoes.get('Ibovespa', 0)
        brent = variacoes.get('Petróleo Brent', 0)
        bitcoin = variacoes.get('Bitcoin', 0)

        recomendacao = ""
        if sp500 > 0.5 and ibov > 0.5 and dolar < -0.2:
            recomendacao = "📈 Recomendação: Momento positivo no exterior e no Brasil. Oportunidade de COMPRA seletiva."
        elif sp500 < -1 and ibov < -1 and dolar > 0.5:
            recomendacao = "📉 Recomendação: Mercado em queda e dólar em alta. Melhor manter cautela ou vender ativos vulneráveis."
        elif ibov > 0.5 and sp500 < 0:
            recomendacao = "⚠️ Recomendação: Ibovespa positivo, mas exterior negativo. Cautela com ativos muito expostos ao mercado global."
        else:
            recomendacao = "⚖️ Recomendação: Cenário misto. Aguardar sinal mais claro antes de realizar novas compras."

        print(recomendacao)

    except Exception as e:
        print(f"Erro ao analisar o cenário externo: {e}")


def main():
    print("🚀 Iniciando análise de ações...\n")
    acoes = [
        'JSLG3.SA',  # JSL
        'VIVA3.SA',  # Vivara
         #'VALE3.SA',  # Vale
         #'INTB3.SA',  # Intelbras
         #'ARML3.SA',  # Armac
        #'VAMO3.SA',  # Grupo Vamos
         #'CRFB3.SA',  # Atacadão
         #'AMER3.SA',  # Americanas
         #'MGLU3.SA',  # Magazine Luiza
         #'DASA3.SA',  # Dasa
         #'HBRE3.SA',  # HBR Realty
        #
        #'MTRE3.SA',  # Mitre Realty
         #'MOVI3.SA',  # Movida
         #'CVCB3.SA',  # CVC Brasil
         #'INBR32.SA',  # Inter
         #'PRIO3.SA',  # PRIO
         #'BPAC11.SA',  # BTG Pactual
         #'MILS3.SA',  # Mills
         #'PRNR3.SA',  # Priner
         #'SUZB3.SA',  # Suzano
         #'MULT3.SA',  # Multiplan
         #'CURY3.SA',  # Cury
        #        'VIVT3.SA',  # Telefônica Brasil
         #'PETR4.SA',  # Petrobras
         #'BBAS3.SA',  # Banco do Brasil
        #        'SBSP3.SA',  # Sabesp
         #'SIMH3.SA',  # Simpar
         #'ECOR3.SA',  # Ecorodovias
         #'GGBR4.SA',  # Gerdau
         #'SLCE3.SA',  # SLC Agrícola
         #'WEGE3.SA',  # WEG
         #'EMBR3.SA',  # Embraer
         #'PSSA3.SA',  # Porto Seguro
         #'CSMG3.SA',  # Copasa
         #'MRFG3.SA',  # Marfrig
    ]

    for acao in acoes:
        analisar_acao(acao)

    buscar_cenario_externo()

    if resultado_alertas:
        print("\n📈 Ranking de Ações com Mais Alertas de Compra (Ordem Alfabética):")
        ranking = sorted(resultado_alertas.items(), key=lambda x: x[0])  # ordena pelo nome da ação
        for acao, datas in ranking:
            datas_formatadas = ', '.join(data.strftime('%d/%m/%Y') for data in datas)
            print(f"🟢 {acao}: {len(datas)} alerta(s) de COMPRA nas datas: {datas_formatadas}")
    else:
        print("\n⚠️ Nenhuma ação com alertas de compra no momento.")

if __name__ == '__main__':
    main()