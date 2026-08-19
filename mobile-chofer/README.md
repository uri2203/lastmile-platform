# Last Mile Chofer (app nativa, Expo)

App nativa para el rol **chofer** de Last Mile Delivery. Consume la misma API
que el resto de la plataforma (`api/server.py`) — no hay backend propio.

## Que incluye (v1)
- Login con las mismas cuentas de rol `chofer` que ya usa el sitio web
- Ver y actualizar mis entregas asignadas (`ENTREGADO` / `NO_ENTREGADO`)
- Foto de comprobante de entrega (camara del dispositivo)
- GPS en tiempo real en segundo plano (`POST /api/tracking`)
- Cobro en efectivo (COD) al entregar
- Notificaciones push (token de Expo, registrado en `NOTIF_DISPOSITIVOS` con `plataforma='EXPO'`)

## Requisitos previos
- Node.js 18+
- App **Expo Go** en tu celular (App Store / Play Store), para probar sin compilar nada
- Una cuenta con rol `chofer` **vinculada** a un perfil de chofer (ver mas abajo)

## Correr en modo desarrollo
```bash
cd mobile-chofer
npm install
npx expo start
```
Escaneas el QR con la app **Expo Go** desde tu celular. Por defecto apunta a
`https://lastmile-platform.onrender.com` (definido en `app.json` → `extra.apiBaseUrl`).
Para apuntar a un backend local, cambialo ahi o exportalo como variable de entorno
y leelo en `src/api.js`.

## Paso obligatorio antes de poder usarla: vincular el chofer
Los perfiles de chofer (tabla `CHOFERES`) no estaban vinculados a ninguna cuenta
de login hasta este cambio. Un admin/operacion tiene que vincular cada chofer
una sola vez:

```
PUT /api/choferes/<CHO_ID>/link-usuario
Authorization: Bearer <token de admin/operacion>
Body: { "usu_id": <USU_ID del usuario con rol chofer> }
```

Sin este paso, la app muestra "Sin perfil de chofer vinculado" al iniciar sesion
(no rompe, pero no hay datos que mostrar).

## Compilar para dispositivo real / tiendas (EAS)
Este proyecto no incluye una build nativa compilada -- para generar un `.apk`/`.ipa`
instalable hace falta usar [EAS Build](https://docs.expo.dev/build/introduction/)
de Expo (requiere cuenta gratuita en expo.dev):

```bash
npm install -g eas-cli
eas login
eas build:configure
eas build --platform android --profile preview   # genera un APK para probar
eas build --platform ios --profile preview        # requiere cuenta de Apple Developer
```

## Limitaciones conocidas de este v1
- La foto de comprobante se guarda como referencia local (`foto_local:<uri>`) en
  `ENT_EVIDENCIA` -- **no se sube a ningun storage todavia**. Para verla desde el
  panel web/admin hace falta un paso de subida de archivos (S3, Cloudinary, etc.)
  que no estaba definido en el alcance de esta primera version.
- Sin build de EAS, la app solo corre dentro de Expo Go (util para probar, no
  para publicar en las tiendas).
