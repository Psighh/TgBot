import asyncio
import os
import sys
import flet as ft
import aiohttp

try:
    from config import TOKEN, DB_CONFIG
except ImportError:
    TOKEN = ""
    DB_CONFIG = ""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class BotDashboardFlet:
    def __init__(self):
        self.process = None
        self.is_restarting = False
        self.log_task = None 

    async def main(self, page: ft.Page):
        self.page = page
        self.page.title = "Панель разработчика бота"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window_width = 950
        self.page.window_height = 650
        self.page.padding = 15

        # --- Кнопки управления (Верхняя панель) ---
        self.btn_start = ft.ElevatedButton(
            text="▶ Старт",
            bgcolor=ft.colors.GREEN_700,
            color=ft.colors.WHITE,
            on_click=self.start_bot,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
        )
        self.btn_stop = ft.ElevatedButton(
            text="⏹ Стоп",
            bgcolor=ft.colors.GREY_800,
            color=ft.colors.GREY_500,
            disabled=True,
            on_click=self.stop_bot,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
        )
        self.btn_restart = ft.ElevatedButton(
            text="🔄 Перезапуск",
            bgcolor=ft.colors.GREY_800,
            color=ft.colors.GREY_500,
            disabled=True,
            on_click=self.restart_bot,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=6))
        )
        self.lbl_status = ft.Text(
            value="Статус: Выключен",
            color=ft.colors.AMBER_400,
            size=16,
            weight=ft.FontWeight.BOLD
        )

        toolbar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row([self.btn_start, self.btn_stop, self.btn_restart], spacing=10),
                    self.lbl_status
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=12,
            border_radius=8,
            margin=ft.margin.only(bottom=10)
        )

        # --- Вкладка 1: Консоль (Логи) ---
        self.lv_logs = ft.ListView(
            expand=True,
            spacing=4,
            auto_scroll=True,
        )
        
        console_view = ft.Container(
            content=self.lv_logs,
            bgcolor=ft.colors.BLACK,
            padding=10,
            border_radius=6,
            expand=True
        )

        # --- Вкладка 2: Бот (Отправка сообщений) ---
        self.dd_chats = ft.Dropdown(
            label="Выбор чата (Пользователи из БД)",
            hint_text="Нажмите обновить для загрузки",
            expand=True
        )
        
        btn_refresh_chats = ft.IconButton(
            icon=ft.icons.REFRESH,
            tooltip="Обновить список чатов из БД",
            on_click=self.load_db_chats
        )

        self.txt_manual_chat_id = ft.TextField(
            label="Или введите ID вручную",
            hint_text="Например: -5160768325 или -1002380022509",
            keyboard_type=ft.KeyboardType.NUMBER
        )

        self.txt_message = ft.TextField(
            label="Текст сообщения",
            hint_text="Введите текст сообщения от лица бота...",
            multiline=True,
            min_lines=4,
            max_lines=8
        )

        self.lbl_send_status = ft.Text("", size=14)

        btn_send = ft.ElevatedButton(
            text="Отправить сообщение",
            icon=ft.icons.SEND,
            bgcolor=ft.colors.BLUE_600,
            color=ft.colors.WHITE,
            on_click=self.send_bot_message
        )

        hint_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("📌 Быстрые ID:", size=11, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_300),
                    ft.Text("-5160768325 — беседа для тестов", size=11, color=ft.colors.GREY_400),
                    ft.Text("-1002380022509 — гватемальская беседа", size=11, color=ft.colors.GREY_400),
                ],
                spacing=2
            ),
            padding=8,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=6,
        )

        bot_view = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Отправка сообщений в Telegram", size=18, weight=ft.FontWeight.BOLD)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START
                    ),
                    ft.Row([self.dd_chats, btn_refresh_chats], alignment=ft.MainAxisAlignment.CENTER),
                    self.txt_manual_chat_id,
                    self.txt_message,
                    ft.Row([btn_send, self.lbl_send_status, hint_box], alignment=ft.MainAxisAlignment.START, spacing=15)
                ],
                spacing=15,
                scroll=ft.ScrollMode.AUTO
            ),
            padding=15,
            expand=True
        )

        # --- Боковая панель навигации (Sidebar) ---
        self.content_area = ft.Container(content=console_view, expand=True)

        self.sidebar = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.TERMINAL_OUTLINED,
                    selected_icon=ft.icons.TERMINAL,
                    label="Консоль",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.CHAT_BUBBLE_OUTLINE,
                    selected_icon=ft.icons.CHAT_BUBBLE,
                    label="Бот",
                ),
            ],
            on_change=lambda e: self.switch_tab(e.control.selected_index, console_view, bot_view),
            bgcolor=ft.colors.BACKGROUND
        )

        # Сборка основного макета
        main_layout = ft.Row(
            controls=[
                self.sidebar,
                ft.VerticalDivider(width=1),
                self.content_area
            ],
            expand=True
        )

        await self.page.add_async(toolbar, main_layout)
        
        # Первичная фоновая загрузка чатов
        asyncio.create_task(self.load_db_chats(None))

    def switch_tab(self, index, console, bot):
        if index == 0:
            self.content_area.content = console
        elif index == 1:
            self.content_area.content = bot
        self.page.update()

    def log(self, text: str, color=ft.colors.WHITE):
        self.lv_logs.controls.append(
            ft.Text(text, font_family="Consolas", size=13, color=color)
        )
        self.page.update()

    def set_buttons_state(self, start=False, stop=True, restart=True):
        self.btn_start.disabled = start
        self.btn_start.bgcolor = ft.colors.GREY_800 if start else ft.colors.GREEN_700
        self.btn_start.color = ft.colors.GREY_500 if start else ft.colors.WHITE

        self.btn_stop.disabled = stop
        self.btn_stop.bgcolor = ft.colors.GREY_800 if stop else ft.colors.RED_700
        self.btn_stop.color = ft.colors.GREY_500 if stop else ft.colors.WHITE

        self.btn_restart.disabled = restart
        self.btn_restart.bgcolor = ft.colors.GREY_800 if restart else ft.colors.BLUE_700
        self.btn_restart.color = ft.colors.GREY_500 if restart else ft.colors.WHITE
        
        self.page.update()

    async def start_bot(self, e):
        if self.process:
            return

        self.set_buttons_state(start=True, stop=True, restart=True)
        self.lbl_status.value = "Статус: Запуск..."
        self.lbl_status.color = ft.colors.AMBER_400
        self.log("[СИСТЕМА] Запуск бота...", color=ft.colors.BLUE_200)

        try:
            current_env = os.environ.copy()
            current_env["PYTHONIOENCODING"] = "utf-8"

            self.process = await asyncio.create_subprocess_exec(
                sys.executable, "-u", "main.py",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=SCRIPT_DIR,
                env=current_env
            )

            self.set_buttons_state(start=True, stop=False, restart=False)
            self.lbl_status.value = "Статус: Работает"
            self.lbl_status.color = ft.colors.GREEN_400
            self.page.update()

            self.log_task = asyncio.create_task(self.stream_logs())

        except Exception as ex:
            self.log(f"[ОШИБКА ЗАПУСКА] Не удалось запустить процесс:\n{str(ex)}", color=ft.colors.RED_400)
            await self.reset_ui()

    async def stream_logs(self):
        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                text = line.decode('utf-8', errors='replace').rstrip('\r\n')
                self.log(text)
            
            await self.process.wait()
            await self.handle_process_exit()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.log(f"\n[ОШИБКА ЧТЕНИЯ ЛОГОВ]: {str(e)}", color=ft.colors.RED_400)
            await self.handle_process_exit()

    async def handle_process_exit(self):
        if self.is_restarting:
            self.is_restarting = False
            self.process = None
            await self.start_bot(None)
        else:
            await self.reset_ui()

    async def stop_bot(self, e):
        if not self.process:
            return
        
        self.set_buttons_state(start=True, stop=True, restart=True)
        self.lbl_status.value = "Статус: Остановка..."
        self.lbl_status.color = ft.colors.RED_ACCENT
        self.page.update()
        
        try:
            self.log("\n[СИСТЕМА] Принудительная остановка бота...\n", color=ft.colors.RED_400)
            
            if self.log_task and not self.log_task.done():
                self.log_task.cancel()

            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            try:
                self.process.kill()
            except Exception:
                pass
        except Exception as ex:
            self.log(f"[СИСТЕМА] Исключение при остановке: {ex}", color=ft.colors.RED_400)
        finally:
            await self.reset_ui()

    async def restart_bot(self, e):
        if not self.process or self.is_restarting:
            return

        self.is_restarting = True
        self.set_buttons_state(start=True, stop=True, restart=True)
        self.lbl_status.value = "Статус: Перезапуск..."
        self.lbl_status.color = ft.colors.BLUE_400
        self.page.update()
        
        try:
            self.log("\n[СИСТЕМА] Инициирован безопасный перезапуск...\n", color=ft.colors.BLUE_200)
            
            if self.log_task and not self.log_task.done():
                self.log_task.cancel()

            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            try:
                self.process.kill()
            except Exception:
                pass
        except Exception as ex:
            self.log(f"[СИСТЕМА] Ошибка при перезапуске: {ex}", color=ft.colors.RED_400)
        finally:
            self.is_restarting = False
            self.process = None
            await self.start_bot(None)

    async def reset_ui(self):
        self.process = None
        self.is_restarting = False
        self.set_buttons_state(start=False, stop=True, restart=True)
        self.lbl_status.value = "Статус: Выключен"
        self.lbl_status.color = ft.colors.AMBER_400
        self.page.update()

    # --- Функционал вкладки Бот ---
    async def load_db_chats(self, e):
        if not DB_CONFIG:
            self.dd_chats.hint_text = "Конфиг БД не найден"
            self.page.update()
            return

        self.dd_chats.options = []
        self.dd_chats.hint_text = "Загрузка чатов из базы..."
        self.page.update()

        try:
            import asyncpg
            conn = await asyncpg.connect(DB_CONFIG)
            
            rows = await conn.fetch("SELECT user_id, custom_nickname FROM users ORDER BY custom_nickname")
            options = []
            for row in rows:
                nick = row['custom_nickname'] or "Без ника"
                options.append(ft.dropdown.Option(key=str(row['user_id']), text=f"👤 {nick} (ID: {row['user_id']})"))
            
            group_rows = await conn.fetch("SELECT DISTINCT chat_id FROM marriages WHERE chat_id IS NOT NULL")
            for grow in group_rows:
                options.append(ft.dropdown.Option(key=str(grow['chat_id']), text=f"💬 Группа (ID: {grow['chat_id']})"))

            await conn.close()

            if options:
                self.dd_chats.options = options
                self.dd_chats.hint_text = "Выберите чат для отправки"
            else:
                self.dd_chats.hint_text = "Чаты в БД не найдены"
        except Exception as ex:
            self.dd_chats.hint_text = "Не удалось подключиться к БД"
            print(f"Ошибка БД: {ex}")
        
        self.page.update()

    async def send_bot_message(self, e):
        chat_id = self.txt_manual_chat_id.value.strip()
        if not chat_id and self.dd_chats.value:
            chat_id = self.dd_chats.value

        if not chat_id:
            self.lbl_send_status.value = "❌ Укажите ID или выберите чат!"
            self.lbl_send_status.color = ft.colors.RED_400
            self.page.update()
            return

        text = self.txt_message.value.strip()
        if not text:
            self.lbl_send_status.value = "❌ Введите текст сообщения!"
            self.lbl_send_status.color = ft.colors.RED_400
            self.page.update()
            return

        if not TOKEN:
            self.lbl_send_status.value = "❌ В config.py отсутствует TOKEN!"
            self.lbl_send_status.color = ft.colors.RED_400
            self.page.update()
            return

        self.lbl_send_status.value = "⏳ Отправка..."
        self.lbl_send_status.color = ft.colors.AMBER_400
        self.page.update()

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        self.lbl_send_status.value = "✅ Отправлено успешно!"
                        self.lbl_send_status.color = ft.colors.GREEN_400
                        self.txt_message.value = ""
                    else:
                        res_text = await resp.text()
                        self.lbl_send_status.value = f"❌ Ошибка API: {resp.status}"
                        self.lbl_send_status.color = ft.colors.RED_400
                        self.log(f"[ОШИБКА ТЕЛЕГРАМА] API вернул: {res_text}", color=ft.colors.RED_400)
        except Exception as ex:
            self.lbl_send_status.value = "❌ Ошибка сети"
            self.lbl_send_status.color = ft.colors.RED_400
            self.log(f"[ОШИБКА СЕТИ ПАНЕЛИ]: {str(ex)}", color=ft.colors.RED_400)
        
        self.page.update()

if __name__ == "__main__":
    dashboard = BotDashboardFlet()
    ft.app(target=dashboard.main)