# Usar una imagen base de Python
FROM python:3.8

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo requirements.txt al directorio de trabajo del contenedor
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el contenido del directorio actual a /app dentro del contenedor
COPY . .

# Comando a ejecutar cuando se inicie el contenedor
CMD ["python", "app.py"]
