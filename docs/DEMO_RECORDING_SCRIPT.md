# LastMile Platform — Script de Grabación del Demo Video

**Duración:** 2:30 - 3:00 minutos
**Resolución:** 1920x1080 @ 30fps
**Herramienta:** OBS Studio (gratis)

---

## Pre-Grabación

1. Abrir Chrome en **1920x1080**
2.最大化 la ventana
3. Cerrar notificaciones del sistema
4. Abrir OBS → Configurar grabación de pantalla
5. Tener la música de fondo lista (volumen bajo)

---

## Escena 1: Landing Page (0:00 - 0:20)

### Acción
1. Abrir `https://lastmile-platform.onrender.com/`
2. Esperar 2 segundos a que cargue
3. Scroll lento hacia abajo pasando por:
   - Hero con terminal mockup
   - 9 tarjetas de features
   - Sección "Cómo funciona" (4 pasos)
4. Click en "Comenzar ahora →"

### Voz en off
> "Last Mile Delivery es la plataforma SaaS que necesitas para gestionar tu negocio de entregas de última milla. Sin instalaciones, sin complicaciones."

---

## Escena 2: Registro (0:20 - 0:45)

### Acción
1. Llenar campo "Nombre de la empresa": `Paquetería Express GDL`
2. Llenar RFC: `PEG230303ABC`
3. Llenar Razón social: `Paquetería Express Guadalajara SA de CV`
4. Click "Siguiente"
5. Llenar nombre: `Carlos López`
6. Llenar email: `carlos@express.mx`
7. Llenar teléfono: `3312345678`
8. Llenar usuario: `carlos`
9. Llenar contraseña: `demo123`
10. Click "Siguiente"
11. Seleccionar plan "Pro ($2,499/mes)"
12. Click "Crear cuenta"

### Voz en off
> "Registra tu empresa en 60 segundos. Solo necesitas tu RFC y los datos de tu administrador."

---

## Escena 3: Login (0:45 - 0:55)

### Acción
1. En la pantalla de login, escribir: `admin`
2. Escribir contraseña: `admin123`
3. Click "Entrar"
4. Seleccionar tenant "Express Delivery MX" si aparece selector
5. Esperar a que cargue el dashboard

### Voz en off
> "Accede desde cualquier dispositivo, en cualquier momento."

---

## Escena 4: Dashboard (0:55 - 1:10)

### Acción
1. Dejar que carguen los KPIs
2. Hover sobre cada KPI: pedidos hoy, choferes activos, ingresos
3. Scroll hacia abajo para ver las gráficas
4. Mouse sobre la gráfica de barras (pedidos por semana)
5. Mouse sobre el pie chart (estados de pedidos)
6. Mouse sobre la tabla de top choferes

### Voz en off
> "Dashboard en tiempo real con todas tus métricas clave. Pedidos, ingresos, rendimiento de choferes, todo en un solo lugar."

---

## Escena 5: Crear Pedido (1:10 - 1:30)

### Acción
1. Click en "Pedidos" en el nav
2. Click "+ Nuevo Pedido"
3. Llenar cliente: `María García`
4. Llenar teléfono: `3312345678`
5. Llenar destino: `Av. Vallarta 2000, Col. Chapalita, Guadalajara`
6. Seleccionar bultos: `2`
7. Llenar costo: `350`
8. Seleccionar forma de pago: `TARJETA`
9. Click "Guardar"
10. Esperar confirmación "Pedido creado"

### Voz en off
> "Crea pedidos en segundos. El sistema calcula automáticamente el costo y asigna un número de seguimiento."

---

## Escena 6: Asignar Chofer (1:30 - 1:45)

### Acción
1. En la lista de pedidos, click en el pedido recién creado
2. Click "Asignar chofer"
3. Seleccionar: `Ana Martínez`
4. Seleccionar vehículo: `Nissan NP300`
5. Click "Confirmar"
6. Verificar que el estado cambió a "ASIGNADO"

### Voz en off
> "Asigna pedidos a tus choferes con un solo click. El chofer recibe la notificación en su teléfono."

---

