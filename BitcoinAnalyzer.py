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

        balance_btc = data['final_balance'] / 100000000
        total_received_btc = data['total_received'] / 100000000
        total_sent_btc = (data['total_received'] - data['final_balance']) / 100000000

        print(f"\nSaldo atual: {balance_btc:.8f} BTC (${balance_btc * self.btc_price:,.2f})")
        print(f"Total recebido: {total_received_btc:.8f} BTC (${total_received_btc * self.btc_price:,.2f})")
        print(f"Total enviado: {total_sent_btc:.8f} BTC (${total_sent_btc * self.btc_price:,.2f})")
        print(f"Número de transações: {data['n_tx']}")

        print(f"\nAnalisando últimas transações (máx. 5):")
        for tx in data['txs'][:5]:  # limitar para evitar sobrecarga
            self.display_transaction(tx, address)

    def display_transaction(self, tx, target_address):
        """Mostra os detalhes de uma transação com foco forense"""
        print(f"\n{'─' * 30}")
        print(f"TRANSAÇÃO ID: {tx['hash']}")
        print(f"Data/Hora: {datetime.fromtimestamp(tx['time']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tamanho: {tx['size']} bytes")

        # Listar inputs (endereços de origem)
        senders = []
        for inp in tx.get('inputs', []):
            if 'prev_out' in inp and 'addr' in inp['prev_out']:
                addr = inp['prev_out']['addr']
                value = inp['prev_out']['value'] / 1e8
                senders.append((addr, value))

        # Listar outputs (endereços de destino)
        receivers = []
        for out in tx['out']:
            if 'addr' in out:
                addr = out['addr']
                value = out['value'] / 1e8
                receivers.append((addr, value))

        # Verificar se o alvo recebeu ou enviou
        is_receiving = any(addr == target_address for addr, _ in receivers)
        is_sending = any(addr == target_address for addr, _ in senders)

        if is_receiving:
            print(f"\n🟢 RECEBIMENTO")
            for addr, value in senders:
                print(f"  🔸 De: {addr} → {target_address} | {value:.8f} BTC (${value * self.btc_price:,.2f})")

        if is_sending:
            print(f"\n🔴 ENVIO")
            for addr, value in receivers:
                if addr != target_address:
                    print(f"  🔸 Para: {addr} ← {target_address} | {value:.8f} BTC (${value * self.btc_price:,.2f})")

        if not is_receiving and not is_sending:
            print("⚪ Movimentação indireta (talvez troca interna)")

        # Valor líquido da transação para o endereço
        net_value = 0
        for output in tx['out']:
            if 'addr' in output and output['addr'] == target_address:
                net_value += output['value']
        for inp in tx.get('inputs', []):
            if 'prev_out' in inp and 'addr' in inp['prev_out']:
                if inp['prev_out']['addr'] == target_address:
                    net_value -= inp['prev_out']['value']

        net_value_btc = net_value / 100000000
        usd_value = net_value_btc * self.btc_price

        print(f"\nResumo líquido da transação:")
        if net_value > 0:
            print(f"  +{net_value_btc:.8f} BTC recebidos (${usd_value:,.2f})")
        elif net_value < 0:
            print(f"  {net_value_btc:.8f} BTC enviados (${usd_value:,.2f})")
        else:
            print("  Nenhuma mudança líquida para o endereço")


if __name__ == "__main__":
    analyzer = BitcoinAnalyzer()

    addresses = [
        "1HQ3Go3ggs8pFnXuHVHRytPCq5fGG8Hbhx",  # Bitcoin Fog
        # "1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX",  # Silk Road
        # "1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF"   # Mt. Gox Hack
    ]

    print("🕵️‍♂️ ANALISADOR DE ENDEREÇOS BITCOIN - USO POLICIAL")
    print("Analisando movimentações, origem e destino de fundos...\n")

    for address in addresses:
        analyzer.analyze_address(address)
        time.sleep(5)  # evitar sobrecarga da API

    custom_address = input("\nDigite um endereço Bitcoin para analisar (ou Enter para sair): ")
    if custom_address:
        analyzer.analyze_address(custom_address)
