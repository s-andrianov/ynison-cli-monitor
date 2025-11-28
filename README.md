# Ynison CLI Monitor

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Терминальный монитор состояния воспроизведения Яндекс.Музыки через протокол Ynison. Отображает текущий трек, прогресс и статус паузы в реальном времени.

```
╔════════════════════════════════════════════════════════════════╗
║ Аккаунт: My_Username                                           ║
╠════════════════════════════════════════════════════════════════╣
║ hell shell (Slowed + Reverb) - Ronliee                         ║
╠════════════════════════════════════════════════════════════════╣
║ 2:35 [██████████████████████████████████████░░░░░░░░░░░░] 3:23 ║
╚════════════════════════════════════════════════════════════════╝
```

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/ynison-cli-monitor.git
cd ynison-cli-monitor
```
2. Установите зависимости:

```bash
pip install aiohttp wcwidth
```

## Получение OAuth-токена Яндекс.Музыки

[MarshalX/yandex-music-api](https://github.com/MarshalX/yandex-music-api/discussions/513)
