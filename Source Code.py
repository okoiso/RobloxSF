import customtkinter as ctk
import requests
import threading
from PIL import Image
from io import BytesIO
import webbrowser

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

class RobloxServerFinder(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Roblox Server Finder")
        self.geometry("900x750")
        self.minsize(750, 600)
        self.configure(fg_color=("gray17", "gray10"))

        self.place_id = ctk.StringVar()
        self.status_text = ctk.StringVar(value="Enter a Place ID and click Search")
        self.servers = []
        self.game_name = " "
        self.game_thumb = None
        self.is_searching = False
        self.search_thread = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)

        self.build_header()
        self.build_search_bar()
        self.build_status_bar()
        self.build_results_area()

    def build_header(self):
        header = ctk.CTkFrame(self.main_frame, height=60, corner_radius=12, fg_color=("gray20", "gray15"))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="ROBLOX SERVER FINDER", font=("Segoe UI", 22, "bold"),
                     text_color=("gray90", "white")).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        ctk.CTkLabel(header, text="Find the least laggy servers instantly", font=("Segoe UI", 13),
                     text_color=("gray60", "gray50")).grid(row=0, column=1, padx=(0, 20), pady=10, sticky="e")

    def build_search_bar(self):
        bar = ctk.CTkFrame(self.main_frame, height=70, corner_radius=10, fg_color=("gray20", "gray15"))
        bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="Place ID", font=("Segoe UI", 14, "bold")).grid(row=0, column=0,
                                                                                padx=(20, 10), pady=15, sticky="w")
        self.entry = ctk.CTkEntry(bar, textvariable=self.place_id, placeholder_text="e.g. 73956553001240",
                                  font=("Segoe UI", 14))
        self.entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")
        self.search_btn = ctk.CTkButton(bar, text="Search", command=self.start_search,
                                        font=("Segoe UI", 14, "bold"), width=140, height=40,
                                        fg_color="#2b5b84", hover_color="#1e405e")
        self.search_btn.grid(row=0, column=2, padx=(10, 20), pady=15)

    def build_status_bar(self):
        status_frame = ctk.CTkFrame(self.main_frame, height=30, corner_radius=6, fg_color="transparent")
        status_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        status_frame.grid_columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(status_frame, textvariable=self.status_text,
                                         font=("Segoe UI", 12), text_color=("gray60", "gray50"))
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.progress = ctk.CTkProgressBar(status_frame, width=200, height=12, corner_radius=6)
        self.progress.grid(row=0, column=1, padx=(10, 10), pady=5, sticky="e")
        self.progress.set(0)
        self.progress.grid_remove()

    def build_results_area(self):
        self.results_frame = ctk.CTkFrame(self.main_frame, corner_radius=12, fg_color=("gray22", "gray17"))
        self.results_frame.grid(row=3, column=0, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(1, weight=1)

        self.banner = ctk.CTkFrame(self.results_frame, height=80, corner_radius=10, fg_color="transparent")
        self.banner.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.banner.grid_columnconfigure(1, weight=1)

        self.game_icon_label = ctk.CTkLabel(self.banner, text="", image=None)
        self.game_icon_label.grid(row=0, column=0, padx=(10, 5), pady=10)

        self.game_name_label = ctk.CTkLabel(self.banner, text="", font=("Segoe UI", 16, "bold"),
                                            text_color=("gray90", "white"))
        self.game_name_label.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        self.scroll = ctk.CTkScrollableFrame(self.results_frame, corner_radius=10,
                                             fg_color=("gray25", "gray20"))
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

    def start_search(self):
        if self.is_searching:
            return

        pid = self.place_id.get().strip()
        if not pid:
            self.status_text.set("Please enter a valid Place ID")
            return

        self.servers = []
        self.game_name = ""
        self.game_thumb = None
        self.clear_results()
        self.status_text.set("Fetching game info...")
        self.progress.set(0)
        self.progress.grid()
        self.search_btn.configure(state="disabled", text="Searching...")
        self.is_searching = True

        self.search_thread = threading.Thread(target=self.perform_search, args=(pid,), daemon=True)
        self.search_thread.start()

    def perform_search(self, place_id):
        try:
            universe_id = self.fetch_universe_id(place_id)
            if universe_id:
                self.fetch_game_details(universe_id)
            else:
                self.fetch_game_details(place_id)

            servers = self.fetch_all_servers(place_id)
            if not servers:
                self.after(0, self.show_no_servers)
                return

            available = [s for s in servers if s["playing"] < s["maxPlayers"]]
            if not available:
                self.after(0, lambda: self.show_info(f"No available slots in {len(servers)} servers found."))
                return

            for s in available:
                fps = s.get("fps", 0)
                ping = s.get("ping", 999)
                s["_score"] = round(ping + (60 - min(60, fps)) * 10)
            available.sort(key=lambda x: x["_score"])
            self.servers = available[:50]

            self.after(0, self.display_results)

        except Exception as e:
            self.after(0, lambda: self.show_error(str(e)))

    def fetch_universe_id(self, place_id):
        try:
            resp = requests.get(
                f"https://apis.roblox.com/universes/v1/places/{place_id}/universe",
                headers=HEADERS, timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("universeId")
        except:
            pass
        return None

    def fetch_game_details(self, identifier):
        try:
            thumb_url = f"https://thumbnails.roblox.com/v1/games/icons?universeIds={identifier}&returnPolicy=PlaceHolder&size=512x512&format=Png&isCircular=false"
            thumb_resp = requests.get(thumb_url, headers=HEADERS, timeout=10)
            if thumb_resp.status_code == 200:
                thumb_data = thumb_resp.json()
                img_url = thumb_data.get("data", [{}])[0].get("imageUrl")
                if img_url:
                    img_resp = requests.get(img_url, headers=HEADERS, timeout=10)
                    self.game_thumb = Image.open(BytesIO(img_resp.content))

            info_resp = requests.get(
                f"https://games.roblox.com/v1/games?universeIds={identifier}",
                headers=HEADERS, timeout=10
            )
            if info_resp.status_code == 200:
                info_data = info_resp.json()
                if "data" in info_data and info_data["data"]:
                    self.game_name = info_data["data"][0].get("name", "Unknown Game")
        except:
            self.game_name = self.game_name or "Unknown Game"

    def fetch_all_servers(self, place_id, max_pages=5):
        all_servers = []
        cursor = None
        for page in range(max_pages):
            progress_val = (page + 1) / max_pages
            self.after(0, lambda v=progress_val, p=page+1: self.update_progress(v, f"Fetching servers (page {p}/{max_pages})..."))

            url = f"https://games.roblox.com/v1/games/{place_id}/servers/Public?sortOrder=Desc&limit=100"
            if cursor:
                url += f"&cursor={cursor}"

            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)
                if resp.status_code != 200:
                    break
                data = resp.json()
                servers = data.get("data", [])
                all_servers.extend(servers)
                cursor = data.get("nextPageCursor")
                if not cursor:
                    break
            except:
                break

            import time
            time.sleep(0.2)

        return all_servers

    def update_progress(self, val, text):
        self.progress.set(val)
        self.status_text.set(f"{text}  Found {len(self.servers)} servers so far...")

    def clear_results(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()
        self.game_name_label.configure(text="")
        self.game_icon_label.configure(image=None)

    def show_no_servers(self):
        self.finish_search()
        self.status_text.set("No servers found. Try again later.")
        self.display_game_banner()

    def show_info(self, message):
        self.finish_search()
        self.status_text.set(message)
        self.display_game_banner()

    def show_error(self, msg):
        self.finish_search()
        self.status_text.set(f"Error: {msg}")

    def finish_search(self):
        self.is_searching = False
        self.search_btn.configure(state="normal", text="Search")
        self.progress.grid_remove()

    def display_results(self):
        self.finish_search()
        self.status_text.set(f"Top {len(self.servers)} servers with lowest lag")
        self.display_game_banner()
        for i, server in enumerate(self.servers):
            self.create_server_card(server, i)

    def display_game_banner(self):
        self.game_name_label.configure(text=self.game_name)
        if self.game_thumb:
            thumb = self.game_thumb.copy()
            thumb.thumbnail((64, 64))
            self.thumb_ctk = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(64, 64))
            self.game_icon_label.configure(image=self.thumb_ctk)
        else:
            self.game_icon_label.configure(image=None)

    def create_server_card(self, server, index):
        score = server["_score"]
        if score < 200: color, emoji = "#4CAF50", "🟢"
        elif score < 400: color, emoji = "#FF9800", "🟡"
        else: color, emoji = "#E53935", "🔴"

        card = ctk.CTkFrame(self.scroll, corner_radius=8, border_width=1,
                            border_color=("gray50", "gray35"), fg_color=("gray30", "gray22"))
        card.pack(fill="x", padx=5, pady=3)
        card.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(card, text=f"{emoji} #{index+1}", font=("Segoe UI", 13, "bold"),
                     text_color=color).grid(row=0, column=0, padx=(12, 5), pady=8, sticky="w")
        ctk.CTkLabel(card, text=f"📶 {server.get('ping', '?')} ms",
                     font=("Segoe UI", 12)).grid(row=0, column=1, padx=5, sticky="w")
        ctk.CTkLabel(card, text=f"🎮 {server.get('fps', '?')} FPS",
                     font=("Segoe UI", 12)).grid(row=0, column=2, padx=5, sticky="w")
        ctk.CTkLabel(card, text=f"👥 {server['playing']}/{server['maxPlayers']}",
                     font=("Segoe UI", 12)).grid(row=0, column=3, padx=5, sticky="w")
        ctk.CTkLabel(card, text=f"📉 {score}",
                     font=("Segoe UI", 12, "bold"), text_color=color).grid(row=0, column=4, padx=5, sticky="w")

        join_btn = ctk.CTkButton(card, text="Join", width=70, height=30,
                                 fg_color=color, hover_color="#144870",
                                 font=("Segoe UI", 12, "bold"),
                                 command=lambda sid=server["id"]: self.join_server(sid))
        join_btn.grid(row=0, column=5, padx=(5, 12), pady=8, sticky="e")

    def join_server(self, server_id):
        pid = self.place_id.get().strip()
        if not pid:
            return
        url = f"roblox://experiences/start?placeId={pid}&gameInstanceId={server_id}"
        webbrowser.open(url)
        self.status_text.set(f"Launching server {server_id[:8]}...")

if __name__ == "__main__":
    app = RobloxServerFinder()
    app.mainloop()
