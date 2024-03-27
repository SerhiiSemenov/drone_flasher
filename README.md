# drone_flasher
## Script for flashing and setting up a drone with betaflight and ELRS or Barvinok

Скрипт для прошивки приймачів FPV дрона.

Протестовано з speedybee405v3 і двома приймачами на ESP8285 та ESP32
Опереційна система Ubuntu 22.04

## Налаштування

### Підготовка

1. Встановити Python3
2. Встановити утіліту dfu-util, для ubuntu/debian sudo apt install dfu-util
3. Покласти файли прошивкі та конфіг в директорію з файлом run.sh

### Прошивка політного контролера(FC)

1. Встановити true для оновлення політного контролера
    ```
    "upload_fc_firmware": true,
    ```
2. Підготувати файл перед прошивкою
    ```    
    python3 src/utils/dfuse-pack.py -i тут_вказати_ім'я_і_шлях_файлу_прошивки.hex ім'я_нового_файлу.dfu
    ```
    Приклад:
        ```
        python3 src/utils/dfuse-pack.py -i obj/betaflight_4.5.0_STM32F405_SPEEDYBEEF405V3.hex obj/betaflight_4.5.0_STM32F405.dfu
        ```
3. Вказати назву файлу
    ```
    "firmware_file_fc": "betaflight_4.5.0_STM32F405.dfu",
    ```

### Завантаження конфігу в політний контролер()
1. Встановити true для завантаження файлу конфігурації політного контролера 
    ```
    "upload_config": true,
    ```
2. Вказати файл конфігу
    ```
    "config_file": "config.txt",
    ```

### Прошивка приймачів (RX)
1. Для активації вказати 
    ```
    "upload_rx_firmware": true,
    ```
2. Вказати тип пристрою
    Для приймачів з процесорами ESP8285 та ESP8266
    ```    
    "target": "Unified_ESP8285_900_RX_via_BetaflightPassthrough",
    ```
    Для приймачів з процесорами ESP32
    ```
    "target": "Unified_ESP32_900_RX_via_BetaflightPassthrough"
    ```
    Список приймачів
    1) BAYCKRC 900MHz Dual Core RX
    2) BETAFPV SuperD 900MHz RX
    3) BETAFPV SuperP 14Ch 900MHz RX
    4) DIY TTGO V1 900MHz RX
    5) DIY TTGO V2 900MHz RX
    6) Generic ESP32 True Diversity 900MHz RX
    7) Generic ESP32 True Diversity 16xPWM 900MHz RX 
    8) GEPRC True Diversity 900MHz RX
    9) HappyModel ES900 Dual RX
    10) iFlight 900MHz 500mW Diversity RX
3. Вказати номера портів у файлі conf.json до яких приєднані приймачі.
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
3. Для прошивкі одразу двох приймачів треба вказати, актуально для прошивкі Barvinok:
   ```
   "dual_rx": true
   ```
### Запуск прошивки
   ```
./run.sh
   ```
