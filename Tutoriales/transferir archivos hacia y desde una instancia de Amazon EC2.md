Para transferir archivos hacia y desde una instancia de Amazon EC2, puedes utilizar varios métodos dependiendo de tu sistema operativo y la configuración de tu instancia EC2. Aquí te presento algunos métodos comunes:

### Usando SCP (Protocolo de Copia Segura)

SCP es una herramienta de línea de comandos que utiliza SSH para transferir archivos. Está disponible en Linux, macOS y Windows (a través de herramientas como PuTTY o Windows Subsystem for Linux).

#### Comando de Ejemplo

```bash
# Copiar un archivo desde tu máquina local a la instancia EC2
scp -i /ruta/a/tu-clave.pem /ruta/a/archivo-local.txt ec2-user@tu-ec2-public-dns:/ruta/a/directorio-remoto/

# Copiar un archivo desde la instancia EC2 a tu máquina local
scp -i /ruta/a/tu-clave.pem ec2-user@tu-ec2-public-dns:/ruta/a/archivo-remoto.txt /ruta/a/directorio-local/

# Copiar un directorio 'aws_edfctalogoqr' desde la instancia EC2 a tu máquina local
scp -i edfcatalogoqr.pem -r ec2-user@edefrutos2025.xyz:/home/ec2-user/aws_edfcatalogoqr/ '/Users/edefrutos/AWS_Instancia_NO_BORRAR'

```

### Usando SFTP (Protocolo de Transferencia de Archivos SSH)

SFTP es otro método que utiliza SSH para transferir archivos. Puedes usar herramientas de línea de comandos o aplicaciones GUI como FileZilla.

#### Comando de Ejemplo

```bash
# Iniciar una sesión SFTP
sftp -i /ruta/a/tu-clave.pem ec2-user@tu-ec2-public-dns

# Una vez conectado, usa comandos SFTP para transferir archivos
# Por ejemplo, para subir un archivo:
put /ruta/a/archivo-local.txt /ruta/a/directorio-remoto/

# Para descargar un archivo:
get /ruta/a/archivo-remoto.txt /ruta/a/directorio-local/
```

### Usando AWS CLI

Si tienes instalado y configurado AWS CLI, puedes usarlo para transferir archivos hacia y desde Amazon S3, y luego acceder a ellos desde tu instancia EC2.

#### Comandos de Ejemplo

```bash
# Subir un archivo a un bucket de S3
aws s3 cp /ruta/a/archivo-local.txt s3://nombre-de-tu-bucket/

# Descargar un archivo de un bucket de S3
aws s3 cp s3://nombre-de-tu-bucket/archivo-remoto.txt /ruta/a/directorio-local/
```

### Usando RDP (Protocolo de Escritorio Remoto) para Instancias Windows

Para instancias EC2 de Windows, puedes usar RDP para conectarte a la instancia y luego usar métodos estándar de transferencia de archivos de Windows, como arrastrar y soltar o copiar y pegar.

### Usando EC2 Instance Connect

Para instancias que soportan EC2 Instance Connect, puedes usar la Consola de Administración de AWS para conectarte a tu instancia y transferir archivos usando el cliente SSH basado en navegador.

### Consideraciones Importantes

- **Grupos de Seguridad**: Asegúrate de que el grupo de seguridad de tu instancia EC2 permita tráfico SSH entrante (puerto 22) desde tu dirección IP.
- **Par de Claves**: Usa el par de claves correcto (archivo `.pem`) asociado con tu instancia EC2 para la autenticación.
- **Permisos**: Asegúrate de que los archivos y directorios que estás transfiriendo tengan los permisos apropiados configurados.

Estos métodos deberían cubrir la mayoría de los escenarios para transferir archivos hacia y desde una instancia EC2.
