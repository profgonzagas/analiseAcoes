import requests
from datetime import datetime
import time


class BitcoinAnalyzer:
    def __init__(self):
        self.btc_price = self.get_current_btc_price()

    def get_current_btc_price(self):
        """Obtém o preço atual do Bitcoin em dólares usando a CoinGecko API"""
        try:
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
            response.raise_for_status()
            return float(response.json()['bitcoin']['usd'])
        except Exception as e:
            print(f"Erro ao obter preço do Bitcoin, usando valor padrão $50,000: {e}")
            return 50000.00

    def get_address_info(self, address):
        """Obtém informações do endereço usando a Blockchain.com API"""
        try:
            url = f"https://blockchain.info/rawaddr/{address}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao buscar informações do endereço: {e}")
            return None

    def analyze_address(self, address):
        """Analisa um endereço Bitcoin e mostra os resultados"""
        data = self.get_address_info(address)
        if not data:
            print(f"Não foi possível obter dados para o endereço {address}")
            return

        print(f"\n{'=' * 60}")
        print(f"ANÁLISE DO ENDEREÇO BITCOIN: {address}")
        print(f"Cotação atual: 1 BTC = ${self.btc_price:,.2f} USD")
        print(f"{'=' * 60}")

        # Converter valores
        balance_btc = data['final_balance'] / 100000000
        total_received_btc = data['total_received'] / 100000000
        total_sent_btc = (data['total_received'] - data['final_balance']) / 100000000

        print(f"\nSaldo atual: {balance_btc:.8f} BTC (${balance_btc * self.btc_price:,.2f})")
        print(f"Total recebido: {total_received_btc:.8f} BTC (${total_received_btc * self.btc_price:,.2f})")
        print(f"Total enviado: {total_sent_btc:.8f} BTC (${total_sent_btc * self.btc_price:,.2f})")
        print(f"Número de transações: {data['n_tx']}")

        # Mostrar últimas transações
        print(f"\nÚltimas transações:")
        for tx in data['txs'][:5]:  # Mostrar apenas 5 transações
            self.display_transaction(tx, address)

    def display_transaction(self, tx, address):
        """Mostra os detalhes de uma transação"""
        print(f"\n{'─' * 30}")
        print(f"ID: {tx['hash']}")
        print(f"Data: {datetime.fromtimestamp(tx['time']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tamanho: {tx['size']} bytes")

        # Calcular valor líquido para o endereço
        net_value = 0
        for output in tx['out']:
            if 'addr' in output and output['addr'] == address:
                net_value += output['value']

        for inp in tx.get('inputs', []):
            if 'prev_out' in inp and 'addr' in inp['prev_out']:
                if inp['prev_out']['addr'] == address:
                    net_value -= inp['prev_out']['value']

        net_value_btc = net_value / 100000000
        usd_value = net_value_btc * self.btc_price

        if net_value > 0:
            print(f"RECEBIDO: +{net_value_btc:.8f} BTC (${usd_value:,.2f} USD)")
        elif net_value < 0:
            print(f"ENVIADO: {net_value_btc:.8f} BTC (${usd_value:,.2f} USD)")
        else:
            print("MOVIMENTAÇÃO INTERNA")


if __name__ == "__main__":
    analyzer = BitcoinAnalyzer()

    # Endereços de exemplo com grande movimentação
    addresses = [
        "1HQ3Go3ggs8pFnXuHVHRytPCq5fGG8Hbhx",  # Bitcoin Fog
       # "1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX",  # Silk Road
        #"1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF"  # Mt. Gox Hack
    ]

    print("ANALISADOR DE ENDEREÇOS BITCOIN")
    print("Mostrando saldos e transações em BTC e USD\n")

    for address in addresses:
        analyzer.analyze_address(address)
        time.sleep(5)  # Espera para não sobrecarregar a API

    # Para analisar um endereço específico:
    custom_address = input("\nDigite um endereço Bitcoin para analisar (ou Enter para sair): ")
    if custom_address:
        analyzer.analyze_address(custom_address)