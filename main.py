import requests
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2


# API Endpoints
TARKOV_GRAPHQL_API = "https://api.tarkov.dev/graphql"

# Lista dos itens filtrados
FILTERED_ITEMS = {"Item case", "Weapon case", "S I C C organizational pouch",
                  "Mr. Holodilnick thermal bag"}  

def fetch_barters():
    """Fetch barter trades from Tarkov GraphQL API with error handling"""
    query = """
    {
      barters {
        id
        trader {
          name
        }
        requiredItems {
          item {
            id
            name
          }
          count
        }
        rewardItems {
          item {
            id
            name
          }
          count
        }
      }
    }
    """
    try:
        response = requests.post(TARKOV_GRAPHQL_API, json={'query': query}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("barters", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching barter data: {e}")
        return []

def fetch_live_prices():
    """Fetch item prices from Tarkov GraphQL API with error handling"""
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
        data = response.json()
        return {item["id"]: (item["name"], item["lastLowPrice"]) for item in data.get("data", {}).get("items", []) if item["lastLowPrice"]}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price data: {e}")
        return {}

def calculate_profit(barters, prices):
    """Calculate profit for each barter trade"""
    profitable_barters = []
    for barter in barters:
        if not barter["rewardItems"]:
            continue
        
        output_item = barter["rewardItems"][0]["item"]["name"]
        trader_name = barter["trader"]["name"]
        if FILTERED_ITEMS and output_item not in FILTERED_ITEMS:
            continue
        
        input_cost = sum(prices.get(req["item"]["id"], (None, 0))[1] * req.get("count", 1) for req in barter.get("requiredItems", []))
        if input_cost == 0:
            continue
        
        output_value = prices.get(barter["rewardItems"][0]["item"]["id"], (None, 0))[1] if barter["rewardItems"][0]["item"]["id"] in prices else 0
        profit = output_value - input_cost
        profitable_barters.append((output_item, trader_name, input_cost, profit))
    return sorted(profitable_barters, key=lambda x: x[3], reverse=True)

def update_table():
    """Fetch data and update the UI table"""
    barters = fetch_barters()
    prices = fetch_live_prices()
    results = calculate_profit(barters, prices)
    
    for row in table.get_children():
        table.delete(row)
    
    for item, trader, cost, profit in results:
        tag = "profit" if profit > 0 else "loss"
        table.insert("", "end", values=(item, trader, f"{cost:,}₽", f"{profit:,}₽"), tags=(tag,))
    
    table.tag_configure("profit", foreground="green")
    table.tag_configure("loss", foreground="red")
    
    root.after(300000, update_table)  # Auto-refresh every 5 minutes

def update_video():
    """Updates the video frame inside the tkinter window"""
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart video when it ends
        return
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, (700, 400))  # Resize to fit window
    img = Image.fromarray(frame)
    img_tk = ImageTk.PhotoImage(image=img)

    bg_label.img_tk = img_tk  # Keep reference
    bg_label.config(image=img_tk)
    
    root.after(30, update_video)  # Schedule next frame update


# Inicializa janela principal do Tkinter
root = tk.Tk()
root.title("Tarkov Barter Profits")
root.geometry("800x600")

# Carrega o vídeo
video_path = "background.mov"
cap = cv2.VideoCapture(video_path)

# Video background label
bg_label = tk.Label(root)
bg_label.place(relwidth=1, relheight=1)  # Cover entire window

# UI elements (make sure they appear on top)
frame = ttk.Frame(root)
frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("Item", "Trader", "Cost", "Profit")
table = ttk.Treeview(frame, columns=columns, show="headings")
for col in columns:
    table.heading(col, text=col)
    table.column(col, anchor="center")

table.pack(fill="both", expand=True)

# Atualiza o vídeo e a tabela
update_video()
update_table()

root.mainloop()

# Libera o vídeo quando o programa termina
cap.release()
cv2.destroyAllWindows()
