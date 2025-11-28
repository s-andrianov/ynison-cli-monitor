# Ynison CLI Monitor

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Терминальный монитор состояния воспроизведения Яндекс.Музыки через протокол Ynison. Отображает текущий трек, прогресс и статус паузы в реальном времени.

![Demo](https://via.placeholder.com/800x200/2D3748/FFFFFF?text=Yandex+Music+Ynison+CLI+Monitor)

- **Реальное время** - отслеживание состояния через Ynison
- **Текущий трек** - отображение названия трека и исполнителей
- **Прогресс-бар** - визуализация прогресса воспроизведения
- **Статус паузы** - индикация воспроизведения/паузы
- **Красивый интерфейс** - адаптивная консольная визуализация
- использует OAuth-токен

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/ynison-cli-monitor.git
cd ynison-cli-monitor
```
Установите зависимости:

```bash
pip install aiohttp wcwidth
```

## Получение OAuth-токена Яндекс.Музыки

[MarshalX/yandex-music-api](https://github.com/MarshalX/yandex-music-api/discussions/513)
