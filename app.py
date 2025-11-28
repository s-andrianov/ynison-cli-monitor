import uuid
import json
import asyncio
import aiohttp
import time
import os
from wcwidth import wcswidth

class YandexMusicClient:
    def __init__(self, token):
        self.token = token
        self.device_id = str(uuid.uuid4())
        self.redirect_data = None
        self.host = None
        self.info = None
        self.is_connected = False
        self.session = None
        self.current_track_info = None
        self.last_progress = 0
        self.last_duration = 0
        self.is_paused = True
        self.init_phase = True
        self.last_update_time = 0
        self.progress_task = None

    def clear_screen(self):
        """Очистка консоли"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def pad_or_trim(self, text: str, width: int) -> str:
        """
        Обрезает или добивает строку пробелами с учётом визуальной ширины
        """
        if not text:
            return " " * width

        current = ""
        current_width = 0

        for ch in text:
            ch_width = wcswidth(ch)
            if current_width + ch_width > width:
                break
            current += ch
            current_width += ch_width

        if current_width < width:
            current += " " * (width - current_width)

        return current

    def visual_len(self, text: str) -> int:
        """Реальная ширина в терминале"""
        return wcswidth(text)

    def visual_pad(self, text: str, width: int) -> str:
        """Паддинг с учетом реальной ширины символов"""
        diff = width - self.visual_len(text)
        if diff > 0:
            return text + (" " * diff)
        return text[:width]

    def draw_player(self):
        if not self.current_track_info:
            message = " ⏹ НЕТ АКТИВНОГО ТРЕКА "
            box_width = self.visual_len(message) + 2
            self.clear_screen()
            print("╔" + "═" * box_width + "╗")
            print(f"║{self.pad_or_trim(message, box_width)}║")
            print("╠" + "═" * box_width + "╣")
            print(f"║{self.pad_or_trim('Ожидание воспроизведения...', box_width)}║")
            print("╠" + "═" * box_width + "╣")
            print(f"║ Аккаунт: {self.pad_or_trim(self.info['login'], box_width - 10)}║")
            print("╚" + "═" * box_width + "╝")
            print("\nНажмите Ctrl+C для выхода")
            return

        track = self.current_track_info
        status = "❚❚" if self.is_paused else ""

        progress_percent = (self.last_progress / self.last_duration * 100) if self.last_duration > 0 else 0
        bar_length = 50
        filled_length = int(bar_length * progress_percent / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        time_progress = self.format_time(self.last_progress)
        time_duration = self.format_time(self.last_duration)

        progress_line = f"{time_progress} [{bar}] {time_duration}"
        progress_line_visual_width = self.visual_len(progress_line)
        box_width = progress_line_visual_width + 2

        self.clear_screen()

        track_line = self.visual_pad(f"{track['title']} - {track['artists']['text']} {status}", box_width - 2)
        login_line = self.visual_pad(f"Аккаунт: {self.info['login']}", box_width - 2)

        print("╔" + "═" * box_width + "╗")
        print(f"║ {login_line} ║")
        print("╠" + "═" * box_width + "╣")
        print(f"║ {track_line} ║")
        print("╠" + "═" * box_width + "╣")
        print(f"║ {progress_line} ║")
        print("╚" + "═" * box_width + "╝")

        print("\nНажмите Ctrl+C для выхода")

    async def update_progress_loop(self):
        """Цикл автоматического обновления прогресса"""
        while self.is_connected:
            if not self.is_paused and self.current_track_info and not self.init_phase:
                current_time = time.time() * 1000
                elapsed = current_time - self.last_update_time
                
                self.last_progress += elapsed
                self.last_update_time = current_time
                
                if self.last_progress > self.last_duration:
                    self.last_progress = self.last_duration
                
                self.draw_player()
            
            await asyncio.sleep(1)

    async def get_redirect(self):
        """Получение редиректа"""
        ws_proto = {
            "Ynison-Device-Id": self.device_id,
            "Ynison-Device-Info": '{"app_name":"Chilipizdrik","type":1}',
        }

        ws_protocol_header = "Bearer, v2, " + json.dumps(ws_proto)

        print(f"[INFO] Получение редиректа...")
        print(f"[INFO] ID устройства: {self.device_id}")

        try:
            headers = {
                "Sec-WebSocket-Protocol": ws_protocol_header,
                "Origin": "http://music.yandex.ru",
                "Authorization": "OAuth " + self.token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    "wss://ynison.music.yandex.ru/redirector.YnisonRedirectService/GetRedirectToYnison",
                    headers=headers,
                    timeout=30,
                ) as websocket:
                    async for msg in websocket:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)

                            if "host" in data:
                                self.info = await self.get_account_info()

                                print(f"[SUCCESS] [{self.info['login']}] Редирект получен")
                                print(f"[INFO] [{self.info['login']}] Хост: {data['host']}")

                                self.redirect_data = data
                                self.host = data["host"]
                                return data
                            else:
                                raise Exception("Неожиданный ответ: " + msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            raise Exception(f"WebSocket error: {msg.data}")

        except Exception as e:
            raise Exception("Ошибка редиректа: " + str(e))

    async def connect_to_ynison(self):
        """Подключение к Ynison"""
        if not self.redirect_data:
            await self.get_redirect()

        ws_proto = {
            "Ynison-Device-Id": self.device_id,
            "Ynison-Device-Info": '{"app_name":"Yandex Music API","type":1}',
            "Ynison-Redirect-Ticket": self.redirect_data["redirect_ticket"],
        }

        ws_protocol_header = "Bearer, v2, " + json.dumps(ws_proto)
        url = f"wss://{self.redirect_data['host']}/ynison_state.YnisonStateService/PutYnisonState"

        print(f"[INFO] [{self.info['name']}] Подключение к Ynison")
        print(f"[INFO] [{self.info['name']}] URL: {url}")

        try:
            headers = {
                "Sec-WebSocket-Protocol": ws_protocol_header,
                "Origin": "http://music.yandex.ru",
                "Authorization": "OAuth " + self.token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            self.session = aiohttp.ClientSession()
            self.websocket = await self.session.ws_connect(url, headers=headers)
            self.is_connected = True

            print(f"[SUCCESS] [{self.info['name']}] Подключено к Ynison")

            await self.send_initial_message()
            
            print("[INFO] Инициализация завершена, переход к отображению плеера...")
            await asyncio.sleep(1)
            self.init_phase = False
            
            self.draw_player()
            
            self.progress_task = asyncio.create_task(self.update_progress_loop())

            async for msg in self.websocket:
                await self.handle_message(msg)

        except Exception as e:
            print(f"[ERROR] [{self.info['name']}] Ошибка подключения: {e}")
            self.is_connected = False
            if self.session:
                await self.session.close()

    async def send_initial_message(self):
        """Отправка начального сообщения"""
        current_time = int(time.time() * 1000)

        capabilities = {
            "can_be_player": False,
            "can_be_remote_controller": True,
            "volume_granularity": 16,
        }

        initial_message = {
            "update_full_state": {
                "player_state": {
                    "player_queue": {
                        "current_playable_index": -1,
                        "entity_id": "",
                        "entity_type": "VARIOUS",
                        "playable_list": [],
                        "options": {"repeat_mode": "NONE"},
                        "entity_context": "BASED_ON_ENTITY_BY_DEFAULT",
                        "version": {
                            "device_id": self.device_id,
                            "version": current_time,
                            "timestamp_ms": current_time,
                        },
                    },
                    "status": {
                        "duration_ms": 0,
                        "paused": True,
                        "playback_speed": 1.0,
                        "progress_ms": 0,
                        "version": {
                            "device_id": self.device_id,
                            "version": current_time,
                            "timestamp_ms": current_time,
                        },
                    },
                },
                "device": {
                    "capabilities": capabilities,
                    "info": {
                        "device_id": self.device_id,
                        "type": "WEB",
                        "title": "YUMI - " + self.info["name"],
                        "app_name": "Sync",
                    },
                    "volume_info": {"volume": 50},
                    "is_shadow": False,
                },
                "is_currently_active": False,
            },
            "rid": str(uuid.uuid4()),
            "player_action_timestamp_ms": current_time,
            "activity_interception_type": "DO_NOT_INTERCEPT_BY_DEFAULT",
        }

        await self.websocket.send_str(json.dumps(initial_message))
        print(f"[INFO] [{self.info['name']}] Начальное сообщение отправлено")

    async def handle_message(self, msg):
        """Обработка входящих сообщений"""
        try:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)

                if "player_state" in data:
                    content = data["player_state"]

                    duration_ms = int(content["status"]["duration_ms"])
                    progress_ms = int(content["status"]["progress_ms"])
                    self.is_paused = content["status"]["paused"]

                    current_playable_index = content["player_queue"][
                        "current_playable_index"
                    ]
                    playable_list = content["player_queue"]["playable_list"]

                    if playable_list and current_playable_index >= 0:
                        current_track_id = playable_list[current_playable_index][
                            "playable_id"
                        ]
                        
                        if not self.current_track_info or self.current_track_info['id'] != current_track_id:
                            self.current_track_info = await self.get_track_info(current_track_id)
                        
                        self.last_progress = progress_ms
                        self.last_duration = duration_ms
                        self.last_update_time = time.time() * 1000
                        
                        if not self.init_phase:
                            self.draw_player()
                    elif not self.init_phase and self.current_track_info:
                        self.draw_player()

            elif msg.type == aiohttp.WSMsgType.ERROR:
                if not self.init_phase:
                    print(f"[ERROR] Ошибка WebSocket: {msg.data}")

        except Exception as e:
            if not self.init_phase:
                print(f"[ERROR] Ошибка обработки сообщения: {e}")

    async def get_track_info(self, track_id):
        """Получение информации о треке"""
        url = f"https://api.music.yandex.net/tracks/{track_id}/full-info"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception("Ошибка запроса API Yandex.")

                data = await response.json()

        track = data["result"]["track"]
        artists = [
            {
                "id": artist["id"],
                "name": artist["name"],
                "cover": artist["cover"]["uri"],
            }
            for artist in track["artists"]
        ]

        return {
            "id": track["id"],
            "title": track["title"],
            "duration": track["durationMs"],
            "artists": {
                "text": ", ".join([artist["name"] for artist in artists]),
                "list": artists,
            },
            "album": {
                "id": track["albums"][0]["id"],
                "title": track["albums"][0]["title"],
            },
            "year": track["albums"][0]["year"],
            "cover": track.get("ogImage") or track.get("coverUri"),
        }

    async def get_account_info(self):
        """Получение информации об аккаунте Яндекс.Музыки"""
        url = "https://api.music.yandex.net/account/status"

        headers = {"Authorization": "OAuth " + self.token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise Exception("Ошибка запроса API Yandex.")

                    data = await response.json()
                    result = data["result"]

                    account = result["account"]
                    subscription = result["subscription"]

                    return {
                        "id": account["uid"],
                        "login": account["login"],
                        "name": account.get("displayName"),
                        "email": result.get("defaultEmail"),
                        "region": account.get("regionCode"),
                        "birthday": account.get("birthday"),
                        "has_plus": result.get("plus", {}).get("hasPlus"),
                        "subscription_active": bool(
                            subscription.get("autoRenewable", [])
                        ),
                        "subscription_until": (
                            subscription.get("autoRenewable", [{}])[0].get("expires")
                            if subscription.get("autoRenewable")
                            else None
                        ),
                    }

        except Exception as e:
            print(f"[ERROR] Ошибка запроса API Yandex: {e}")
            return {"login": "unknown", "name": "unknown"}

    def format_time(self, milliseconds):
        """Форматирование времени"""
        if isinstance(milliseconds, str):
            milliseconds = int(milliseconds)

        total_seconds = int(milliseconds // 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    async def close(self):
        """Закрытие соединения"""
        self.is_connected = False
        if self.progress_task:
            self.progress_task.cancel()
            try:
                await self.progress_task
            except asyncio.CancelledError:
                pass
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()
        print("[INFO] Соединение закрыто")


async def main():
    client = YandexMusicClient(
        token="токен_яндекс_музыки"
    )
    try:
        await client.connect_to_ynison()
    except KeyboardInterrupt:
        print("\n[INFO] Завершение работы...")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
