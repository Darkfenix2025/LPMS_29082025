# Modelos de Escritos Legales

Este directorio contiene los modelos de escritos legales que se pueden completar automáticamente con datos del caso.

## Estructura de Carpetas

- `civil/` - Modelos para casos civiles
- `familia/` - Modelos para casos de familia
- `laboral/` - Modelos para casos laborales
- `penal/` - Modelos para casos penales
- `comercial/` - Modelos para casos comerciales
- `general/` - Modelos de uso general
- `mediacion/` - Modelos para mediaciones

## Formato de Archivos

Los modelos deben estar en formato `.docx` y pueden usar las siguientes variables:

### Variables del Caso
- `{{numero_expediente}}` - Número de expediente
- `{{anio_caratula}}` - Año de la carátula
- `{{caratula}}` - Carátula completa del caso
- `{{juzgado}}` - Juzgado donde tramita
- `{{jurisdiccion}}` - Jurisdicción
- `{{etapa_procesal}}` - Etapa procesal actual

### Variables del Cliente
- `{{cliente_nombre}}` - Nombre del cliente
- `{{cliente_direccion}}` - Dirección del cliente
- `{{cliente_email}}` - Email del cliente
- `{{cliente_whatsapp}}` - WhatsApp del cliente

### Variables de Fecha
- `{{fecha_hoy}}` - Fecha actual (formato argentino)
- `{{fecha_hoy_largo}}` - Fecha actual en formato largo

### Variables del Abogado
- `{{abogado_nombre}}` - Nombre del abogado
- `{{matricula_nacion}}` - Matrícula nacional
- `{{matricula_pba}}` - Matrícula PBA
- `{{domicilio_procesal}}` - Domicilio procesal

## Ejemplo de Uso

Para crear un modelo, simplemente cree un archivo `.docx` con el contenido deseado y use las variables entre llaves dobles `{{variable}}`.

El sistema reemplazará automáticamente estas variables con los datos reales del caso seleccionado.
