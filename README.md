# Conducción autónoma en Webots

Proyecto final (Equipo 21) de navegación autónoma. Un BMW X5 recorre una ciudad en [Webots](https://cyberbotics.com/) y una red convolucional predice el ángulo de dirección a partir de la cámara frontal. El modelo se entrenó con imágenes capturadas en el mismo mundo y se ejecuta en tiempo real dentro del simulador.

La demostración está en `Proyecto Final _ Equipo 21.mp4`.
https://drive.google.com/file/d/1wD4n8l5DMxsg_ulRO4labDd2KhKCk5Tx/view?usp=sharing

## Cómo funciona

1. En Webots se recorre el circuito a mano y se guardan frames de la cámara junto con el ángulo de dirección (archivos CSV). Esas capturas no están en este repositorio: vivían en Google Drive y la carpeta `Data/` está vacía.
2. El notebook entrena una CNN de regresión que, dada una imagen del camino, devuelve un ángulo de dirección.
3. El controlador `Prueba_modelo_mundo2.py` corre como controlador externo del vehículo, lee la cámara central en cada paso y envía el ángulo predicho al driver del auto. La velocidad de crucero inicial es 25 km/h.

## Estructura

| Ruta | Contenido |
| --- | --- |
| `Código/Proyecto_Final_entrenamiento.ipynb` | Carga de datos, preprocesado, entrenamiento y guardado del modelo (Google Colab). |
| `Código/Prueba_modelo_mundo2.py` | Controlador de inferencia para Webots. |
| `Modelo/Modelo_2025-06-22_12-32-00.keras` | Pesos entrenados (~18 MB). |
| `Worlds/city_traffic_2025_01_para_captura.wbt` | Mundo para capturar datos (Webots R2023b). El auto arranca detenido. |
| `Worlds/city_traffic_2025_01_funcionando.wbt` | Mundo para la prueba autónoma (Webots R2025a). |
| `Data/` | Reservada para imágenes y CSV. Vacía en este repositorio. |
| `Proyecto Final _ Equipo 21.mp4` | Video de la prueba. |

El mundo es una ciudad con calles, cruces, semáforos, edificios y señales. El vehículo es un `BmwX5` con controlador `<extern>` y estos sensores:

- `camera izquierda`, `camera central` y `camera derecha` (240×120). La inferencia usa solo la central.
- GPS y giroscopio (presentes en el mundo; el controlador no los consulta).
- Un `Display` de 200×150 donde se pinta la imagen de la cámara.

## Datos y preprocesado

El notebook concatena cuatro recorridos registrados en CSV (`Nombre`, `Steering`):

| Conjunto | Imágenes |
| --- | ---: |
| Sentido horario (tiempo) | 13 455 |
| Sentido antihorario (tiempo) | 12 465 |
| Antihorario (nuevo) | 2 454 |
| Horario (nuevo) | 2 733 |
| **Total etiquetado** | **31 107** |

Cada imagen se pasa a escala de grises, se recorta la franja del camino (filas 54–120 en frames de 120 px de alto, o 32–66 si ya miden 66), se redimensiona a 200×66 y se normaliza dividiendo entre 255. La forma final es `(66, 200, 1)`.

División 80/20 con `random_state=42`: 24 885 entrenamiento y 6 222 prueba. Del entrenamiento se aparta un 10 % como validación.

## Modelo

CNN de regresión inspirada en la arquitectura NVIDIA para dirección a partir de cámara, con `BatchNormalization` después de cada capa y `Dropout` (0.25 tras el cuarto convolucional, 0.5 tras la primera densa).

| Bloque | Detalle |
| --- | --- |
| Conv | 24 filtros 5×5, stride 2 |
| Conv | 36 filtros 5×5, stride 2 |
| Conv | 48 filtros 5×5, stride 2 |
| Conv | 64 filtros 3×3 |
| Conv | 64 filtros 3×3 |
| Densas | 1164 → 100 → 50 → 10 → **1** (ángulo) |

- Optimizador: Adam
- Pérdida: error cuadrático medio (MSE)
- Entrenamiento: 30 épocas, batch de 128

Resultados de la corrida guardada en el notebook:

| Métrica | Valor |
| --- | ---: |
| Pérdida de entrenamiento (época 30) | 3.63e-4 |
| Pérdida de validación (época 30) | 2.69e-4 |
| MSE en el conjunto de prueba | 2.52e-4 |

El modelo se guarda como `Modelo_AAAA-MM-DD_HH-MM-SS.keras`. El archivo incluido es `Modelo_2025-06-22_12-32-00.keras`.

## Requisitos

- Webots R2023b o superior (el mundo de prueba declara R2025a).
- Python 3 con los paquetes del controlador de Webots.
- `numpy`, `opencv-python` y `tensorflow` (el notebook se ejecutó con Keras sobre TensorFlow en Colab, Python 3.11).

El controlador importa `controller` y `vehicle`, que vienen con la instalación de Webots y hay que exponerlos en `PYTHONPATH`.

## Ejecutar la conducción autónoma

1. Abre `Worlds/city_traffic_2025_01_funcionando.wbt` en Webots. El BMW usa el controlador `<extern>`, así que la simulación espera a que arranque el script de Python.
2. En `Código/Prueba_modelo_mundo2.py`, apunta `folder_path` a la carpeta `Modelo` de este repositorio. Hoy el script busca el archivo en `/home/raven/Desktop/MNA/ProyectoFinal/Models`.
3. Desde una terminal, con Webots ya abierto en ese mundo:

```bash
# macOS (ajusta la ruta si Webots no está en Aplicaciones)
export WEBOTS_HOME="/Applications/Webots.app"
export PYTHONPATH="${WEBOTS_HOME}/Contents/lib/controller/python:${PYTHONPATH}"

# Linux
# export WEBOTS_HOME="/usr/local/webots"
# export PYTHONPATH="${WEBOTS_HOME}/lib/controller/python:${PYTHONPATH}"

cd "Código"
python3 Prueba_modelo_mundo2.py
```

4. Pulsa el play de Webots. El script carga el modelo, muestra la cámara central en el display del auto y aplica el ángulo predicho. El cambio de dirección se limita a 0.1 rad por paso.

Teclado mientras corre el controlador:

| Tecla | Efecto en el código |
| --- | --- |
| `W` | Fija la velocidad de crucero en 5 km/h |
| `S` | Fija la velocidad de crucero en −5 km/h |
| `A` / `D` | Suma o resta dirección manual (±0.5 sobre un tope de ±25), que el modelo vuelve a sobrescribir en el siguiente frame |

## Reentrenar

Abre `Código/Proyecto_Final_entrenamiento.ipynb` en Colab, monta Drive y deja las imágenes y los CSV bajo `Navegacion autonoma/Webots_Proyecto_final`, con la misma estructura de carpetas que usa el notebook (`Imagenes_Webots_Final_tiempo_h`, `Imagenes_Webots_Final_tiempo_anti`, `Imagenes_Webots_Final_newhorario`, `Imagenes_Webots_Final_newantihorario`). Al terminar, copia el `.keras` generado a `Modelo/` y actualiza `base_filename` en el controlador.

El preprocesado de inferencia tiene que coincidir con el de entrenamiento: gris, recorte de filas 54–120, resize a 200×66, división entre 255 y forma `(1, 66, 200, 1)`.
