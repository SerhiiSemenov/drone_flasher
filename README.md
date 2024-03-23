# drone_flasher
## Script for flashing RX via FC

Скрипт для прошивки приймачів FPV дрона.

Протестовано з speedybee405v3 і двома приймачами на ESP8285
Опереційна система Ubuntu 22.04

### Налаштування
1. Вказати номера портів у файлі conf.json до яких приєднані приймачі.
    На приклад приймачі приєднані до портів UART2 та UART6
    ```
    "rx1_port": 6,
    "rx2_port": 2,
    ```
2. Вказати ім'я файлів з прошивкою
    ```
    "firmware_file_rx1": "firmware_rx1.bin",
    "firmware_file_rx2": "firmware_rx2.bin"
    ```
3. Для прошивкі одразу двох приймачів треба вказати:
   ```
   "dual_rx": true
   ```
### Запуск прошивки
./run.sh
