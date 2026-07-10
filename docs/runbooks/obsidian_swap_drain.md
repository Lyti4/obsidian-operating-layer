# Runbook — `obsidian_swap_drain.py`

## Назначение

Инструмент временно выключает swap (подкачку памяти), затем восстанавливает
обычный swap и zram. Это изменение состояния хоста, поэтому требуется отдельное
разрешение и рабочий recovery-доступ (способ восстановить сервер).

## До запуска

1. Подтвердить хост и отсутствие другой тяжёлой задачи.
2. Иметь SSH и консоль восстановления VPS.
3. Сохранить вывод `free -m`, `swapon --show` и списка swap/zram units.
4. Запустить read-only preflight:

```bash
python3 tools/obsidian_resource_preflight.py
```

5. Не запускать, если projected available memory ниже выбранного порога.

## Запуск

```bash
python3 tools/obsidian_swap_drain.py --min-post-drain-available-mb 256
```

Для более консервативного запуска без очистки page cache:

```bash
python3 tools/obsidian_swap_drain.py \
  --min-post-drain-available-mb 256 \
  --no-drop-caches
```

## Проверка

- JSON имеет status `ok` или `ok-already-empty`.
- После выполнения `swapon --show` снова показывает ожидаемый swap/zram.
- `after_swap_total_mb` не равен нулю, если swap был настроен до запуска.
- `after_swap_used_mb` равен нулю; затем повторно проходит resource preflight.

## Откат и восстановление

Если восстановление внутри инструмента не сработало:

```bash
sudo swapon -a
sudo systemctl start systemd-zram-setup@zram0.service
sudo systemctl start dev-zram0.swap
swapon --show
free -m
```

Запускать только существующие на хосте units. Если swap не вернулся, прекратить
embedding/indexing-задачу и использовать recovery-консоль; не перезагружать
сервер вслепую.

## Стоп-условия

Недостаточно RAM, нет recovery-доступа, активна тяжёлая задача, неизвестна
текущая swap-конфигурация, `sudo` требует неожиданных прав или после операции
swap не восстановлен.