## Escena 7: GPS Tracking (1:45 - 2:05)

### Acción
1. Click en "Operación" o "Mapa"
2. Esperar a que cargue el mapa (Leaflet)
3. **Punto clave:** Ver los puntos verdes de los choferes en el mapa
4. Click en un punto verde → Ver popup con nombre, velocidad, batería
5. Zoom in/out para mostrar la vista completa
6. Si hay datos GPS reales, mostrar la ruta recorrida
7. Si no hay GPS real, mostrar los markers de demo

### Voz en off
> "GPS en tiempo real para que sepas dónde está cada entrega. Velocidad, ubicación, batería, todo actualizado cada 30 segundos."

---

## Escena 8: Cambiar Estado (2:05 - 2:15)

### Acción
1. Volver a "Pedidos"
2. Seleccionar el pedido asignado
3. Click "Cambiar estado" → Seleccionar "EN_RUTA"
4. Verificar cambio de estado
5. Click "Cambiar estado" → Seleccionar "ENTREGADO"
6. Verificar que el pedido ahora dice "ENTREGADO"

### Voz en off
> "Actualiza el estado y notifica al cliente automáticamente. Sin llamadas, sin mensajes manuales."

---

## Escena 9: Panel Cliente (2:15 - 2:25)

### Acción
1. Abrir nueva pestaña → `https://lastmile-platform.onrender.com/login`
2. Login: `cliente1` / `clie123`
3. Ver el dashboard del cliente
4. Click en "Tracking" o "Mis pedidos"
5. Ver el pedido con su estado actual
6. Ver el mapa con la ubicación del chofer

### Voz en off
> "Tus clientes pueden rastrear sus pedidos en tiempo real. Mayor satisfacción, menos llamadas de '¿dónde está mi pedido?'."

---

## Escena 10: Facturación (2:25 - 2:35)

### Acción
1. Volver al admin
2. Click en "Facturación"
3. Ver lista de facturas CFDI 4.0
4. Click en una factura → Ver detalle
5. Click "Descargar PDF"

### Voz en off
> "Genera facturas electrónicas CFDI 4.0 automáticamente. Cumple con el SAT sin complicaciones."

---

## Escena 11: Cierre (2:35 - 2:45)

### Acción
1. Volver al dashboard
2. Mostrar las estadísticas del día
3. Zoom out en el mapa mostrando todos los choferes
4. Fade a negro

### Voz en off
> "Last Mile Delivery. Tu negocio de entregas, en la palma de tu mano."

### Texto en pantalla
```
Last Mile Delivery
lastmile-platform.onrender.com

Comienza tu prueba gratuita hoy
$999 MXN/mes
```

---

## Datos para Demo

| Credenciales | Usuario | Contraseña | Emp ID | Rol |
|---|---|---|---|---|
| Admin principal | admin | admin123 | 1 | admin |
| Admin tenant 2 | maria_admin | demo123 | 6 | admin |
| Chofer | chofer1 | chof123 | 1 | chofer |
| Cliente | cliente1 | clie123 | 1 | cliente |
| Operador | operador | oper123 | 1 | operacion |

## Notas Técnicas para Grabación

### GPS Tracking (Escena 7)
- El mapa usa **Leaflet.js** con tiles de CartoDB (dark/light)
- Los markers muestran posición real del GPS del chofer
- Auto-refresh cada 30 segundos
- Popup muestra: nombre, velocidad (km/h), batería, coordenadas
- Si no hay GPS real, muestra markers de demo en CDMX

### Para simular GPS real
1. Abrir panel del chofer en un celular real
2. Activar GPS
3. El sistema envía coordenadas cada 30 segundos
4. El mapa de operaciones las muestra en tiempo real

### Música sugerida
- Epidemic Sound: "Tech Corporate" o "Innovation"
- Artlist: "Upbeat Technology"
- YouTube Audio Library: "Corporate upbeat"

### Post-Producción
- Agregar subtítulos en español
- Agregar logo watermark
- Fade in/out entre escenas
- Agregar música de fondo (volumen -20dB)
- Exportar en 1080p, H.264
