import requests
import tkinter as tk
from tkinter import ttk

# API Endpoints
TARKOV_GRAPHQL_API = "https://api.tarkov.dev/graphql"

# Filtro de lucro mínimo
MIN_PROFIT = 100_000  
EXCLUDED_TRADER = "Ref"  # Trader a ser removido

def fetch_barters():
    """Busca os barter trades da API do Tarkov"""
    query = """
    {
      barters {
        id
        trader { name }
        requiredItems {
          item { id name }
          count
        }
        rewardItems {
          item { id name }
          count
        }
      }
    }
    """
    try:
        response = requests.post(TARKOV_GRAPHQL_API, json={'query': query}, timeout=10)
        response.raise_for_status()
        return response.json().get("data", {}).get("barters", [])
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar barters: {e}")
        return []

def fetch_live_prices():
    """Busca os preços dos itens da API"""
    query = """
    {
      items {
        id
        name
        lastLowPrice
      }
    }
    """
    try:
        response = requests.post(TARKOV_GRAPHQL_API, json={"query": query}, timeout=10)
        response.raise_for_status()
        items = response.json().get("data", {}).get("items", [])
        return {item["id"]: item["lastLowPrice"] for item in items if item["lastLowPrice"]}
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar preços: {e}")
        return {}

def calculate_profit(barters, prices):
    """Calcula o lucro de cada barter trade, aplicando filtros"""
    profitable_barters = []

    for barter in barters:
        trader_name = barter["trader"]["name"]
        
        # Filtro: Remover o trader "Ref"
        if trader_name == EXCLUDED_TRADER:
            continue

        if not barter.get("rewardItems"):  
            continue
        
        output_item = barter["rewardItems"][0]["item"]["name"]
        
        # Calcula o custo total dos itens requeridos
        input_cost = sum(prices.get(req["item"]["id"], 0) * req.get("count", 1) for req in barter.get("requiredItems", []))

        # Filtro: Remover barters com cost = 0
        if input_cost == 0:
            continue

        output_value = prices.get(barter["rewardItems"][0]["item"]["id"], 0)
        profit = output_value - input_cost

        if profit >= MIN_PROFIT:
            profitable_barters.append((output_item, trader_name, input_cost, profit))

    return sorted(profitable_barters, key=lambda x: x[3], reverse=True)

def update_table():
    """Busca os dados e atualiza a tabela"""
    barters = fetch_barters()
    prices = fetch_live_prices()
    results = calculate_profit(barters, prices)
    
    table.delete(*table.get_children())  # Limpa a tabela

    for item, trader, cost, profit in results:
        tag = "profit" if profit > 0 else "loss"
        table.insert("", "end", values=(item, trader, f"{cost:,}₽", f"{profit:,}₽"), tags=(tag,))
    
    table.tag_configure("profit", foreground="green")
    root.after(300000, update_table)  # Atualiza a cada 5 minutos

# Inicializa janela principal do Tkinter
root = tk.Tk()
root.title("Tarkov Barter Profits")
root.geometry("800x600")

# UI elements
frame = ttk.Frame(root)
frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("Item", "Trader", "Cost", "Profit")
table = ttk.Treeview(frame, columns=columns, show="headings")
for col in columns:
    table.heading(col, text=col)
    table.column(col, anchor="center")

table.pack(fill="both", expand=True)

# Atualiza a tabela
update_table()
root.mainloop()
